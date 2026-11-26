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

## Duplicate policy (B5)

B5 permits repeated findings and does not deduplicate them. A `code` identifies
a diagnostic category, not a unique observation. Two findings with the same
`code` may describe distinct observations; even byte-for-byte equivalent
Finding instances are retained as separate entries when added more than once.

`VerificationReport.add()` and `extend()` preserve every supplied finding and
its insertion position. Serialization preserves that sequence. Aggregation
considers every entry but remains order-independent; repeated outcomes do not
change the precedence rules.

B5 does not define a finding identity key, `occurrence_id`, duplicate counter,
or conflict-resolution behavior. Those require a stable source identity and
an explicit definition of what constitutes the same observation. Until that
model exists, no identity is inferred from `code`, message, serialized
context, severity, or outcome, and no finding is discarded or merged.

## Compatibility

`VerificationReport` derives its status from its findings and retains the
legacy two-item tuple interface. Findings also temporarily support
mapping-style access for existing tests and callers.

## Explicit non-goals

- No validation rule collection or execution loop is introduced.
- No global or singleton report state is introduced.
- No changes are made to A1-A3 or the verifier's semantic rules.
- No policy is inferred from finding codes or message text.
