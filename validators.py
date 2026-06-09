"""Email validation, lead partitioning, and LLM response normalization."""

from __future__ import annotations

import json
import re
from typing import Any

PUBLIC_DOMAINS = frozenset(
    {
        "gmail.com",
        "hotmail.com",
        "yahoo.com",
        "outlook.com",
        "live.com",
        "icloud.com",
    }
)

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

COL_EMAIL = "Original Email"
COL_DOMAIN = "Domain"
COL_STATUS = "Validation Status"
COL_DECISION = "Decision-Making Status (AI)"
COL_B2B = "B2B Fit Level (AI)"
COL_INSIGHT = "Company Insight (AI)"

RESULT_COLUMNS = [
    COL_EMAIL,
    COL_DOMAIN,
    COL_STATUS,
    COL_DECISION,
    COL_B2B,
    COL_INSIGHT,
]

DECISION_STATUSES = frozenset(
    {"Executive", "Director", "Manager", "Specialist/IC", "Unknown"}
)


def validate_email_format(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email.strip()))


def extract_domain(email: str) -> str:
    return email.strip().split("@", 1)[-1].lower()


def is_public_domain(domain: str) -> bool:
    return domain.lower() in PUBLIC_DOMAINS


def parse_lines(raw: str) -> list[str]:
    return [line.strip() for line in raw.splitlines() if line.strip()]


def format_company_insight(
    b2b_fit: str,
    company_summary: str = "",
    fit_rationale: str = "",
) -> str:
    """Combine AI company fields for High/Medium B2B fit; otherwise em dash."""
    if b2b_fit not in ("High", "Medium"):
        return "—"
    summary = (company_summary or "").strip()
    rationale = (fit_rationale or "").strip()
    if summary and rationale:
        return f"{summary} — {rationale}"
    if summary:
        return summary
    if rationale:
        return rationale
    return "—"


def parse_classification_response(text: str) -> tuple[str, str, str, str]:
    """Extract decision_status, b2b_fit, and optional insight fields from JSON."""
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("Empty model response.")

    json_match = re.search(r"\{[\s\S]*\}", cleaned)
    if json_match:
        try:
            data = json.loads(json_match.group())
            if isinstance(data, dict):
                decision = _pick_field(
                    data,
                    (
                        "decision_status",
                        "decision-making status",
                        "decision_making_status",
                        "decision_role",
                        "decisionRole",
                    ),
                )
                b2b_fit = _pick_field(
                    data,
                    ("b2b_fit", "b2b_fit_level", "b2b_assessment", "fit"),
                )
                if decision and b2b_fit:
                    normalized_decision = _normalize_decision_status(decision)
                    normalized_fit = _normalize_b2b_fit(b2b_fit)
                    summary = _pick_field(
                        data,
                        ("company_summary", "company_description", "company"),
                    )
                    rationale = _pick_field(
                        data,
                        ("fit_rationale", "rationale", "fit_reason", "why_fit"),
                    )
                    insight = format_company_insight(
                        normalized_fit, summary, rationale
                    )
                    return normalized_decision, normalized_fit, summary, rationale
        except json.JSONDecodeError:
            pass

    decision = _extract_labeled_value(
        cleaned,
        ("decision_status", "decision-making status", "decision making status"),
    )
    b2b_raw = _extract_labeled_value(
        cleaned,
        ("b2b_fit", "b2b fit", "b2b_fit_level", "b2b fit level"),
    )
    if decision and b2b_raw:
        normalized_decision = _normalize_decision_status(decision)
        normalized_fit = _normalize_b2b_fit(b2b_raw)
        summary = _extract_labeled_value(
            cleaned, ("company_summary", "company summary", "company_description")
        )
        rationale = _extract_labeled_value(
            cleaned, ("fit_rationale", "fit rationale", "rationale")
        )
        insight = format_company_insight(normalized_fit, summary, rationale)
        return normalized_decision, normalized_fit, summary, rationale

    raise ValueError(f"Could not parse model response: {cleaned[:200]}")


