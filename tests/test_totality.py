"""Totality tests (B4): malformed inputs must produce a report, never an
uncaught exception.

These tests gate the v0.3 totality contract (see
docs/decisions/0001-result-status-and-findings.md).
"""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sif.verifier import verify

B4_PATH = os.path.join(
    os.path.dirname(__file__),
    "fixtures",
    "adversarial",
    "b4-preconditions-not-a-list.json",
)
BASE_PATH = os.path.join(
    os.path.dirname(__file__), "fixtures", "valid", "valid-add-label.json"
)


class TotalityTests(unittest.TestCase):
    def test_b4_malformed_preconditions_returns_report(self):
        with open(B4_PATH, encoding="utf-8") as f:
            x = json.load(f)
        report = verify(x)
        self.assertEqual(report.status, "UNKNOWN")
        self.assertTrue(report.findings)
        self.assertEqual(report.findings[0]["code"], "STRUCTURAL_ERROR")

    def test_deeply_nested_value_returns_report(self):
        with open(BASE_PATH, encoding="utf-8") as f:
            x = json.load(f)
        deep = "revisado"
        for _ in range(3000):
            deep = [deep]
        x["STATE"]["facts"]["/labels"] = deep
        report = verify(x)
        self.assertEqual(report.status, "UNKNOWN")
        self.assertTrue(report.findings)
        self.assertEqual(report.findings[0]["code"], "RESOURCE_LIMIT")


if __name__ == "__main__":
    unittest.main(verbosity=2)
