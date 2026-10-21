from mapple.classes.controlFlow import ControlFlow
from mapple.mappleenv import Environment


def Scope(self, stmt, env):
    n_env = Environment(env)
    n_env.localsOnly = True
    result = self.execute_block(stmt.body, n_env)
    env.define(stmt.name, n_env)
    if isinstance(result, ControlFlow):
        return result
