# MappleScript
A language made for convenience and ease of writing.
By consequence, you don't get conventional syntax out of it.
(Basically `BASIC` mixed with a bunch of other languages' stuff, only using what's convenient)

## About
MappleScript is a interpreted language written in python, it uses a AST-walking mechanism(because I can't be bothered to implement bytecode compilation).

>!
> Functions get turned into real callable stuff, so python itself can call them,
> mapple just makes it a shell around the same interpreting work it does

## Requirements
- Python 3.12+

## Running

```bash
python mapple.py your_script.mapple
```

Or pipe from stdin:

```bash
echo 'print("hello")' | python mapple.py -
```

## Syntax Highlighting

Sublime Text support is included (`mapple.sublime-syntax`).
Just run this and you'll get an up-to-date syntax every time you `git pull`:

```bash
ln -sf $(pwd)/*.subl* ~/.config/sublime-text/Packages/User/
```

## Standard library

The standard library is extension-based. Python modules under `modules/` are
automatically loaded and bound according to `modules/module_info.toml`.
You can also `load("some_module")` Mapple or Python modules at runtime.

---

## License
GPLv3
