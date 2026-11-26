# SIF — Relational verifier for transitions

SIF checks whether a represented transition is coherent:

```
SIF = (STATE, INTENT, TRANSFORMATION, CONSEQUENCE)
```

The verifier judges a transition — `V(S, I, T, C) ∈ {PASS, FAIL, UNKNOWN}` —
against the semantic contract in `docs/semantic-contract-v0.2.md`. It checks
coherence and structural integrity only. It does **not** determine
authorization, and it does **not** demonstrate that an external system
executed the transformation or that the declared consequence occurred.

## Status — v0.2, exploratory prototype

- First prototype run: 9 tests passed, 0 failed (`tests/test_verifier.py`).
- The 9 tests do **not** establish that the four blocks are correctly linked:
  v0.2 does not check the correspondences between `INTENT.target`,
  `TRANSFORMATION.arguments` and `TRANSFORMATION.rule` (see A1–A3 below).
- No authorization, no correspondence with real state, and no effective
  execution have been demonstrated.
- License: none chosen yet. The author's other repositories carry no license;
  adding one is a separate decision.

## Layout

```
src/sif/verifier.py            # v0.2 prototype verifier (single module; split into
                               # models/validation/paths/canonicalize/semantics in v0.3)
schemas/sif-0.2.schema.json
tests/test_verifier.py         # 9 relation tests + A1-A3/B8 regressions (expected failures)
tests/test_totality.py         # B4 totality tests (expected failures until v0.3)
tests/fixtures/valid/          # valid example
tests/fixtures/adversarial/    # B4 regression input
docs/semantic-contract-v0.2.md
docs/audit-log.md
docs/decisions/0001-result-status-and-findings.md
examples/valid-add-label.json
```

## Running the tests

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```

Current v0.3 increment: 12 passed, 3 expected failures (A1, A2, A3), subject to a local full-suite run before review.
Expected failures are obligations from the contract that v0.2 does not
implement; they must turn green in v0.3. Do not delete them to make the
suite pass.

## Known gaps (regressions)

- **A1**: `TRANSFORMATION.arguments.path` and `INTENT.target` contradict
  `rule.path` → still PASS. `verify()` never reads `arguments`, `target`
  or `operator`.
- **A2**: `operator` contradicts `rule.kind` → still PASS.
- **A3**: `INTENT.action` contradicts `operator`/`rule.kind` → still PASS.
- **B4**: closed in the current increment: malformed `preconditions` returns
  `UNKNOWN/STRUCTURAL_ERROR`; deeply nested values return
  `UNKNOWN/RESOURCE_LIMIT`, without an uncaught exception.
- **B8**: closed in the current increment: a `scope` with the wrong type
  returns `UNKNOWN/STRUCTURAL_ERROR`, not a misleading semantic `FAIL`.

See `docs/audit-log.md` for the full record.

## The v0.3 contract

The semantic contract (`docs/semantic-contract-v0.2.md`) defines the
obligations. The closing criterion for v0.3
(`docs/decisions/0001-result-status-and-findings.md`): the verifier returns a structured report `{status, findings[]}` for tested
inputs; invalid structure yields UNKNOWN with a STRUCTURAL_ERROR finding;
status precedence is FAIL > UNKNOWN > PASS; ordinary evaluation exceptions
are contained. This increment closes B4 and B8 only. A1-A3 and B5 remain open.

StarkCore is intentionally not a dependency: SIF stays decoupled until there
is enough evidence to integrate it.
