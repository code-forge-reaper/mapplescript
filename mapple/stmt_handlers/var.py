from mapple.typechecker import check_type


def declare(self, stmt, env):
    value = self.evaluate_expr(stmt.initializer, env)
    if stmt.type_annotation:
        check_type(stmt.type_annotation, value, stmt)
    env.define(stmt.name, value, stmt.type == "ConstDecl", stmt.type_annotation)

