class CustomTypeProperty:
    def __init__(self, name, type):
        self.name = name
        self.type = type

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"CustomTypeProperty(name='{self.name}', type='{self.type}')"

    def to_dict(self):
        return {"name": self.name, "type": self.type}
