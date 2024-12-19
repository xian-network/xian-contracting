@export
def call_me():
    return call_me_again()

@export
def call_me_again():
    return call_me_again_again()

@export
def call_me_again_again():
    return {
        'owner': ctx.owner,
        'this': ctx.this,
        'signer': ctx.signer,
        'caller': ctx.caller
    }
