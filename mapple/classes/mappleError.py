class MappleError(Exception):
    """Custom error class for MappleScript, including location information."""

    def __init__(self, token, user_message=None):
        file = getattr(token, "file", "unknown_file") if token else "unknown_file"
        line = getattr(token, "line", 0) if token else 0
        column = getattr(token, "column", 0) if token else 0
        token_value = getattr(token, "value", "N/A") if token else "N/A"
        self.message = f"{file}:{line}:{column}: {user_message or 'unknown error at token: ' + str(token_value)}"
        super().__init__(self.message)
        self.line = line
        self.column = column
        self.file = file
        self.user_message = user_message
        self.token_value = token_value

    def to_dict(self):
        return {
            "type": "MappleError",
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "user_message": self.user_message,
            "token_value": str(self.token_value),
        }
