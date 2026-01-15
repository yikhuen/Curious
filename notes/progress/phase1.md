## Phase 1 — Progress checklist (MVP prompt pool generation)

### Status

- [ ] Not started
- [x] In progress
- [ ] Blocked
- [ ] Done

---

## Checklist

### Setup

- [x] Confirm Phase 0 artifacts exist (configs + judge prompts + seed set)
- [x] Decide generator model: Qwen2.5-72B-Instruct vs Qwen3-72B-Instruct (document in `configs/llm.yaml`)
- [x] Decide run_id format + output locations (`data/runs/<run_id>/...`)

### Generation templates

- [x] Create `prompts/generation/question_gen_<type>.md` for each question_type
- [x] Include contrastive examples (good vs leaky) drawn from seed negatives
- [x] Require strict JSON output (parseable)

### Generation run (coverage-first)

- [x] Generate initial small batch per (domain×type) (10–30 prompts) — script ready: `phase1_generate_questions.py`
- [x] Save `questions_raw.jsonl` + generator provenance
- [ ] Review top failure modes (leakage patterns, repetitive prompts)

### Hard filters

- [x] Implement explicit leakage blocklist filtering
- [x] Implement shape checks (is-question, length bounds, language)
- [x] Implement PII heuristics
- [x] Save `questions_filtered.jsonl` + filter reasons — script ready: `phase1_filter_questions.py`

### Dedup / novelty

- [x] Implement ROUGE-L novelty gate (Self-Instruct-style threshold ≈0.7) — script ready: `phase1_dedup_questions.py`
- [x] Save `questions_deduped.jsonl` + novelty scores
- [ ] Decide if semantic dedup is needed (only add if ROUGE-L insufficient)

### Judge scoring (leakage + salience)

- [x] Run judge to add leakage_score + salience_score + rationale — script ready: `phase1_score_questions.py`
- [x] Gate: accept leakage=0 and salience≥1
- [x] Save `questions_scored.jsonl` and `questions_accepted.jsonl`

### Audit loop (small but required)

- [ ] Sample ~100 accepted + ~50 rejected prompts
- [ ] Verify leakage false positives/negatives
- [ ] Verify salience false positives (prompts that don’t actually diverge)
- [ ] Update blocklists and/or templates based on findings

### Reporting / reproducibility

- [x] Write `run_manifest.json` (models, decoding params, template versions, counts)
- [x] Produce a simple distribution report (domain×type counts, acceptance rates) — script ready: `phase1_report.py`
- [ ] Promote latest accepted set to `data/questions.jsonl` (or document the canonical path)

---

## Definition of done (Phase 1)

- [ ] `questions_accepted.jsonl` exists with 500–2,000 prompts
- [ ] Coverage achieved across 10–15 domains × 5–7 types
- [ ] Audit shows ≤5% leakage in accepted sample
- [ ] Audit shows ≥50% salience≥1 in accepted sample (tracked and improving)
- [ ] Run is reproducible (manifest + cached calls; rerun produces same artifacts)

