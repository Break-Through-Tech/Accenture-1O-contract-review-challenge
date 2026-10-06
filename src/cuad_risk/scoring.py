from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any


SEVERITY_BANDS = {0: "none", 1: "low", 2: "medium", 3: "high"}


def _normalize_text(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        text.replace("’", "'").replace("–", "-").replace("—", "-"),
    ).strip()


@dataclass(frozen=True)
class FindingAssessment:
    severity_ordinal: int | None
    risk_band: str
    direction: str
    confidence: str
    label_status: str
    applicability: str
    trigger_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    rule_card_id: str
    review_bundle_id: str
    risk_domain: str
    issue_family_template: str
    material_if_unresolved: bool
    rationale: str


def load_rule_cards(path: Path) -> dict[str, dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        config = json.load(handle)
    return {
        category["category_id"]: category for category in config["categories"]
    }


def _matches(rule: dict[str, Any], text: str, contract_type: str) -> bool:
    text = _normalize_text(text)
    allowed_contract_types = rule.get("contract_types")
    if allowed_contract_types and contract_type not in allowed_contract_types:
        return False

    when_all = rule.get("when_all", [])
    when_any = rule.get("when_any", [])
    when_none = rule.get("when_none", [])
    count_patterns = rule.get("count_patterns", [])
    match_count = sum(
        bool(re.search(pattern, text, flags=re.IGNORECASE))
        for pattern in count_patterns
    )
    return (
        all(re.search(pattern, text, flags=re.IGNORECASE) for pattern in when_all)
        and (
            not when_any
            or any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in when_any)
        )
        and not any(
            re.search(pattern, text, flags=re.IGNORECASE) for pattern in when_none
        )
        and match_count >= rule.get("min_pattern_matches", 0)
        and match_count <= rule.get("max_pattern_matches", len(count_patterns))
    )


def _assessment_from_rule(
    rule: dict[str, Any], card: dict[str, Any]
) -> FindingAssessment:
    severity = rule.get("severity_ordinal")
    if severity is None:
        risk_band = rule.get("risk_band", "not_applicable")
        default_label_status = "weak_not_applicable"
    else:
        risk_band = rule.get("risk_band", SEVERITY_BANDS[severity])
        default_label_status = "weak_automatic"
    return FindingAssessment(
        severity_ordinal=severity,
        risk_band=risk_band,
        direction=rule.get("direction", "unclear"),
        confidence=rule.get("confidence", "medium"),
        label_status=rule.get("label_status", default_label_status),
        applicability=rule.get(
            "applicability", "not_applicable" if severity is None else "applicable"
        ),
        trigger_ids=(rule["rule_id"],),
        source_ids=tuple(rule.get("source_ids", card.get("source_ids", []))),
        rule_card_id=card["rule_card_id"],
        review_bundle_id=card["review_bundle_id"],
        risk_domain=card["risk_domain"],
        issue_family_template=card["issue_family_template"],
        material_if_unresolved=card["material_if_unresolved"],
        rationale=rule["rationale"],
    )


def score_finding(
    *,
    rule_cards: dict[str, dict[str, Any]],
    category_id: str,
    presence_status: str,
    evidence_text: str,
    contract_type: str,
) -> FindingAssessment:
    if category_id not in rule_cards:
        raise KeyError(f"Unknown risk category: {category_id}")
    card = rule_cards[category_id]
    rule_group = "present_rules" if presence_status == "present" else "missing_rules"
    ordered_rules = sorted(
        card.get(rule_group, []),
        key=lambda rule: (rule.get("priority", 0), rule.get("severity_ordinal", -1)),
        reverse=True,
    )
    for rule in ordered_rules:
        if _matches(rule, evidence_text, contract_type):
            return _assessment_from_rule(rule, card)

    return FindingAssessment(
        severity_ordinal=None,
        risk_band="unresolved",
        direction="unclear",
        confidence="low",
        label_status="weak_abstain",
        applicability="unclear",
        trigger_ids=(),
        source_ids=tuple(card.get("source_ids", [])),
        rule_card_id=card["rule_card_id"],
        review_bundle_id=card["review_bundle_id"],
        risk_domain=card["risk_domain"],
        issue_family_template=card["issue_family_template"],
        material_if_unresolved=card["material_if_unresolved"],
        rationale=card.get(
            "abstain_rationale",
            "The available text does not satisfy a documented project rule.",
        ),
    )
