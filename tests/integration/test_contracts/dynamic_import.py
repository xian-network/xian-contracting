@export
def called_from_a_far():
    m = importlib.import_module('con_all_in_one')
    res = m.call_me_again_again()

    return [res, {
        'name': 'called_from_a_far',
        'owner': ctx.owner,
        'this': ctx.this,
        'signer': ctx.signer,
        'caller': ctx.caller,
        'entry': ctx.entry,
        'submission_name': ctx.submission_name
    }]