class PropertyHandler(Statement):
    def __init__(self, name, getter, setter, file, line, column):
        super().__init__("PropertyHandler", file, line, column)
        self.name = name
        self.getter = getter
        self.setter = setter

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"PropertyHandler(name={self.name}, getter={self.getter}, setter={self.setter})"

    def to_dict(self):
        base = super().to_dict()
        base["name"] = _serialize_node(self.name)
        base["getter"] = _serialize_node(self.getter)
        base["setter"] = _serialize_node(self.setter)
        return base
