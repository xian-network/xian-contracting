@export
def called_from_a_far():
    m = importlib.import_module('all_in_one')
    return m.call_me_again_again()

@export
def called_from_a_far_stacked():
    m = importlib.import_module('all_in_one')
    return m.call()