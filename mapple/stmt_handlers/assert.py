from mapple.classes.mappleError import MappleError


def Assert(self, stmt, env):
    e = self.evaluate_expr(stmt.expression, env)
    if not e:
        raise MappleError(stmt, f"{stmt.message}")