def _pick_field(data: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        if key in data and data[key]:
            return str(data[key]).strip()
    return ""


def _extract_labeled_value(text: str, labels: tuple[str, ...]) -> str:
    for label in labels:
        pattern = rf"(?im)^\s*{re.escape(label)}\s*[:=]\s*(.+?)\s*$"
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip().strip('"').strip("'")
    return ""


def _normalize_decision_status(value: str) -> str:
    normalized = value.strip().lower()
    if "executive" in normalized or "c-level" in normalized or "c level" in normalized:
        return "Executive"
    if "director" in normalized:
        return "Director"
    if "manager" in normalized:
        return "Manager"
    if "specialist" in normalized or "contributor" in normalized or "/ic" in normalized:
        return "Specialist/IC"
    if normalized == "unknown" or "unknown" in normalized:
        return "Unknown"
    for status in DECISION_STATUSES:
        if status.lower() == normalized:
            return status
    raise ValueError(f"Invalid decision-making status: {value}")


def _normalize_b2b_fit(value: str) -> str:
    normalized = value.strip().lower()
    if "high" in normalized or "strong" in normalized:
        return "High"
    if "medium" in normalized or "moderate" in normalized or "med" in normalized:
        return "Medium"
    if "low" in normalized or "weak" in normalized:
        return "Low"
    raise ValueError(f"Invalid B2B fit level: {value}")


def row_invalid(email: str, domain: str) -> dict[str, str]:
    return {
        COL_EMAIL: email,
        COL_DOMAIN: domain or "—",
        COL_STATUS: "Invalid Email",
        COL_DECISION: "—",
        COL_B2B: "—",
        COL_INSIGHT: "—",
    }


def row_public(email: str, domain: str) -> dict[str, str]:
    return {
        COL_EMAIL: email,
        COL_DOMAIN: domain,
        COL_STATUS: "B2C / Personal (Low Fit)",
        COL_DECISION: "—",
        COL_B2B: "Low",
        COL_INSIGHT: "—",
    }


def row_corporate(
    email: str,
    domain: str,
    domain_cache: dict[str, tuple[str, str, str, str | None]],
    *,
    missing_api_key: bool = False,
) -> dict[str, str]:
    if missing_api_key:
        return {
            COL_EMAIL: email,
            COL_DOMAIN: domain,
            COL_STATUS: "API Key Required",
            COL_DECISION: "—",
            COL_B2B: "—",
            COL_INSIGHT: "—",
        }

    decision, b2b_fit, insight, error = domain_cache.get(
        domain, ("—", "—", "—", "Domain not classified")
    )
    if error:
        return {
            COL_EMAIL: email,
            COL_DOMAIN: domain,
            COL_STATUS: f"API Error: {error}",
            COL_DECISION: "—",
            COL_B2B: "—",
            COL_INSIGHT: "—",
        }
    return {
        COL_EMAIL: email,
        COL_DOMAIN: domain,
        COL_STATUS: "Corporate Email",
        COL_DECISION: decision,
        COL_B2B: b2b_fit,
        COL_INSIGHT: insight,
    }


def partition_emails(
    emails: list[str],
) -> tuple[list[dict[str, str] | None], list[tuple[int, str, str]]]:
    """Return slots in input order and corporate (index, email, domain) tuples."""
    slots: list[dict[str, str] | None] = []
    corporate: list[tuple[int, str, str]] = []

    for index, email in enumerate(emails):
        domain = extract_domain(email) if "@" in email else ""
        if not validate_email_format(email):
            slots.append(row_invalid(email, domain))
            continue
        if is_public_domain(domain):
            slots.append(row_public(email, domain))
            continue
        slots.append(None)
        corporate.append((index, email, domain))

    return slots, corporate
