"""SIF transition verifier.

The semantic engine remains the v0.2 prototype. This v0.3 increment adds
structural pre-validation, structured reports, and exception containment
for B4/B8. A1-A3, B5, and snapshot_digest verification remain open.
"""

from copy import deepcopy

from .reporting import Finding, Severity, Status, VerificationReport

class Unknown(Exception): pass
class Invalid(Exception): pass

def get_path(sif, namespace, path):
    if namespace == "state":
        if path == "/revision":
            return sif["STATE"]["revision"]
        if path == "/subject":
            return sif["STATE"]["subject"]
        facts = sif["STATE"]["facts"]
        if path not in facts: raise Unknown(f"missing STATE path {path}")
        return facts[path]
    if namespace == "result":
        if path not in sif["_RESULT"]: raise Unknown(f"missing RESULT path {path}")
        return sif["_RESULT"][path]
    raise Invalid(f"unknown namespace {namespace}")

def value_of(expr, sif):
    if not isinstance(expr, dict) or len(expr) != 1:
        raise Invalid("expression must have exactly one source")
    if "literal" in expr: return expr["literal"]
    if "state" in expr: return get_path(sif, "state", expr["state"])
    if "result" in expr: return get_path(sif, "result", expr["result"])
    raise Invalid("unsupported expression")

def predicate(p, sif):
    op = p.get("op")
    if op == "eq":
        return value_of(p["left"], sif) == value_of(p["right"], sif)
    if op in ("contains", "not-contains"):
        seq = value_of(p["list"], sif)
        val = value_of(p["value"], sif)
        if not isinstance(seq, list): raise Invalid("contains expects a list")
        found = val in seq
        return found if op == "contains" else not found
    raise Invalid(f"unsupported predicate operator {op}")

def derive(sif):
    rule = sif["TRANSFORMATION"]["rule"]
    if rule.get("kind") != "append-unique":
        raise Unknown("unsupported transformation rule")
    path = rule["path"]
    if path not in sif["STATE"]["facts"]: raise Unknown(f"missing source path {path}")
    value_ref = rule["value_from"]
    if not value_ref.startswith("INTENT:"): raise Invalid("unsupported value source")
    parameter_path = value_ref.split(":",1)[1]
    if parameter_path not in sif["INTENT"]["parameters"]: raise Unknown(f"missing intent parameter {parameter_path}")
    before = sif["STATE"]["facts"][path]
    if not isinstance(before, list): raise Invalid("append-unique target must be a list")
    value = sif["INTENT"]["parameters"][parameter_path]
    if value in before: raise Unknown("append-unique would be a no-op under current precondition contract")
    result = {k:deepcopy(v) for k,v in sif["STATE"]["facts"].items()}
    result[path] = before + [value]
    return result

def _verify_v02(sif):
    try:
        if sif.get("schema_version") != "SIF-0.2": raise Invalid("unsupported schema")
        for p in sif["TRANSFORMATION"]["preconditions"]:
            if not predicate(p, sif): return "FAIL", "precondition false"
        result = derive(sif)
        work = dict(sif); work["_RESULT"] = result
        for p in sif["TRANSFORMATION"]["postconditions"] + sif["CONSEQUENCE"]["invariants"]:
            if not predicate(p, work): return "FAIL", "postcondition/invariant false"
        before = sif["STATE"]["facts"]
        changed = {k for k in set(before)|set(result) if before.get(k) != result.get(k)}
        scope = set(sif["CONSEQUENCE"]["scope"])
        frame = set(sif["TRANSFORMATION"]["frame"])
        if not changed.issubset(scope): return "FAIL", "change outside consequence scope"
        if any(before.get(k) != result.get(k) for k in frame): return "FAIL", "frame condition violated"
        for effect in sif["CONSEQUENCE"]["forbidden_effects"]:
            if effect.get("kind") == "change" and effect.get("target") in changed:
                return "FAIL", "forbidden effect derived"
        derived_effects = []
        for path in sorted(changed):
            derived_effects.append({
                "kind":"append" if isinstance(before.get(path), list) and isinstance(result.get(path), list) else "change",
                "target":path, "before":before.get(path), "after":result.get(path)
            })
        expected = sif["CONSEQUENCE"]["expected_effects"]
        if derived_effects != expected: return "FAIL", "derived effects differ from expected effects"
        return "PASS", {"result":result, "derived_effects":derived_effects}
    except Unknown as e:
        return "UNKNOWN", str(e)
    except (KeyError, TypeError, Invalid, ValueError) as e:
        return "UNKNOWN", f"cannot evaluate: {e}"


