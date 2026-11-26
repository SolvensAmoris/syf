# B5 reporting implementation — CI record

- Date: 2026-11-26
- Pull request: #3
- Tested commit: `537bb10739908a9a98e25d27303cc2bb0efc8454`
- Workflow run: [45822634291](https://github.com/SolvensAmoris/syf/actions/runs/45822634291)
- Job: `unittest` (ID `139918532531`)
- Runtime: CPython 3.13.18
- Command: `PYTHONPATH=src python -m unittest discover -s tests -v`

## Result

```
Ran 30 tests in 0.010s

OK (expected failures=3)
```

- 15 B5 reporting tests passed.
- 12 existing active tests passed.
- A1-A3 remain 3 expected failures.
- B4 and B8 regressions passed.

## Scope of evidence

This run verifies the typed finding model, severity/outcome separation,
logical status precedence, order independence, retention of findings,
serialization, and legacy access compatibility.

It does not demonstrate multi-rule finding collection. B5 remains partial
until the validation engine is changed to accumulate findings from multiple
rules. No merge was performed.
