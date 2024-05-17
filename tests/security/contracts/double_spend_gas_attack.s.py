import con_erc20

@construct
def seed():
    pass

@export
def double_spend(receiver: str):
    allowance = con_erc20.allowance(owner=ctx.caller, spender=ctx.this)
    con_erc20.transfer_from(amount=allowance, to=receiver, main_account=ctx.caller)

    i = 0
    while True:
        i += 1
