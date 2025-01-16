@export
def exported():
    return ctx.this, ctx.caller

@export
def getthis():
    return ctx.this, ctx.caller

@export
def nested_exported():
    return exported()
