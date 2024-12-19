old_time = datetime.datetime(2019, 1, 1)

@export
def gt():
    return now > old_time

@export
def lt():
    return now < old_time

@export
def eq():
    return now == old_time
