from .baseToken import Token


class Statement(Token):
    def __init__(self, type, file, line, column):
        super().__init__(type, None, file, line, column)
