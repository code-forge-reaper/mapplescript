import json

# --- AST Node Base Classes ---
class Token:
    def __init__(self, type, value, file, line, column):
        self.type = type
        self.value = value
        self.file = file
        self.line = line
        self.column = column

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Token(type='{self.type}', value={repr(self.value)}, file='{self.file}', line={self.line}, column={self.column})"

    def to_dict(self):
        """Base serialization – overridden in subclasses."""
        return {
            "type": self.type,
            "value": repr(self.value),
            "file": self.file,
            "line": self.line,
            "column": self.column,
        }

    def to_json(self):
        """Return a JSON string for debug."""
        return json.dumps(self.to_dict(), indent=2)
