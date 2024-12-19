import module4
import module5

@export
def get_context():
    return {
        'owner': ctx.owner,
        'this': ctx.this,
        'signer': ctx.signer,
        'caller': ctx.caller
    }
