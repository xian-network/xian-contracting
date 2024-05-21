fv = ForeignVariable(foreign_contract='con_test_orm_variable_contract', foreign_name='v')

@export
def set_fv(i: int):
    fv.set(i)

@export
def get_fv():
    return fv.get()
