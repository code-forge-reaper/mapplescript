#!/usr/bin/env python

import argparse
import sys

from mapple.nodes import MappleError
from mapple.runtime import Interpreter

# Extension-based standard library
from modules.modules import setup


def main():
    parser = argparse.ArgumentParser(
        prog="Mapple",
        description="Mapple programming language interpreter",
    )

    parser.add_argument(
        "script",
        nargs="?",
        help="Mapple source file (or '-' for stdin). Omit to start the REPL.",
    )
    parser.add_argument(
        "-d",
        "--dump",
        default=False,
        help="dump ast?",
        required=False,
        action="store_true",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        default=False,
        action="store_true",
        help="start the REPL (default when no script is given)",
    )

    args = parser.parse_args()

    # No script, or explicit -i with no file → interactive REPL
    if args.script is None or (args.interactive and args.script is None):
        from mapple.repl import run_repl
        return run_repl()

    if args.script == "-":
        source = sys.stdin.read()
        filename = "<stdin>"
    else:
        with open(args.script, "r", encoding="utf8") as f:
            source = f.read()
        filename = args.script

    interp = Interpreter(source, filename)
    setup(interp, interp.globals)

    if args.dump:
        from pprint import pprint

        bb = interp.tk.parse_block()
        for b in bb:
            pprint(b.to_dict())
    else:
        interp.interpret()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
