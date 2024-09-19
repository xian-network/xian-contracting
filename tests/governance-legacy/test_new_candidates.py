from unittest import TestCase
from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Timedelta, DAYS, WEEKS, Datetime
from datetime import datetime as dt, timedelta as td


def master_candidates():
    import currency
    import election_house

    candidate_state = Hash(default_value=0)
    top_candidate = Variable(default_value='sys')

    no_confidence_state = Hash(default_value=0)
    top_no_confidence = Variable(default_value='sys')

    to_be_relinquished = Variable()

    STAMP_COST = 20_000
    MASTER_COST = 100_000

    controller = Variable()

    @construct
    def seed(masternode_contract='masternodes'):
        controller.set(masternode_contract)

    ###
    # STAKING
    ###
    @export
    def register():
        # Make sure someone is already staked
        assert not candidate_state['registered', ctx.signer], 'Already registered.'

        currency.transfer_from(MASTER_COST, ctx.this, ctx.caller)

        candidate_state['registered', ctx.signer] = True
        candidate_state['votes', ctx.signer] = 0

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
        candidate_state['votes', ctx.signer] += 1

        current_top = top_candidate.get()
        if candidate_state['votes', ctx.signer] > candidate_state['votes', current_top]:
            top_candidate.set(ctx.signer)

    @export
    def top_masternode():
        return top_candidate.get()

    @export
    def clear_top_votes():
        assert ctx.caller == controller.get(), 'Wrong smart contract caller.'
        candidate_state.clear('votes')

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
        no_confidence_state['votes', ctx.signer] += 1

        current_low = top_candidate.get()
        if no_confidence_state['votes', ctx.signer] > no_confidence_state['votes', current_low]:
            top_no_confidence.set(ctx.signer)

    # Returns relinquished first
    @export
    def last_masternode():
        r = to_be_relinquished.get()
        if r is not None:
            return r

        return top_no_confidence.get()

    @export
    def clear_nc_votes():
        assert ctx.caller == controller.get(), 'Wrong smart contract caller.'
        no_confidence_state.clear('votes')

    @export
    def force_removal(address):
        assert ctx.caller == controller.get(), 'Wrong smart contract caller.'
        candidate_state['registered', address] = False  # Registration is lost when no confidence vote. AKA: Stake revoked.

    @export
    def relinquish():
        assert ctx.signer in election_house.current_value_for_policy(controller.get())

        r = to_be_relinquished.get()
        if r is None:
            r.set(ctx.signer)
