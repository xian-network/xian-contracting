balances = Hash(default_value=0)

@construct
def seed():
    balances.key = 'con_erc20.balances'
    balances['stu'] = 99999999999999999

@export
def blah():
    return 1