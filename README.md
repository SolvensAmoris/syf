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

## Status — v0.3 incremental implementation

- The original 9 relation tests remain as compatibility regressions.
- A1-A3 remain open: the verifier does not yet check all correspondences
  between `INTENT.target`, `TRANSFORMATION.arguments` and
  `TRANSFORMATION.rule`.
- B5 is partially implemented: typed findings and pure logical-status
  aggregation exist; the verifier does not yet accumulate multiple rule
  findings because the rule engine has not been refactored.
- No authorization, no correspondence with real state, and no effective
  execution have been demonstrated.
- License: none chosen yet. The author's other repositories carry no license;
  adding one is a separate decision.

## Layout

```
src/sif/verifier.py            # v0.2 semantic engine and verification entry point
src/sif/reporting.py           # typed Finding, VerificationReport, aggregation
schemas/sif-0.2.schema.json
tests/test_verifier.py         # 9 relation tests + A1-A3 expected failures + B8
tests/test_totality.py         # active B4 totality regressions
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

Run the complete suite with the command above. The A1-A3 cases remain
expected failures; B4 and B8 are active regressions. The CI workflow executes
the same command on pushes and pull requests. Do not delete expected failures
to make the suite pass.

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
- **B5**: partial: `Finding`, severity/outcome separation, pure aggregation,
  and report serialization are implemented and unit-tested. Multi-finding
  accumulation across validation rules remains open.

See `docs/audit-log.md` for the full record.

## The v0.3 contract

The semantic contract (`docs/semantic-contract-v0.2.md`) defines the
obligations. The closing criterion for v0.3
(`docs/decisions/0001-result-status-and-findings.md`): the verifier returns a structured report `{status, findings[]}` for tested
inputs; invalid structure yields UNKNOWN with a STRUCTURAL_ERROR finding;
status precedence is FAIL > UNKNOWN > PASS; ordinary evaluation exceptions
are contained. The B4/B8 increment is closed. The B5 reporting-model increment is partial:
aggregation is implemented, but multi-rule collection remains open. A1-A3
remain open.

StarkCore is intentionally not a dependency: SIF stays decoupled until there
is enough evidence to integrate it.
