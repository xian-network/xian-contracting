votable = Variable()

votes = Hash()

in_election = Variable()
last_election_end_time = Variable() # Datetime. now - last_election_end_time to determine if a new election can start
election_interval = Variable() # Time delta. How often elections can be run
voting_period = Variable() # Time delta. How long you can vote for
election_start_time = Variable()

@construct
def seed():
    votable.set(100)

    election_interval.set(datetime.WEEKS * 1)
    voting_period.set(datetime.DAYS * 1)

    reset_election_variables()

@export
def get_votable():
    return votable.get()

@export
def vote(v):
    # Check to make sure that there is an election
    if in_election.get():
        submit_vote(v)
        if now - election_start_time.get() >= voting_period.get():
            # Tally votes and set the new value
            result = median(votes.all())
            votable.set(result)

            reset_election_variables()
    else:
        # If there isn't, it might be time for a new one, so start it if so.
        # You can then submit your vote as well.
        if now - last_election_end_time.get() > election_interval.get():
            # Start the election and set the proper variables
            election_start_time.set(now)
            in_election.set(True)

            submit_vote(v)
        else:
            raise Exception('Outside of governance parameters.')


def submit_vote(v):
    v = int(v) # Cast to int. Fails if not an int
    assert votes[ctx.caller] is None, '{} has already voted! Cannot vote twice.'.format(ctx.caller)
    votes[ctx.caller] = v


def median(vs):
    sorted_votes = sorted(vs)
    index = (len(sorted_votes) - 1) // 2

    if len(sorted_votes) % 2:
        return sorted_votes[index]
    else:
        return (sorted_votes[index] + sorted_votes[index + 1])/2


def reset_election_variables():
    last_election_end_time.set(now)
    in_election.set(False)
    votes.clear()
