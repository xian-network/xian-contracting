import currency
import election_house

candidate_state = Hash()
candidate_votes = Variable()

no_confidence_state = Hash()
no_confidence_votes = Variable()
to_be_relinquished = Variable()

STAMP_COST = 20_000
MASTER_COST = 100_000

controller = Variable()


@construct
def seed(masternode_contract='masternodes'):
    controller.set(masternode_contract)

    candidate_votes.set({})
    to_be_relinquished.set([])
    no_confidence_votes.set({})


###
# STAKING
###
@export
def register():
    # Make sure someone is already staked
    assert not candidate_state['registered', ctx.signer], 'Already registered.'

    currency.transfer_from(MASTER_COST, ctx.this, ctx.caller)

    candidate_state['registered', ctx.signer] = True

    cv = candidate_votes.get()
    cv[ctx.signer] = 0
    candidate_votes.set(cv)


@export
def unregister():
    mns = election_house.current_value_for_policy(controller.get())
    assert candidate_state['registered', ctx.signer], 'Not registered.'
    assert ctx.caller not in mns, "Can't unstake if in governance."

    currency.transfer(MASTER_COST, ctx.caller)


### ### ###

###
# VOTE CANDIDATE
###
@export
def vote_candidate(address):
    assert candidate_state['registered', address]

    # Determine if caller can vote
    v = candidate_state['last_voted', ctx.signer]
    assert v is None or now - v > datetime.DAYS * 1, 'Voting again too soon.'

    # Deduct small vote fee
    vote_cost = STAMP_COST / election_house.current_value_for_policy('stamp_cost')
    currency.transfer_from(vote_cost, 'blackhole', ctx.signer)

    # Update last voted variable
    candidate_state['last_voted', ctx.signer] = now

    # Update vote dict
    cv = candidate_votes.get()
    cv[address] += 1
    candidate_votes.set(cv)


@export
def top_masternode():
    cv = candidate_votes.get()

    if len(cv) == 0:
        return None

    top = sorted(cv.items(), key=lambda x: x[1], reverse=True)

    return top[0][0]


@export
def pop_top():
    assert ctx.caller == controller.get(), 'Wrong smart contract caller.'

    top = top_masternode()

    if top is None:
        return None

    cv = candidate_votes.get()
    del cv[top]
    candidate_votes.set(cv)


### ### ###

###
# NO CONFIDENCE VOTES
###
@export
def vote_no_confidence(address):
    # Determine if caller can vote
    assert address in election_house.current_value_for_policy(controller.get()), \
        'Cannot vote against a non-committee member'

    v = no_confidence_state['last_voted', ctx.signer]
    assert v is None or now - v > datetime.DAYS * 1, 'Voting again too soon.'

    # Deduct small vote fee
    vote_cost = STAMP_COST / election_house.current_value_for_policy('stamp_cost')
    currency.transfer_from(vote_cost, 'blackhole', ctx.signer)

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
    r = to_be_relinquished.get()
    if len(r) > 0:
        return r[0]

    nc = no_confidence_votes.get()
    if len(nc) == 0:
        return None

    last = sorted(nc.items(), key=lambda x: x[1], reverse=True)
    return last[0][0]


@export
def pop_last():
    assert ctx.caller == controller.get(), 'Wrong smart contract caller.'

    r = to_be_relinquished.get()

    if len(r) > 0:
        stepping_down = r.pop(0)

        to_be_relinquished.set(r)

        # If stepping down in no confidence, remove them
        nc = no_confidence_votes.get()
        if nc.get(stepping_down) is not None:
            del nc[stepping_down]
            no_confidence_votes.set(nc)

    else:
        last = last_masternode()

        nc = no_confidence_votes.get()
        if nc.get(last) is not None:
            del nc[last]
            no_confidence_votes.set(nc)

            candidate_state[
                'registered', last] = False  # Registration is lost when no confidence vote. AKA: Stake revoked.


@export
def force_removal(address):
    assert ctx.caller == controller.get(), 'Wrong smart contract caller.'
    candidate_state['registered', address] = False  # Registration is lost when no confidence vote. AKA: Stake revoked.


@export
def relinquish():
    assert ctx.signer in election_house.current_value_for_policy(controller.get())

    r = to_be_relinquished.get()
    r.append(ctx.signer)
    to_be_relinquished.set(r)
### ### ###