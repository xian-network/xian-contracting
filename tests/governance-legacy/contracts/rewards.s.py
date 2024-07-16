value = Variable()
current_votes = Hash(default_value=0)
has_voted = Hash()

last_election = Variable()
election_start = Variable()

election_length = datetime.DAYS * 1
election_interval = datetime.WEEKS * 1

@construct
def seed():
    value.set([0.5, 0.5, 0, 0])
    last_election.set(now)
    election_start.set(None)

@export
def current_value():
    return value.get()

@export
def vote(vk, obj):
    if election_start.get() is not None:
        tally_vote(vk, obj)

        # If it has been over a day since the election started... End the election
        if now - election_start.get() >= election_length:
            # Calculate ratio of votes
            masternode_votes = current_votes['masternodes'] or 1
            delegate_votes = current_votes['delegates'] or 1
            blackhole_votes = current_votes['blackhole'] or 1
            foundation_votes = current_votes['foundation'] or 1

            total_votes = masternode_votes + delegate_votes + blackhole_votes + foundation_votes

            # Do the same for each party before dividing
            mn = masternode_votes / total_votes
            dl = delegate_votes / total_votes
            bh = blackhole_votes / total_votes
            fd = foundation_votes / total_votes

            # Set the new value
            value.set([mn, dl, bh, fd])

            # Reset everything
            election_start.set(None)
            last_election.set(now)
            current_votes.clear()
            has_voted.clear()

    # If its been 1 week since the last election ended... Start the election
    elif now - last_election.get() > election_interval:
        # Set start to now
        election_start.set(now)
        current_votes.clear()
        tally_vote(vk, obj)


def tally_vote(vk, obj):
    assert vote_is_valid(obj), 'Invalid vote object passed!'
    assert has_voted[vk] is None, 'VK has already voted!'

    has_voted[vk] = True

    a, b, c, d = obj

    current_votes['masternodes'] += a
    current_votes['delegates'] += b
    current_votes['blackhole'] += c
    current_votes['foundation'] += d


def vote_is_valid(obj):
    if type(obj) != list:
        return False

    if len(obj) != 4:
        return False

    s = 0
    for o in obj:
        if type(o) != int:
            return False
        if o < 0:
            return False
        s += o

    if s != 100:
        return False

    return True
