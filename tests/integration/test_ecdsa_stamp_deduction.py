import unittest
import os
from contracting.client import ContractingClient
from contracting.execution import runtime


class TestECDSAStampDeduction(unittest.TestCase):
    def setUp(self):
        self.client = ContractingClient()
        self.client.flush()
        
        # Submit the currency contract first (needed for stamp deduction)
        currency_contract = '''
balances = Hash()

@construct
def seed():
    balances['stu'] = 1000000
    balances['test_user'] = 1000000
    balances['sys'] = 1000000

@export
def transfer(amount: int, to: str):
    sender = ctx.signer
    assert balances[sender] >= amount, 'Not enough coins to send!'

    balances[sender] -= amount

    if balances[to] is None:
        balances[to] = amount
    else:
        balances[to] += amount

@export
def balance(account: str):
    return balances[account]
'''
        
        self.client.submit(currency_contract, name='currency')
        
        # Create a test contract that uses ecdsa_verify
        ecdsa_contract = '''
@export
def test_ecdsa_verify(public_key: str, message: str, signature: str, curve: str = 'secp256k1'):
    return crypto.ecdsa_verify(public_key, message, signature, curve)

@export
def test_multiple_verifications(public_key: str, message: str, signature: str, count: int = 3):
    results = []
    for i in range(count):
        result = crypto.ecdsa_verify(public_key, message, signature, 'secp256k1')
        results.append(result)
    return results

@export
def test_mixed_operations(public_key: str, message: str, signature: str):
    # Test mixing ECDSA with other operations
    result1 = crypto.ecdsa_verify(public_key, message, signature, 'secp256k1')
    
    # Some other operations that consume stamps
    x = 0
    for i in range(100):
        x += i
    
    result2 = crypto.ecdsa_verify(public_key, message, signature, 'secp256r1')
    
    return {
        'result1': result1,
        'result2': result2,
        'sum': x
    }
'''
        
        self.client.submit(ecdsa_contract, name='ecdsa_test')
        self.ecdsa_contract = self.client.get_contract('ecdsa_test')

    def tearDown(self):
        self.client.flush()

    def test_ecdsa_verify_deducts_stamps_based_on_message_size(self):
        """Test that ECDSA verification deducts stamps based on message size (3 base + 1 per KB)"""
        # Enable metering
        self.client.executor.metering = True
        
        # Test data (will fail verification but should still deduct stamps)
        public_key = "04a34b99f22c790c4e36b2b3c2c35a36db06226e41c692fc82b8b56ac1c540c5bd5b8dec5235a0fa8722476c7709c02559e3aa73aa03918ba2d492eea75abea235"
        signature = "3045022100f51d6cc21b4c7e4c1c4e1e6c7e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e022033a1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c"
        
        # Test cases with different message sizes
        test_cases = [
            ("small message", 4),        # < 1KB: 3 + 1 = 4 stamps minimum
            ("x" * 1024, 4),            # Exactly 1KB: 3 + 1 = 4 stamps minimum
            ("x" * 1025, 5),            # 1KB + 1 byte: 3 + 2 = 5 stamps minimum (rounds up)
        ]
        
        for message, min_expected_stamps in test_cases:
            with self.subTest(message_size=len(message)):
                # Execute ECDSA verification
                result = self.client.executor.execute(
                    sender='test_user',
                    contract_name='ecdsa_test',
                    function_name='test_ecdsa_verify',
                    kwargs={
                        'public_key': public_key,
                        'message': message,
                        'signature': signature,
                        'curve': 'secp256k1'
                    },
                    stamps=10000,
                    auto_commit=True
                )
                
                # Should have used at least the expected stamps for ECDSA verification (plus overhead)
                stamps_used = result['stamps_used']
                print(f"Stamps used for {len(message)} byte message: {stamps_used}")
                
                # The minimum should be the expected stamps for ECDSA + some overhead for contract execution
                self.assertGreaterEqual(stamps_used, min_expected_stamps, 
                                       f"Expected at least {min_expected_stamps} stamps for {len(message)} byte message, but used {stamps_used}")
                
                # But shouldn't be too high (sanity check)
                self.assertLess(stamps_used, 100, 
                               f"Used {stamps_used} stamps, which seems too high for a simple verification")
        
        # Disable metering
        self.client.executor.metering = False

    def test_multiple_ecdsa_verifications_scale_linearly(self):
        """Test that multiple ECDSA verifications scale linearly in stamp cost"""
        # Enable metering
        self.client.executor.metering = True
        
        # Test data
        public_key = "04a34b99f22c790c4e36b2b3c2c35a36db06226e41c692fc82b8b56ac1c540c5bd5b8dec5235a0fa8722476c7709c02559e3aa73aa03918ba2d492eea75abea235"
        message = "test message"
        signature = "3045022100f51d6cc21b4c7e4c1c4e1e6c7e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e022033a1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c"
        
        # Test with different numbers of verifications
        verification_counts = [1, 3, 5]
        stamps_used_list = []
        
        for count in verification_counts:
            result = self.client.executor.execute(
                sender='test_user',
                contract_name='ecdsa_test',
                function_name='test_multiple_verifications',
                kwargs={
                    'public_key': public_key,
                    'message': message,
                    'signature': signature,
                    'count': count
                },
                stamps=50000,
                auto_commit=True
            )
            
            stamps_used = result['stamps_used']
            stamps_used_list.append(stamps_used)
            print(f"Stamps used for {count} ECDSA verifications: {stamps_used}")
        
        # Check that stamps scale roughly linearly
        # Each additional verification should cost approximately 3 more stamps
        stamps_1 = stamps_used_list[0]
        stamps_3 = stamps_used_list[1]
        stamps_5 = stamps_used_list[2]
        # The difference between 3 and 1 verifications should be approximately 2*3 = 6 stamps
        diff_3_1 = stamps_3 - stamps_1
        print(f"Difference between 3 and 1 verifications: {diff_3_1} stamps")
        
        # The difference between 5 and 3 verifications should be approximately 2*3 = 6 stamps
        diff_5_3 = stamps_5 - stamps_3
        print(f"Difference between 5 and 3 verifications: {diff_5_3} stamps")
        
        # Both differences should be roughly similar (within some tolerance for overhead)
        # Allow 50% tolerance for execution overhead
        self.assertAlmostEqual(diff_3_1, diff_5_3, delta=max(3, diff_3_1 * 0.5),
                              msg=f"Stamp costs don't scale linearly: {diff_3_1} vs {diff_5_3}")
        
        # Each difference should be at least 6 stamps (2 verifications * 3 stamps each)
        self.assertGreaterEqual(diff_3_1, 6, 
                               f"Expected at least 6 stamps difference, got {diff_3_1}")
        self.assertGreaterEqual(diff_5_3, 6, 
                               f"Expected at least 6 stamps difference, got {diff_5_3}")
        
        # Disable metering
        self.client.executor.metering = False

    def test_ecdsa_stamps_vs_baseline(self):
        """Test ECDSA stamp cost compared to baseline contract execution"""
        # Enable metering
        self.client.executor.metering = True
        
        # Create a baseline contract with no ECDSA operations
        baseline_contract = '''
@export
def baseline_operation():
    # Simple operation without ECDSA
    x = 0
    for i in range(100):
        x += i
    return x
'''
        
        self.client.submit(baseline_contract, name='baseline_test')
        baseline_contract_obj = self.client.get_contract('baseline_test')
        
        # Execute baseline operation
        baseline_result = self.client.executor.execute(
            sender='test_user',
            contract_name='baseline_test',
            function_name='baseline_operation',
            kwargs={},
            stamps=10000,
            auto_commit=True
        )
        
        baseline_stamps = baseline_result['stamps_used']
        print(f"Baseline stamps (no ECDSA): {baseline_stamps}")
        
        # Execute mixed operation (baseline + 2 ECDSA verifications)
        public_key = "04a34b99f22c790c4e36b2b3c2c35a36db06226e41c692fc82b8b56ac1c540c5bd5b8dec5235a0fa8722476c7709c02559e3aa73aa03918ba2d492eea75abea235"
        message = "test message"
        signature = "3045022100f51d6cc21b4c7e4c1c4e1e6c7e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e022033a1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c"
        
        mixed_result = self.client.executor.execute(
            sender='test_user',
            contract_name='ecdsa_test',
            function_name='test_mixed_operations',
            kwargs={
                'public_key': public_key,
                'message': message,
                'signature': signature
            },
            stamps=20000,
            auto_commit=True
        )
        
        mixed_stamps = mixed_result['stamps_used']
        print(f"Mixed operation stamps (baseline + 2 ECDSA): {mixed_stamps}")
        
        # The difference should be approximately 6 stamps (2 ECDSA verifications * 3 stamps each)
        ecdsa_overhead = mixed_stamps - baseline_stamps
        print(f"ECDSA overhead: {ecdsa_overhead} stamps")
        
        # Should be at least 6 stamps for 2 ECDSA verifications
        self.assertGreaterEqual(ecdsa_overhead, 6, 
                               f"Expected at least 6 stamps overhead for 2 ECDSA verifications, got {ecdsa_overhead}")
        
        # But shouldn't be too much more (allowing for some execution overhead)
        self.assertLess(ecdsa_overhead, 50, 
                       f"ECDSA overhead of {ecdsa_overhead} stamps seems too high")
        
        # Disable metering
        self.client.executor.metering = False

    def test_ecdsa_with_metering_disabled(self):
        """Test that no stamps are deducted when metering is disabled"""
        # Disable metering
        self.client.executor.metering = False
        
        # Test data
        public_key = "04a34b99f22c790c4e36b2b3c2c35a36db06226e41c692fc82b8b56ac1c540c5bd5b8dec5235a0fa8722476c7709c02559e3aa73aa03918ba2d492eea75abea235"
        message = "test message"
        signature = "3045022100f51d6cc21b4c7e4c1c4e1e6c7e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e022033a1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c"
        
        # Execute ECDSA verification without metering
        result = self.client.executor.execute(
            sender='test_user',
            contract_name='ecdsa_test',
            function_name='test_ecdsa_verify',
            kwargs={
                'public_key': public_key,
                'message': message,
                'signature': signature,
                'curve': 'secp256k1'
            },
            stamps=10000,
            auto_commit=True
        )
        
        # When metering is disabled, stamps_used should be minimal (just the base overhead)
        stamps_used = result['stamps_used']
        print(f"Stamps used with metering disabled: {stamps_used}")
                
        # Should be very low since metering is disabled
        self.assertLess(stamps_used, 10, 
                       f"Expected minimal stamps when metering disabled, got {stamps_used}")

    def test_ecdsa_different_curves_same_cost(self):
        """Test that different curves have the same stamp cost"""
        # Enable metering
        self.client.executor.metering = True
        
        # Test data
        public_key = "04a34b99f22c790c4e36b2b3c2c35a36db06226e41c692fc82b8b56ac1c540c5bd5b8dec5235a0fa8722476c7709c02559e3aa73aa03918ba2d492eea75abea235"
        message = "test message"
        signature = "3045022100f51d6cc21b4c7e4c1c4e1e6c7e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e022033a1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c4e1c"
        
        curves = ['secp256k1', 'secp256r1', 'secp384r1', 'secp521r1']
        stamps_by_curve = {}
        
        for curve in curves:
            result = self.client.executor.execute(
                sender='test_user',
                contract_name='ecdsa_test',
                function_name='test_ecdsa_verify',
                kwargs={
                    'public_key': public_key,
                    'message': message,
                    'signature': signature,
                    'curve': curve
                },
                stamps=10000,
                auto_commit=True
            )
            
            stamps_used = result['stamps_used']
            stamps_by_curve[curve] = stamps_used
            print(f"Stamps used for {curve}: {stamps_used}")
        
        # All curves should use approximately the same number of stamps
        # (within a small tolerance for any curve-specific overhead)
        base_stamps = stamps_by_curve['secp256k1']
        
        for curve, stamps in stamps_by_curve.items():
            self.assertAlmostEqual(stamps, base_stamps, delta=5,
                                  msg=f"Curve {curve} used {stamps} stamps vs {base_stamps} for secp256k1")
        # Disable metering
        self.client.executor.metering = False


if __name__ == '__main__':
    unittest.main() 