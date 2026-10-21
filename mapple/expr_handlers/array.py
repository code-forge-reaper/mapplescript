from mapple.nodes import MappleError


def Array(self, expr, env):
    return [self.evaluate_expr(element, env) for element in expr.elements]


def Access(self, expr, env):
    arr = self.evaluate_expr(expr.object, env)
    index = self.evaluate_expr(expr.index, env)
    if not isinstance(arr, (list, dict, str, tuple)) and not hasattr(
        arr, "__getitem__"
    ):
        raise MappleError(
            expr,
            f"Cannot access index of non-list/dict/indexible: {type(arr).__name__}",
        )
    if not isinstance(index, (int, str)):
        raise MappleError(
            expr,
            f"List/dict index must be a number or string. Got: {type(index).__name__}",
        )

    # TODO: instead of whatever we're doing here,
    ## we should check if it is indexable and index is number, if it is,
    ## we should check length, and see if it can actually get the value
    ## otherwise, do what lua does
    try:
        return arr[index]  # pyright: ignore[reportCallIssue, reportArgumentType]
    except (IndexError, KeyError):
        return None
        # raise MappleError(
        #    expr, f"Index/key '{index}' out of bounds or not found for object."
        # )
