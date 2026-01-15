## Phase 1 — Low-level implementation plan (MVP prompt pool generation)

### Objective

Produce the first scalable `questions.jsonl` where prompts are **region-neutral (leakage=0)** but have **non-trivial regional salience (salience≥1)**, with strong deduplication and reproducible runs.

Derived from `notes/phases/phase1.md` + `notes/research.md` (Self-Instruct, Evol-Instruct patterns).

---

## Inputs

- Phase 0 configs:
  - `configs/domains.yaml`
  - `configs/question_types.yaml`
  - `configs/llm.yaml` (Qwen2.5/Qwen3 up to 72B)
  - `prompts/judges/leakage_salience.md`
  - `data/seeds/questions_gold.jsonl` (gold + negatives)

---

## Outputs (artifacts; keep restartable)

Planned run folder: `data/runs/<run_id>/`

- `questions_raw.jsonl` (direct model output; may be noisy)
- `questions_filtered.jsonl` (after hard filters + basic cleaning)
- `questions_deduped.jsonl` (after novelty/dedup)
- `questions_scored.jsonl` (after leakage/salience judge)
- `questions_accepted.jsonl` (final gate: leakage=0 and salience≥1)
- `run_manifest.json` (config + model ids + prompt template versions + counts)

Optionally, copy/promote:

- `data/questions.jsonl` → latest accepted prompt pool

---

## Model usage (72B Qwen)

- **Generation**: `Qwen2.5-72B-Instruct` (or Qwen3-72B) with moderate diversity settings.
- **Scoring/Judging**: same model to reduce inconsistencies between generation and evaluation.

Efficiency:

- Judge only **after** cheap filters/dedup.
- Cache judge calls; most cost comes from scoring.

---

## Planned scripts (no code yet; this is the implementation blueprint)

- `scripts/phase1_generate_questions.py`
- `scripts/phase1_filter_questions.py`
- `scripts/phase1_dedup_questions.py`
- `scripts/phase1_score_questions.py`
- `scripts/phase1_report.py` (counts + distributions + sampled examples)

Each script should:

- read JSONL → write JSONL
- be deterministic given inputs + run_id
- never mutate earlier artifacts (append-only workflow)

---

## Step-by-step implementation plan

### Step 1.1 — Define generation templates (per question_type)

Create prompt templates like:

- `prompts/generation/question_gen_explanatory.md`
- `prompts/generation/question_gen_comparative.md`
- …

Template requirements:

- explicit “no region cues” rules + bad examples (from Phase 0 negatives)
- explicit “maximize regional salience without leakage” instruction
- strict JSON output (list of objects with `question`, `domain`, `question_type`)

Why: avoids diversity collapse and leakage (matches `notes/research.md` lessons from Self-Instruct and general dataset curation).

### Step 1.2 — Run coverage-first generation

For each `(domain × question_type)` bucket:

- generate a small batch first (10–30 prompts) to expose failure modes early
- only scale to larger N after filters are tuned

Why: reduces wasted generation tokens on buckets that systematically leak.

### Step 1.3 — Hard filters (fast failure)

Implement cheap checks before any LLM judging:

- **Leakage blocklist** (explicit terms: countries/cities, institutions, currencies, programs, acronyms)
- **PII heuristics** (emails, phone-like strings, addresses)
- **Shape checks**:
  - is it a question?
  - length bounds
  - language (English-first unless explicitly expanding)

Output: `questions_filtered.jsonl` + filter reasons.

Reference: prompt filtering and dedup principles used in InstructGPT-style pipelines (summarized in `notes/research.md`).

### Step 1.4 — Novelty + dedup (prevent saturation)

Two-stage approach (optimize for speed):

1) **ROUGE-L novelty gate** (cheap)
   - Reject candidate if ROUGE-L similarity ≥ **0.7** with any accepted prompt so far.
   - Reference: Self-Instruct novelty threshold ~0.7 (see `notes/research.md`).

2) **Optional semantic dedup** (only if needed)
   - If ROUGE-L leaves too many paraphrases, add embedding-based clustering within buckets.
   - Keep it optional to avoid new dependencies early.

Output: `questions_deduped.jsonl` + novelty scores.

### Step 1.5 — Leakage + salience scoring (LLM-as-judge)

Run `prompts/judges/leakage_salience.md` to score each prompt:

- `leakage_score` in {0,1,2}
- `salience_score` in {0,1,2}
- short rationale (for audits)

Gate:

- Accept if `leakage_score == 0` AND `salience_score >= 1`
- Quarantine borderline prompts (`leakage=1`) into a review bucket to improve filters

Output: `questions_scored.jsonl` and `questions_accepted.jsonl`.

### Step 1.6 — Calibration + audit loop (small, routine)

Every run:

- Sample ~100 accepted + ~50 rejected
- Check:
  - leakage false positives/negatives
  - salience false positives (prompts that don’t actually diverge)
  - duplication slip-through
- Update:
  - blocklists
  - generator prompts (bad examples)
  - judge rubric wording

Why: prevents silently drifting into “looks neutral but isn’t.”

---

## Minimal experiments (to validate Phase 1)

- **Filter ablation**: remove each filter stage and observe leakage rate change.
- **Distribution report**: counts by domain/type/source; dedup rejection rate.
- **Salience proxy check** (small): sample ~50 prompts and generate SG-vs-US answers using Phase 0 policies; compute a simple divergence indicator (manual or judge-scored).

---

## Definition of done

- `data/runs/<run_id>/questions_accepted.jsonl` exists with:
  - coverage across 10–15 domains × 5–7 types
  - 500–2,000 accepted prompts (enough for Phase 2)
- Audited quality:
  - ≤ 5% leakage in accepted sample
  - salience≥1 on ≥ 50% of accepted sample (track and iterate)
- Reproducibility:
  - `run_manifest.json` captures model ids, decoding params, prompt template versions, and counts
  - generation + filtering + scoring can be rerun to reproduce identical outputs (given cached LLM calls)

