#!/usr/bin/env python3
"""
Phase 1: Generate distribution report and sample audit examples.

Usage:
    python scripts/phase1_report.py --run-id run_001
    python scripts/phase1_report.py --run-id run_001 --sample 50

Requires:
    pip install pyyaml tabulate
"""

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_yaml_config(name: str) -> dict:
    with open(ROOT / "configs" / name) as f:
        return yaml.safe_load(f)


def load_records(path: Path) -> list[dict]:
    records = []
    if path.exists():
        with open(path) as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
    return records


def print_table(headers: list[str], rows: list[list], widths: list[int] = None):
    """Simple table printer without external dependencies."""
    if widths is None:
        widths = [max(len(str(h)), max((len(str(r[i])) for r in rows), default=0)) for i, h in enumerate(headers)]

    # Header
    header_line = " | ".join(str(h).ljust(w) for h, w in zip(headers, widths))
    print(header_line)
    print("-+-".join("-" * w for w in widths))

    # Rows
    for row in rows:
        print(" | ".join(str(c).ljust(w) for c, w in zip(row, widths)))


def main():
    parser = argparse.ArgumentParser(description="Generate Phase 1 report")
    parser.add_argument("--run-id", required=True, help="Run identifier")
    parser.add_argument("--sample", type=int, default=20, help="Number of samples to show per category")
    parser.add_argument("--output", default=None, help="Output file for report (default: stdout + JSON)")
    args = parser.parse_args()

    run_dir = ROOT / "data" / "runs" / args.run_id

    # Load all pipeline stage files
    raw_path = run_dir / "questions_raw.jsonl"
    filtered_path = run_dir / "questions_filtered.jsonl"
    deduped_path = run_dir / "questions_deduped.jsonl"
    scored_path = run_dir / "questions_scored.jsonl"
    accepted_path = run_dir / "questions_accepted.jsonl"

    raw = load_records(raw_path)
    filtered = load_records(filtered_path)
    deduped = load_records(deduped_path)
    scored = load_records(scored_path)
    accepted = load_records(accepted_path)

    # Load configs for reference
    domains_config = load_yaml_config("domains.yaml")
    types_config = load_yaml_config("question_types.yaml")
    domain_ids = [d["id"] for d in domains_config["domains"]]
    type_ids = [t["id"] for t in types_config["question_types"]]

    print("=" * 70)
    print(f"PHASE 1 REPORT: {args.run_id}")
    print("=" * 70)
    print()

    # =========================================================================
    # PIPELINE FUNNEL
    # =========================================================================
    print("PIPELINE FUNNEL")
    print("-" * 40)
    stages = [
        ("Raw generated", len(raw)),
        ("Passed filters", sum(1 for r in filtered if r.get("filters", {}).get("passed", False))),
        ("Passed dedup", sum(1 for r in deduped if r.get("filters", {}).get("dedup_passed", False))),
        ("Scored", sum(1 for r in scored if r.get("leakage_score") is not None)),
        ("Accepted", len(accepted)),
    ]
    for stage, count in stages:
        pct = f"({100*count/stages[0][1]:.1f}%)" if stages[0][1] > 0 else ""
        print(f"  {stage:20s}: {count:5d} {pct}")
    print()

    # =========================================================================
    # FILTER BREAKDOWN
    # =========================================================================
    print("FILTER BREAKDOWN")
    print("-" * 40)
    filter_stats = {
        "explicit_leakage": 0,
        "implicit_leakage": 0,
        "not_question": 0,
        "length_fail": 0,
        "not_english": 0,
        "pii": 0,
    }
    for r in filtered:
        f = r.get("filters", {})
        if f.get("explicit_leakage"):
            filter_stats["explicit_leakage"] += 1
        if f.get("implicit_leakage"):
            filter_stats["implicit_leakage"] += 1
        if not f.get("is_question", True):
            filter_stats["not_question"] += 1
        if not f.get("length_ok", True):
            filter_stats["length_fail"] += 1
        if not f.get("is_english", True):
            filter_stats["not_english"] += 1
        if f.get("pii"):
            filter_stats["pii"] += 1

    for reason, count in filter_stats.items():
        print(f"  {reason:20s}: {count:5d}")
    print()

    # =========================================================================
    # DEDUP STATS
    # =========================================================================
    print("DEDUP STATS")
    print("-" * 40)
    dedup_rejected = sum(1 for r in deduped if not r.get("filters", {}).get("dedup_passed", True) and r.get("filters", {}).get("passed", False))
    novelty_scores = [r.get("filters", {}).get("novelty_score", 0) for r in deduped if r.get("filters", {}).get("dedup_passed", True)]
    if novelty_scores:
        avg_novelty = sum(novelty_scores) / len(novelty_scores)
        print(f"  Rejected as duplicates: {dedup_rejected}")
        print(f"  Average novelty score:  {avg_novelty:.3f}")
    else:
        print("  No novelty data available")
    print()

    # =========================================================================
    # SCORING DISTRIBUTION
    # =========================================================================
    print("SCORING DISTRIBUTION")
    print("-" * 40)
    leakage_dist = defaultdict(int)
    salience_dist = defaultdict(int)
    for r in scored:
        if r.get("leakage_score") is not None:
            leakage_dist[r["leakage_score"]] += 1
        if r.get("salience_score") is not None:
            salience_dist[r["salience_score"]] += 1

    print("  Leakage:")
    for k in sorted(leakage_dist.keys()):
        print(f"    {k}: {leakage_dist[k]}")
    print("  Salience:")
    for k in sorted(salience_dist.keys()):
        print(f"    {k}: {salience_dist[k]}")
    print()

    # =========================================================================
    # DOMAIN × TYPE COVERAGE
    # =========================================================================
    print("DOMAIN × TYPE COVERAGE (Accepted)")
    print("-" * 40)

    # Build coverage matrix
    coverage = defaultdict(lambda: defaultdict(int))
    for r in accepted:
        coverage[r.get("domain", "unknown")][r.get("question_type", "unknown")] += 1

    # Print as table
    headers = ["Domain"] + type_ids + ["Total"]
    rows = []
    for domain in domain_ids:
        row = [domain]
        total = 0
        for qtype in type_ids:
            count = coverage[domain][qtype]
            row.append(count)
            total += count
        row.append(total)
        rows.append(row)

    # Add totals row
    totals_row = ["TOTAL"]
    grand_total = 0
    for qtype in type_ids:
        col_total = sum(coverage[d][qtype] for d in domain_ids)
        totals_row.append(col_total)
        grand_total += col_total
    totals_row.append(grand_total)
    rows.append(totals_row)

    print_table(headers, rows)
    print()

    # =========================================================================
    # SAMPLE OUTPUTS
    # =========================================================================
    print("SAMPLE ACCEPTED QUESTIONS")
    print("-" * 70)
    sample_accepted = random.sample(accepted, min(args.sample, len(accepted))) if accepted else []
    for i, r in enumerate(sample_accepted, 1):
        print(f"{i}. [{r.get('domain')}/{r.get('question_type')}] leak={r.get('leakage_score')} sal={r.get('salience_score')}")
        print(f"   {r['question']}")
        if r.get("judge_rationale"):
            print(f"   Rationale: {r['judge_rationale'][:100]}...")
        print()

    # =========================================================================
    # SAMPLE REJECTED (for audit)
    # =========================================================================
    print("SAMPLE REJECTED QUESTIONS (for audit)")
    print("-" * 70)
    rejected = [r for r in scored if r.get("leakage_score") is not None and not r.get("filters", {}).get("accepted", False)]
    sample_rejected = random.sample(rejected, min(args.sample, len(rejected))) if rejected else []
    for i, r in enumerate(sample_rejected, 1):
        print(f"{i}. [{r.get('domain')}/{r.get('question_type')}] leak={r.get('leakage_score')} sal={r.get('salience_score')}")
        print(f"   {r['question']}")
        if r.get("judge_rationale"):
            print(f"   Rationale: {r['judge_rationale'][:100]}...")
        print()

    # =========================================================================
    # SAVE JSON REPORT
    # =========================================================================
    report = {
        "run_id": args.run_id,
        "funnel": dict(stages),
        "filter_breakdown": filter_stats,
        "leakage_distribution": dict(leakage_dist),
        "salience_distribution": dict(salience_dist),
        "coverage": {d: dict(coverage[d]) for d in domain_ids},
        "totals": {
            "raw": len(raw),
            "accepted": len(accepted),
            "acceptance_rate": len(accepted) / len(raw) if raw else 0,
        },
    }

    report_path = run_dir / "phase1_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()
