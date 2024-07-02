delegates = Variable()

@construct
def seed():
    masternodes.set([
        'poo',
        '222',
        '333'
    ])


@export
def get_all():
    return delegates.get()