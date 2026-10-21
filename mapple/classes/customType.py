class CustomType:
    def __init__(self, name, properties, file, line, column):
        self.name = name
        self.properties = properties
        self.file = file
        self.line = line
        self.column = column

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        props = ", ".join(str(p) for p in self.properties)
        return f"CustomType(name='{self.name}', properties=[{props}])"

    def to_dict(self):
        return {
            "type": "CustomType",
            "name": self.name,
            "properties": [p.to_dict() for p in self.properties],
            "file": self.file,
            "line": self.line,
            "column": self.column,
        }

