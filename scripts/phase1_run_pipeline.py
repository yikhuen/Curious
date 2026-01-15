#!/usr/bin/env python3
"""
Phase 1: Run the full question generation pipeline.

Usage:
    python scripts/phase1_run_pipeline.py --run-id run_001 --base-url http://localhost:8000/v1
    python scripts/phase1_run_pipeline.py --run-id run_001 --base-url http://localhost:8000/v1 --skip-generate

This script orchestrates all Phase 1 steps:
1. Generate questions (if not skipped)
2. Filter questions
3. Deduplicate questions
4. Score questions with LLM judge
5. Generate report
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"


def run_step(name: str, script: str, args: list[str], required_input: Path = None) -> bool:
    """Run a pipeline step. Returns True if successful."""
    print()
    print("=" * 70)
    print(f"STEP: {name}")
    print("=" * 70)

    if required_input and not required_input.exists():
        print(f"Skipping: required input not found: {required_input}")
        return False

    cmd = [sys.executable, str(SCRIPTS / script)] + args
    print(f"Running: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Run full Phase 1 pipeline")
    parser.add_argument("--run-id", required=True, help="Run identifier (e.g., run_001)")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OPENAI_BASE_URL", "http://localhost:8000/v1"),
        help="OpenAI-compatible API base URL",
    )
    parser.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY", "not-needed"))
    parser.add_argument("--profile", default=None, help="Model profile to use")
    parser.add_argument("--num", type=int, default=None, help="Override questions per bucket")
    parser.add_argument("--skip-generate", action="store_true", help="Skip generation (use existing raw file)")
    parser.add_argument("--skip-score", action="store_true", help="Skip scoring (use existing scored file)")
    parser.add_argument("--score-limit", type=int, default=None, help="Limit questions to score")
    parser.add_argument("--dedup-threshold", type=float, default=0.7, help="ROUGE-L dedup threshold")
    args = parser.parse_args()

    run_dir = ROOT / "data" / "runs" / args.run_id

    print("=" * 70)
    print(f"PHASE 1 PIPELINE: {args.run_id}")
    print("=" * 70)
    print(f"Base URL: {args.base_url}")
    print(f"Profile: {args.profile or 'default'}")
    print(f"Output: {run_dir}")

    # Build common args
    common_args = ["--run-id", args.run_id]
    llm_args = ["--base-url", args.base_url, "--api-key", args.api_key]
    if args.profile:
        llm_args += ["--profile", args.profile]

    success = True

    # Step 1: Generate
    if not args.skip_generate:
        gen_args = common_args + llm_args
        if args.num:
            gen_args += ["--num", str(args.num)]
        success = run_step(
            "Generate Questions",
            "phase1_generate_questions.py",
            gen_args,
        )
        if not success:
            print("Generation failed, stopping pipeline")
            return 1

    # Step 2: Filter
    success = run_step(
        "Filter Questions",
        "phase1_filter_questions.py",
        common_args,
        required_input=run_dir / "questions_raw.jsonl",
    )
    if not success:
        print("Filtering failed, stopping pipeline")
        return 1

    # Step 3: Dedup
    dedup_args = common_args + ["--threshold", str(args.dedup_threshold), "--include-seeds"]
    success = run_step(
        "Deduplicate Questions",
        "phase1_dedup_questions.py",
        dedup_args,
        required_input=run_dir / "questions_filtered.jsonl",
    )
    if not success:
        print("Dedup failed, stopping pipeline")
        return 1

    # Step 4: Score
    if not args.skip_score:
        score_args = common_args + llm_args
        if args.score_limit:
            score_args += ["--limit", str(args.score_limit)]
        success = run_step(
            "Score Questions",
            "phase1_score_questions.py",
            score_args,
            required_input=run_dir / "questions_deduped.jsonl",
        )
        if not success:
            print("Scoring failed, stopping pipeline")
            return 1

    # Step 5: Report
    success = run_step(
        "Generate Report",
        "phase1_report.py",
        common_args,
        required_input=run_dir / "questions_scored.jsonl",
    )

    print()
    print("=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print(f"Output directory: {run_dir}")
    print()
    print("Files created:")
    for f in sorted(run_dir.glob("*")):
        print(f"  - {f.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
