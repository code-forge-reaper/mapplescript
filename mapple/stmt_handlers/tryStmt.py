from mapple.classes.controlFlow import ControlFlow
from mapple.classes.returnFlow import ReturnFlow
from mapple.mappleenv import Environment


def Try(self, stmt, env):
    try:
        result = self.execute_block(stmt.try_block, env)
        if isinstance(result, ControlFlow) and not isinstance(result, ReturnFlow):
            return result
    except Exception as e:  # Catch all other Python exceptions
        catch_env = Environment(env)
        # If e is a MappleError, use it directly. Otherwise, wrap it.
        catch_env.define(stmt.error_var, e, True)
        result = self.execute_block(stmt.catch_block, catch_env)
        if isinstance(result, ControlFlow):
            return result
