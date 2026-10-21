from mapple.classes.baseToken import Token


class Expression(Token):
    def __init__(self, type, file, line, column):
        super().__init__(type, None, file, line, column)
