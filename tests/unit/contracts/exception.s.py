balances = Hash(default_value=0)

@construct
def seed():
    balances['stu'] = 999
    balances['colin'] = 555

@export
def transfer(amount: int, to: str):
    sender = ctx.caller
    assert balances[sender] >= amount, 'Not enough coins to send!'

    balances[sender] -= amount
    balances[to] += amount

    raise Exception('This is an exception')

@export
def balance_of(account: str):
    return balances[account]