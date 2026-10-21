from mapple.classes.controlFlow import ControlFlow
from mapple.classes.mappleError import MappleError
from mapple.mappleenv import Environment


def Switch(self, stmt, env):
    value = self.evaluate_expr(stmt.expression, env)
    matched = False
    default_case_body = None
    for case in stmt.cases:
        if case.case_expr is None:  # This is the default case
            default_case_body = case.body
        else:
            case_val = self.evaluate_expr(case.case_expr, env)
            if value == case_val:
                result = self.execute_block(case.body, Environment(env))
                if isinstance(result, ControlFlow):
                    return result
                matched = True
                break  # Exit switch after first match

    if not matched and default_case_body and not stmt.strict:
        result = self.execute_block(default_case_body, Environment(env))
        if isinstance(result, ControlFlow):
            return result

    if stmt.strict and not matched:
        raise MappleError(
            stmt, f"Switch statement did not match any case for value: {value}"
        )
