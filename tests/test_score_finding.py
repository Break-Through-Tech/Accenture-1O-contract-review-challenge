from pathlib import Path
import json
import re
import unittest

from cuad_risk.scoring import load_rule_cards, score_finding


class ScoreFindingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        project_root = Path(__file__).resolve().parents[1]
        cls.project_root = project_root
        cls.cards = load_rule_cards(
            project_root / "data/risk/rule_cards.json"
        )

    def test_all_locked_categories_have_traceable_rule_card_metadata(self) -> None:
        self.assertEqual(len(self.cards), 10)
        required_fields = {
            "rule_card_id",
            "review_bundle_id",
            "risk_domain",
            "issue_family_template",
            "source_ids",
            "material_if_unresolved",
            "missing_clause_policy",
        }
        for card in self.cards.values():
            with self.subTest(category=card["category_id"]):
                self.assertTrue(required_fields.issubset(card))
                self.assertTrue(card["source_ids"])

    def test_rule_card_sources_directions_and_patterns_are_valid(self) -> None:
        registry = json.loads(
            (
                self.project_root / "data/risk/source_registry.json"
            ).read_text(encoding="utf-8")
        )
        registered_ids = {
            source["source_id"] for source in registry["sources"]
        }
        allowed_directions = {
            "protective",
            "balanced",
            "adverse",
            "mixed",
            "unclear",
        }
        pattern_fields = ("when_all", "when_any", "when_none", "count_patterns")

        for card in self.cards.values():
            with self.subTest(category=card["category_id"], check="sources"):
                self.assertTrue(set(card["source_ids"]).issubset(registered_ids))
            for rule_group in ("present_rules", "missing_rules"):
                for rule in card.get(rule_group, []):
                    with self.subTest(rule=rule["rule_id"]):
                        self.assertIn(rule.get("direction", "unclear"), allowed_directions)
                        severity = rule.get("severity_ordinal")
                        self.assertTrue(severity is None or severity in {0, 1, 2, 3})
                        for field in pattern_fields:
                            for pattern in rule.get(field, []):
                                re.compile(pattern)

    def test_mutual_liability_cap_is_low_buyer_side_deviation(self) -> None:
        assessment = score_finding(
            rule_cards=self.cards,
            category_id="cap_on_liability",
            presence_status="present",
            evidence_text=(
                "In no event shall either party's aggregate liability exceed "
                "the fees paid during the preceding twelve months."
            ),
            contract_type="services",
        )

        self.assertEqual(assessment.severity_ordinal, 1)
        self.assertEqual(assessment.risk_band, "low")
        self.assertEqual(assessment.direction, "balanced")
        self.assertEqual(assessment.label_status, "weak_automatic")
        self.assertIn("cap_mutual", assessment.trigger_ids)

    def test_buyer_uncapped_against_capped_vendor_is_high(self) -> None:
        assessment = score_finding(
            rule_cards=self.cards,
            category_id="cap_on_liability",
            presence_status="present",
            evidence_text=(
                "Vendor's total liability shall not exceed $100. "
                "Customer's liability is unlimited."
            ),
            contract_type="services",
        )

        self.assertEqual(assessment.severity_ordinal, 3)
        self.assertEqual(assessment.risk_band, "high")
        self.assertEqual(assessment.direction, "adverse")
        self.assertIn("cap_buyer_uncapped", assessment.trigger_ids)

    def test_ambiguous_cap_abstains_instead_of_forcing_a_band(self) -> None:
        assessment = score_finding(
            rule_cards=self.cards,
            category_id="cap_on_liability",
            presence_status="present",
            evidence_text="Liability is limited as set forth elsewhere herein.",
            contract_type="unknown",
        )

        self.assertIsNone(assessment.severity_ordinal)
        self.assertEqual(assessment.risk_band, "unresolved")
        self.assertEqual(assessment.direction, "unclear")
        self.assertEqual(assessment.label_status, "weak_abstain")

    def test_missing_governing_law_is_medium_for_procurement_review(self) -> None:
        assessment = score_finding(
            rule_cards=self.cards,
            category_id="governing_law",
            presence_status="missing",
            evidence_text="",
            contract_type="services",
        )

        self.assertEqual(assessment.severity_ordinal, 2)
        self.assertEqual(assessment.risk_band, "medium")
        self.assertEqual(assessment.applicability, "applicable")
        self.assertIn("governing_law_missing", assessment.trigger_ids)

    def test_rule_matching_normalizes_contract_whitespace(self) -> None:
        assessment = score_finding(
            rule_cards=self.cards,
            category_id="governing_law",
            presence_status="present",
            evidence_text=(
                "This Agreement is construed under the laws          of the "
                "State of Illinois."
            ),
            contract_type="distribution",
        )

        self.assertEqual(assessment.severity_ordinal, 0)
        self.assertIn("governing_law_us_state", assessment.trigger_ids)

    def test_party_neutral_structural_rules_create_low_confidence_silver_labels(
        self,
    ) -> None:
        cases = {
            "renewal_term": (
                "The agreement renews on an annual basis and either party may "
                "terminate on written notice.",
                1,
            ),
            "revenue_profit_sharing": (
                "A royalty of five percent of net sales is payable quarterly.",
                1,
            ),
            "cap_on_liability": (
                "Neither party shall be liable for consequential damages.",
                1,
            ),
            "uncapped_liability": (
                "Nothing limits either party's liability for fraud or death.",
                0,
            ),
            "termination_for_convenience": (
                "Either party may terminate this Agreement upon written notice.",
                1,
            ),
            "anti_assignment": (
                "Neither party may assign without the other party's consent, "
                "which shall not be unreasonably withheld.",
                1,
            ),
            "audit_rights": (
                "An independent auditor may inspect the books and records during "
                "business hours on reasonable notice.",
                1,
            ),
            "license_grant": (
                "Acme grants a limited, non-exclusive license during the term to "
                "use the software.",
                1,
            ),
            "exclusivity": (
                "Acme appoints Beta as its exclusive distributor in the territory.",
                1,
            ),
        }

        for category_id, (text, expected_severity) in cases.items():
            with self.subTest(category_id=category_id):
                assessment = score_finding(
                    rule_cards=self.cards,
                    category_id=category_id,
                    presence_status="present",
                    evidence_text=text,
                    contract_type="distribution",
                )
                self.assertEqual(
                    assessment.severity_ordinal, expected_severity
                )
                self.assertEqual(assessment.label_status, "weak_automatic")
                self.assertIn(
                    assessment.direction,
                    {"protective", "balanced", "adverse", "mixed", "unclear"},
                )

    def test_optional_missing_categories_are_not_numeric_zeroes(self) -> None:
        optional_categories = (
            "renewal_term",
            "uncapped_liability",
            "anti_assignment",
            "exclusivity",
        )
        for category_id in optional_categories:
            with self.subTest(category_id=category_id):
                assessment = score_finding(
                    rule_cards=self.cards,
                    category_id=category_id,
                    presence_status="missing",
                    evidence_text="",
                    contract_type="distribution",
                )

                self.assertIsNone(assessment.severity_ordinal)
                self.assertEqual(assessment.risk_band, "not_applicable")
                self.assertEqual(assessment.applicability, "not_applicable")
                self.assertEqual(assessment.direction, "unclear")
                self.assertEqual(assessment.label_status, "weak_not_applicable")

    def test_missing_audit_is_medium_when_variable_revenue_needs_verification(self) -> None:
        assessment = score_finding(
            rule_cards=self.cards,
            category_id="audit_rights",
            presence_status="absent",
            evidence_text=(
                "Supplier shall calculate and pay Customer ten percent of net sales."
            ),
            contract_type="distribution",
        )

        self.assertEqual(assessment.severity_ordinal, 2)
        self.assertEqual(assessment.risk_band, "medium")
        self.assertIn("audit_missing_revenue_verification", assessment.trigger_ids)

    def test_missing_exclusivity_is_not_an_abstention(self) -> None:
        assessment = score_finding(
            rule_cards=self.cards,
            category_id="exclusivity",
            presence_status="missing",
            evidence_text="",
            contract_type="distribution",
        )

        self.assertIsNone(assessment.severity_ordinal)
        self.assertEqual(assessment.risk_band, "not_applicable")
        self.assertEqual(assessment.label_status, "weak_not_applicable")

    def test_missing_license_is_material_for_software_but_not_for_services(self) -> None:
        software = score_finding(
            rule_cards=self.cards,
            category_id="license_grant",
            presence_status="missing",
            evidence_text="",
            contract_type="software_license",
        )
        services = score_finding(
            rule_cards=self.cards,
            category_id="license_grant",
            presence_status="missing",
            evidence_text="",
            contract_type="services",
        )

        self.assertEqual(software.severity_ordinal, 2)
        self.assertEqual(software.applicability, "applicable")
        self.assertIsNone(services.severity_ordinal)
        self.assertEqual(services.risk_band, "not_applicable")
        self.assertEqual(services.applicability, "not_applicable")
        self.assertEqual(services.label_status, "weak_not_applicable")

    def test_supplier_only_convenience_termination_is_high(self) -> None:
        assessment = score_finding(
            rule_cards=self.cards,
            category_id="termination_for_convenience",
            presence_status="present",
            evidence_text=(
                "Supplier may terminate this Agreement for convenience upon "
                "thirty days notice. Customer may not terminate for convenience."
            ),
            contract_type="services",
        )

        self.assertEqual(assessment.severity_ordinal, 3)
        self.assertEqual(assessment.direction, "adverse")
        self.assertIn("tfc_supplier_only", assessment.trigger_ids)

    def test_broad_buyer_to_supplier_license_is_high(self) -> None:
        assessment = score_finding(
            rule_cards=self.cards,
            category_id="license_grant",
            presence_status="present",
            evidence_text=(
                "Customer hereby grants Provider an exclusive, perpetual, "
                "irrevocable, worldwide and transferable license to Customer Data."
            ),
            contract_type="services",
        )

        self.assertEqual(assessment.severity_ordinal, 3)
        self.assertEqual(assessment.direction, "adverse")
        self.assertIn("license_buyer_broad_grant", assessment.trigger_ids)

    def test_exclusive_right_granted_to_buyer_is_not_adverse_high(self) -> None:
        assessment = score_finding(
            rule_cards=self.cards,
            category_id="exclusivity",
            presence_status="present",
            evidence_text=(
                "The Client is hereby granted an exclusive, worldwide, "
                "royalty-free, perpetual license to use the work product."
            ),
            contract_type="services",
        )

        self.assertEqual(assessment.severity_ordinal, 0)
        self.assertEqual(assessment.risk_band, "none")
        self.assertEqual(assessment.direction, "protective")
        self.assertIn("exclusivity_right_granted_to_buyer", assessment.trigger_ids)

    def test_mutual_exclusive_license_is_not_adverse_high(self) -> None:
        assessment = score_finding(
            rule_cards=self.cards,
            category_id="exclusivity",
            presence_status="present",
            evidence_text=(
                "Each Party hereby provides a worldwide, exclusive, "
                "royalty-free, perpetual license for use by each licensee."
            ),
            contract_type="collaboration",
        )

        self.assertEqual(assessment.severity_ordinal, 1)
        self.assertEqual(assessment.risk_band, "low")
        self.assertEqual(assessment.direction, "balanced")
        self.assertIn("exclusivity_mutual_grant", assessment.trigger_ids)

    def test_supplier_damages_exclusion_is_not_uncapped_buyer_liability(self) -> None:
        assessment = score_finding(
            rule_cards=self.cards,
            category_id="uncapped_liability",
            presence_status="present",
            evidence_text=(
                "In no event shall eGain be liable to Customer for indirect "
                "damages, including, without limitation, lost profits."
            ),
            contract_type="services",
        )

        self.assertNotEqual(assessment.severity_ordinal, 3)
        self.assertNotEqual(assessment.direction, "adverse")

    def test_explicit_uncapped_buyer_liability_remains_high(self) -> None:
        assessment = score_finding(
            rule_cards=self.cards,
            category_id="uncapped_liability",
            presence_status="present",
            evidence_text="Customer's liability shall be unlimited.",
            contract_type="services",
        )

        self.assertEqual(assessment.severity_ordinal, 3)
        self.assertEqual(assessment.risk_band, "high")
        self.assertEqual(assessment.direction, "adverse")
        self.assertIn("uncapped_buyer_general", assessment.trigger_ids)

    def test_material_uncapped_carveout_with_unknown_party_is_medium(self) -> None:
        assessment = score_finding(
            rule_cards=self.cards,
            category_id="uncapped_liability",
            presence_status="present",
            evidence_text=(
                "The limitation of liability shall not apply to obligations "
                "arising from indemnification, confidentiality, or data security."
            ),
            contract_type="services",
        )

        self.assertEqual(assessment.severity_ordinal, 2)
        self.assertEqual(assessment.risk_band, "medium")
        self.assertEqual(assessment.direction, "unclear")
        self.assertIn(
            "uncapped_material_carveout_role_unresolved",
            assessment.trigger_ids,
        )

    def test_ambiguous_renewal_reference_abstains(self) -> None:
        assessment = score_finding(
            rule_cards=self.cards,
            category_id="renewal_term",
            presence_status="present",
            evidence_text="The renewal term is set forth in Schedule 3.",
            contract_type="services",
        )

        self.assertIsNone(assessment.severity_ordinal)
        self.assertEqual(assessment.risk_band, "unresolved")
        self.assertEqual(assessment.applicability, "unclear")


if __name__ == "__main__":
    unittest.main()
