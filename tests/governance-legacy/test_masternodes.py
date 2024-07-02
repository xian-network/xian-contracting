from unittest import TestCase
from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Timedelta, DAYS, WEEKS, Datetime
from datetime import datetime as dt, timedelta as td


def masternodes():
    INTRODUCE_MOTION = 'introduce_motion'
    VOTE_ON_MOTION = 'vote_on_motion'

    NO_MOTION = 0
    ADD_MASTER = 1
    REMOVE_MASTER = 2
    ADD_SEAT = 3
    REMOVE_SEAT = 4

    VOTING_PERIOD = datetime.DAYS * 1

    S = Hash()

    @construct
    def seed(initial_masternodes, initial_open_seats):
        S['masternodes'] = initial_masternodes
        S['open_seats'] = initial_open_seats

        S['yays'] = 0
        S['nays'] = 0

        S['current_motion'] = NO_MOTION
        S['motion_opened'] = now

    @export
    def current_value():
        return {
            'masternodes': S['masternodes'],
            'open_seats': S['open_seats']
        }

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

            elif now - S['motion_opened'] >= VOTING_PERIOD:
                reset()

    def assert_vote_is_valid(vk, action, position, arg=None):
        assert vk in S['masternodes'], 'Not a masternode.'

        assert action in [INTRODUCE_MOTION, VOTE_ON_MOTION], 'Invalid action.'

        if action == INTRODUCE_MOTION:
            assert S['current_motion'] == NO_MOTION, 'Already in motion.'
            assert 0 < position <= REMOVE_SEAT, 'Invalid motion.'
            if position == ADD_MASTER or position == REMOVE_MASTER:
                assert_vk_is_valid(arg)

        elif action == VOTE_ON_MOTION:
            assert type(position) == bool, 'Invalid position'

    def assert_vk_is_valid(vk):
        assert vk is not None, 'No VK provided.'
        assert type(vk) == str, 'VK not a string.'
        assert len(vk) == 64, 'VK is not 64 characters.'
        int(vk, 16)

    def introduce_motion(position, arg):
        if position == ADD_MASTER or position == REMOVE_SEAT:
            assert S['open_seats'] > 0, 'No open seats to add or remove.'

        if position == ADD_MASTER or position == REMOVE_MASTER:
            # If remove master, must be a master that already exists
            if position == REMOVE_MASTER:
                assert arg in S['masternodes'], 'Master does not exist.'

            S['master_in_question'] = arg

        S['current_motion'] = position
        S['motion_opened'] = now

    def pass_current_motion():
        current_motion = S['current_motion']
        masters = S['masternodes']

        if current_motion == ADD_MASTER:
            masters.append(S['master_in_question'])
            S['open_seats'] -= 1

        elif current_motion == REMOVE_MASTER:
            masters.remove(S['master_in_question'])
            S['open_seats'] += 1

        elif current_motion == ADD_SEAT:
            S['open_seats'] += 1

        elif current_motion == REMOVE_SEAT:
            S['open_seats'] -= 1

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

        with open('./contracts/election_house.s.py') as f:
            contract = f.read()

        self.client.submit(contract, name='election_house')
        self.election_house = self.client.get_contract('election_house')

    def tearDown(self):
        self.client.flush()

    def test_init(self):
        self.client.submit(masternodes, owner='election_house', constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        self.assertEqual(mn_contract.current_value(signer='election_house'), {
            'masternodes': [1, 2, 3],
            'open_seats': 0
        })

        self.assertEqual(mn_contract.S['yays'], 0)
        self.assertEqual(mn_contract.S['nays'], 0)
        self.assertEqual(mn_contract.S['current_motion'], 0)

    def test_voter_not_masternode_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
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
            'initial_open_seats': 0
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
            'initial_open_seats': 0
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
            'initial_open_seats': 0
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
            'initial_open_seats': 0
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
            'initial_open_seats': 0
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
            'initial_open_seats': 0
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
            'initial_open_seats': 0
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
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        with self.assertRaises(ValueError):
            mn_contract.run_private_function(
                f='assert_vote_is_valid',
                vk=1,
                action='introduce_motion',
                position=1,
                arg='x' * 64
            )

    def test_action_vote_on_motion_fails_if_not_bool(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
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
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')
        with self.assertRaises(AssertionError):
            mn_contract.vote(vk='sys', obj={'hanky': 'panky'})

    def test_vote_1_elem_tuple_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 'sys'],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')
        with self.assertRaises(ValueError):
            mn_contract.vote(vk='sys', obj=(1, ))

    def test_vote_4_elem_tuple_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 'sys'],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')
        with self.assertRaises(ValueError):
            mn_contract.vote(vk='sys', obj=(1, 2, 3, 4))

    # ADD_MASTER = 1
    # REMOVE_MASTER = 2
    # ADD_SEAT = 3
    # REMOVE_SEAT = 4
    def test_introduce_motion_add_master_fails_if_no_open_seats(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        with self.assertRaises(AssertionError):
            mn_contract.run_private_function(
                f='introduce_motion',
                position=1,
                arg=None
            )

    def test_introduce_motion_remove_seat_fails_if_no_open_seats(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
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
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        mn_contract.quick_write('S', 'open_seats', 1)

        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        mn_contract.run_private_function(
            f='introduce_motion',
            position=1,
            arg=None,
            environment=env
        )

        self.assertEqual(mn_contract.quick_read('S', 'current_motion'), 1)
        self.assertEqual(mn_contract.quick_read('S', 'motion_opened'), env['now'])

    def test_add_master_or_remove_master_adds_arg(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
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
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        with self.assertRaises(AssertionError):
            mn_contract.run_private_function(
                f='introduce_motion',
                position=2,
                arg='abc',
            )

    def test_remove_master_that_exists_passes(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        mn_contract.run_private_function(
            f='introduce_motion',
            position=2,
            arg=1,
        )

    def test_pass_current_motion_add_master_appends_and_removes_seat(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        mn_contract.quick_write('S', 'open_seats', 1)
        mn_contract.quick_write('S', 'master_in_question', 'abc')
        mn_contract.quick_write('S', 'current_motion', 1)

        mn_contract.run_private_function(
            f='pass_current_motion',
        )

        self.assertEqual(mn_contract.quick_read('S', 'masternodes'), [1, 2, 3, 'abc'])
        self.assertEqual(mn_contract.quick_read('S', 'open_seats'), 0)

    def test_pass_current_motion_remove_master_adds_new_seat_and_removes_master(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        mn_contract.quick_write('S', 'open_seats', 0)
        mn_contract.quick_write('S', 'master_in_question', 1)
        mn_contract.quick_write('S', 'current_motion', 2)

        mn_contract.run_private_function(
            f='pass_current_motion',
        )

        self.assertEqual(mn_contract.quick_read('S', 'masternodes'), [2, 3])
        self.assertEqual(mn_contract.quick_read('S', 'open_seats'), 1)

    def test_pass_current_motion_add_seat_adds_a_seat(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        mn_contract.quick_write('S', 'open_seats', 0)
        mn_contract.quick_write('S', 'current_motion', 3)

        mn_contract.run_private_function(
            f='pass_current_motion',
        )

        self.assertEqual(mn_contract.quick_read('S', 'open_seats'), 1)

    def test_pass_current_motion_remove_seat_removes_a_seat(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        mn_contract.quick_write('S', 'open_seats', 1)
        mn_contract.quick_write('S', 'current_motion', 4)

        mn_contract.run_private_function(
            f='pass_current_motion',
        )

        self.assertEqual(mn_contract.quick_read('S', 'open_seats'), 0)

    def test_current_value_returns_dict(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        d = mn_contract.current_value()

        self.assertEqual(d.get('masternodes'), [1, 2, 3])
        self.assertEqual(d.get('open_seats'), 0)

    # S['current_motion'] = NO_MOTION
    # S['master_in_question'] = None
    # S['votes'] = 0
    # S.clear('positions')
    def test_reset_alters_state_correctly(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
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
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        env = {'now': Datetime._from_datetime(dt.today())}

        mn_contract.vote(vk='a' * 64, obj=('introduce_motion', 3), environment=env)

        self.assertEqual(mn_contract.quick_read('S', 'current_motion'), 3)
        self.assertEqual(mn_contract.quick_read('S', 'motion_opened'), env['now'])

    def test_vote_no_motion_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': ['a' * 64, 'b' * 64, 'c' * 64],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        env = {'now': Datetime._from_datetime(dt.today())}

        with self.assertRaises(AssertionError):
            mn_contract.vote(vk='a' * 64, obj=('vote_on_motion', False), environment=env)

    def test_vote_on_motion_works(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': ['a' * 64, 'b' * 64, 'c' * 64],
            'initial_open_seats': 0
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
            'initial_open_seats': 0
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
            'initial_open_seats': 0
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
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        env = {'now': Datetime._from_datetime(dt.today())}

        mn_contract.vote(vk='a' * 64, obj=('introduce_motion', 3), environment=env)

        mn_contract.vote(vk='a' * 64, obj=('vote_on_motion', True))
        mn_contract.vote(vk='b' * 64, obj=('vote_on_motion', True))

        self.assertEqual(mn_contract.quick_read('S', 'open_seats'), 1)

        self.assertEqual(mn_contract.quick_read('S', 'current_motion'), 0)
        self.assertEqual(mn_contract.quick_read('S', 'master_in_question'), None)
        self.assertEqual(mn_contract.quick_read('S', 'yays'), 0)

    def test_vote_reaches_more_than_half_nays_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': ['a' * 64, 'b' * 64, 'c' * 64],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        env = {'now': Datetime._from_datetime(dt.today())}

        mn_contract.vote(vk='a' * 64, obj=('introduce_motion', 3), environment=env)

        mn_contract.vote(vk='a' * 64, obj=('vote_on_motion', False))
        mn_contract.vote(vk='b' * 64, obj=('vote_on_motion', False))

        self.assertEqual(mn_contract.quick_read('S', 'open_seats'), 0)

        self.assertEqual(mn_contract.quick_read('S', 'current_motion'), 0)
        self.assertEqual(mn_contract.quick_read('S', 'master_in_question'), None)
        self.assertEqual(mn_contract.quick_read('S', 'nays'), 0)

    def test_vote_doesnt_reach_consensus_after_voting_period_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': ['a' * 64, 'b' * 64, 'c' * 64],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        env = {'now': Datetime._from_datetime(dt.today())}

        mn_contract.vote(vk='a' * 64, obj=('introduce_motion', 3), environment=env)

        env = {'now': Datetime._from_datetime(dt.today() + td(days=2))}

        mn_contract.vote(vk='a' * 64, obj=('vote_on_motion', True), environment=env)

        self.assertEqual(mn_contract.quick_read('S', 'open_seats'), 0)

        self.assertEqual(mn_contract.quick_read('S', 'current_motion'), 0)
        self.assertEqual(mn_contract.quick_read('S', 'master_in_question'), None)
        self.assertEqual(mn_contract.quick_read('S', 'nays'), 0)
