'''
how the modules import each other. this is to test ctx.caller etc

   1
 |   |
 2   3
| | | |
4 5 6 7
  |
  8

'''

import module2
import module3


@export
def get_context():
    return {
        'owner': ctx.owner,
        'this': ctx.this,
        'signer': ctx.signer,
        'caller': ctx.caller
    }
