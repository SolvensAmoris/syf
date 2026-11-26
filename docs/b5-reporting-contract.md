# B5 — Finding model and logical status aggregation

## Scope

This increment introduces typed findings and a pure aggregation function.
It does not change rule execution, the semantic engine, or A1-A3.

## Finding

Each finding contains:

- `code`: stable diagnostic identifier.
- `message`: human-readable explanation.
- `severity`: `error`, `warning`, or `info`.
- `outcome`: `FAIL`, `UNKNOWN`, or `None`.
- `context`: structured location or other diagnostic context.

Severity and logical outcome are independent. Severity does not determine
the verifier verdict.

## Aggregation

`aggregate_status(findings)` is a pure function:

1. Any `FAIL` outcome produces `FAIL`.
2. Otherwise, any `UNKNOWN` outcome produces `UNKNOWN`.
3. Otherwise, the result is `PASS`.

The order of findings does not affect the result. Aggregation never removes
or rewrites findings. Warnings and informational findings may be exposed as
report indicators; they do not change the logical status without an outcome.

## Compatibility

`VerificationReport` derives its status from its findings and retains the
legacy two-item tuple interface. Findings also temporarily support
mapping-style access for existing tests and callers.

## Explicit non-goals

- No validation rule collection or execution loop is introduced.
- No global or singleton report state is introduced.
- No changes are made to A1-A3 or the verifier's semantic rules.
- No policy is inferred from finding codes or message text.
