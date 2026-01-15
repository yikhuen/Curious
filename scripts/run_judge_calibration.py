#!/usr/bin/env python3
"""
Run leakage/salience judge on the seed set for calibration.

Usage:
    python scripts/run_judge_calibration.py --base-url http://localhost:8000/v1

Requires:
    pip install openai pyyaml
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml
from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent


def load_config():
    with open(ROOT / "configs" / "llm.yaml") as f:
        return yaml.safe_load(f)


def load_judge_prompt():
    with open(ROOT / "prompts" / "judges" / "leakage_salience.md") as f:
        return f.read()


def load_seed_set(seed_file: str = None):
    seeds = []
    seed_path = Path(seed_file) if seed_file else ROOT / "data" / "seeds" / "questions_gold.jsonl"
    with open(seed_path) as f:
        for line in f:
            if line.strip():
                seeds.append(json.loads(line))
    return seeds


def render_prompt(template: str, question: str) -> str:
    return template.replace("{{question}}", question)


def parse_json_response(text: str) -> dict | None:
    """Extract JSON from response, handling markdown code blocks."""
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

    # Try finding any JSON object
    match = re.search(r"\{[^{}]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def run_judge(client: OpenAI, model_id: str, decoding_params: dict, prompt: str) -> dict:
    response = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": prompt}],
        temperature=decoding_params.get("temperature", 0.2),
        top_p=decoding_params.get("top_p", 0.9),
        max_tokens=decoding_params.get("max_tokens", 512),
    )
    raw = response.choices[0].message.content
    parsed = parse_json_response(raw)
    return {"raw": raw, "parsed": parsed}


def main():
    parser = argparse.ArgumentParser(description="Run judge calibration on seed set")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OPENAI_BASE_URL", "http://localhost:8000/v1"),
        help="OpenAI-compatible API base URL",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("OPENAI_API_KEY", "not-needed"),
        help="API key (use 'not-needed' for local vLLM)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of seeds to process (for quick testing)",
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "data" / "runs" / "phase0_calibration" / "judge_results.jsonl"),
        help="Output file path",
    )
    parser.add_argument(
        "--seed-file",
        default=None,
        help="Path to seed file (default: data/seeds/questions_gold.jsonl)",
    )
    args = parser.parse_args()

    config = load_config()
    judge_template = load_judge_prompt()
    seeds = load_seed_set(args.seed_file)

    if args.limit:
        seeds = seeds[: args.limit]

    client = OpenAI(base_url=args.base_url, api_key=args.api_key)
    model_id = config["judge"]["model_id"]
    decoding_params = config["judge"]["decoding_params"]

    print(f"Running judge on {len(seeds)} seeds using {model_id}")
    print(f"Base URL: {args.base_url}")
    print()

    results = []
    correct = {"leakage": 0, "salience": 0}
    total = 0

    for i, seed in enumerate(seeds):
        prompt = render_prompt(judge_template, seed["question"])
        try:
            response = run_judge(client, model_id, decoding_params, prompt)
        except Exception as e:
            print(f"[{i+1}/{len(seeds)}] ERROR: {seed['id']} - {e}")
            results.append({"seed_id": seed["id"], "error": str(e)})
            continue

        parsed = response["parsed"]
        if parsed:
            pred_leak = parsed.get("leakage_score")
            pred_sal = parsed.get("salience_score")
            gold_leak = seed["leakage_score"]
            gold_sal = seed["salience_score"]

            leak_match = pred_leak == gold_leak
            sal_match = pred_sal == gold_sal

            if leak_match:
                correct["leakage"] += 1
            if sal_match:
                correct["salience"] += 1
            total += 1

            status = "OK" if (leak_match and sal_match) else "MISMATCH"
            print(
                f"[{i+1}/{len(seeds)}] {status}: {seed['id']} | "
                f"leak={pred_leak}(gold={gold_leak}) sal={pred_sal}(gold={gold_sal})"
            )

            results.append({
                "seed_id": seed["id"],
                "question": seed["question"],
                "gold_leakage": gold_leak,
                "gold_salience": gold_sal,
                "pred_leakage": pred_leak,
                "pred_salience": pred_sal,
                "rationale": parsed.get("rationale"),
                "leakage_match": leak_match,
                "salience_match": sal_match,
            })
        else:
            print(f"[{i+1}/{len(seeds)}] PARSE_FAIL: {seed['id']} - {response['raw'][:100]}")
            results.append({
                "seed_id": seed["id"],
                "question": seed["question"],
                "parse_error": True,
                "raw_response": response["raw"],
            })

    # Summary
    print()
    print("=" * 60)
    print("CALIBRATION SUMMARY")
    print("=" * 60)
    if total > 0:
        print(f"Leakage accuracy:  {correct['leakage']}/{total} ({100*correct['leakage']/total:.1f}%)")
        print(f"Salience accuracy: {correct['salience']}/{total} ({100*correct['salience']/total:.1f}%)")
    else:
        print("No successful evaluations.")

    # Write results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"\nResults written to: {output_path}")


if __name__ == "__main__":
    main()
