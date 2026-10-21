from mapple.classes.breakFlow import BreakFlow
from mapple.classes.continueFlow import ContinueFlow
from mapple.classes.mappleError import MappleError
from mapple.classes.returnFlow import ReturnFlow
from mapple.mappleenv import Environment


def For(self, stmt, env):
    start = self.evaluate_expr(stmt.start, env)
    end = self.evaluate_expr(stmt.end, env)
    step = self.evaluate_expr(stmt.step, env) if stmt.step else 1

    if not all(isinstance(val, (int, float)) for val in [start, end, step]):
        raise MappleError(
            stmt,
            f"For loop bounds and step must be numbers. Got start: {type(start).__name__}, end: {type(end).__name__}, step: {type(step).__name__}",
        )

    # Python's range handles step correctly. For float steps, manual loop.
    # Assuming integer steps for now, as floats can lead to precision issues.
    # If MappleScript intends float steps, this will need adjustment.
    if isinstance(step, float):
        current_val = start
        while (step > 0 and current_val <= end) or (step < 0 and current_val >= end):
            loop_env = Environment(env)
            loop_env.define(stmt.variable, current_val)
            result = self.execute_block(stmt.body, loop_env)
            if isinstance(result, BreakFlow):
                break
            if isinstance(result, ReturnFlow):
                return result
            if isinstance(result, ContinueFlow):
                current_val += step
                continue
            current_val += step
    else:  # Integer step
        for i in range(start, end + (1 if step > 0 else -1), step):
            loop_env = Environment(env)
            loop_env.define(stmt.variable, i)
            result = self.execute_block(stmt.body, loop_env)
            if isinstance(result, BreakFlow):
                break
            if isinstance(result, ReturnFlow):
                return result
            if isinstance(result, ContinueFlow):
                continue


def ForEach(self, stmt, env):
    list_val = self.evaluate_expr(stmt.list, env)
    if not isinstance(list_val, (list, dict)) and not hasattr(list_val, "__iter__"):
        raise MappleError(
            stmt,
            f"Cannot iterate over non-array type for forEach loop. Got: {type(list_val).__name__}",
        )
    for item in list_val:
        loop_env = Environment(env)
        loop_env.define(stmt.variable, item)
        result = self.execute_block(stmt.body, loop_env)
        if isinstance(result, BreakFlow):
            break
        if isinstance(result, ReturnFlow):
            return result
        if isinstance(result, ContinueFlow):
            continue
