balances = Hash()

@construct
def seed():
    balances['stu'] = 1000000
    balances['colin'] = 100

@export
def transfer(amount: int, to: str):
    sender = ctx.signer
    assert balances[sender] >= amount, 'Not enough coins to send!'

    balances[sender] -= amount

    if balances[to] is None:
        balances[to] = amount
    else:
        balances[to] += amount

@export
def balance(account: str):
    return balances[account]
