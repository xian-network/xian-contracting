from unittest import TestCase
from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Timedelta, DAYS, WEEKS, Datetime
from datetime import datetime as dt, timedelta as td


def masternodes():
    INTRODUCE_MOTION = 'introduce_motion'
    VOTE_ON_MOTION = 'vote_on_motion'

    # Motions that can be raised
    NO_MOTION = 0
    REMOVE_MASTER = 1
    ADD_SEAT = 2
    REMOVE_SEAT = 3

    # Maximum time until a motion expires
    VOTING_PERIOD = Variable()

    # General contract state variable
    S = Hash()

    # Constants
    boot_num = Variable()
    candidates = Variable()

    @construct
    def seed(initial_masternodes, bn=1, candidates_contract='master_candidates',  period=datetime.DAYS * 1):
        S['masternodes'] = initial_masternodes
        boot_num.set(bn)
        candidates.set(candidates_contract)

        S['yays'] = 0
        S['nays'] = 0

        S['current_motion'] = NO_MOTION
        S['motion_opened'] = now

        VOTING_PERIOD.set(period)

    @export
    def quorum_max():
        return int(len(S['masternodes']) * 2 / 3) + 1

    @export
    def quorum_min():
        return min(quorum_max(), boot_num.get())

    @export
    def current_value():
        return S['masternodes']

    @export
    def vote(vk, obj):
        assert type(obj) == tuple, 'Pass a tuple!'

        arg = None
        try:
            action, position, arg = obj
        except ValueError:
            action, position = obj

        assert_vote_is_valid(vk, action, position, arg)

        if action == INTRODUCE_MOTION:
            introduce_motion(position, arg)

        else:
            assert S['current_motion'] != NO_MOTION, 'No motion proposed.'
            assert S['positions', vk] is None, 'VK already voted.'

            if position is True:
                S['yays'] += 1
                S['positions', vk] = position
            else:
                S['nays'] += 1
                S['positions', vk] = position

            if S['yays'] >= len(S['masternodes']) // 2 + 1:
                pass_current_motion()
                reset()

            elif S['nays'] >= len(S['masternodes']) // 2 + 1:
                reset()

            elif now - S['motion_opened'] >= VOTING_PERIOD.get():
                reset()

    def assert_vote_is_valid(vk, action, position, arg=None):
        assert vk in S['masternodes'], 'Not a masternode.'

        assert action in [INTRODUCE_MOTION, VOTE_ON_MOTION], 'Invalid action.'

        if action == INTRODUCE_MOTION:
            assert S['current_motion'] == NO_MOTION, 'Already in motion.'
            assert 0 < position <= REMOVE_SEAT, 'Invalid motion.'
            if position == REMOVE_MASTER:
                assert_vk_is_valid(arg)

        elif action == VOTE_ON_MOTION:
            assert type(position) == bool, 'Invalid position'

    def assert_vk_is_valid(vk):
        assert vk is not None, 'No VK provided.'
        assert type(vk) == str, 'VK not a string.'
        assert len(vk) == 64, 'VK is not 64 characters.'
        assert vk == ctx.signer, 'Signer has to be the one voting to remove themselves.'
        int(vk, 16)

    def introduce_motion(position, arg):
        assert 0 <= position <= 3, 'Invalid position'
        # If remove master, must be a master that already exists
        if position == REMOVE_MASTER:
            assert arg in S['masternodes'], 'Master does not exist.'

            S['master_in_question'] = arg

        S['current_motion'] = position
        S['motion_opened'] = now

    def pass_current_motion():
        current_motion = S['current_motion']
        masters = S['masternodes']

        if current_motion == REMOVE_MASTER:
            masters.remove(S['master_in_question'])

        elif current_motion == ADD_SEAT:
            master_candidates = importlib.import_module(candidates.get())
            # Get the top master
            new_mn = master_candidates.top_masternode()

            # Append it to the list, and remove it from pending
            if new_mn is not None:
                masters.append(new_mn)
                master_candidates.pop_top()

        elif current_motion == REMOVE_SEAT:
            master_candidates = importlib.import_module(candidates.get())
            # Get least popular master
            old_mn = master_candidates.last_masternode()

            # Remove them from the list and pop them from deprecating
            if old_mn is not None:
                masters.remove(old_mn)
                master_candidates.pop_last()

        S['masternodes'] = masters

    def reset():
        S['current_motion'] = NO_MOTION
        S['master_in_question'] = None
        S['yays'] = 0
        S['nays'] = 0
        S.clear('positions')


