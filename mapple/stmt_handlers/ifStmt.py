from mapple.classes.controlFlow import ControlFlow
from mapple.mappleenv import Environment


def If(self, stmt, env):
    condition = self.evaluate_expr(stmt.condition, env)
    if condition:
        result = self.execute_block(stmt.then_block, Environment(env))
        if isinstance(result, ControlFlow):
            return result
    elif stmt.else_if:
        matched = False
        for elseif_block in stmt.else_if:
            elseif_condition = self.evaluate_expr(elseif_block["condition"], env)
            if elseif_condition:
                result = self.execute_block(elseif_block["body"], Environment(env))
                if isinstance(result, ControlFlow):
                    return result
                matched = True
                break
        if not matched and stmt.else_block:
            result = self.execute_block(stmt.else_block, Environment(env))
            if isinstance(result, ControlFlow):
                return result
    elif stmt.else_block:
        result = self.execute_block(stmt.else_block, Environment(env))
        if isinstance(result, ControlFlow):
            return result
