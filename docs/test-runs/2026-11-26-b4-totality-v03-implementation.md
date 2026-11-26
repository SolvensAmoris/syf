# SIF v0.3 — B4/B8 implementation test run

- Date: 2026-11-26
- Branch: `work/sif-v0.3-totality`
- Tested commit: `a0f047bda6927f07751dd4fb7c5cf068feb0a28a`
- Workflow run: [45820994217](https://github.com/SolvensAmoris/syf/actions/runs/45820994217)
- Runtime: CPython 3.13.18
- Command: `PYTHONPATH=src python -m unittest discover -s tests -v`

## Result

```
Ran 15 tests in 0.007s
OK (expected failures=3)
```

- 12 tests passed.
- A1, A2, A3 remain expected failures.
- B4 malformed `preconditions`: PASS; returns `UNKNOWN/STRUCTURAL_ERROR`.
- B4 3,000-level nested value: PASS; returns `UNKNOWN/RESOURCE_LIMIT`.
- B8 malformed `CONSEQUENCE.scope`: PASS; returns `UNKNOWN/STRUCTURAL_ERROR`.

## Scope and limitations

This run verifies the B4/B8 implementation increment only. It does not close
A1-A3, B5 multi-finding accumulation, digest verification, authorization, or
external execution. A successful test harness is not evidence for those
unimplemented obligations.

The run was performed by GitHub Actions on the exact tested commit above.
