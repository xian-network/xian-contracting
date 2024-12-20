v = Variable()

@export
def get():
    return v.get()

@construct
def seed():
    v.set(42)
