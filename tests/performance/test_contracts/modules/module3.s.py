import module6
import module7

@export
def get_context():
    return {
        'owner': ctx.owner,
        'this': ctx.this,
        'signer': ctx.signer,
        'caller': ctx.caller
    }
