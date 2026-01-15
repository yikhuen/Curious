## Phase 0 — Progress checklist (rubrics, schemas, seed set)

### Status

- [ ] Not started
- [ ] In progress
- [ ] Blocked
- [x] Done

---

## Checklist

### Objective + scope

- [x] Confirm objective statement: **salience without leakage** (matches `notes/plan.md`)
- [x] Freeze Phase 0 scope (rubrics + schemas + seed set only; no large-scale generation yet)

### Configs (minimal)

- [x] Create `configs/domains.yaml` (10–15 high-salience domains)
- [x] Create `configs/question_types.yaml` (5–7 question types)
- [x] Add per-bucket budgets for Phase 1 (counts per domain×type)
- [x] Create `configs/llm.yaml` specifying Qwen model ids (prefer Qwen2.5/Qwen3 up to 72B)

### Region policies (for Phase 2)

- [x] Create `configs/policies.yaml` with:
  - [x] `policy_sg` (SG-grounded, **no explicit “I’m from SG”**)
  - [x] `policy_us` (US-grounded, **no explicit “I’m from US”**)

### Judge prompts (machine-parseable)

- [x] Write `prompts/judges/leakage_salience.md` (outputs JSON with leakage_score + salience_score + rationale)
- [x] Write `prompts/judges/response_helpfulness.md` (pairwise helpfulness judgement; JSON output)
- [x] Write `prompts/judges/region_alignment.md` (pairwise region-alignment judgement; JSON output)

### Seed set (gold + negatives)

- [x] Create `data/seeds/questions_gold.jsonl`
- [x] Add 30–50 gold prompts (leakage=0, salience varied)
- [x] Add 20–30 negative prompts (leakage=2, leakage=1, salience=0 cases)
- [x] Label each seed prompt with leakage_score + salience_score

### Calibration note (quick but required)

- [x] Run leakage/salience judge on seed set (small batch)
- [x] Document failure modes + rubric tweaks (keep as a short note in Phase 0 work log)

---

## Definition of done (Phase 0)

- [x] Domains + question types + budgets defined
- [x] Region policies defined (SG/US, no explicit self-location)
- [x] Judge prompts written and parseable
- [x] Gold + negative seed set exists and is labeled
- [x] Calibration notes captured (what to fix before Phase 1)

