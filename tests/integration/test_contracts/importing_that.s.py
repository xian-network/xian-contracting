import con_import_this

@export
def test():
    a = con_import_this.howdy()
    a -= 1000
    return a