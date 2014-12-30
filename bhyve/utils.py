def flatten(itr):
    return (y for x in itr for y in x)


def flatmap(fn, itr):
    return flatten(map(fn, itr))
