#!/usr/bin/env python3
"""
Phase 1: Score questions with LLM judge (leakage + salience).

Usage:
    python scripts/phase1_score_questions.py --run-id run_001 --base-url http://localhost:8000/v1
    python scripts/phase1_score_questions.py --run-id run_001 --base-url http://localhost:8000/v1 --limit 100

Requires:
    pip install openai pyyaml
"""

import argparse
import json
import os
import re
from pathlib import Path

import yaml
from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent


def load_yaml_config(name: str) -> dict:
    with open(ROOT / "configs" / name) as f:
        return yaml.safe_load(f)


def load_judge_prompt() -> str:
    with open(ROOT / "prompts" / "judges" / "leakage_salience.md") as f:
        return f.read()


def get_profile(config: dict, profile_name: str = None) -> dict:
    if profile_name is None:
        profile_name = config.get("default_profile", "qwen32b")
    profiles = config.get("profiles", {})
    if profile_name not in profiles:
        raise ValueError(f"Profile '{profile_name}' not found. Available: {list(profiles.keys())}")
    return profiles[profile_name]


def render_prompt(template: str, question: str) -> str:
    return template.replace("{{question}}", question)


def parse_json_response(text: str, is_reasoning_model: bool = False) -> dict | None:
    """Extract JSON from response, handling markdown code blocks and reasoning chains."""

    # For reasoning models, find JSON at the end
    if is_reasoning_model:
        json_pattern = r'\{[^{}]*"leakage_score"[^{}]*"salience_score"[^{}]*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        if matches:
            for match in reversed(matches):
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from code block
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding JSON object with expected keys
    match = re.search(r'\{[^{}]*"leakage_score"[^{}]*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def score_question(
    client: OpenAI,
    model_id: str,
    decoding_params: dict,
    judge_template: str,
    question: str,
    is_reasoning_model: bool = False,
) -> dict:
    """Score a question with the judge model."""
    prompt = render_prompt(judge_template, question)
    response = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": prompt}],
        temperature=decoding_params.get("temperature", 0.2),
        top_p=decoding_params.get("top_p", 0.9),
        max_tokens=decoding_params.get("max_tokens", 512),
    )
    raw = response.choices[0].message.content
    parsed = parse_json_response(raw, is_reasoning_model=is_reasoning_model)
    return {"raw": raw, "parsed": parsed}


