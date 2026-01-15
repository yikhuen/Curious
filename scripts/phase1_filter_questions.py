#!/usr/bin/env python3
"""
Phase 1: Filter questions with hard filters (blocklist, shape, PII).

Usage:
    python scripts/phase1_filter_questions.py --run-id run_001
    python scripts/phase1_filter_questions.py --run-id run_001 --input questions_raw.jsonl

Requires:
    pip install pyyaml
"""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ============================================================================
# LEAKAGE BLOCKLIST
# ============================================================================

# Explicit region terms (leakage=2)
COUNTRY_TERMS = {
    # Countries
    "singapore", "singaporean", "malaysia", "malaysian", "indonesia", "indonesian",
    "thailand", "thai", "vietnam", "vietnamese", "philippines", "filipino", "filipina",
    "japan", "japanese", "korea", "korean", "china", "chinese", "taiwan", "taiwanese",
    "india", "indian", "pakistan", "pakistani", "bangladesh", "bangladeshi",
    "usa", "u.s.a", "u.s.", "united states", "american", "america",
    "canada", "canadian", "mexico", "mexican",
    "uk", "u.k.", "britain", "british", "england", "english", "scotland", "scottish",
    "wales", "welsh", "ireland", "irish",
    "germany", "german", "france", "french", "italy", "italian", "spain", "spanish",
    "australia", "australian", "new zealand", "kiwi",
    # Cities
    "new york", "nyc", "los angeles", "la", "chicago", "houston", "phoenix",
    "san francisco", "seattle", "boston", "miami", "denver", "atlanta",
    "london", "manchester", "birmingham", "edinburgh", "glasgow", "dublin",
    "tokyo", "osaka", "kyoto", "seoul", "busan", "beijing", "shanghai", "hong kong",
    "mumbai", "delhi", "bangalore", "chennai",
    "sydney", "melbourne", "brisbane", "auckland",
    "toronto", "vancouver", "montreal",
    "paris", "berlin", "munich", "rome", "milan", "madrid", "barcelona",
    # Singapore-specific
    "changi", "orchard", "sentosa", "jurong", "tampines", "bedok", "woodlands",
}

# Institution/program terms (leakage=2)
INSTITUTION_TERMS = {
    # Singapore
    "hdb", "cpf", "mrt", "lrt", "ez-link", "nets", "giro", "medisave", "medishield",
    "polyclinic", "psle", "o-level", "a-level", "nus", "ntu", "smu", "polytechnic",
    "bto", "resale flat", "coe", "erp", "gst voucher", "cdc voucher",
    # US
    "401k", "401(k)", "ira", "roth", "medicare", "medicaid", "social security",
    "dmv", "irs", "fafsa", "sat", "act", "gpa", "community college",
    "hsa", "fsa", "ppo", "hmo", "cobra", "aca", "obamacare",
    "ez-pass", "e-zpass",
    # UK
    "nhs", "gp surgery", "a&e", "gcse", "ofsted", "council tax", "ni number",
    "national insurance", "oyster card", "contactless", "ucas",
    # Australia
    "medicare card", "centrelink", "hecs", "help debt", "myki", "opal card",
    # Canada
    "ohip", "presto card", "rrsp", "tfsa",
    # Currencies (when used as identifiers)
    "sgd", "usd", "gbp", "aud", "cad", "eur", "jpy", "krw", "inr", "myr",
}

# Implicit cultural terms (leakage=1, borderline)
IMPLICIT_TERMS = {
    # US-centric customs
    "tipping", "tip jar", "gratuity", "15%", "20%", "tip percentage",
    "prom", "homecoming", "sorority", "fraternity", "spring break",
    "thanksgiving", "fourth of july", "independence day", "super bowl",
    "tailgate", "tailgating", "black friday", "cyber monday",
    "school district", "property tax school",
    # UK-centric customs
    "gap year", "sixth form", "boxing day", "bonfire night",
    # Asian customs (when too specific)
    "red packet", "ang bao", "hongbao", "lunar new year bonus",
    "13th month", "double pay",
    "golden week",
}

# Combined blocklist with categories
BLOCKLIST = {
    "explicit": COUNTRY_TERMS | INSTITUTION_TERMS,
    "implicit": IMPLICIT_TERMS,
}


def check_blocklist(text: str) -> tuple[bool, str | None, str | None]:
    """
    Check if text contains blocklisted terms.
    Returns (blocked, term, category).
    """
    text_lower = text.lower()

    # Check explicit terms first
    for term in BLOCKLIST["explicit"]:
        # Use word boundary matching for short terms
        if len(term) <= 3:
            pattern = rf"\b{re.escape(term)}\b"
            if re.search(pattern, text_lower):
                return True, term, "explicit"
        elif term in text_lower:
            return True, term, "explicit"

    # Check implicit terms
    for term in BLOCKLIST["implicit"]:
        if len(term) <= 4:
            pattern = rf"\b{re.escape(term)}\b"
            if re.search(pattern, text_lower):
                return True, term, "implicit"
        elif term in text_lower:
            return True, term, "implicit"

    return False, None, None


# ============================================================================
# SHAPE CHECKS
# ============================================================================

