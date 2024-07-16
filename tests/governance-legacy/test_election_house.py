from unittest import TestCase
from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Timedelta, DAYS, WEEKS, Datetime
from datetime import datetime as dt, timedelta as td


def election_house():
    # Convenience
    I = importlib

    # Subhash IDs
    CONTRACT = 'contract'

    POLICY = 'policy'

    VOTES = 'votes'
    CURRENT_VALUE = 'current_value'

    IN_ELECTION = 'in_election'
    ELECTION_START_TIME = 'election_start_time'
    LAST_ELECTION_END_TIME = 'election_end_time'
    VOTING_PERIOD = 'voting_period'
    ELECTION_INTERVAL = 'election_interval'

    # Main state datum
    states = Hash()

    # Policy interface
    policy_interface = [
        I.Func('voter_is_valid', args=('vk',)),
        I.Func('vote_is_valid', args=('obj',)),
        I.Func('new_policy_value', args=('values',)),
    ]

    @export
    def register_policy(policy, contract, election_interval, voting_period, initial_value=None):
        # Make sure the policy is not registered
        if states[CONTRACT, policy] is None and states[POLICY, contract] is None:

            # Attempt to import the contract to make sure it is already submitted
            p = I.import_module(contract)

            # Assert ownership is election_house and interface is correct
            assert I.owner_of(p) == ctx.this, \
                'Election house must control the policy contract!'

            assert I.enforce_interface(p, policy_interface), \
                'Policy contract does not follow the correct interface'

            # Double linked hash to prevent double submission of policies
            states[CONTRACT, policy] = contract
            states[POLICY, contract] = policy

            states[ELECTION_INTERVAL, policy] = election_interval
            states[VOTING_PERIOD, policy] = voting_period
            states[CURRENT_VALUE, policy] = initial_value

            reset_election(policy)
        else:
            raise Exception('Policy already registered')

    @export
    def get_policy(policy: str):
        # Simple getter
        return states[CURRENT_VALUE, policy]

    @export
    def vote(policy, value):
        # Verify policy has been registered
        assert states[CONTRACT, policy] is not None, 'Invalid policy.'

        # Import the module associated with this policy
        p = I.import_module(states[CONTRACT, policy])

        if states[IN_ELECTION, policy] and p.voter_is_valid(ctx.caller) and p.vote_is_valid(value):

            states[VOTES, policy, ctx.caller] = value

            # If between now and the start time, the voting interval length has passed, tally the votes and set the
            # new value. Reset the policy election state.
            if now - states[ELECTION_START_TIME, policy] >= states[VOTING_PERIOD, policy]:
                votes = states.all(VOTES, policy)
                states[CURRENT_VALUE, policy] = p.new_policy_value(votes)
                reset_election(policy)

        else:
            if now - states[LAST_ELECTION_END_TIME, policy] > states[ELECTION_INTERVAL, policy]:
                # Start the election and set the proper variables
                states[ELECTION_START_TIME, policy] = now
                states[IN_ELECTION, policy] = True

                if p.voter_is_valid(ctx.caller) and p.vote_is_valid(value):
                    states[VOTES, policy, ctx.caller] = value
            else:
                raise Exception('Outside of governance parameters.')

    def reset_election(policy: str):
        states[LAST_ELECTION_END_TIME, policy] = now
        states[IN_ELECTION, policy] = False
        states.clear(VOTES, policy)


def good_policy():
    @export
    def voter_is_valid(vk):
        return True

    @export
    def vote_is_valid(obj):
        return True

    @export
    def new_policy_value(values):
        return values[0]


def bad_policy():
    @export
    def xvoter_is_validx(vk):
        return True

    @export
    def xvote_is_validx(obj):
        return True

    @export
    def xnew_policy_valuex(values):
        return values[0]


def fail_voter_policy():
    @export
    def voter_is_valid(vk):
        if vk == 'sys':
            return False
        return True

    @export
    def vote_is_valid(obj):
        return True

    @export
    def new_policy_value(values):
        return values[0]


def fail_vote_policy():
    @export
    def voter_is_valid(vk):
        return True

    @export
    def vote_is_valid(obj):
        if obj == 123:
            return True
        return False

    @export
    def new_policy_value(values):
        return values[0]


