v = Variable()

@export
def set_v(i: int):
    v.set(i)

@export
def get_v():
    return v.get()
