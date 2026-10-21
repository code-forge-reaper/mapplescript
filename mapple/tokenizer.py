import pathlib

from mapple.classes.mappleError import MappleError
from mapple.classes.baseToken import Token

# from .classes import MappleError, Token


# TODO: convert each "if" to a function call
# so it's actually decent


class Tokenizer:
    keywords = [
        "var",
        "const",
        "if",
        "else",
        "elseif",
        "end",
        "break",
        "continue",
        "func",
        "local",
        "return",
        "as",
        "export",
        "scope",
        "while",
        "until",
        "for",
        "do",
        "in",
        "test",
        "failed",
        "defer",
        "matches",
        "private",
        "strict",
        "default",
        "using",
        "define",
        "enum",
        "assert",
        "class",
        "record",
        "inherits",
        "static",
        "new",
        "with",
        "unpack",
        "compact",
        "property",
    ]

    # --- Tokenization ---
    def __init__(self, source: str, file: str | pathlib.Path):
        self.source = source
        self.file = file

    def tokenize(self):
        tokens = []
        i = 0
        line = 1
        col = 1
        source = self.source
        file = self.file
        length = len(source)

        while i < length:
            char = source[i]
            start_col = col
            next_char = source[i + 1] if i + 1 < length else ""
            # --- Shebang support (must be at file start) ---
            if (
                line == 1
                and col == 1
                and char == "#"
                and i + 1 < length
                and source[i + 1] == "!"
            ):
                # Consume everything until newline or EOF
                while i < length and source[i] != "\n":
                    i += 1
                # If we stopped at a newline, consume it so the whitespace handler doesn't see it
                if i < length and source[i] == "\n":
                    i += 1
                    line += 1
                    col = 1
                # else: reached EOF without newline – that's fine, just stop
                continue
            # Skip whitespace.
            if char.isspace():
                if char == "\n":
                    line += 1
                    col = 1
                else:
                    col += 1
                i += 1
                continue

            # --- Comment support ---
            if char == "/" and next_char == "/":  # Single-line comment
                while i < length and source[i] != "\n":
                    i += 1
                continue
            if char == "/" and next_char == "*":  # Multi-line comment
                i += 2
                col += 2
                while i < length and not (
                    source[i] == "*" and i + 1 < length and source[i + 1] == "/"
                ):
                    if source[i] == "\n":
                        line += 1
                        col = 1
                    else:
                        col += 1
                    i += 1
                if i + 1 < length and source[i] == "*" and source[i + 1] == "/":
                    i += 2
                    col += 2
                else:
                    raise MappleError(
                        Token("error", "Unterminated comment", file, line, col),
                        "Unterminated multi-line comment",
                    )
                continue

            # --- Operators (prioritize longer matches) ---
            matched_operator = False
            two_char_ops = [
                "+=",
                ">>",
                "<<",
                "-=",
                "*=",
                "/=",
                "%=",
                "==",
                "!=",
                "<=",
                ">=",
                "&&",
                "||",
                "->",
                "=>",
                "**",
            ]
            current_two_char = char + next_char

            if current_two_char in two_char_ops:
                tokens.append(
                    Token("operator", current_two_char, file, line, start_col)
                )
                i += 2
                col += 2
                matched_operator = True
            else:
                # Single-character operators that might be part of two-char ops, or stand alone
                potential_single_ops = "=+-*/%^<>!.|&"
                if char in potential_single_ops:
                    tokens.append(Token("operator", char, file, line, start_col))
                    i += 1
                    col += 1
                    matched_operator = True
                else:
                    # Other single-character punctuation/operators
                    other_single_ops = "()[]{},:#$@"
                    if other_single_ops.find(char) != -1:  # Use find for string check
                        tokens.append(Token("operator", char, file, line, start_col))
                        i += 1
                        col += 1
                        matched_operator = True

            if matched_operator:
                continue
            # Numbers (decimal, hex, unicode, binary)

            if char.isdigit():

                def collect_digits(valid, allow_underscore=True):
                    nonlocal i, col

                    digits = ""

                    while i < length:
                        c = source[i]

                        if allow_underscore and c == "_":
                            i += 1
                            col += 1
                            continue

                        if c not in valid:
                            break

                        digits += c
                        i += 1
                        col += 1

                    if not digits:
                        raise MappleError(
                            Token("error", "Invalid numeric literal", file, line, col),
                            "Invalid numeric literal",
                        )
                    return digits

                def read_digits(valid, base, allow_underscore=True):
                    return int(collect_digits(valid, allow_underscore), base)

                # prefixed numbers
                if i + 1 < length and source[i] == "0":
                    prefix = source[i + 1].lower()

                    if prefix in ("x", "b"):
                        i += 2
                        col += 2

                        if prefix == "x":
                            value = read_digits("0123456789abcdefABCDEF", 16)
                            tokens.append(Token("number", value, file, line, start_col))

                        elif prefix == "b":
                            bits = ""
                            while i < length and source[i] in "01":
                                bits += source[i]
                                i += 1
                                col += 1

                            tokens.append(
                                Token("number", int(bits, 2), file, line, start_col)
                            )

                        continue

                # decimal / float (with underscores, no trailing dot)
                int_part = collect_digits("0123456789")  # integer part mandatory
                if i < length and source[i].isalpha():
                    raise MappleError(
                        Token("error", "Invalid integer", file, line, col),
                        "This is not a valid integer",
                    )

                if i < length and source[i] == ".":
                    i += 1
                    col += 1
                    # fractional part must contain at least one digit (underscores allowed but must resolve to digits)
                    try:
                        frac_part = collect_digits("0123456789")
                    except MappleError as e:
                        # collect_digits raised because no digits found -> that's a trailing dot
                        raise MappleError(
                            Token("error", "Invalid numeric literal", file, line, col),
                            "Trailing dot in numeric literal",
                        ) from e
                    if i < length and source[i].isalpha():
                        raise MappleError(
                            Token("error", "Invalid float", file, line, col),
                            "This is not a valid float",
                        )

                    num_str = f"{int_part}.{frac_part}"
                    tokens.append(
                        Token("number", float(num_str), file, line, start_col)
                    )
                else:
                    # plain integer
                    tokens.append(
                        Token("number", int(int_part, 10), file, line, start_col)
                    )
                continue
            # Module-level constants (hoisted out of the lexer loop)
            string_quotes = ('"', "'", "`")
            octal_digits = "01234567"

            string_escapes = {
                "n": "\n",
                "t": "\t",
                "r": "\r",
                "\\": "\\",
                '"': '"',
                "'": "'",
            }
            if char in string_quotes:
                quote = char
                is_raw = quote == "`"
                i += 1
                value = []

                while i < length:
                    c = source[i]

                    if c == quote:
                        break

                    if c == "\\":
                        i += 1
                        if i >= length:
                            raise MappleError(
                                Token("error", "Unterminated escape", file, line, col),
                                "Unterminated escape sequence",
                            )

                        esc = source[i]

                        if is_raw:
                            # Raw string: keep the backslash and the escaped char verbatim.
                            value.append("\\")
                            value.append(esc)
                        elif esc in octal_digits:
                            # Octal escape: \o, \oo, or \ooo
                            start = i
                            while (
                                i < length
                                and i - start < 3
                                and source[i] in octal_digits
                            ):
                                i += 1
                            value.append(chr(int(source[start:i], 8)))
                            col += i - start
                            continue
                        elif esc in string_escapes:
                            value.append(string_escapes[esc])
                        else:
                            raise MappleError(
                                Token(
                                    "error", "Invalid escape sequence", file, line, col
                                ),
                                f"Invalid escape sequence \\{esc}",
                            )

                        # We consumed one extra source character (the escaped one).
                        if esc == "\n":
                            line += 1
                            col = 1
                        else:
                            col += 2
                        i += 1
                        continue

                    value.append(c)

                    if c == "\n":
                        line += 1
                        col = 1
                    else:
                        col += 1
                    i += 1

                if i >= length or source[i] != quote:
                    raise MappleError(
                        Token("error", "Unterminated string", file, line, col),
                        "Unterminated string literal",
                    )

                i += 1
                col += 1
                tokens.append(Token("string", "".join(value), file, line, start_col))
                continue
            # Identifiers, keywords, booleans.
            if char.isalpha() or char == "_":
                id_str = ""
                while i < length and (source[i].isalnum() or source[i] == "_"):
                    id_str += source[i]
                    i += 1
                    col += 1
                if id_str in self.keywords:
                    tokens.append(Token("keyword", id_str, file, line, start_col))
                elif id_str == "between":
                    tokens.append(Token("operator", "between", file, line, start_col))
                else:
                    tokens.append(Token("identifier", id_str, file, line, start_col))
                continue

            raise MappleError(
                Token("error", char, file, line, col), f"Unexpected character: {char}"
            )

        return tokens
