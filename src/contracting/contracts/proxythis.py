@export
def proxythis(con: str):
    return importlib.import_module(con).getthis()

@export
def noproxy():
    return ctx.this, ctx.caller