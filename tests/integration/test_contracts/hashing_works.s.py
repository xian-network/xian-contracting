@export
def t_sha3(s: str):
    return hashlib.sha3(s)

@export
def t_sha256(s: str):
    return hashlib.sha256(s)
