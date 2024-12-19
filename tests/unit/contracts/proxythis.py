@export
def proxythis(con: str):
    return importlib.import_module(con).getthis()

@export
def nestedproxythis(con: str):
    return importlib.import_module(con).nested_exported()

@export
def noproxy():
    return ctx.this, ctx.caller