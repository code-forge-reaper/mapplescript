from mapple.classes.breakFlow import BreakFlow
from mapple.classes.continueFlow import ContinueFlow
from mapple.classes.returnFlow import ReturnFlow
from mapple.mappleenv import Environment


def Until(self, stmt, env):
    while not self.evaluate_expr(stmt.condition, env):
        result = self.execute_block(stmt.body, Environment(env))
        if isinstance(result, BreakFlow):
            break
        if isinstance(result, ReturnFlow):
            return result
        if isinstance(result, ContinueFlow):
            continue
