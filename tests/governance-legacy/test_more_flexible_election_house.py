from unittest import TestCase
from contracting.client import ContractingClient

def election_house():
    # Convenience
    I = importlib

    # Main state datum
    contract_to_policy = Hash()
    policy_to_contract = Hash()

    # Policy interface
    policy_interface = [
        I.Func('vote', args=('vk', 'obj')),
        I.Func('current_value')
    ]

    @export
    def register_policy(policy, contract):
        if policy_to_contract[policy] is None and contract_to_policy[contract] is None:
            # Attempt to import the contract to make sure it is already submitted
            p = I.import_module(contract)

            # Assert ownership is election_house and interface is correct
            assert I.owner_of(p) == ctx.this, \
                'Election house must control the policy contract!'

            assert I.enforce_interface(p, policy_interface), \
                'Policy contract does not follow the correct interface'

            policy_to_contract[policy] = contract
            contract_to_policy[contract] = policy
        else:
            raise Exception('Policy already registered')

    @export
    def current_value_for_policy(policy: str):
        contract = policy_to_contract[policy]
        assert contract is not None, 'Invalid policy.'

        p = I.import_module(contract)

        return p.current_value()

    @export
    def vote(policy, value):
        # Verify policy has been registered
        contract_name = policy_to_contract[policy]
        assert contract_name is not None, 'Invalid policy.'

        p = I.import_module(contract_name)

        p.vote(vk=ctx.caller, obj=value)


def test_policy():
    value = Variable()
    @construct
    def seed():
        value.set('1234')

    @export
    def current_value():
        return value.get()

    @export
    def vote(vk, obj):
        value.set(obj)

    def another_func():
        print('this shouldnt matter')


def bad_interface():
    @export
    def current_value():
        return 0


class TestBetterElectionHouse(TestCase):
    def setUp(self):
        self.client = ContractingClient()
        self.client.flush()
        self.client.submit(election_house, name='election_house2')

        self.election_house = self.client.get_contract(name='election_house2')

    def tearDown(self):
        self.client.flush()

    def test_register_doesnt_fail(self):
        self.client.submit(test_policy, owner='election_house2')
        self.election_house.register_policy(policy='testing', contract='test_policy')

    def test_register_without_owner_fails(self):
        self.client.submit(test_policy)
        with self.assertRaises(AssertionError):
            self.election_house.register_policy(policy='testing', contract='test_policy')

    def test_register_same_contract_twice_fails(self):
        self.client.submit(test_policy, owner='election_house2')
        self.election_house.register_policy(policy='testing', contract='test_policy')

        with self.assertRaises(Exception):
            self.election_house.register_policy(policy='testing', contract='test_policy')

    def test_register_contract_without_entire_interface_fails(self):
        self.client.submit(test_policy, owner='election_house2')

        with self.assertRaises(Exception):
            self.election_house.register_policy(policy='testing', contract='bad_interface')

    def test_register_same_contract_under_another_name_fails(self):
        self.client.submit(test_policy, owner='election_house2')
        self.election_house.register_policy(policy='testing', contract='test_policy')

        with self.assertRaises(Exception):
            self.election_house.register_policy(policy='testing2', contract='test_policy')

    def test_current_value_for_policy_returns_correct_value(self):
        self.client.submit(test_policy, owner='election_house2')
        self.election_house.register_policy(policy='testing', contract='test_policy')

        res = self.election_house.current_value_for_policy(policy='testing')

        self.assertEqual(res, '1234')

    def test_current_value_for_non_existant_policy_fails(self):
        self.client.submit(test_policy, owner='election_house2')

        with self.assertRaises(AssertionError):
            self.election_house.current_value_for_policy(policy='testing')

    def test_vote_delegate_calls_policy(self):
        self.client.submit(test_policy, owner='election_house2')
        self.election_house.register_policy(policy='testing', contract='test_policy')
        self.election_house.vote(policy='testing', value='5678')

    def test_full_vote_flow_works(self):
        self.client.submit(test_policy, owner='election_house2')
        self.election_house.register_policy(policy='testing', contract='test_policy')
        self.election_house.vote(policy='testing', value='5678')

        res = self.election_house.current_value_for_policy(policy='testing')

        self.assertEqual(res, '5678')