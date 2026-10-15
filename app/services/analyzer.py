from dataclasses import dataclass
from app.services.rules import RULES


@dataclass(frozen=True)
class FindingResult:
    rule_id: str
    category: str
    evidence_line: int
    evidence: str
    explanation: str
    verification: str


def analyze_log(log_text: str) -> list[FindingResult]:
    """Find evidence-backed matches. No speculative diagnosis is returned."""
    results: list[FindingResult] = []
    for line_number, line in enumerate(log_text.splitlines(), start=1):
        lowered = line.lower()
        for rule in RULES:
            if all(keyword in lowered for keyword in rule.keywords):
                results.append(FindingResult(
                    rule_id=rule.identifier,
                    category=rule.category,
                    evidence_line=line_number,
                    evidence=line.strip()[:1000],
                    explanation=rule.explanation,
                    verification=rule.verification,
                ))
    return results[:50]


def summarize(findings: list[FindingResult]) -> str:
    if not findings:
        return "Tanımlı kurallarla eşleşen bulgu yok. Bu, sistemin sağlıklı olduğunu kanıtlamaz."
    unique_categories = sorted({finding.category for finding in findings})
    return f"{len(findings)} kanıt eşleşmesi bulundu. Kategoriler: {', '.join(unique_categories)}. Teşhis henüz doğrulanmadı."
