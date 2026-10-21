from mapple.mappleenv import Environment


def FuncDef(self, stmt, env):
    # Named function – same machinery as a lambda, just with a name
    # and stored in the environment.
    func_wrapper = self._create_callable(
        stmt.parameters,
        stmt.body,
        env,
        name=stmt.name,
        node=stmt,
        context_name=f"function '{stmt.name}'",
    )
    env.define(stmt.name, func_wrapper)


def LocalFuncDef(self, stmt, env):
    _env = Environment(env)
    _env.localsOnly = True
    self.execute_stmt(stmt.fn, _env)
    env.define(stmt.fn.name, _env.get(stmt.fn.name).value, _env.get(stmt.fn.name).const)
