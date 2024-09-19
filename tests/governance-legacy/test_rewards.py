from unittest import TestCase
from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import WEEKS, DAYS, Datetime
from datetime import datetime as dt, timedelta as td


def rewards():
    import election_house

    S = Hash()

    @construct
    def seed(initial_split: list = [0.44, 0.44, 0.01, 0.01, 0.1],
             master_contract='masternodes',
             delegate_contract='delegates',
             election_max_length=datetime.DAYS * 1):

        S['value'] = initial_split
        S['master_contract'] = master_contract
        S['delegate_contract'] = delegate_contract
        S['election_max_length'] = election_max_length

        S['vote_count'] = 0

        reset_current_votes()

    def reset_current_votes():
        S['current_votes', 'masternodes'] = 0
        S['current_votes', 'delegates'] = 0
        S['current_votes', 'blackhole'] = 0
        S['current_votes', 'foundation'] = 0
        S['current_votes', 'developer'] = 0

    @export
    def current_value():
        return S['value']

    @export
    def vote(vk: str, obj: list):
        # Start a new election
        if S['election_start'] is None:
            total_nodes = len(election_house.current_value_for_policy(S['master_contract'])) + \
                          len(election_house.current_value_for_policy(S['delegate_contract']))

            S['vote_count'] = 0
            S['min_votes_required'] = (total_nodes * 2 // 3) + 1

            # Set start to now
            S['election_start'] = now
            S.clear('has_voted')

            reset_current_votes()

            tally_vote(vk, obj)

        else:
            tally_vote(vk, obj)

            if election_is_over():
                update_value()

                # Reset everything
                S['election_start'] = None

    def update_value():
        # Calculate ratio of votes
        masternode_votes = S['current_votes', 'masternodes'] or 1
        delegate_votes = S['current_votes', 'delegates'] or 1
        blackhole_votes = S['current_votes', 'blackhole'] or 1
        foundation_votes = S['current_votes', 'foundation'] or 1
        developer_votes = S['current_votes', 'developer'] or 1

        total_votes = masternode_votes + delegate_votes + blackhole_votes + foundation_votes + developer_votes

        # Do the same for each party before dividing
        mn = masternode_votes / total_votes
        dl = delegate_votes / total_votes
        bh = blackhole_votes / total_votes
        fd = foundation_votes / total_votes
        dv = developer_votes / total_votes

        # Set the new value
        S['value'] = [mn, dl, bh, fd, dv]

    def election_is_over():
        return S['vote_count'] >= S['min_votes_required'] or \
               now - S['election_start'] >= S['election_max_length']

    def tally_vote(vk: str, obj: list):
        validate_vote(vk, obj)

        a, b, c, d, e = obj

        S['current_votes', 'masternodes'] += a
        S['current_votes', 'delegates'] += b
        S['current_votes', 'blackhole'] += c
        S['current_votes', 'foundation'] += d
        S['current_votes', 'developer'] += e

        S['has_voted', vk] = True
        S['vote_count'] += 1

    def validate_vote(vk: str, obj: list):
        assert vk in election_house.current_value_for_policy(S['master_contract']) or \
               vk in election_house.current_value_for_policy(S['delegate_contract']), 'Not allowed to vote!'

        assert type(obj) == list, 'Pass a list!'
        assert len(obj) == 5, 'Must have 5 elements!'

        s = 0
        for o in obj:
            assert int(o) >= 0, 'No non-negative numbers!'
            s += o

        assert s == 100, 'Elements must add to 100!'

        assert S['has_voted', vk] is None, 'VK has already voted!'


def mock_nodes():
    value = Variable()

    @construct
    def seed(initial):
        value.set(initial)

    @export
    def vote(vk: str, obj: list):
        pass

    @export
    def current_value():
        return value.get()


class TestRewards(TestCase):
    def setUp(self):
        self.c = ContractingClient()
        self.c.flush()

        with open('./contracts/election_house.s.py') as f:
            contract = f.read()

        self.c.submit(contract, name='election_house')
        self.c.submit(rewards, owner='election_house')
        self.c.raw_driver.commit()

        self.election_house = self.c.get_contract('election_house')
        self.rewards = self.c.get_contract('rewards')

        self.election_house.register_policy(contract='rewards')

        self.c.submit(mock_nodes, name='masternodes', owner='election_house', constructor_args={
            'initial': ['v1', 'v2']
        })

        self.c.submit(mock_nodes, name='delegates', owner='election_house', constructor_args={
            'initial': ['v3', 'v4', 'v5']
        })

        self.election_house.register_policy(contract='masternodes')
        self.election_house.register_policy(contract='delegates')

    def tearDown(self):
        self.c.flush()

    def test_invalid_signer_fails(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        with self.assertRaises(AssertionError):
            self.election_house.vote(policy='rewards', value=[1, 2, 3, 4, 5], environment=env)

    def test_vote_not_list_fails(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        with self.assertRaises(AssertionError):
            self.election_house.vote(policy='rewards', value=False, environment=env, signer='v1')

    def test_vote_list_not_ints_fails(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        with self.assertRaises(AssertionError):
            self.election_house.vote(policy='rewards', value=['a', 'b', 'c', 'd'], environment=env, signer='v2')

    def test_vote_list_not_5_elements_fails(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        with self.assertRaises(AssertionError):
            self.election_house.vote(policy='rewards', value=[1, 2, 3], environment=env, signer='v3')

    def test_vote_list_negatives_fails(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        with self.assertRaises(AssertionError):
            self.election_house.vote(policy='rewards', value=[1, 2, 3, -1, 0], environment=env, signer='v4')

    def test_vote_list_sum_not_100_fails(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        with self.assertRaises(AssertionError):
            self.election_house.vote(policy='rewards', value=[99, 0, 0, 0, 0], environment=env, signer='v1')

    def test_vote_list_sum_100_succeeds(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.election_house.vote(policy='rewards', value=[20, 20, 20, 20, 20], environment=env, signer='v2')
        self.assertEqual(self.rewards.S['current_votes', 'masternodes'], 20)
        self.assertEqual(self.rewards.S['current_votes', 'delegates'], 20)
        self.assertEqual(self.rewards.S['current_votes', 'blackhole'], 20)
        self.assertEqual(self.rewards.S['current_votes', 'foundation'], 20)
        self.assertEqual(self.rewards.S['current_votes', 'developer'], 20)

    def test_vote_twice_fails(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.election_house.vote(policy='rewards', value=[25, 25, 25, 25, 0], environment=env, signer='v1')
        with self.assertRaises(AssertionError):
            self.election_house.vote(policy='rewards', value=[25, 25, 25, 25, 0], environment=env, signer='v1')

    def test_vote_finished_returns_average_sum(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.election_house.vote(policy='rewards', value=[20, 20, 20, 20, 20], environment=env, signer='v1')
        self.election_house.vote(policy='rewards', value=[25, 0, 50, 25, 0], environment=env, signer='v2')
        self.election_house.vote(policy='rewards', value=[25, 0, 0, 75, 0], environment=env, signer='v3')
        self.election_house.vote(policy='rewards', value=[100, 0, 0, 0, 0], environment=env, signer='v4')

        env = {'now': Datetime._from_datetime(dt.today() + td(days=8))}

        self.election_house.vote(policy='rewards', value=[100, 0, 0, 0, 0], environment=env, signer='v5')

        # Expected [176, 26, 76, 126] / 404 = [0.4375, 0.0625, 0.1875, 0.3125]

        self.assertEqual(self.election_house.current_value_for_policy(policy='rewards'), [0.425, 0.05, 0.175, 0.30, 0.05])