def Lambda(self, expr, env):
    # A lambda is just an unnamed / uuid-named function.
    # Same creation path as FuncDecl; class context is captured
    # automatically by _create_callable.
    return self._create_callable(
        expr.parameters,
        expr.body,
        env,
        name=None,  # → random uuid
        node=expr,
        context_name="lambda",
    )
