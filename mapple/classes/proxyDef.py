class ProxyDef(Statement):
    def __init__(
        self,
        setter,
        getter,
        name,
        file,
        line,
        column,
    ):
        super().__init__("ProxyDef", file, line, column)
        self.name = name
        self.setter = setter
        self.getter = getter

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"ProxyDef({self.name})"

