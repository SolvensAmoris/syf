# B4 totality baseline — 2026-11-26

## Scope

Execution of the two existing totality regressions in `tests/test_totality.py`
against the unchanged v0.2 verifier from the frozen `main` snapshot.

- Base branch: `main`
- Base commit: `7bb05587c95041b59f4799f99fbd3993a22cc70d`
- Verifier blob: `4db7a51c3b129da9ed4802b6bf07d95d093cc2ca`
- Test blob: `dfbc62ae69eab93e3c95b846286f457a1d694e17`
- Runtime: Python 3.13.5
- Command: `PYTHONPATH=src python -m unittest discover -s tests -v`

## Harness result

```
test_b4_malformed_preconditions_returns_report ... expected failure
test_deeply_nested_value_returns_report ... expected failure

Ran 2 tests in 0.384s
OK (expected failures=2)
```

The unittest result is not a pass of the obligations. Both tests are decorated
with `unittest.expectedFailure`, so the harness reports the known failures as
expected.

## Direct exception reproduction

The same two inputs were then executed without the `expectedFailure`
decorator:

| Case | Observed result |
|---|---|
| B4: `TRANSFORMATION.preconditions` is a string | Uncaught `AttributeError: 'str' object has no attribute 'get'` |
| Deep nesting: 3,000 nested list levels in `STATE.facts./labels` | Uncaught `RecursionError: maximum recursion depth exceeded` |

Both failures were reproduced against the unchanged v0.2 verifier.

## Interpretation

B4 totality is **not satisfied** in v0.2. The verifier does not guarantee a
structured return for malformed or deeply nested inputs. This run establishes
the baseline failure only. It does not implement or validate the v0.3 fix.

## Freeze boundary

This record freezes the observed baseline and source identifiers. The v0.2
verifier and its tests were not modified. v0.3 work must preserve these cases
as required regressions and make both return a structured report without an
uncaught exception.

No merge was performed.
