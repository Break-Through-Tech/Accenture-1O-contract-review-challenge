from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class ContractAssessment:
    risk_band: str
    risk_ordinal: int
    review_priority_band: str
    review_priority_ordinal: int
    triggering_finding_ids: tuple[str, ...]
    triggering_domains: tuple[str, ...]
    rationale: str


def _representative_findings(
    findings: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    def priority(finding: dict[str, Any]) -> int:
        severity = finding.get("severity_ordinal")
        numeric_priority = -1 if severity is None else int(severity) * 2
        if finding.get("unresolved_material") is True:
            # A material abstention must outrank None/Low findings in the same
            # linked issue family so uncertainty cannot be silently suppressed.
            return max(numeric_priority, 3)
        return numeric_priority

    by_issue_family: dict[str, dict[str, Any]] = {}
    for finding in findings:
        family = str(finding["issue_family_id"])
        current = by_issue_family.get(family)
        if current is None or priority(finding) > priority(current):
            by_issue_family[family] = finding
    return list(by_issue_family.values())


def _result(
    band: str,
    findings: list[dict[str, Any]],
    rationale: str,
    *,
    review_priority_band: str | None = None,
) -> ContractAssessment:
    priority_band = review_priority_band or band
    return ContractAssessment(
        risk_band=band,
        risk_ordinal={"low": 1, "medium": 2, "high": 3}[band],
        review_priority_band=priority_band,
        review_priority_ordinal={"low": 1, "medium": 2, "high": 3}[
            priority_band
        ],
        triggering_finding_ids=tuple(
            sorted(str(finding["finding_id"]) for finding in findings)
        ),
        triggering_domains=tuple(
            sorted({str(finding["risk_domain"]) for finding in findings})
        ),
        rationale=rationale,
    )


def roll_up_contract(findings: Iterable[dict[str, Any]]) -> ContractAssessment:
    representatives = _representative_findings(findings)
    high_findings = [
        finding
        for finding in representatives
        if finding.get("severity_ordinal") == 3
    ]
    if high_findings:
        return _result(
            "high",
            high_findings,
            "At least one distinct issue family contains a High finding.",
        )

    medium_findings = [
        finding
        for finding in representatives
        if finding.get("severity_ordinal") == 2
    ]
    if medium_findings:
        return _result(
            "medium",
            medium_findings,
            "At least one distinct issue family contains a Medium finding.",
        )

    unresolved = [
        finding
        for finding in representatives
        if finding.get("unresolved_material") is True
    ]
    if unresolved:
        return _result(
            "low",
            unresolved,
            "No explicit finding exceeds Low severity, but a material issue "
            "remains unresolved and raises review priority to Medium.",
            review_priority_band="medium",
        )

    low_findings = [
        finding
        for finding in representatives
        if finding.get("severity_ordinal") in {0, 1}
    ]
    return _result(
        "low",
        low_findings,
        "No distinct issue family exceeds Low severity.",
    )
