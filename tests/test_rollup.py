import unittest

from cuad_risk.rollup import roll_up_contract


def _finding(
    finding_id: str,
    *,
    severity: int | None,
    domain: str,
    issue_family: str,
    unresolved_material: bool = False,
) -> dict:
    return {
        "finding_id": finding_id,
        "severity_ordinal": severity,
        "risk_domain": domain,
        "issue_family_id": issue_family,
        "unresolved_material": unresolved_material,
    }


class ContractRollupTest(unittest.TestCase):
    def test_any_high_finding_makes_contract_high(self) -> None:
        result = roll_up_contract(
            [
                _finding(
                    "f-high",
                    severity=3,
                    domain="liability",
                    issue_family="liability-allocation",
                ),
                _finding(
                    "f-low",
                    severity=1,
                    domain="governance",
                    issue_family="governing-law",
                ),
            ]
        )

        self.assertEqual(result.risk_band, "high")
        self.assertEqual(result.risk_ordinal, 3)
        self.assertEqual(result.triggering_finding_ids, ("f-high",))

    def test_linked_medium_findings_do_not_double_count(self) -> None:
        result = roll_up_contract(
            [
                _finding(
                    "cap",
                    severity=2,
                    domain="liability",
                    issue_family="liability-allocation",
                ),
                _finding(
                    "uncapped",
                    severity=2,
                    domain="liability",
                    issue_family="liability-allocation",
                ),
            ]
        )

        self.assertEqual(result.risk_band, "medium")
        self.assertEqual(result.triggering_domains, ("liability",))

    def test_multiple_medium_domains_remain_medium_without_a_high_finding(self) -> None:
        result = roll_up_contract(
            [
                _finding("a", severity=2, domain="liability", issue_family="a"),
                _finding("b", severity=2, domain="commercial", issue_family="b"),
                _finding("c", severity=2, domain="ip", issue_family="c"),
            ]
        )

        self.assertEqual(result.risk_band, "medium")
        self.assertEqual(
            result.triggering_domains,
            ("commercial", "ip", "liability"),
        )

    def test_unresolved_material_finding_does_not_invent_numeric_risk(self) -> None:
        result = roll_up_contract(
            [
                _finding(
                    "unknown",
                    severity=None,
                    domain="termination",
                    issue_family="termination",
                    unresolved_material=True,
                )
            ]
        )

        self.assertEqual(result.risk_band, "low")
        self.assertEqual(result.risk_ordinal, 1)
        self.assertEqual(result.review_priority_band, "medium")

    def test_linked_zero_does_not_hide_material_unresolved_finding(self) -> None:
        result = roll_up_contract(
            [
                _finding(
                    "cap",
                    severity=0,
                    domain="liability",
                    issue_family="liability-allocation",
                ),
                _finding(
                    "uncapped",
                    severity=None,
                    domain="liability",
                    issue_family="liability-allocation",
                    unresolved_material=True,
                ),
            ]
        )

        self.assertEqual(result.risk_band, "low")
        self.assertEqual(result.review_priority_band, "medium")
        self.assertEqual(result.triggering_finding_ids, ("uncapped",))

    def test_numeric_low_with_material_uncertainty_has_medium_review_priority(self) -> None:
        result = roll_up_contract(
            [
                _finding(
                    "mixed-category",
                    severity=1,
                    domain="commercial",
                    issue_family="mixed-category",
                    unresolved_material=True,
                )
            ]
        )

        self.assertEqual(result.risk_band, "low")
        self.assertEqual(result.review_priority_band, "medium")
        self.assertEqual(result.triggering_finding_ids, ("mixed-category",))


if __name__ == "__main__":
    unittest.main()
