#!/usr/bin/env python3
"""
Phase 1: Deduplicate questions using ROUGE-L novelty gate.

Usage:
    python scripts/phase1_dedup_questions.py --run-id run_001
    python scripts/phase1_dedup_questions.py --run-id run_001 --threshold 0.7

Based on Self-Instruct novelty filtering (threshold ~0.7).

Requires:
    pip install rouge-score
"""

import argparse
import json
from pathlib import Path

try:
    from rouge_score import rouge_scorer
except ImportError:
    print("Error: rouge-score not installed. Run: pip install rouge-score")
    exit(1)

ROOT = Path(__file__).resolve().parent.parent


def compute_rouge_l(scorer, text1: str, text2: str) -> float:
    """Compute ROUGE-L F1 score between two texts."""
    scores = scorer.score(text1, text2)
    return scores["rougeL"].fmeasure


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    return text.lower().strip()


def find_max_similarity(
    scorer,
    candidate: str,
    accepted: list[str],
    sample_size: int = 100,
) -> tuple[float, int]:
    """
    Find maximum ROUGE-L similarity between candidate and accepted questions.
    For efficiency, only compare against the most recent `sample_size` accepted.
    Returns (max_score, index_of_most_similar).
    """
    if not accepted:
        return 0.0, -1

    # Compare against recent accepted questions (most likely to be similar)
    compare_set = accepted[-sample_size:] if len(accepted) > sample_size else accepted
    start_idx = max(0, len(accepted) - sample_size)

    max_score = 0.0
    max_idx = -1

    for i, acc in enumerate(compare_set):
        score = compute_rouge_l(scorer, candidate, acc)
        if score > max_score:
            max_score = score
            max_idx = start_idx + i

    return max_score, max_idx


def main():
    parser = argparse.ArgumentParser(description="Deduplicate questions for Phase 1")
    parser.add_argument("--run-id", required=True, help="Run identifier")
    parser.add_argument("--input", default="questions_filtered.jsonl", help="Input file name")
    parser.add_argument("--output", default="questions_deduped.jsonl", help="Output file name")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="ROUGE-L threshold for rejection (default: 0.7, per Self-Instruct)",
    )
    parser.add_argument(
        "--include-seeds",
        action="store_true",
        help="Include seed questions in dedup pool (avoid generating near-duplicates of seeds)",
    )
    args = parser.parse_args()

    run_dir = ROOT / "data" / "runs" / args.run_id
    input_path = run_dir / args.input
    output_path = run_dir / args.output

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return

    print(f"Phase 1 Deduplication")
    print(f"=====================")
    print(f"Run ID: {args.run_id}")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"ROUGE-L threshold: {args.threshold}")
    print()

    # Initialize ROUGE scorer
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)

    # Optionally load seed questions into the accepted pool
    accepted_texts: list[str] = []
    if args.include_seeds:
        seed_path = ROOT / "data" / "seeds" / "questions_gold.jsonl"
        if seed_path.exists():
            with open(seed_path) as f:
                for line in f:
                    if line.strip():
                        seed = json.loads(line)
                        # Only include gold seeds (leakage=0)
                        if seed.get("leakage_score") == 0:
                            accepted_texts.append(normalize_text(seed["question"]))
            print(f"Loaded {len(accepted_texts)} seed questions into dedup pool")
            print()

    stats = {
        "total": 0,
        "skipped_not_passed": 0,
        "accepted": 0,
        "rejected_duplicate": 0,
        "scores": [],  # For distribution analysis
    }

    with open(input_path) as f_in, open(output_path, "w") as f_out:
        for line in f_in:
            if not line.strip():
                continue

            record = json.loads(line)
            stats["total"] += 1

            # Skip questions that didn't pass filters
            if not record.get("filters", {}).get("passed", False):
                stats["skipped_not_passed"] += 1
                record["filters"]["dedup_skipped"] = True
                record["filters"]["dedup_passed"] = False
                f_out.write(json.dumps(record) + "\n")
                continue

            # Compute novelty
            question = normalize_text(record["question"])
            max_sim, similar_idx = find_max_similarity(scorer, question, accepted_texts)

            stats["scores"].append(max_sim)
            record["filters"]["novelty_score"] = round(1 - max_sim, 3)  # Higher = more novel
            record["filters"]["max_rouge_l"] = round(max_sim, 3)

            if max_sim >= args.threshold:
                # Too similar to existing question
                stats["rejected_duplicate"] += 1
                record["filters"]["dedup_passed"] = False
                record["filters"]["dedup_reason"] = f"similar to idx {similar_idx} (rouge={max_sim:.3f})"
            else:
                # Accept and add to pool
                stats["accepted"] += 1
                record["filters"]["dedup_passed"] = True
                accepted_texts.append(question)

            f_out.write(json.dumps(record) + "\n")

            # Progress indicator
            if stats["total"] % 100 == 0:
                print(f"  Processed {stats['total']} (accepted: {stats['accepted']}, rejected: {stats['rejected_duplicate']})")

    # Print summary
    print()
    print("Dedup Results")
    print("-" * 40)
    print(f"Total records:        {stats['total']}")
    print(f"Skipped (not passed): {stats['skipped_not_passed']}")
    print(f"Accepted (novel):     {stats['accepted']}")
    print(f"Rejected (duplicate): {stats['rejected_duplicate']}")

    if stats["scores"]:
        avg_score = sum(stats["scores"]) / len(stats["scores"])
        max_score = max(stats["scores"])
        print()
        print("ROUGE-L similarity stats (among passed):")
        print(f"  Average: {avg_score:.3f}")
        print(f"  Max:     {max_score:.3f}")
        # Distribution buckets
        buckets = {"<0.3": 0, "0.3-0.5": 0, "0.5-0.7": 0, ">=0.7": 0}
        for s in stats["scores"]:
            if s < 0.3:
                buckets["<0.3"] += 1
            elif s < 0.5:
                buckets["0.3-0.5"] += 1
            elif s < 0.7:
                buckets["0.5-0.7"] += 1
            else:
                buckets[">=0.7"] += 1
        print("  Distribution:")
        for k, v in buckets.items():
            print(f"    {k}: {v}")

    print()
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
