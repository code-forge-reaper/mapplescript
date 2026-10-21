from mapple.mappleenv import Environment


def Enum(self, expr, env):
    v = Environment()  # no sense copying env here
    v.values = {}
    for i, name in enumerate(expr.values):
        v.define(name, i)

    v.lock()
    return v
