import con_erc20_clone

swaps = Hash()

@export
def initiate(participant: str, expiration: datetime.datetime, hashlock: str, amount: float):
    allowance = con_erc20_clone.allowance(ctx.caller, ctx.this)

    assert allowance >= amount, \
        "You cannot initiate an atomic swap without allowing '{}' " \
        "at least {} coins. You have only allowed {} coins".format(ctx.this, amount, allowance)

    swaps[participant, hashlock] = [expiration, amount]

    con_erc20_clone.transfer_from(amount, ctx.this, ctx.caller)

@export
def redeem(secret: str):

    hashlock = hashlib.sha256(secret)

    result = swaps[ctx.caller, hashlock]

    assert result is not None, 'Incorrect sender or secret passed.'

    expiration, amount = result

    assert expiration >= now, 'Swap has expired.'

    con_erc20_clone.transfer(amount, ctx.caller)
    swaps[ctx.caller, hashlock] = None # change this to respond to the del keyword?

@export
def refund(participant: str, secret: str):

    assert participant != ctx.caller and participant != ctx.signer, \
        'Caller and signer cannot issue a refund.'

    hashlock = hashlib.sha256(secret)

    result = swaps[participant, hashlock]

    assert result is not None, 'No swap to refund found.'

    expiration, amount = result

    assert expiration < now, 'Swap has not expired.'

    con_erc20_clone.transfer(amount, ctx.caller)
    swaps[participant, hashlock] = None


# Should fail if called
def test():
    return 123