import currency
import election_house

S = Hash()
Q = Variable()
STAMP_COST = 20_000
MASTER_COST = 100_000

@construct
def seed():
    # Set as empty list
    Q.set({})

@export
def register():
    # Make sure someone is already staked
    assert not S['registered', ctx.signer], 'Already registered.'

    currency.transfer_from(MASTER_COST, ctx.caller, ctx.this)

    S['registered', ctx.signer] = True

    _q = Q.get()
    _q[ctx.signer] = 0
    Q.set(_q)

@export
def unregister():
    mns = election_house.get_policy('masternodes')
    assert ctx.caller not in mns, "Can't unstake if in governance."
    currency.transfer(MASTER_COST, ctx.caller)

@export
def vote(address):
    assert S['registered', address]

    # Determine if caller can vote
    v = S['last_voted', ctx.signer]
    assert now - v > DAYS * 1 or v is None, 'Voting again too soon.'

    # Deduct small vote fee
    vote_cost = STAMP_COST / election_house.get_policy('stamp_cost')
    currency.transfer_from(vote_cost, ctx.signer, 'blackhole')

    # Update last voted variable
    S['last_voted', ctx.signer] = now

    # Update vote dict
    _q = Q.get()
    _q[address] += 1
    Q.set(_q)

@export
def top_masternode():
    _q = Q.get()

    if len(_q) == 0:
        return None

    top = sorted(_q.items(), key=lambda x: x[1], reverse=True)

    return top[0][0]

@export
def pop_top():
    assert ctx.caller == 'masternodes', 'Wrong smart contract caller.'

    top = top_masternode()

    _q = Q.get()
    del _q[top]
    Q.set(_q)
