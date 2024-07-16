import currency
import election_house

no_confidence_state = Hash()
no_confidence_votes = Variable()
to_be_relinquished = Variable()

STAMP_COST = 20_000

@construct
def seed():
    to_be_relinquished.set([])
    no_confidence_votes.set({})

@export
def vote_no_confidence(address):
    # Determine if caller can vote
    v = no_confidence_state['last_voted', ctx.signer]
    assert now - v > DAYS * 1 or v is None, 'Voting again too soon.'

    # Deduct small vote fee
    vote_cost = STAMP_COST / election_house.get_policy('stamp_cost')
    currency.transfer_from(vote_cost, ctx.signer, 'blackhole')

    # Update last voted variable
    no_confidence_state['last_voted', ctx.signer] = now

    # Update vote dict
    nc = no_confidence_votes.get()

    if nc.get(address) is None:
        nc[address] = 1
    else:
        nc[address] += 1

    no_confidence_votes.set(nc)

@export
def last_masternode():
    r = relinquish.get()
    if len(r) > 0:
        return r[0]

    nc = no_confidence_votes.get()
    last = sorted(nc.items(), key=lambda x: x[1], reverse=True)
    return last[0][0]


@export
def pop_last():
    assert ctx.caller == 'masternodes', 'Wrong smart contract caller.'

    r = relinquish.get()

    if len(r) > 0:
        r.pop(0)
        relinquish.set(r)

    else:
        last = last_masternode()

        nc = no_confidence_votes.get()
        del nc[last]
        no_confidence_votes.set(nc)

@export
def relinquish():
    assert ctx.signer in election_house.get_policy('masternodes')

    r = relinquish.get()
    r.append(ctx.signer)
    relinquish.set(r)