"""Unit tests for B5 finding models and pure status aggregation."""

import os
import sys
import unittest
from itertools import permutations

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sif.reporting import (
    Finding,
    Severity,
    Status,
    VerificationReport,
    aggregate_status,
)


def finding(severity, outcome=None, code="TEST", message="test finding"):
    return Finding(
        code=code,
        message=message,
        severity=severity,
        outcome=outcome,
        context={"path": "/example"},
    )


class AggregateStatusTests(unittest.TestCase):
    def test_no_findings_is_pass(self):
        self.assertIs(aggregate_status([]), Status.PASS)

    def test_info_only_is_pass(self):
        items = [finding(Severity.INFO), finding(Severity.INFO)]
        self.assertIs(aggregate_status(items), Status.PASS)

    def test_warning_without_logical_outcome_does_not_change_status(self):
        items = [finding(Severity.WARNING)]
        self.assertIs(aggregate_status(items), Status.PASS)

    def test_unknown_outcome_precedes_pass_independently_of_severity(self):
        items = [finding(Severity.ERROR, Status.UNKNOWN)]
        self.assertIs(aggregate_status(items), Status.UNKNOWN)

    def test_fail_precedes_unknown(self):
        items = [
            finding(Severity.ERROR, Status.UNKNOWN),
            finding(Severity.WARNING, Status.FAIL),
            finding(Severity.INFO),
        ]
        self.assertIs(aggregate_status(items), Status.FAIL)

    def test_severity_does_not_determine_logical_status(self):
        self.assertIs(
            aggregate_status([finding(Severity.INFO, Status.UNKNOWN)]),
            Status.UNKNOWN,
        )
        self.assertIs(
            aggregate_status([finding(Severity.WARNING, Status.FAIL)]),
            Status.FAIL,
        )

    def test_aggregation_is_order_independent(self):
        items = [
            finding(Severity.INFO),
            finding(Severity.WARNING, Status.UNKNOWN),
            finding(Severity.ERROR, Status.FAIL),
        ]
        results = {aggregate_status(order) for order in permutations(items)}
        self.assertEqual(results, {Status.FAIL})

    def test_non_finding_input_is_rejected(self):
        with self.assertRaises(TypeError):
            aggregate_status([{"severity": "error", "outcome": "FAIL"}])

    def test_invalid_item_is_not_hidden_after_fail(self):
        items = [finding(Severity.ERROR, Status.FAIL), object()]
        with self.assertRaises(TypeError):
            aggregate_status(items)


class FindingAndReportTests(unittest.TestCase):
    def test_invalid_pass_outcome_is_rejected(self):
        with self.assertRaises(ValueError):
            finding(Severity.INFO, Status.PASS)

    def test_string_outcome_is_rejected(self):
        with self.assertRaises(ValueError):
            finding(Severity.ERROR, "FAIL")

    def test_report_retains_all_findings_and_derives_status(self):
        report = VerificationReport()
        first = finding(Severity.WARNING, Status.UNKNOWN, code="MISSING")
        second = finding(Severity.INFO, code="NOTE")
        third = finding(Severity.ERROR, Status.FAIL, code="CONTRADICTION")

        report.add(first)
        report.extend([second, third])

        self.assertIs(report.status, Status.FAIL)
        self.assertEqual(report.findings, [first, second, third])
        self.assertTrue(report.has_warnings)
        self.assertTrue(report.has_info)

    def test_report_status_updates_after_add(self):
        report = VerificationReport()
        self.assertIs(report.status, Status.PASS)
        report.add(finding(Severity.ERROR, Status.UNKNOWN))
        self.assertIs(report.status, Status.UNKNOWN)

    def test_as_dict_serializes_enums_and_context(self):
        report = VerificationReport(findings=[
            finding(Severity.ERROR, Status.UNKNOWN, code="STRUCTURAL_ERROR")
        ])
        self.assertEqual(report.as_dict(), {
            "status": "UNKNOWN",
            "findings": [{
                "code": "STRUCTURAL_ERROR",
                "message": "test finding",
                "severity": "error",
                "outcome": "UNKNOWN",
                "context": {"path": "/example"},
            }],
        })

    def test_legacy_tuple_and_mapping_access_remain_available(self):
        report = VerificationReport(findings=[
            finding(Severity.ERROR, Status.UNKNOWN, code="STRUCTURAL_ERROR")
        ])
        status, message = report
        self.assertEqual(status, "UNKNOWN")
        self.assertEqual(message, "test finding")
        self.assertEqual(report.findings[0]["code"], "STRUCTURAL_ERROR")
        self.assertEqual(report.findings[0]["path"], "/example")


if __name__ == "__main__":
    unittest.main(verbosity=2)
