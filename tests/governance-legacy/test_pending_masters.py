from unittest import TestCase
from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Timedelta, DAYS, WEEKS, Datetime
from datetime import datetime as dt, timedelta as td


def pending_masters():
    import currency
    import election_house

    S = Hash()
    Q = Variable()
    STAMP_COST = 20_000

    @construct
    def seed():
        # Set as empty list
        Q.set({})

    @export
    def register():
        # Make sure someone is already staked
        assert not S['registered', ctx.signer], 'Already registered.'

        S['registered', ctx.signer] = True

        q = Q.get()
        q[ctx.signer] = 0
        Q.set(q)

    @export
    def vote(address):
        assert S['registered', address]

        # Determine if caller can vote
        v = S['last_voted', ctx.signer]
        assert v is None or now - v > datetime.DAYS * 1, 'Voting again too soon.'

        # Deduct small vote fee
        vote_cost = STAMP_COST / election_house.current_value_for_policy('stamp_cost')
        currency.transfer_from(vote_cost, 'blackhole', ctx.signer)

        # Update last voted variable
        S['last_voted', ctx.signer] = now

        # Update vote dict
        q = Q.get()
        q[address] += 1
        Q.set(q)

    @export
    def top_masternode():
        q = Q.get()

        if len(q) == 0:
            return None

        top = sorted(q.items(), key=lambda x: x[1], reverse=True)

        return top[0][0]

    @export
    def pop_top():
        assert ctx.caller == 'masternodes', 'Wrong smart contract caller.'

        top = top_masternode()

        q = Q.get()
        del q[top]
        Q.set(q)


class TestPendingMasters(TestCase):
    def setUp(self):
        self.client = ContractingClient()

        f = open('./contracts/currency.s.py')
        self.client.submit(f.read(), 'currency')
        f.close()

        f = open('./contracts/election_house.s.py')
        self.client.submit(f.read(), 'election_house')
        f.close()

        f = open('./contracts/stamp_cost.s.py')
        self.client.submit(f.read(), 'stamp_cost', owner='election_house', constructor_args={'initial_rate': 20_000})
        f.close()

        f = open('./contracts/masternodes.s.py')
        self.client.submit(f.read(), 'masternodes', owner='election_house', constructor_args={'initial_masternodes':
                                                                                              ['stu', 'raghu'],
                                                                                              'initial_open_seats': 0})
        f.close()

        self.client.submit(pending_masters)

        self.pending_masters = self.client.get_contract(name='pending_masters')
        self.currency = self.client.get_contract(name='currency')

        self.stamp_cost = self.client.get_contract(name='stamp_cost')
        self.election_house = self.client.get_contract(name='election_house')
        self.election_house.register_policy(contract='stamp_cost')

    def tearDown(self):
        self.client.flush()

    def test_register(self):
        self.pending_masters.register(signer='stu')
        q = self.pending_masters.Q.get()

        self.assertEqual(q['stu'], 0)

    def test_register_twice_throws_assertion_error(self):
        self.pending_masters.register(signer='stu')

        with self.assertRaises(AssertionError):
            self.pending_masters.register(signer='stu')

    def test_vote_for_someone_not_registered_throws_assertion_error(self):
        with self.assertRaises(AssertionError):
            self.pending_masters.vote(address='stu')

    def test_vote_for_someone_registered_deducts_tau_and_adds_vote(self):
        self.pending_masters.register(signer='joe')

        self.currency.approve(signer='stu', amount=10_000, to='pending_masters')

        env = {'now': Datetime._from_datetime(dt.today())}

        self.pending_masters.vote(signer='stu', address='joe', environment=env)

        self.assertEqual(self.currency.balances['stu'], 999999)
        self.assertEqual(self.pending_masters.Q.get()['joe'], 1)
        self.assertEqual(self.currency.balances['blackhole'], 1)
        self.assertEqual(self.pending_masters.S['last_voted', 'stu'], env['now'])

    def test_voting_again_too_soon_throws_assertion_error(self):
        self.pending_masters.register(signer='joe')

        self.currency.approve(signer='stu', amount=10_000, to='pending_masters')

        env = {'now': Datetime._from_datetime(dt.today())}

        self.pending_masters.vote(signer='stu', address='joe', environment=env)

        with self.assertRaises(AssertionError):
            self.pending_masters.vote(signer='stu', address='joe', environment=env)

    def test_voting_again_after_waiting_one_day_works(self):
        self.pending_masters.register(signer='joe')

        self.currency.approve(signer='stu', amount=10_000, to='pending_masters')

        env = {'now': Datetime._from_datetime(dt.today())}

        self.pending_masters.vote(signer='stu', address='joe', environment=env)

        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.pending_masters.vote(signer='stu', address='joe', environment=env)

        self.assertEqual(self.currency.balances['stu'], 999998)
        self.assertEqual(self.pending_masters.Q.get()['joe'], 2)
        self.assertEqual(self.currency.balances['blackhole'], 2)
        self.assertEqual(self.pending_masters.S['last_voted', 'stu'], env['now'])