def is_question(text: str) -> bool:
    """Check if text is a question (ends with ? or starts with question words)."""
    text = text.strip()
    if text.endswith("?"):
        return True
    question_starters = (
        "what", "how", "why", "when", "where", "which", "who", "whom",
        "is", "are", "do", "does", "can", "could", "should", "would", "will",
        "if", "in what", "under what",
    )
    text_lower = text.lower()
    return any(text_lower.startswith(starter) for starter in question_starters)


def check_length(text: str, min_len: int = 20, max_len: int = 500) -> tuple[bool, str | None]:
    """Check if text length is within bounds."""
    if len(text) < min_len:
        return False, f"too_short ({len(text)} < {min_len})"
    if len(text) > max_len:
        return False, f"too_long ({len(text)} > {max_len})"
    return True, None


def is_english(text: str) -> bool:
    """Basic check for English text (ASCII-heavy)."""
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    return ascii_chars / len(text) > 0.9 if text else False


# ============================================================================
# PII HEURISTICS
# ============================================================================

PII_PATTERNS = [
    # Email
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "email"),
    # Phone numbers (various formats)
    (r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", "phone"),
    (r"\b\+\d{1,3}[-.\s]?\d{6,14}\b", "phone"),
    # SSN-like
    (r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b", "ssn_like"),
    # Credit card-like
    (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "cc_like"),
    # Street addresses (basic)
    (r"\b\d{1,5}\s+\w+\s+(street|st|avenue|ave|road|rd|drive|dr|lane|ln|way|court|ct)\b", "address"),
]


def check_pii(text: str) -> tuple[bool, str | None]:
    """Check for PII patterns. Returns (has_pii, pii_type)."""
    for pattern, pii_type in PII_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True, pii_type
    return False, None


# ============================================================================
# MAIN FILTER LOGIC
# ============================================================================

def filter_question(record: dict) -> dict:
    """
    Apply all filters to a question record.
    Returns updated record with filters populated.
    """
    question = record.get("question", "")
    filters = record.get("filters", {}).copy()

    # 1. Blocklist check
    blocked, term, category = check_blocklist(question)
    if blocked:
        filters["blocked"] = True
        filters["block_term"] = term
        filters["block_category"] = category
        if category == "explicit":
            filters["explicit_leakage"] = True
        else:
            filters["implicit_leakage"] = True
    else:
        filters["blocked"] = False
        filters["explicit_leakage"] = False
        filters["implicit_leakage"] = False

    # 2. Shape checks
    filters["is_question"] = is_question(question)

    length_ok, length_reason = check_length(question)
    filters["length_ok"] = length_ok
    if not length_ok:
        filters["length_reason"] = length_reason

    filters["is_english"] = is_english(question)

    # 3. PII check
    has_pii, pii_type = check_pii(question)
    filters["pii"] = has_pii
    if has_pii:
        filters["pii_type"] = pii_type

    # 4. Overall pass/fail
    filters["passed"] = (
        not filters["blocked"]
        and filters["is_question"]
        and filters["length_ok"]
        and filters["is_english"]
        and not filters["pii"]
    )

    record["filters"] = filters
    return record


def main():
    parser = argparse.ArgumentParser(description="Filter questions for Phase 1")
    parser.add_argument("--run-id", required=True, help="Run identifier")
    parser.add_argument("--input", default="questions_raw.jsonl", help="Input file name")
    parser.add_argument("--output", default="questions_filtered.jsonl", help="Output file name")
    args = parser.parse_args()

    run_dir = ROOT / "data" / "runs" / args.run_id
    input_path = run_dir / args.input
    output_path = run_dir / args.output

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return

    print(f"Phase 1 Filtering")
    print(f"=================")
    print(f"Run ID: {args.run_id}")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print()

    stats = {
        "total": 0,
        "passed": 0,
        "blocked_explicit": 0,
        "blocked_implicit": 0,
        "not_question": 0,
        "length_fail": 0,
        "not_english": 0,
        "pii": 0,
    }

    with open(input_path) as f_in, open(output_path, "w") as f_out:
        for line in f_in:
            if not line.strip():
                continue

            record = json.loads(line)
            record = filter_question(record)
            stats["total"] += 1

            filters = record["filters"]
            if filters["passed"]:
                stats["passed"] += 1
            else:
                if filters.get("explicit_leakage"):
                    stats["blocked_explicit"] += 1
                elif filters.get("implicit_leakage"):
                    stats["blocked_implicit"] += 1
                if not filters.get("is_question"):
                    stats["not_question"] += 1
                if not filters.get("length_ok"):
                    stats["length_fail"] += 1
                if not filters.get("is_english"):
                    stats["not_english"] += 1
                if filters.get("pii"):
                    stats["pii"] += 1

            f_out.write(json.dumps(record) + "\n")

    # Print summary
    print("Filter Results")
    print("-" * 40)
    print(f"Total records:       {stats['total']}")
    print(f"Passed:              {stats['passed']} ({100*stats['passed']/max(1,stats['total']):.1f}%)")
    print()
    print("Failure breakdown:")
    print(f"  Blocked (explicit): {stats['blocked_explicit']}")
    print(f"  Blocked (implicit): {stats['blocked_implicit']}")
    print(f"  Not a question:     {stats['not_question']}")
    print(f"  Length fail:        {stats['length_fail']}")
    print(f"  Not English:        {stats['not_english']}")
    print(f"  PII detected:       {stats['pii']}")
    print()
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