def always_yay_policy():
    @export
    def voter_is_valid(vk):
        return True

    @export
    def vote_is_valid(obj):
        if obj == 123:
            return True
        return False

    @export
    def new_policy_value(values):
        return 'yay'

def average_votes_policy():
    @export
    def voter_is_valid(vk):
        return True

    @export
    def vote_is_valid(obj):
        if type(obj) == int:
            return True
        return False

    @export
    def new_policy_value(values):
        vv = 0
        for v in values:
            vv += v
        return vv // len(values)


class TestElectionHouse(TestCase):
    def setUp(self):
        self.client = ContractingClient()
        self.client.flush()
        self.client.submit(election_house)
        self.election_house = self.client.get_contract('election_house')

    def tearDown(self):
        self.client.flush()

    def test_submit_policy_works(self):
        self.client.submit(good_policy, owner='election_house')

        self.election_house.register_policy(policy='testing',
                                            contract='good_policy',
                                            election_interval=WEEKS*1,
                                            voting_period=DAYS*1)

        self.assertEqual(self.election_house.states['contract', 'testing'], 'good_policy')
        self.assertEqual(self.election_house.states['election_interval', 'testing'], WEEKS*1)
        self.assertEqual(self.election_house.states['voting_period', 'testing'], DAYS*1)
        self.assertEqual(self.election_house.states['in_election', 'testing'], False)

    def test_submit_policy_wrong_owner_fails(self):
        self.client.submit(good_policy, owner='wrong_owner')

        with self.assertRaises(Exception):
            self.election_house.register_policy(policy='testing',
                                                contract='good_policy',
                                                election_interval=WEEKS * 1,
                                                voting_period=DAYS * 1)

    def test_submit_policy_that_does_not_exist_fails(self):
        with self.assertRaises(AssertionError):
            self.election_house.register_policy(policy='testing',
                                                contract='good_policy',
                                                election_interval=WEEKS * 1,
                                                voting_period=DAYS * 1)

    def test_submit_policy_with_bad_interface_fails(self):
        self.client.submit(bad_policy, owner='election_house')

        with self.assertRaises(Exception):
            self.election_house.register_policy(policy='testing',
                                                contract='bad_policy',
                                                election_interval=WEEKS * 1,
                                                voting_period=DAYS * 1)

    def test_submit_same_policy_twice_fails(self):
        self.client.submit(good_policy, owner='election_house')

        self.election_house.register_policy(policy='testing',
                                            contract='good_policy',
                                            election_interval=WEEKS * 1,
                                            voting_period=DAYS * 1)

        with self.assertRaises(Exception):
            self.election_house.register_policy(policy='testing',
                                                contract='good_policy',
                                                election_interval=WEEKS * 1,
                                                voting_period=DAYS * 1)

    def test_submit_same_policy_different_name_fails(self):
        self.client.submit(good_policy, owner='election_house')

        self.election_house.register_policy(policy='testing',
                                            contract='good_policy',
                                            election_interval=WEEKS * 1,
                                            voting_period=DAYS * 1)

        with self.assertRaises(Exception):
            self.election_house.register_policy(policy='testing2',
                                                contract='good_policy',
                                                election_interval=WEEKS * 1,
                                                voting_period=DAYS * 1)

    def test_submit_different_policy_same_name_fails(self):
        self.client.submit(good_policy, owner='election_house')

        self.election_house.register_policy(policy='testing',
                                            contract='good_policy',
                                            election_interval=WEEKS * 1,
                                            voting_period=DAYS * 1)

        with self.assertRaises(Exception):
            self.election_house.register_policy(policy='testing',
                                                contract='bad_policy',
                                                election_interval=WEEKS * 1,
                                                voting_period=DAYS * 1)

    def test_submit_with_initial_value_can_be_retrieved(self):
        self.client.submit(good_policy, owner='election_house')

        self.election_house.register_policy(policy='testing',
                                            contract='good_policy',
                                            election_interval=WEEKS * 1,
                                            voting_period=DAYS * 1,
                                            initial_value='XYZ')

        self.assertEqual(self.election_house.get_policy(policy='testing'), 'XYZ')

    def test_vote_invalid_policy_fails(self):
        with self.assertRaises(AssertionError):
            self.election_house.vote(policy='not_existing', value=False)

    def test_vote_right_after_submission_fails(self):
        self.client.submit(good_policy, owner='election_house')

        self.election_house.register_policy(policy='testing',
                                            contract='good_policy',
                                            election_interval=WEEKS * 1,
                                            voting_period=DAYS * 1)

        with self.assertRaises(Exception):
            self.election_house.vote(policy='testing', value=False)

    def test_not_in_election_but_past_election_interval_starts_election_and_tallies_vote(self):
        self.client.submit(good_policy, owner='election_house')

        self.election_house.register_policy(policy='testing',
                                            contract='good_policy',
                                            election_interval=WEEKS * 1,
                                            voting_period=DAYS * 1)

        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.election_house.vote(policy='testing', value=False, environment=env)

        self.assertEqual(self.election_house.states['in_election', 'testing'], True)
        self.assertEqual(self.election_house.states['election_start_time', 'testing'], env['now'])
        self.assertEqual(self.election_house.states['votes', 'testing', 'sys'], False)

    def test_anyone_can_start_vote_but_invalid_voters_vote_does_not_count(self):
        self.client.submit(fail_voter_policy, owner='election_house')

        self.election_house.register_policy(policy='testing',
                                            contract='fail_voter_policy',
                                            election_interval=WEEKS * 1,
                                            voting_period=DAYS * 1)

        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.election_house.vote(policy='testing', value=False, environment=env)

        self.assertEqual(self.election_house.states['in_election', 'testing'], True)
        self.assertEqual(self.election_house.states['election_start_time', 'testing'], env['now'])
        self.assertEqual(self.election_house.states['votes', 'testing', 'sys'], None)

    def test_invalid_voters_vote_not_counted_if_in_vote(self):
        self.client.submit(fail_voter_policy, owner='election_house')

        self.election_house.register_policy(policy='testing',
                                            contract='fail_voter_policy',
                                            election_interval=WEEKS * 1,
                                            voting_period=DAYS * 1)

        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.election_house.vote(policy='testing', value=123, environment=env, signer='not_sys')

        self.assertEqual(self.election_house.states['in_election', 'testing'], True)
        self.assertEqual(self.election_house.states['election_start_time', 'testing'], env['now'])
        self.assertEqual(self.election_house.states['votes', 'testing', 'not_sys'], 123)

        self.election_house.vote(policy='testing', value=999, environment=env, signer='sys')

        self.assertEqual(self.election_house.states['votes', 'testing', 'sys'], None)

    def test_invalid_vote_from_valid_voter_is_not_counted_if_starting_election(self):
        self.client.submit(fail_vote_policy, owner='election_house')

        self.election_house.register_policy(policy='testing',
                                            contract='fail_vote_policy',
                                            election_interval=WEEKS * 1,
                                            voting_period=DAYS * 1)

        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.election_house.vote(policy='testing', value=999, environment=env)

        self.assertEqual(self.election_house.states['in_election', 'testing'], True)
        self.assertEqual(self.election_house.states['election_start_time', 'testing'], env['now'])
        self.assertEqual(self.election_house.states['votes', 'testing', 'sys'], None)

    def test_invalid_vote_from_valid_voter_is_not_counted_after_starting_election_either(self):
        self.client.submit(fail_vote_policy, owner='election_house')

        self.election_house.register_policy(policy='testing',
                                            contract='fail_vote_policy',
                                            election_interval=WEEKS * 1,
                                            voting_period=DAYS * 1)

        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.election_house.vote(policy='testing', value=999, environment=env)

        self.assertEqual(self.election_house.states['in_election', 'testing'], True)
        self.assertEqual(self.election_house.states['election_start_time', 'testing'], env['now'])
        self.assertEqual(self.election_house.states['votes', 'testing', 'sys'], None)

        self.election_house.vote(policy='testing', value=222, environment=env, signer='not_sys')

        self.assertEqual(self.election_house.states['votes', 'testing', 'not_sys'], None)

    def test_valid_vote_and_voter_after_voting_started_counts(self):
        self.client.submit(good_policy, owner='election_house')

        self.election_house.register_policy(policy='testing',
                                            contract='good_policy',
                                            election_interval=WEEKS * 1,
                                            voting_period=DAYS * 1)

        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.election_house.vote(policy='testing', value=999, environment=env)

        self.assertEqual(self.election_house.states['in_election', 'testing'], True)
        self.assertEqual(self.election_house.states['election_start_time', 'testing'], env['now'])
        self.assertEqual(self.election_house.states['votes', 'testing', 'sys'], 999)

        self.election_house.vote(policy='testing', value=123, environment=env, signer='not_sys')

        self.assertEqual(self.election_house.states['votes', 'testing', 'not_sys'], 123)

    def test_voting_twice_overwrites_vote(self):
        self.client.submit(good_policy, owner='election_house')

        self.election_house.register_policy(policy='testing',
                                            contract='good_policy',
                                            election_interval=WEEKS * 1,
                                            voting_period=DAYS * 1)

        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.election_house.vote(policy='testing', value=999, environment=env)

        self.assertEqual(self.election_house.states['in_election', 'testing'], True)
        self.assertEqual(self.election_house.states['election_start_time', 'testing'], env['now'])
        self.assertEqual(self.election_house.states['votes', 'testing', 'sys'], 999)

        self.election_house.vote(policy='testing', value=123, environment=env)

        self.assertEqual(self.election_house.states['votes', 'testing', 'sys'], 123)

    def test_in_election_voting_ends_creates_new_policy_value(self):
        self.client.submit(always_yay_policy, owner='election_house')

        self.election_house.register_policy(policy='testing',
                                            contract='always_yay_policy',
                                            election_interval=WEEKS * 1,
                                            voting_period=DAYS * 1,
                                            initial_value='not_yay')

        self.assertEqual(self.election_house.states['current_value', 'testing'], 'not_yay')

        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.election_house.vote(policy='testing', value=999, environment=env)

        env = {'now': Datetime._from_datetime(dt.today() + td(days=8))}

        self.election_house.vote(policy='testing', value=123, environment=env)

        self.assertEqual(self.election_house.states['current_value', 'testing'], 'yay')

    def test_in_election_voting_ends_creates_new_policy_that_is_mutated_by_policy(self):
        self.client.submit(average_votes_policy, owner='election_house')

        self.election_house.register_policy(policy='testing',
                                            contract='average_votes_policy',
                                            election_interval=WEEKS * 1,
                                            voting_period=DAYS * 1,
                                            initial_value=0)

        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.election_house.vote(policy='testing', value=10, environment=env, signer='v1')
        self.election_house.vote(policy='testing', value=10, environment=env, signer='v2')
        self.election_house.vote(policy='testing', value=10, environment=env, signer='v3')

        env = {'now': Datetime._from_datetime(dt.today() + td(days=8))}

        self.election_house.vote(policy='testing', value=50, environment=env, signer='v4')

        self.assertEqual(self.election_house.states['current_value', 'testing'], 20)

    def test_in_election_voting_period_ends_resets_state(self):
        self.client.submit(average_votes_policy, owner='election_house')

        self.election_house.register_policy(policy='testing',
                                            contract='average_votes_policy',
                                            election_interval=WEEKS * 1,
                                            voting_period=DAYS * 1,
                                            initial_value=0)

        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.election_house.vote(policy='testing', value=10, environment=env, signer='v1')
        self.election_house.vote(policy='testing', value=10, environment=env, signer='v2')
        self.election_house.vote(policy='testing', value=10, environment=env, signer='v3')

        env = {'now': Datetime._from_datetime(dt.today() + td(days=8))}

        self.election_house.vote(policy='testing', value=50, environment=env, signer='v4')

        self.assertEqual(self.election_house.states['election_end_time', 'testing'], env['now'])
        self.assertEqual(self.election_house.states['in_election', 'testing'], False)

        self.assertEqual(self.election_house.states['votes', 'testing', 'v1'], None)
        self.assertEqual(self.election_house.states['votes', 'testing', 'v2'], None)
        self.assertEqual(self.election_house.states['votes', 'testing', 'v3'], None)
        self.assertEqual(self.election_house.states['votes', 'testing', 'v4'], None)
