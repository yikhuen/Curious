#!/usr/bin/env python3
"""
Phase 1: Generate questions using LLM.

Usage:
    python scripts/phase1_generate_questions.py --base-url http://localhost:8000/v1 --run-id run_001
    python scripts/phase1_generate_questions.py --base-url http://localhost:8000/v1 --run-id run_001 --domain transport_commuting --type explanatory

Requires:
    pip install openai pyyaml
"""

import argparse
import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path

import yaml
from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent


def load_yaml_config(name: str) -> dict:
    with open(ROOT / "configs" / name) as f:
        return yaml.safe_load(f)


def load_generation_template(question_type: str) -> str:
    path = ROOT / "prompts" / "generation" / f"question_gen_{question_type}.md"
    with open(path) as f:
        return f.read()


def get_profile(config: dict, profile_name: str = None) -> dict:
    if profile_name is None:
        profile_name = config.get("default_profile", "qwen32b")
    profiles = config.get("profiles", {})
    if profile_name not in profiles:
        raise ValueError(f"Profile '{profile_name}' not found. Available: {list(profiles.keys())}")
    return profiles[profile_name]


def render_template(template: str, domain: dict, question_type: dict, num_questions: int) -> str:
    return (
        template
        .replace("{{domain_id}}", domain["id"])
        .replace("{{domain_name}}", domain["name"])
        .replace("{{domain_description}}", domain["description"])
        .replace("{{question_type}}", question_type["id"])
        .replace("{{num_questions}}", str(num_questions))
    )


def parse_json_response(text: str) -> list | None:
    """Extract JSON array from response."""
    # Try direct parse
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Try extracting from code block
    match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding any JSON array
    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def generate_questions(
    client: OpenAI,
    model_id: str,
    decoding_params: dict,
    prompt: str,
) -> tuple[list, str]:
    """Generate questions and return (parsed_list, raw_response)."""
    response = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": prompt}],
        temperature=decoding_params.get("temperature", 0.7),
        top_p=decoding_params.get("top_p", 0.9),
        max_tokens=decoding_params.get("max_tokens", 2048),
    )
    raw = response.choices[0].message.content
    parsed = parse_json_response(raw)
    return parsed or [], raw


def generate_id() -> str:
    return f"gen-{uuid.uuid4().hex[:12]}"


def main():
    parser = argparse.ArgumentParser(description="Generate questions for Phase 1")
    parser.add_argument("--run-id", required=True, help="Run identifier (e.g., run_001)")
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
    parser.add_argument("--domain", default=None, help="Specific domain to generate (default: all)")
    parser.add_argument("--type", default=None, help="Specific question type (default: all)")
    parser.add_argument("--num", type=int, default=None, help="Override number of questions per bucket")
    parser.add_argument("--append", action="store_true", help="Append to existing output file")
    args = parser.parse_args()

    # Load configs
    llm_config = load_yaml_config("llm.yaml")
    domains_config = load_yaml_config("domains.yaml")
    types_config = load_yaml_config("question_types.yaml")

    profile = get_profile(llm_config, args.profile)
    model_id = profile["model_id"]
    decoding_params = profile.get("generator", {})
    profile_name = args.profile or llm_config.get("default_profile", "qwen32b")

    # Build domain and type lists
    domains = domains_config["domains"]
    question_types = types_config["question_types"]
    budgets = types_config.get("budgets", {})
    default_budget = budgets.get("default_per_domain_type", 30)
    type_overrides = budgets.get("per_type_overrides", {})

    if args.domain:
        domains = [d for d in domains if d["id"] == args.domain]
        if not domains:
            print(f"Domain '{args.domain}' not found")
            return

    if args.type:
        question_types = [t for t in question_types if t["id"] == args.type]
        if not question_types:
            print(f"Question type '{args.type}' not found")
            return

    # Prepare output
    run_dir = ROOT / "data" / "runs" / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    output_path = run_dir / "questions_raw.jsonl"

    mode = "a" if args.append else "w"
    client = OpenAI(base_url=args.base_url, api_key=args.api_key)

    print(f"Phase 1 Generation")
    print(f"==================")
    print(f"Run ID: {args.run_id}")
    print(f"Profile: {profile_name} ({profile.get('name', model_id)})")
    print(f"Model: {model_id}")
    print(f"Domains: {len(domains)}")
    print(f"Question types: {len(question_types)}")
    print(f"Output: {output_path}")
    print()

    total_generated = 0
    total_buckets = len(domains) * len(question_types)
    bucket_idx = 0

    with open(output_path, mode) as f:
        for domain in domains:
            for qtype in question_types:
                bucket_idx += 1
                num_questions = args.num or type_overrides.get(qtype["id"], default_budget)

                # Load and render template
                template = load_generation_template(qtype["id"])
                prompt = render_template(template, domain, qtype, num_questions)

                print(f"[{bucket_idx}/{total_buckets}] {domain['id']} × {qtype['id']} (n={num_questions})...", end=" ", flush=True)

                try:
                    questions, raw = generate_questions(client, model_id, decoding_params, prompt)
                except Exception as e:
                    print(f"ERROR: {e}")
                    continue

                if not questions:
                    print(f"PARSE_FAIL (raw: {raw[:100]}...)")
                    continue

                # Write records
                timestamp = datetime.utcnow().isoformat() + "Z"
                for q in questions:
                    record = {
                        "id": generate_id(),
                        "question": q.get("question", ""),
                        "domain": q.get("domain", domain["id"]),
                        "question_type": q.get("question_type", qtype["id"]),
                        "source": "llm_generate",
                        "leakage_score": None,
                        "salience_score": None,
                        "filters": {},
                        "provenance": {
                            "model_id": model_id,
                            "profile": profile_name,
                            "prompt_template_version": llm_config.get("prompt_template_version", "v1"),
                            "timestamp": timestamp,
                            "run_id": args.run_id,
                        },
                    }
                    f.write(json.dumps(record) + "\n")

                total_generated += len(questions)
                print(f"OK ({len(questions)} questions)")

    print()
    print(f"Total generated: {total_generated}")
    print(f"Output: {output_path}")

    # Write manifest
    manifest = {
        "run_id": args.run_id,
        "phase": 1,
        "step": "generate",
        "model_id": model_id,
        "profile": profile_name,
        "prompt_template_version": llm_config.get("prompt_template_version", "v1"),
        "decoding_params": decoding_params,
        "domains": [d["id"] for d in domains],
        "question_types": [t["id"] for t in question_types],
        "budgets": {
            "default": default_budget,
            "overrides": type_overrides,
        },
        "total_generated": total_generated,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    manifest_path = run_dir / "run_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
