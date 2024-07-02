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
def vote(vk: int, obj: Any):
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


def assert_vote_is_valid(vk: int, action: str, position: bool, arg=None):
    assert vk in S['masternodes'], 'Not a masternode.'

    assert action in [INTRODUCE_MOTION, VOTE_ON_MOTION], 'Invalid action.'

    if action == INTRODUCE_MOTION:
        assert S['current_motion'] == NO_MOTION, 'Already in motion.'
        assert 0 < position <= REMOVE_SEAT, 'Invalid motion.'
        if position == ADD_MASTER or position == REMOVE_MASTER:
            assert_vk_is_valid(arg)

    elif action == VOTE_ON_MOTION:
        assert type(position) == bool, 'Invalid position'


def assert_vk_is_valid(vk: str):
    assert vk is not None, 'No VK provided.'
    assert type(vk) == str, 'VK not a string.'
    assert len(vk) == 64, 'VK is not 64 characters.'
    int(vk, 16)


def introduce_motion(position: str, arg: str):
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