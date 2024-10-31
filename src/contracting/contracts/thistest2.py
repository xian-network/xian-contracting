@export
def exported():
    return 0

@export
def getthis():
    exported()
    return ctx.this, ctx.caller
 