def _structural_finding(sif):
    """Return the first structural defect before semantic evaluation."""
    if not isinstance(sif, dict):
        return "/", "document must be an object"
    if sif.get("schema_version") != "SIF-0.2":
        return "/schema_version", "unsupported or missing schema version"

    blocks = ("STATE", "INTENT", "TRANSFORMATION", "CONSEQUENCE")
    for name in blocks:
        if not isinstance(sif.get(name), dict):
            return f"/{name}", f"{name} must be an object"

    state, intent = sif["STATE"], sif["INTENT"]
    transform, consequence = sif["TRANSFORMATION"], sif["CONSEQUENCE"]

    checks = [
        (state.get("facts"), dict, "/STATE/facts"),
        (state.get("revision"), str, "/STATE/revision"),
        (state.get("subject"), str, "/STATE/subject"),
        (intent.get("parameters"), dict, "/INTENT/parameters"),
        (intent.get("target"), list, "/INTENT/target"),
        (transform.get("operator"), str, "/TRANSFORMATION/operator"),
        (transform.get("arguments"), dict, "/TRANSFORMATION/arguments"),
        (transform.get("rule"), dict, "/TRANSFORMATION/rule"),
        (transform.get("preconditions"), list, "/TRANSFORMATION/preconditions"),
        (transform.get("postconditions"), list, "/TRANSFORMATION/postconditions"),
        (transform.get("frame"), list, "/TRANSFORMATION/frame"),
        (consequence.get("scope"), list, "/CONSEQUENCE/scope"),
        (consequence.get("expected_effects"), list, "/CONSEQUENCE/expected_effects"),
        (consequence.get("forbidden_effects"), list, "/CONSEQUENCE/forbidden_effects"),
        (consequence.get("invariants"), list, "/CONSEQUENCE/invariants"),
    ]
    for value, expected, path in checks:
        if not isinstance(value, expected):
            return path, f"{path} must be {expected.__name__}"

    for path, values in (
        ("/INTENT/target", intent["target"]),
        ("/TRANSFORMATION/frame", transform["frame"]),
        ("/CONSEQUENCE/scope", consequence["scope"]),
    ):
        if not all(isinstance(value, str) for value in values):
            return path, f"{path} entries must be strings"

    for block, key in ((transform, "preconditions"), (transform, "postconditions"),
                       (consequence, "invariants")):
        if not all(isinstance(item, dict) for item in block[key]):
            return f"/{ 'TRANSFORMATION' if block is transform else 'CONSEQUENCE' }/{key}", f"{key} entries must be objects"

    for i, effect in enumerate(consequence["expected_effects"] + consequence["forbidden_effects"]):
        if not isinstance(effect, dict):
            return f"/CONSEQUENCE/effects/{i}", "effect entries must be objects"

    rule = transform["rule"]
    for key in ("kind", "path", "value_from"):
        if not isinstance(rule.get(key), str):
            return f"/TRANSFORMATION/rule/{key}", f"rule.{key} must be a string"
    return None


def verify(sif):
    """Return a structured report; malformed inputs never escape as exceptions."""
    try:
        defect = _structural_finding(sif)
        if defect is not None:
            path, message = defect
            return VerificationReport(findings=[Finding(
                code="STRUCTURAL_ERROR",
                message=f"structural error: {message}",
                severity=Severity.ERROR,
                outcome=Status.UNKNOWN,
                context={"path": path},
            )])

        status, detail = _verify_v02(sif)
        if status == "PASS":
            return VerificationReport(findings=[], result=detail)
        code = "CONTRADICTION" if status == "FAIL" else "UNRESOLVED"
        return VerificationReport(findings=[Finding(
            code=code,
            message=str(detail),
            severity=Severity.ERROR if status == "FAIL" else Severity.WARNING,
            outcome=Status.FAIL if status == "FAIL" else Status.UNKNOWN,
            context={"path": "/"},
        )])
    except RecursionError as exc:
        return VerificationReport(findings=[Finding(
            code="RESOURCE_LIMIT",
            message=f"evaluation recursion limit reached: {type(exc).__name__}",
            severity=Severity.ERROR,
            outcome=Status.UNKNOWN,
            context={"path": "/"},
        )])
    except Exception as exc:
        return VerificationReport(findings=[Finding(
            code="EVALUATION_ERROR",
            message=f"evaluation could not be completed: {type(exc).__name__}",
            severity=Severity.ERROR,
            outcome=Status.UNKNOWN,
            context={"path": "/"},
        )])
