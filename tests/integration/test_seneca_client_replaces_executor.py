from unittest import TestCase
from contracting.stdlib.bridge.time import Datetime
from contracting.client import ContractingClient
import os

class TestSenecaClientReplacesExecutor(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.raw_driver.flush_full()

        submission_path = os.path.join(os.path.dirname(__file__), "test_contracts", "submission.s.py")

        with open(submission_path) as f:
            contract = f.read()

        self.c.raw_driver.set_contract(name='submission', code=contract,)

        self.c.raw_driver.commit()

        submission = self.c.get_contract('submission')

        # submit erc20 clone
        erc20_clone_path = os.path.join(os.path.dirname(__file__), "test_contracts", "erc20_clone.s.py")

        with open(erc20_clone_path) as f:
            code = f.read()
            self.c.submit(code, name='con_erc20_clone')

        atomic_swaps_path = os.path.join(os.path.dirname(__file__), "test_contracts", "atomic_swaps.s.py")

        with open(atomic_swaps_path) as f:
            code = f.read()
            self.c.submit(code, name='con_atomic_swaps')

        self.erc20_clone = self.c.get_contract('con_erc20_clone')
        self.atomic_swaps = self.c.get_contract('con_atomic_swaps')

    def tearDown(self):
        self.c.raw_driver.flush_full()

    def test_initiate_not_enough_approved(self):
        self.erc20_clone.approve(amount=1000000, to='con_atomic_swaps')

        with self.assertRaises(AssertionError):
            self.atomic_swaps.initiate(participant='raghu',
                                       expiration=Datetime(2020, 1, 1),
                                       hashlock='eaf48a02d3a4bb3aeb0ecb337f6efb026ee0bbc460652510cff929de78935514',
                                       amount=5000000)

    def test_initiate_transfers_coins_correctly(self):
        self.erc20_clone.approve(amount=1000000, to='con_atomic_swaps')

        self.atomic_swaps.initiate(participant='raghu',
                                   expiration=Datetime(2020, 1, 1),
                                   hashlock='eaf48a02d3a4bb3aeb0ecb337f6efb026ee0bbc460652510cff929de78935514',
                                   amount=5)

        atomic_swaps = self.erc20_clone.balance_of(account='con_atomic_swaps')
        stu_bal = self.erc20_clone.balance_of(account='stu')
        stu_as = self.erc20_clone.allowance(owner='stu', spender='con_atomic_swaps')

        self.assertEqual(atomic_swaps, 5)
        self.assertEqual(stu_bal, 999995)
        self.assertEqual(stu_as, 999995)

    def test_initiate_writes_to_correct_key_and_properly(self):
        self.erc20_clone.approve(amount=1000000, to='con_atomic_swaps')

        self.atomic_swaps.initiate(participant='raghu',
                                   expiration=Datetime(2020, 1, 1),
                                   hashlock='eaf48a02d3a4bb3aeb0ecb337f6efb026ee0bbc460652510cff929de78935514',
                                   amount=5)

        key = 'con_atomic_swaps.swaps:raghu:eaf48a02d3a4bb3aeb0ecb337f6efb026ee0bbc460652510cff929de78935514'

        expiration, amount = self.c.raw_driver.get(key)
        self.assertEqual(expiration, Datetime(2020, 1, 1))
        self.assertEqual(amount, 5)

    def test_redeem_on_wrong_secret_fails(self):
        self.erc20_clone.approve(amount=1000000, to='con_atomic_swaps')

        self.atomic_swaps.initiate(participant='raghu',
                                   expiration=Datetime(2020, 1, 1),
                                   hashlock='eaf48a02d3a4bb3aeb0ecb337f6efb026ee0bbc460652510cff929de78935514',
                                   amount=5)

        with self.assertRaises(AssertionError):
            self.atomic_swaps.redeem(signer='raghu', secret='00')

    def test_redeem_on_wrong_sender_fails(self):
        self.erc20_clone.approve(amount=1000000, to='con_atomic_swaps')
        self.atomic_swaps.initiate(participant='raghu',
                                   expiration=Datetime(2020, 1, 1),
                                   hashlock='eaf48a02d3a4bb3aeb0ecb337f6efb026ee0bbc460652510cff929de78935514',
                                   amount=5)

        with self.assertRaises(AssertionError):
            self.atomic_swaps.redeem(secret='842b65a7d48e3a3c3f0e9d37eaced0b2')

    def test_past_expiration_fails(self):
        self.erc20_clone.approve(amount=1000000, to='con_atomic_swaps')

        self.atomic_swaps.initiate(participant='raghu',
                                   expiration=Datetime(2020, 1, 1),
                                   hashlock='eaf48a02d3a4bb3aeb0ecb337f6efb026ee0bbc460652510cff929de78935514',
                                   amount=5)

        environment = {'now': Datetime(2021, 1, 1)}

        with self.assertRaises(AssertionError):
            self.atomic_swaps.redeem(secret='842b65a7d48e3a3c3f0e9d37eaced0b2',
                                     signer='raghu',
                                     environment=environment)

    def test_successful_redeem_transfers_coins_correctly(self):
        self.erc20_clone.approve(amount=1000000, to='con_atomic_swaps')

        self.atomic_swaps.initiate(participant='raghu',
                                   expiration=Datetime(2020, 1, 1),
                                   hashlock='eaf48a02d3a4bb3aeb0ecb337f6efb026ee0bbc460652510cff929de78935514',
                                   amount=5)

        environment = {'now': Datetime(2019, 1, 1)}

        self.atomic_swaps.redeem(secret='842b65a7d48e3a3c3f0e9d37eaced0b2',
                                 signer='raghu',
                                 environment=environment)

        atomic_swaps = self.erc20_clone.balance_of(account='con_atomic_swaps')
        raghu = self.erc20_clone.balance_of(account='raghu')

        self.assertEqual(raghu, 5)
        self.assertEqual(atomic_swaps, 0)

    def test_successful_redeem_deletes_entry(self):
        self.erc20_clone.approve(amount=1000000, to='con_atomic_swaps')

        self.atomic_swaps.initiate(participant='raghu',
                                   expiration=Datetime(2020, 1, 1),
                                   hashlock='eaf48a02d3a4bb3aeb0ecb337f6efb026ee0bbc460652510cff929de78935514',
                                   amount=5)

        environment = {'now': Datetime(2019, 1, 1)}

        self.atomic_swaps.redeem(secret='842b65a7d48e3a3c3f0e9d37eaced0b2',
                                 signer='raghu',
                                 environment=environment)

        key = 'atomic_swaps.swaps:raghu:eaf48a02d3a4bb3aeb0ecb337f6efb026ee0bbc460652510cff929de78935514'
        v = self.c.raw_driver.get(key)

        self.assertEqual(v, None)

    def test_refund_works(self):
        self.erc20_clone.approve(amount=1000000, to='con_atomic_swaps')

        self.atomic_swaps.initiate(participant='raghu',
                                   expiration=Datetime(2020, 1, 1),
                                   hashlock='eaf48a02d3a4bb3aeb0ecb337f6efb026ee0bbc460652510cff929de78935514',
                                   amount=5)

        environment = {'now': Datetime(2021, 1, 1)}

        self.atomic_swaps.refund(participant='raghu', secret='842b65a7d48e3a3c3f0e9d37eaced0b2',
                                 environment=environment)

        atomic_swaps = self.erc20_clone.balance_of(account='con_atomic_swaps')
        stu = self.erc20_clone.balance_of(account='stu')

        self.assertEqual(stu, 1000000)
        self.assertEqual(atomic_swaps, 0)

    def test_refund_too_early_fails(self):
        self.erc20_clone.approve(amount=1000000, to='con_atomic_swaps')

        self.atomic_swaps.initiate(participant='raghu',
                                   expiration=Datetime(2020, 1, 1),
                                   hashlock='eaf48a02d3a4bb3aeb0ecb337f6efb026ee0bbc460652510cff929de78935514',
                                   amount=5)

        environment = {'now': Datetime(2019, 1, 1)}

        with self.assertRaises(AssertionError):
            self.atomic_swaps.refund(participant='raghu', secret='842b65a7d48e3a3c3f0e9d37eaced0b2',
                                    environment=environment)

    def test_refund_participant_is_signer_fails(self):
        self.erc20_clone.approve(amount=1000000, to='con_atomic_swaps')

        self.atomic_swaps.initiate(participant='raghu',
                                   expiration=Datetime(2020, 1, 1),
                                   hashlock='eaf48a02d3a4bb3aeb0ecb337f6efb026ee0bbc460652510cff929de78935514',
                                   amount=5)

        environment = {'now': Datetime(2021, 1, 1)}

        with self.assertRaises(AssertionError):
            self.atomic_swaps.refund(participant='raghu', secret='842b65a7d48e3a3c3f0e9d37eaced0b2',
                                     environment=environment,
                                     signer='raghu')

    def test_refund_fails_with_wrong_secret(self):
        self.erc20_clone.approve(amount=1000000, to='con_atomic_swaps')

        self.atomic_swaps.initiate(participant='raghu',
                                   expiration=Datetime(2020, 1, 1),
                                   hashlock='eaf48a02d3a4bb3aeb0ecb337f6efb026ee0bbc460652510cff929de78935514',
                                   amount=5)

        environment = {'now': Datetime(2021, 1, 1)}

        with self.assertRaises(AssertionError):
            self.atomic_swaps.refund(participant='raghu', secret='00',
                                     environment=environment,
                                     )

    def test_refund_resets_swaps(self):
        self.erc20_clone.approve(amount=1000000, to='con_atomic_swaps')

        self.atomic_swaps.initiate(participant='raghu',
                                   expiration=Datetime(2020, 1, 1),
                                   hashlock='eaf48a02d3a4bb3aeb0ecb337f6efb026ee0bbc460652510cff929de78935514',
                                   amount=5)

        environment = {'now': Datetime(2021, 1, 1)}

        self.atomic_swaps.refund(participant='raghu', secret='842b65a7d48e3a3c3f0e9d37eaced0b2',
                                 environment=environment)

        key = 'atomic_swaps.swaps:raghu:eaf48a02d3a4bb3aeb0ecb337f6efb026ee0bbc460652510cff929de78935514'
        v = self.c.raw_driver.get(key)

        self.assertEqual(v, None)
