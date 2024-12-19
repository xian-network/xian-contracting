import con_pass_hash

my_hash = Hash()

@export
def store(k: Any, v: Any):
    con_pass_hash.store_on_behalf(my_hash, k, v)

@export
def get(k: Any):
    return my_hash[k]
