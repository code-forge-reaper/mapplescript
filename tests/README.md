# MappleScript tests

These are **automated tests**, not language tutorials.

- Examples for humans live in `../examples/`.
- Tests here use `assert` and should stay quiet on success (they only print a single OK line).

## Running

From the repository root:

```bash
python tests/run_tests.py
```

Or run a single file:

```bash
python mapple.py tests/test_basics.mapple
```

## Layout

| File | Covers |
|------|--------|
| `test_basics.mapple` | Literals, vars, consts, arithmetic, comparison, logical, bitwise, compound on scalars |
| `test_arrays_objects.mapple` | Arrays, objects/dicts, indexing, nested structures, compound on indexes |
| `test_index_compound.mapple` | Regression for `$name[i] +=` / `-=` / etc. |
| `test_control.mapple` | if/elseif/else, while, for, for-in, break, continue |
| `test_functions.mapple` | Named funcs, recursion, short funcs, closures, higher-order |
| `test_classes.mapple` | class, record, methods, properties |
| `test_errors.mapple` | assert, test/failed, raise |
| `test_misc.mapple` | between, enum, matches, map (`=>`), defer |