def main():
    parser = argparse.ArgumentParser(description="Score questions with LLM judge")
    parser.add_argument("--run-id", required=True, help="Run identifier")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OPENAI_BASE_URL", "http://localhost:8000/v1"),
        help="OpenAI-compatible API base URL",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("OPENAI_API_KEY", "not-needed"),
        help="API key",
    )
    parser.add_argument("--profile", default=None, help="Model profile to use")
    parser.add_argument("--input", default="questions_deduped.jsonl", help="Input file name")
    parser.add_argument("--output-scored", default="questions_scored.jsonl", help="Scored output file")
    parser.add_argument("--output-accepted", default="questions_accepted.jsonl", help="Accepted output file")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of questions to score")
    parser.add_argument("--skip-scored", action="store_true", help="Skip already-scored questions")
    args = parser.parse_args()

    run_dir = ROOT / "data" / "runs" / args.run_id
    input_path = run_dir / args.input
    output_scored_path = run_dir / args.output_scored
    output_accepted_path = run_dir / args.output_accepted

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return

    # Load config
    llm_config = load_yaml_config("llm.yaml")
    profile = get_profile(llm_config, args.profile)
    model_id = profile["model_id"]
    decoding_params = profile.get("judge", {})
    is_reasoning_model = profile.get("is_reasoning_model", False)
    profile_name = args.profile or llm_config.get("default_profile", "qwen32b")

    judge_template = load_judge_prompt()

    print(f"Phase 1 Scoring")
    print(f"===============")
    print(f"Run ID: {args.run_id}")
    print(f"Profile: {profile_name} ({profile.get('name', model_id)})")
    print(f"Model: {model_id}")
    print(f"Input: {input_path}")
    print(f"Output (scored): {output_scored_path}")
    print(f"Output (accepted): {output_accepted_path}")
    if args.limit:
        print(f"Limit: {args.limit}")
    print()

    client = OpenAI(base_url=args.base_url, api_key=args.api_key)

    stats = {
        "total": 0,
        "skipped_dedup": 0,
        "skipped_already_scored": 0,
        "scored": 0,
        "parse_errors": 0,
        "api_errors": 0,
        "accepted": 0,
        "rejected_leakage": 0,
        "rejected_salience": 0,
        "leakage_dist": {0: 0, 1: 0, 2: 0},
        "salience_dist": {0: 0, 1: 0, 2: 0},
    }

    # Load all records first (to handle limits correctly)
    records = []
    with open(input_path) as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    # Filter to scoreable records
    to_score = []
    for record in records:
        filters = record.get("filters", {})
        # Skip if didn't pass dedup
        if not filters.get("dedup_passed", False):
            continue
        # Skip if already scored (and flag is set)
        if args.skip_scored and record.get("leakage_score") is not None:
            continue
        to_score.append(record)

    if args.limit:
        to_score = to_score[:args.limit]

    print(f"Records to score: {len(to_score)}")
    print()

    # Score questions
    scored_records = []
    for i, record in enumerate(to_score):
        stats["total"] += 1
        question = record["question"]

        print(f"[{i+1}/{len(to_score)}] Scoring: {question[:60]}...", end=" ", flush=True)

        try:
            result = score_question(
                client, model_id, decoding_params, judge_template, question, is_reasoning_model
            )
        except Exception as e:
            print(f"ERROR: {e}")
            stats["api_errors"] += 1
            scored_records.append(record)
            continue

        parsed = result["parsed"]
        if parsed:
            leakage = parsed.get("leakage_score")
            salience = parsed.get("salience_score")
            rationale = parsed.get("rationale", "")

            record["leakage_score"] = leakage
            record["salience_score"] = salience
            record["judge_rationale"] = rationale
            record["provenance"]["judge_model_id"] = model_id
            record["provenance"]["judge_profile"] = profile_name

            stats["scored"] += 1
            if leakage in stats["leakage_dist"]:
                stats["leakage_dist"][leakage] += 1
            if salience in stats["salience_dist"]:
                stats["salience_dist"][salience] += 1

            # Gate: accept if leakage=0 and salience>=1
            if leakage == 0 and salience is not None and salience >= 1:
                record["filters"]["accepted"] = True
                stats["accepted"] += 1
                status = "ACCEPT"
            else:
                record["filters"]["accepted"] = False
                if leakage != 0:
                    stats["rejected_leakage"] += 1
                    status = f"REJECT (leak={leakage})"
                else:
                    stats["rejected_salience"] += 1
                    status = f"REJECT (sal={salience})"

            print(f"{status} leak={leakage} sal={salience}")
        else:
            print(f"PARSE_FAIL")
            stats["parse_errors"] += 1
            record["leakage_score"] = None
            record["salience_score"] = None
            record["judge_raw_response"] = result["raw"][:500]
            record["filters"]["accepted"] = False

        scored_records.append(record)

    # Merge with non-scored records and write output
    scored_ids = {r["id"] for r in scored_records}
    all_records = []

    for record in records:
        if record["id"] in scored_ids:
            # Find the scored version
            for sr in scored_records:
                if sr["id"] == record["id"]:
                    all_records.append(sr)
                    break
        else:
            all_records.append(record)

    # Write scored output
    with open(output_scored_path, "w") as f:
        for record in all_records:
            f.write(json.dumps(record) + "\n")

    # Write accepted output
    accepted_records = [r for r in all_records if r.get("filters", {}).get("accepted", False)]
    with open(output_accepted_path, "w") as f:
        for record in accepted_records:
            f.write(json.dumps(record) + "\n")

    # Print summary
    print()
    print("Scoring Results")
    print("-" * 40)
    print(f"Total scored:         {stats['scored']}")
    print(f"Parse errors:         {stats['parse_errors']}")
    print(f"API errors:           {stats['api_errors']}")
    print()
    print(f"Accepted:             {stats['accepted']}")
    print(f"Rejected (leakage):   {stats['rejected_leakage']}")
    print(f"Rejected (salience):  {stats['rejected_salience']}")
    print()
    print("Leakage distribution:")
    for k, v in stats["leakage_dist"].items():
        print(f"  {k}: {v}")
    print()
    print("Salience distribution:")
    for k, v in stats["salience_dist"].items():
        print(f"  {k}: {v}")
    print()
    print(f"Output (scored): {output_scored_path}")
    print(f"Output (accepted): {output_accepted_path} ({len(accepted_records)} records)")


if __name__ == "__main__":
    main()
