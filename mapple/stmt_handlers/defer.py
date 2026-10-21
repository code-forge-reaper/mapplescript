def defer(self, stmt,env):
    for s in stmt.body:
        env.add_deferred(s)
