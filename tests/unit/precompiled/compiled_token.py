# Monkey patch for testing, as this is purely for 'interface enforcement' testing
from contracting.storage.orm import Variable, Hash

class ctx:
    caller = 1

__supply = Variable(contract='__main__', name='supply')
__balances = Hash(default_value=0, contract='__main__', name='balances')


def ____():
    __balances['stu'] = 1000000
    __balances['colin'] = 100
    __supply.set(__balances['stu'] + __balances['colin'])

def transfer(amount, to):
    sender = ctx.caller
    assert __balances[sender] >= amount, 'Not enough coins to send!'
    __balances[sender] -= amount
    __balances[to] += amount

def balance_of(account):
    return __balances[account]

def total_supply():
    return __supply.get()

def allowance(owner, spender):
    return __balances[owner, spender]

def approve(amount, to):
    sender = ctx.caller
    __balances[sender, to] += amount
    return __balances[sender, to]

def transfer_from(amount, to, main_account):
    sender = ctx.caller
    assert __balances[main_account, sender
        ] >= amount, 'Not enough coins approved to send! You have {} and are trying to spend {}'.format(
        __balances[main_account, sender], amount)
    assert __balances[main_account] >= amount, 'Not enough coins to send!'
    __balances[main_account, sender] -= amount
    __balances[main_account] -= amount
    __balances[to] += amount

def __private_func():
    return 5