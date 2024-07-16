INTRODUCE_MOTION = 'introduce_motion'
VOTE_ON_MOTION = 'vote_on_motion'

NO_MOTION = 0
REMOVE_MASTER = 1
ADD_SEAT = 2
REMOVE_SEAT = 3

VOTING_PERIOD = datetime.DAYS * 1

S = Hash()
boot_num = Variable()

@construct
def seed(initial_masternodes, bn=1):
    S['masternodes'] = initial_masternodes
    boot_num.set(bn)

    S['yays'] = 0
    S['nays'] = 0

    S['current_motion'] = NO_MOTION
    S['motion_opened'] = now

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

        elif now - S['motion_opened'] >= VOTING_PERIOD:
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
        # Get the top master
        new_mn = master_candidates.top_masternode()

        # Append it to the list, and remove it from pending
        if new_mn is not None:
            masters.append(new_mn)
            master_candidates.pop_top()

    elif current_motion == REMOVE_SEAT:
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
