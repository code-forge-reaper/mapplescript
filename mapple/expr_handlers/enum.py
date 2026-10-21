from mapple.mappleenv import Environment


def Enum(self, expr, env):
    v = Environment()  # no sense copying env here
    v.values = {}
    for i in enumerate(expr.values):
        v.define(expr.values[i], i)

    v.lock()
    return v
