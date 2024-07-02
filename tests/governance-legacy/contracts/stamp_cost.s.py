import election_house

S = Hash()

ELECTION_INTERVAL = datetime.DAYS * 3
VOTING_PERIOD = datetime.DAYS * 1


@construct
def seed(initial_rate):
    S['rate'] = initial_rate
    reset()


@export
def current_value():
    return S['rate']


@export
def vote(vk, obj):
    assert_vote_is_valid(vk, obj)

    # Check to make sure that there is an election
    if S['in_election']:
        S['votes', vk] = obj

        if now - S['election_start_time'] >= VOTING_PERIOD:
            # Tally votes and set the new value
            result = median(S.all('votes'))
            S['rate'] = result

            reset()
    elif now - S['last_election_end_time'] > ELECTION_INTERVAL:
        # Start the election and set the proper variables
        S['election_start_time'] = now
        S['in_election'] = True
        S['votes', vk] = obj


def assert_vote_is_valid(vk, obj):
    current_rate = S['rate']
    assert type(obj) == int, 'Vote is not an int'
    assert current_rate / 2 <= obj <= current_rate * 2, 'Proposed rate is not within proper boundaries.'

    masternode_policy = election_house.current_value_for_policy(policy='masternodes')

    assert vk in masternode_policy['masternodes'], 'VK is not a masternode!'
    assert S['votes', vk] is None, 'VK already voted!'


def median(vs):
    sorted_votes = sorted(vs)
    index = (len(sorted_votes) - 1) // 2

    if len(sorted_votes) % 2:
        return sorted_votes[index]
    else:
        return (sorted_votes[index] + sorted_votes[index + 1]) / 2


def reset():
    S['last_election_end_time'] = now
    S['in_election'] = False
    S.clear('votes')