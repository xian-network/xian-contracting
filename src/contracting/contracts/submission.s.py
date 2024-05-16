@__export('submission')
def submit_contract(name: str, code: str, owner: Any=None, constructor_args: dict={}):
    if ctx.caller != 'sys':
        assert name.startswith('con_'), 'Contract must start with con_!'

    assert ctx.caller == ctx.signer, 'Contract cannot be called from another contract!'
    assert len(name) <= 64, 'Contract name length exceeds 64 characters!'
    assert name.islower(), 'Contract name must be lowercase!'

    __Contract().submit(
        name=name,
        code=code,
        owner=owner,
        constructor_args=constructor_args,
        developer=ctx.caller
    )


@__export('submission')
def change_developer(contract: str, new_developer: str):
    d = __Contract()._driver.get_var(contract=contract, variable='__developer__')
    assert ctx.caller == d, 'Sender is not current developer!'

    __Contract()._driver.set_var(
        contract=contract,
        variable='__developer__',
        value=new_developer
    )
