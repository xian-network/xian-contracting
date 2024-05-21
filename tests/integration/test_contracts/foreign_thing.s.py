thing_H = ForeignHash(foreign_contract='con_thing', foreign_name='H')
thing_V = ForeignVariable(foreign_contract='con_thing', foreign_name='V')

@export
def read_H_hello():
    return thing_H['hello']

@export
def read_H_something():
    return thing_H['something']

@export
def read_V():
    return thing_V.get()

@export
def set_H(k: str, v: Any):
    thing_H[k] = v

@export
def set_V(v: Any):
    thing_V.set(v)