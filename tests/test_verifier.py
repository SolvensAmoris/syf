"""SIF relation tests plus A1-A3/B8 contract regressions.

The 9 relation tests come from the v0.2 prototype. A1-A3 remain expected
failures. B8 is now an active structural-validation regression.
Do not delete expected failures to make the suite pass.
"""

import copy
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sif.verifier import verify

BASE_PATH = os.path.join(
    os.path.dirname(__file__), "fixtures", "valid", "valid-add-label.json"
)


def load_base():
    with open(BASE_PATH, encoding="utf-8") as f:
        return json.load(f)


class SIFRelationTests(unittest.TestCase):
    def test_valid_transition_passes(self):
        self.assertEqual(verify(copy.deepcopy(load_base()))[0], "PASS")

    def test_failed_precondition_fails(self):
        x = copy.deepcopy(load_base())
        x["STATE"]["revision"] = "r2"
        self.assertEqual(verify(x)[0], "FAIL")

    def test_out_of_scope_change_fails(self):
        # The DSL can only derive a change on the rule's path, so an
        # out-of-scope change is tested by shrinking scope, not by
        # deriving a foreign change (see docs/audit-log.md).
        x = copy.deepcopy(load_base())
        x["CONSEQUENCE"]["scope"] = []
        self.assertEqual(verify(x)[0], "FAIL")

    def test_forbidden_effect_fails(self):
        x = copy.deepcopy(load_base())
        x["CONSEQUENCE"]["forbidden_effects"] = [
            {"kind": "change", "target": "/labels"}
        ]
        self.assertEqual(verify(x)[0], "FAIL")

    def test_missing_fact_is_unknown(self):
        x = copy.deepcopy(load_base())
        del x["STATE"]["facts"]["/labels"]
        self.assertEqual(verify(x)[0], "UNKNOWN")

    def test_missing_parameter_is_unknown(self):
        x = copy.deepcopy(load_base())
        del x["INTENT"]["parameters"]["/label"]
        self.assertEqual(verify(x)[0], "UNKNOWN")

    def test_wrong_expected_effect_fails(self):
        x = copy.deepcopy(load_base())
        x["CONSEQUENCE"]["expected_effects"][0]["after"] = ["borrador", "otra"]
        self.assertEqual(verify(x)[0], "FAIL")

    def test_deterministic(self):
        x = copy.deepcopy(load_base())
        self.assertEqual(verify(x), verify(x))

    def test_unknown_is_not_pass(self):
        x = copy.deepcopy(load_base())
        del x["STATE"]["facts"]["/labels"]
        self.assertNotEqual(verify(x)[0], "PASS")


class SIFRegressionTests(unittest.TestCase):
    """Contract obligations v0.2 does not implement yet (expected failures)."""

    @unittest.expectedFailure
    def test_a1_arguments_target_mismatch_fails(self):
        x = copy.deepcopy(load_base())
        x["TRANSFORMATION"]["arguments"]["/path"] = "/owner"
        x["INTENT"]["target"] = ["/owner"]
        self.assertEqual(verify(x)[0], "FAIL")

    @unittest.expectedFailure
    def test_a2_operator_mismatch_fails(self):
        x = copy.deepcopy(load_base())
        x["TRANSFORMATION"]["operator"] = "delete-everything"
        self.assertEqual(verify(x)[0], "FAIL")

    @unittest.expectedFailure
    def test_a3_action_mismatch_fails(self):
        x = copy.deepcopy(load_base())
        x["INTENT"]["action"] = "borrar-todo"
        self.assertEqual(verify(x)[0], "FAIL")

    def test_b8_scope_wrong_type_reports_structural_error(self):
        x = copy.deepcopy(load_base())
        x["CONSEQUENCE"]["scope"] = "/labels"
        status, reason = verify(x)
        self.assertEqual(status, "UNKNOWN")
        self.assertIn("structural", str(reason).lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
