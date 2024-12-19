fh = ForeignHash(foreign_contract='con_orm_hash_contract', foreign_name='h')

@export
def set_fh(k: str, v: int):
    fh[k] = v

@export
def get_fh(k: str):
    return fh[k]