class TestMasternodePolicy(TestCase):
    def setUp(self):
        self.client = ContractingClient()

        f = open('./contracts/currency.s.py')
        self.client.submit(f.read(), 'currency')
        f.close()

        with open('./contracts/election_house.s.py') as f:
            contract = f.read()

        self.client.submit(contract, name='election_house')

        f = open('./contracts/master_candidates.s.py')
        self.client.submit(f.read(), 'master_candidates')
        f.close()

        f = open('./contracts/stamp_cost.s.py')
        self.client.submit(f.read(), 'stamp_cost', owner='election_house', constructor_args={'initial_rate': 20_000})
        f.close()

        self.election_house = self.client.get_contract('election_house')
        self.stamp_cost = self.client.get_contract(name='stamp_cost')
        self.election_house.register_policy(contract='stamp_cost')
        self.master_candidates = self.client.get_contract('master_candidates')
        self.currency = self.client.get_contract('currency')

    def tearDown(self):
        self.client.flush()

    def test_init(self):
        self.client.submit(masternodes, owner='election_house', constructor_args={
            'initial_masternodes': [1, 2, 3],
        })

        mn_contract = self.client.get_contract('masternodes')

        self.assertEqual(mn_contract.current_value(signer='election_house'), [1, 2, 3])

        self.assertEqual(mn_contract.S['yays'], 0)
        self.assertEqual(mn_contract.S['nays'], 0)
        self.assertEqual(mn_contract.S['current_motion'], 0)

    def test_voter_not_masternode_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
        })

        mn_contract = self.client.get_contract('masternodes')

        with self.assertRaises(AssertionError):
            mn_contract.run_private_function(
                f='assert_vote_is_valid',
                vk='sys',
                action='introduce_motion',
                position=1
            )

    def test_vote_invalid_action_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
        })

        mn_contract = self.client.get_contract('masternodes')

        with self.assertRaises(AssertionError):
            mn_contract.run_private_function(
                f='assert_vote_is_valid',
                vk=1,
                action='xxx',
                position=1
            )

    def test_vote_on_motion_bool_succeeds(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
        })

        mn_contract = self.client.get_contract('masternodes')

        mn_contract.run_private_function(
            f='assert_vote_is_valid',
            vk=1,
            action='vote_on_motion',
            position=True
        )

    def test_action_introduce_motion_current_motion_not_no_motion_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
        })

        mn_contract = self.client.get_contract('masternodes')

        mn_contract.quick_write(variable='S', key='current_motion', value=1)

        with self.assertRaises(AssertionError):
            mn_contract.run_private_function(
                f='assert_vote_is_valid',
                vk=1,
                action='introduce_motion',
                position=1
            )

    def test_action_introduce_motion_out_of_range_motion_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
        })

        mn_contract = self.client.get_contract('masternodes')

        with self.assertRaises(AssertionError):
            mn_contract.run_private_function(
                f='assert_vote_is_valid',
                vk=1,
                action='introduce_motion',
                position=10
            )

    def test_action_introduce_motion_no_arg_provided_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
        })

        mn_contract = self.client.get_contract('masternodes')

        with self.assertRaises(AssertionError):
            mn_contract.run_private_function(
                f='assert_vote_is_valid',
                vk=1,
                action='introduce_motion',
                position=1
            )

    def test_action_introduce_motion_vk_not_str_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
        })

        mn_contract = self.client.get_contract('masternodes')

        with self.assertRaises(AssertionError):
            mn_contract.run_private_function(
                f='assert_vote_is_valid',
                vk=1,
                action='introduce_motion',
                position=1,
                arg=True
            )

    def test_action_introduce_motion_vk_not_64_chars_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
        })

        mn_contract = self.client.get_contract('masternodes')

        with self.assertRaises(AssertionError):
            mn_contract.run_private_function(
                f='assert_vote_is_valid',
                vk=1,
                action='introduce_motion',
                position=1,
                arg='a'
            )

    def test_action_introduce_motion_not_valid_hex_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
        })

        mn_contract = self.client.get_contract('masternodes')

        with self.assertRaises(ValueError):
            mn_contract.run_private_function(
                f='assert_vote_is_valid',
                vk=1,
                action='introduce_motion',
                position=1,
                arg='x' * 64,
                signer='x' * 64
            )

    def test_action_vote_on_motion_fails_if_not_bool(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
        })

        mn_contract = self.client.get_contract('masternodes')

        with self.assertRaises(AssertionError):
            mn_contract.run_private_function(
                f='assert_vote_is_valid',
                vk=1,
                action='vote_on_motion',
                position=1,
            )

    def test_vote_not_tuple_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 'sys'],
        })

        mn_contract = self.client.get_contract('masternodes')
        with self.assertRaises(AssertionError):
            mn_contract.vote(vk='sys', obj={'hanky': 'panky'})

    def test_vote_1_elem_tuple_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 'sys'],
        })

        mn_contract = self.client.get_contract('masternodes')
        with self.assertRaises(ValueError):
            mn_contract.vote(vk='sys', obj=(1, ))

    def test_vote_4_elem_tuple_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 'sys'],
        })

        mn_contract = self.client.get_contract('masternodes')
        with self.assertRaises(ValueError):
            mn_contract.vote(vk='sys', obj=(1, 2, 3, 4))

    # ADD_MASTER = 1
    # REMOVE_MASTER = 2
    # ADD_SEAT = 3
    # REMOVE_SEAT = 4

    def test_introduce_motion_remove_seat_fails_if_position_out_of_index(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
        })

        mn_contract = self.client.get_contract('masternodes')

        with self.assertRaises(AssertionError):
            mn_contract.run_private_function(
                f='introduce_motion',
                position=4,
                arg=None
            )

    def test_introduce_motion_remove_seat_works_and_sets_position_and_motion_opened(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
        })

        mn_contract = self.client.get_contract('masternodes')

        mn_contract.quick_write('S', 'open_seats', 1)

        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        mn_contract.run_private_function(
            f='introduce_motion',
            position=3,
            arg=None,
            environment=env
        )

        self.assertEqual(mn_contract.quick_read('S', 'current_motion'), 3)
        self.assertEqual(mn_contract.quick_read('S', 'motion_opened'), env['now'])

    def test_add_master_or_remove_master_adds_arg(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': ['abc', 'bcd', 'cde'],
        })

        mn_contract = self.client.get_contract('masternodes')

        mn_contract.quick_write('S', 'open_seats', 1)

        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        mn_contract.run_private_function(
            f='introduce_motion',
            position=1,
            arg='abc',
            environment=env
        )

        self.assertEqual(mn_contract.quick_read('S', 'current_motion'), 1)
        self.assertEqual(mn_contract.quick_read('S', 'motion_opened'), env['now'])
        self.assertEqual(mn_contract.quick_read('S', 'master_in_question'), 'abc')

    def test_remove_master_that_does_not_exist_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
        })

        mn_contract = self.client.get_contract('masternodes')

        with self.assertRaises(AssertionError):
            mn_contract.run_private_function(
                f='introduce_motion',
                position=1,
                arg='abc',
            )

    def test_remove_master_that_exists_passes(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
        })

        mn_contract = self.client.get_contract('masternodes')

        mn_contract.run_private_function(
            f='introduce_motion',
            position=2,
            arg=1,
        )

    def test_pass_current_motion_add_master_appends_and_removes_seat(self):
        # Give joe money
        self.currency.transfer(signer='stu', amount=100_000, to='joe')

        # Joe Allows Spending
        self.currency.approve(signer='joe', amount=100_000, to='master_candidates')

        self.master_candidates.register(signer='joe')

        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
        })

        mn_contract = self.client.get_contract('masternodes')

        mn_contract.quick_write('S', 'current_motion', 2)

        mn_contract.run_private_function(
            f='pass_current_motion',
        )

        self.assertEqual(mn_contract.quick_read('S', 'masternodes'), [1, 2, 3, 'joe'])

    def test_pass_current_motion_remove_master_adds_new_seat_and_removes_master(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
        })

        mn_contract = self.client.get_contract('masternodes')

        mn_contract.quick_write('S', 'master_in_question', 1)
        mn_contract.quick_write('S', 'current_motion', 1)

        mn_contract.run_private_function(
            f='pass_current_motion',
        )

        self.assertEqual(mn_contract.quick_read('S', 'masternodes'), [2, 3])

    def test_pass_remove_seat_removes_least_popular(self):
        self.client.submit(masternodes, owner='election_house', constructor_args={
            'initial_masternodes': ['abc', 'bcd', 'def'],
        })
        self.election_house.register_policy(contract='masternodes')
        self.currency.approve(signer='stu', amount=100_000, to='master_candidates')

        self.master_candidates.vote_no_confidence(signer='stu', address='bcd')

        self.election_house.vote(signer='abc', policy='masternodes', value=('introduce_motion', 3))
        self.election_house.vote(signer='bcd', policy='masternodes', value=('vote_on_motion', True))
        self.election_house.vote(signer='def', policy='masternodes', value=('vote_on_motion', True))

        self.assertListEqual(self.election_house.current_value_for_policy(policy='masternodes'), ['abc', 'def'])

    def test_pass_remove_seat_removes_relinquished_first(self):
        self.client.submit(masternodes, owner='election_house', constructor_args={
            'initial_masternodes': ['abc', 'bcd', 'def'],
        })
        self.election_house.register_policy(contract='masternodes')

        self.master_candidates.relinquish(signer='abc')

        self.election_house.vote(signer='abc', policy='masternodes', value=('introduce_motion', 3))

        self.election_house.vote(signer='bcd', policy='masternodes', value=('vote_on_motion', True))
        self.election_house.vote(signer='def', policy='masternodes', value=('vote_on_motion', True))

        self.assertListEqual(self.election_house.current_value_for_policy(policy='masternodes'), ['bcd', 'def'])

    def test_remove_seat_not_current_masternode_fails(self):
        self.client.submit(masternodes, owner='election_house', constructor_args={
            'initial_masternodes': ['abc', 'bcd', 'def'],
        })
        self.election_house.register_policy(contract='masternodes')

        with self.assertRaises(AssertionError):
            self.election_house.vote(signer='abc', policy='masternodes', value=('introduce_motion', 1, 'blah'))

    def test_pass_add_seat_adds_most_popular(self):
        # Give joe money
        self.currency.transfer(signer='stu', amount=100_000, to='joe')

        # Joe Allows Spending
        self.currency.approve(signer='joe', amount=100_000, to='master_candidates')

        self.master_candidates.register(signer='joe')

        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
        })

        mn_contract = self.client.get_contract('masternodes')

        mn_contract.vote(vk=1, obj=('introduce_motion', 2))

        mn_contract.vote(vk=2, obj=('vote_on_motion', True))
        mn_contract.vote(vk=3, obj=('vote_on_motion', True))

        self.assertListEqual(mn_contract.current_value(), [1, 2, 3, 'joe'])

    def test_current_value_returns_dict(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
        })

        mn_contract = self.client.get_contract('masternodes')

        d = mn_contract.current_value()

        self.assertEqual(d, [1, 2, 3])

    # S['current_motion'] = NO_MOTION
    # S['master_in_question'] = None
    # S['votes'] = 0
    # S.clear('positions')
    def test_reset_alters_state_correctly(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
        })

        mn_contract = self.client.get_contract('masternodes')

        mn_contract.quick_write('S', 'current_motion', 1)
        mn_contract.quick_write('S', 'master_in_question', 'abc')
        mn_contract.quick_write('S', 'yays', 100)
        mn_contract.quick_write('S', 'nays', 999)
        mn_contract.quick_write(variable='S', key='positions', value=[1, 2, 3, 4], args=['id1'])
        mn_contract.quick_write(variable='S', key='positions', value=[1, 2, 3, 4], args=['id2'])
        mn_contract.quick_write(variable='S', key='positions', value=[1, 2, 3, 4], args=['id3'])
        mn_contract.quick_write(variable='S', key='positions', value=[1, 2, 3, 4], args=['id4'])
        mn_contract.quick_write(variable='S', key='positions', value=[1, 2, 3, 4], args=['id5'])
        mn_contract.quick_write(variable='S', key='positions', value=[1, 2, 3, 4], args=['id6'])
        mn_contract.quick_write(variable='S', key='positions', value=[1, 2, 3, 4], args=['id7'])
        mn_contract.quick_write(variable='S', key='positions', value=[1, 2, 3, 4], args=['id8'])

        mn_contract.run_private_function(
            f='reset',
        )

        self.assertEqual(mn_contract.quick_read('S', 'current_motion'), 0)
        self.assertEqual(mn_contract.quick_read('S', 'master_in_question'), None)
        self.assertEqual(mn_contract.quick_read('S', 'yays'), 0)
        self.assertEqual(mn_contract.quick_read('S', 'nays'), 0)
        self.assertIsNone(mn_contract.quick_read('S', 'positions', args=['id1']))
        self.assertIsNone(mn_contract.quick_read('S', 'positions', args=['id2']))
        self.assertIsNone(mn_contract.quick_read('S', 'positions', args=['id3']))
        self.assertIsNone(mn_contract.quick_read('S', 'positions', args=['id4']))
        self.assertIsNone(mn_contract.quick_read('S', 'positions', args=['id5']))
        self.assertIsNone(mn_contract.quick_read('S', 'positions', args=['id6']))
        self.assertIsNone(mn_contract.quick_read('S', 'positions', args=['id7']))
        self.assertIsNone(mn_contract.quick_read('S', 'positions', args=['id8']))

    def test_vote_introduce_motion_affects_state_when_done_properly(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': ['a' * 64, 'b' * 64, 'c' * 64],
        })

        mn_contract = self.client.get_contract('masternodes')

        env = {'now': Datetime._from_datetime(dt.today())}

        mn_contract.vote(vk='a' * 64, obj=('introduce_motion', 3), environment=env)

        self.assertEqual(mn_contract.quick_read('S', 'current_motion'), 3)
        self.assertEqual(mn_contract.quick_read('S', 'motion_opened'), env['now'])

    def test_vote_no_motion_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': ['a' * 64, 'b' * 64, 'c' * 64],
        })

        mn_contract = self.client.get_contract('masternodes')

        env = {'now': Datetime._from_datetime(dt.today())}

        with self.assertRaises(AssertionError):
            mn_contract.vote(vk='a' * 64, obj=('vote_on_motion', False), environment=env)

    def test_vote_on_motion_works(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': ['a' * 64, 'b' * 64, 'c' * 64],
        })

        mn_contract = self.client.get_contract('masternodes')

        env = {'now': Datetime._from_datetime(dt.today())}

        mn_contract.vote(vk='a' * 64, obj=('introduce_motion', 3), environment=env)

        mn_contract.vote(vk='b' * 64, obj=('vote_on_motion', True))

        self.assertEqual(mn_contract.quick_read('S', 'yays'), 1)
        self.assertEqual(mn_contract.quick_read(variable='S', key='positions', args=['b' * 64]), True)

    def test_vote_on_motion_works_nays(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': ['a' * 64, 'b' * 64, 'c' * 64],
        })

        mn_contract = self.client.get_contract('masternodes')

        env = {'now': Datetime._from_datetime(dt.today())}

        mn_contract.vote(vk='a' * 64, obj=('introduce_motion', 3), environment=env)

        mn_contract.vote(vk='b' * 64, obj=('vote_on_motion', False))

        self.assertEqual(mn_contract.quick_read('S', 'nays'), 1)
        self.assertEqual(mn_contract.quick_read('S', 'yays'), 0)
        self.assertEqual(mn_contract.quick_read(variable='S', key='positions', args=['b' * 64]), False)

    def test_vote_on_motion_twice_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': ['a' * 64, 'b' * 64, 'c' * 64],
        })

        mn_contract = self.client.get_contract('masternodes')

        env = {'now': Datetime._from_datetime(dt.today())}

        mn_contract.vote(vk='a' * 64, obj=('introduce_motion', 3), environment=env)

        mn_contract.vote(vk='b' * 64, obj=('vote_on_motion', True))

        with self.assertRaises(AssertionError):
            mn_contract.vote(vk='b' * 64, obj=('vote_on_motion', False))

    def test_vote_reaches_more_than_half_passes(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': ['a' * 64, 'b' * 64, 'c' * 64],
        })

        mn_contract = self.client.get_contract('masternodes')

        env = {'now': Datetime._from_datetime(dt.today())}

        mn_contract.vote(vk='a' * 64, obj=('introduce_motion', 3), environment=env)

        mn_contract.vote(vk='a' * 64, obj=('vote_on_motion', True))
        mn_contract.vote(vk='b' * 64, obj=('vote_on_motion', True))

        self.assertEqual(mn_contract.quick_read('S', 'current_motion'), 0)
        self.assertEqual(mn_contract.quick_read('S', 'master_in_question'), None)
        self.assertEqual(mn_contract.quick_read('S', 'yays'), 0)

    def test_vote_reaches_more_than_half_nays_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': ['a' * 64, 'b' * 64, 'c' * 64],
        })

        mn_contract = self.client.get_contract('masternodes')

        env = {'now': Datetime._from_datetime(dt.today())}

        mn_contract.vote(vk='a' * 64, obj=('introduce_motion', 3), environment=env)

        mn_contract.vote(vk='a' * 64, obj=('vote_on_motion', False))
        mn_contract.vote(vk='b' * 64, obj=('vote_on_motion', False))

        self.assertEqual(mn_contract.quick_read('S', 'current_motion'), 0)
        self.assertEqual(mn_contract.quick_read('S', 'master_in_question'), None)
        self.assertEqual(mn_contract.quick_read('S', 'nays'), 0)

    def test_vote_doesnt_reach_consensus_after_voting_period_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': ['a' * 64, 'b' * 64, 'c' * 64],
        })

        mn_contract = self.client.get_contract('masternodes')

        env = {'now': Datetime._from_datetime(dt.today())}

        mn_contract.vote(vk='a' * 64, obj=('introduce_motion', 3), environment=env)

        env = {'now': Datetime._from_datetime(dt.today() + td(days=2))}

        mn_contract.vote(vk='a' * 64, obj=('vote_on_motion', True), environment=env)

        self.assertEqual(mn_contract.quick_read('S', 'current_motion'), 0)
        self.assertEqual(mn_contract.quick_read('S', 'master_in_question'), None)
        self.assertEqual(mn_contract.quick_read('S', 'nays'), 0)
