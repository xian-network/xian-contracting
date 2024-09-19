import election_house
import currency

masternode_stakes = Hash()
delegate_stakes = Hash()

MASTER_COST = 100_000
DELEGATE_COST = 10_000

@export
def stake_masternode():
    currency.transfer_from(MASTER_COST, ctx.caller, ctx.this)
    masternode_stakes[ctx.caller] = MASTER_COST

@export
def stake_delegate():
    currency.transfer_from(DELEGATE_COST, ctx.caller, ctx.this)
    delegate_stakes[ctx.caller] = DELEGATE_COST

@export
def unstake_masternode():
    mns = election_house.get_policy('masternodes')

    assert masternode_stakes[ctx.caller] >= MASTER_COST
    assert ctx.caller not in mns, "Can't unstake if in governance."

    currency.transfer(masternode_stakes[ctx.caller], ctx.caller)

@export
def unstake_delegate():
    mns = election_house.get_policy('delegate')

    assert delegate_stakes[ctx.caller] >= DELEGATE_COST
    assert ctx.caller not in mns, "Can't unstake if in governance."

    currency.transfer(delegate_stakes[ctx.caller], ctx.caller)

