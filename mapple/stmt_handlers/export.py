from mapple.classes.mappleError import MappleError


def export(self, stmt, env):
    # Execute the inner statement first
    self.execute_stmt(stmt.expr, env)

    # Ensure exports dictionary exists (it should in modules, but create if missing)
    if not env.has("exports"):
        env.define("exports", {})
    exports_dict = env.get("exports").value

    inner = stmt.expr
    name = inner.name
    if inner.type in ("VarDecl", "ConstDecl", "FuncDecl", "ClassDefinition"):
        # For declarations, export the declared name
        if name in exports_dict:
            raise MappleError(stmt, f"cannot re-export: {name}")
        value = env.get(name).value
        exports_dict[name] = value

    elif inner.type == "ExpressionStmt":
        expr = inner.expression
        if expr.type == "ObjectLiteral":
            # export { a, b, c: d } → evaluate each property
            for prop in expr.properties:
                key = prop["key"]
                val_expr = prop["value"]
                if key in exports_dict:
                    raise MappleError(stmt, f"cannot re-export: {name}")
                if val_expr.type == "Identifier":
                    val = env.get(val_expr.name).value
                else:
                    val = self.evaluate_expr(val_expr, env)
                exports_dict[key] = val
        elif expr.type == "Identifier":
            # export a → export the variable 'a'
            name = expr.name
            if name in exports_dict:
                raise MappleError(stmt, f"cannot re-export: {name}")
            val = env.get(name).value
            exports_dict[name] = val
        else:
            raise MappleError(
                stmt, f"Cannot export expression of type {expr.type}"
            )

    else:
        raise MappleError(stmt, f"Cannot export statement of type {inner.type}")