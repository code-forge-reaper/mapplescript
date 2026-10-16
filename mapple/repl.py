"""Interactive Read-Eval-Print Loop for MappleScript."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

from mapple.nodes import MappleError, ControlFlow
from mapple.runtime import Interpreter
from mapple.tokenizer import Tokenizer
from modules.modules import setup


PROMPT = "mapple> "
CONT_PROMPT = "   ...> "
EXIT_COMMANDS = {"exit", "quit", ":q", ":quit", ":exit"}


def _is_incomplete(err: BaseException) -> bool:
    """Heuristic: parse error that usually means the user is still typing a block."""
    msg = str(err).lower()
    markers = (
        "unexpected end of input",
        "unexpected eof",
        "got eof",
        "expected token",
    )
    # "expected token ... got EOF" is the common incomplete-block signal
    if "got eof" in msg or "unexpected end of input" in msg:
        return True
    if "expected token" in msg and "eof" in msg:
        return True
    return False


def _read_line(prompt: str) -> str | None:
    try:
        return input(prompt)
    except EOFError:
        print()
        return None
    except KeyboardInterrupt:
        print()
        return ""  # cancel current line, stay in REPL


def run_repl() -> int:
    """Start an interactive Mapple session. Returns process exit code."""
    # Bootstrap a long-lived interpreter whose globals persist across inputs.
    interp = Interpreter("", "<repl>")
    setup(interp, interp.globals)

    print("MappleScript REPL  (exit / quit / Ctrl-D to leave)")
    print("Multi-line blocks are accepted until they parse cleanly.\n")

    buffer: list[str] = []

    while True:
        prompt = PROMPT if not buffer else CONT_PROMPT
        line = _read_line(prompt)
        if line is None:
            # Ctrl-D
            if buffer:
                buffer.clear()
                print("(cancelled)")
                continue
            break

        stripped = line.strip()
        if not buffer and stripped in EXIT_COMMANDS:
            break

        # Empty line with nothing buffered → just show prompt again
        if not buffer and stripped == "":
            continue

        buffer.append(line)
        source = "\n".join(buffer)

        try:
            tk = Tokenizer(source, "<repl>")
            statements = tk.parse_block()
        except MappleError as err:
            if _is_incomplete(err):
                # Keep buffering
                continue
            print(err.message, file=sys.stderr)
            buffer.clear()
            continue
        except Exception as err:
            print(f"{type(err).__name__}: {err}", file=sys.stderr)
            buffer.clear()
            continue

        # Parsed successfully — execute against the shared globals
        buffer.clear()
        try:
            # Prefer showing the value of a lone expression
            if (
                len(statements) == 1
                and getattr(statements[0], "type", None) == "ExpressionStmt"
            ):
                value = interp.evaluate_expr(statements[0].expression, interp.globals)
                if value is not None:
                    # Use the same pretty-printer the language uses when available
                    printer = None
                    try:
                        printer = interp.globals.get("print").value
                    except Exception:
                        printer = print
                    printer(value)
            else:
                result = interp.execute_block(statements, interp.globals)
                if isinstance(result, ControlFlow):
                    # top-level return/break shouldn't kill the session
                    pass
        except MappleError as err:
            if interp.errorStack:
                print("\n".join(reversed(interp.errorStack)), file=sys.stderr)
                interp.errorStack.clear()
            print(err.message, file=sys.stderr)
        except SystemExit:
            # Runtime.exit() etc. — leave the REPL
            raise
        except Exception as err:
            if interp.errorStack:
                print("\n".join(reversed(interp.errorStack)), file=sys.stderr)
                interp.errorStack.clear()
            print(f"{type(err).__name__}: {err}", file=sys.stderr)
            # Uncomment for debugging:
            # traceback.print_exc()

    return 0


if __name__ == "__main__":
    raise SystemExit(run_repl())
