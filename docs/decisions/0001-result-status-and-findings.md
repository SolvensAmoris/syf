# ADR 0001 — Result status and findings

- Status: accepted
- Date: 2026-11-26
- Context: SIF v0.2, B4 totality

## Context

The v0.2 verifier returns a single `(status, reason)` pair and raises
uncaught exceptions on malformed input. Two failures follow:

1. **B4** — `preconditions` given as a string makes `verify()` raise an
   uncaught `AttributeError` (`'str' object has no attribute 'get'`)
   instead of returning a verdict. A deeply nested value raises an
   uncaught `RecursionError` from `deepcopy`. The verifier disappears
   inside an exception.
2. **B5** — a contradiction plus an uncertainty returns FAIL with a
   single reason and drops the UNKNOWN finding. The verdict cannot carry
   more than one diagnosis.

The contract draft (§1) says an invalid structure produces FAIL. The
B4 closing criterion says an invalid structure produces UNKNOWN with
the structural error recorded. Both cannot stand.

## Decision

Every input produces a structured report:

```json
{
  "status": "UNKNOWN",
  "findings": [
    {
      "code": "STRUCTURAL_ERROR",
      "path": "/TRANSFORMATION/rule",
      "message": "La regla no tiene la estructura esperada"
    }
  ]
}
```

Rules:

- Invalid structure → `UNKNOWN`, with a `STRUCTURAL_ERROR` finding
  recorded (not silently dropped).
- Detectable contradictions are also kept in the same report; one
  finding never hides the others.
- `status` is the worst finding present: **FAIL > UNKNOWN > PASS**.
- No uncaught exception escapes the verifier.

## Consequences

- Contract §1 must be corrected: invalid structure yields UNKNOWN with
  the structural error recorded, not FAIL. (A FAIL finding can still
  coexist in the same report when a contradiction is demonstrable.)
- `tests/test_totality.py` gates this decision; the B4 case and its
  variants must produce valid, complete reports without uncaught
  exceptions.
- The report schema (`status` + accumulable `findings[]`) is part of
  the v0.3 contract. Do not call v0.3 implemented until code and tests
  back it.
- Fuzzing (schema-guided mutations + property-based testing) must
  confirm totality: every malformed input returns a valid report, and
  repeating the same input returns the same report. Each failing input
  is kept as a regression with its seed.
