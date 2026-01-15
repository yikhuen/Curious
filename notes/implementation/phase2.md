## Phase 2 — Low-level implementation plan (responses + pair selection)

### Objective

Turn `questions.jsonl` into a **preference-ready pair candidate set** (`pairs.jsonl`) by:

1) generating multiple responses per prompt under different “region policies”, and  
2) selecting informative pairs (cross-policy disagreement + best-vs-worst).

Derived from `notes/phases/phase2.md` + preference-data patterns in `notes/research.md` (InstructGPT multi-completion, UltraFeedback, OpenRLHF best-of-n).

---

## Inputs

- `data/questions.jsonl` (or `data/runs/<run_id>/questions_accepted.jsonl`)
- `configs/policies.yaml` (at least `policy_sg`, `policy_us`)
- `configs/llm.yaml` (Qwen2.5/Qwen3 up to 72B)
- `prompts/judges/response_helpfulness.md`
- `prompts/judges/region_alignment.md`

---

## Outputs

Planned run folder: `data/runs/<run_id>/`

- `responses.jsonl` (all generated responses, *not* yet paired)
- `pairs_candidates.jsonl` (paired responses + provenance; may be unlabeled or AI-judged)
- `pairs.jsonl` (export in TRL-compatible schema: `prompt`, `chosen`, `rejected`, `pair_meta`)
- `run_manifest.json` (N, decoding params, policy prompts, counts, rejection reasons)

---

## Model usage (72B Qwen)

- **Answer generation**: Qwen2.5-72B-Instruct (or Qwen3-72B) with region policy system prompts.
- **Pair scoring/judging** (optional but recommended for selection):
  - Qwen 72B as a judge for helpfulness scoring and region-alignment scoring.

Efficiency:

- Generate **N responses per prompt per policy** only for a subset until the pipeline is stable.
- Cache generations and judge calls.

---

## Planned scripts (no code yet; this is the blueprint)

- `scripts/phase2_generate_responses.py`
- `scripts/phase2_score_responses.py` (optional; for best-vs-worst within-policy)
- `scripts/phase2_select_pairs.py`
- `scripts/phase2_report.py` (divergence rates, pair distributions, samples)

---

## Step-by-step implementation plan

### Step 2.1 — Define region policies as *system prompts* (no explicit “I’m from X”)

Policy design rule:

- answers should be culturally/regionally grounded **without stating the region name**
  - (we want content divergence, not location disclaimers)

Store the policy prompts verbatim in `configs/policies.yaml` and copy into `run_manifest.json` for reproducibility.

### Step 2.2 — Generate responses (multi-completion)

For each prompt:

- Generate at least 1 response for:
  - `policy_sg`
  - `policy_us`
- Preferably generate N samples (e.g., N=4) per policy for “best-vs-worst” selection.

Reference: InstructGPT collected multiple completions per prompt for ranking; multi-completion yields better preference signal than random single pairs (`notes/research.md`).

Output schema for `responses.jsonl` (planned):

- `prompt_id`
- `prompt`
- `policy_id`
- `response_id`
- `response`
- `decoding` (temperature/top_p/max_tokens)
- `model_id`
- `timestamp`

### Step 2.3 — Cross-policy pairing (coverage-first)

Create a base pair candidate per prompt:

- SG response vs US response (same prompt)

Store as:

- `pair_type = "cross_policy"`
- `pair_meta.policy_a = "policy_sg"`, `pair_meta.policy_b = "policy_us"`

Purpose:

- directly tests whether prompts actually elicit regional differences (salience validation)
- provides candidates for later “region alignment” labeling

### Step 2.4 — Within-policy best-vs-worst pairing (clarity-first)

If N>1 responses per policy:

- Score each response for **helpfulness** using a judge prompt (pairwise or scalar).
- Select:
  - `best` response
  - `worst` response
  - create a pair candidate `(best, worst)` for that policy

Reference: UltraFeedback-style “multi-response + judge → preference pairs” is a known scaling path (but judge bias must be calibrated later; `notes/research.md`).

Store as:

- `pair_type = "best_vs_worst"`
- `label_source = "ai_judge"` (explicit provenance)

### Step 2.5 — Divergence proxy + prioritization (to spend labels efficiently)

To select which cross-policy pairs are worth human labeling later, compute a cheap proxy:

- Option A (no extra deps): LLM judge “divergence score” on the two responses (0–2) and keep pairs with score≥1.
- Option B (optional): embedding similarity threshold if you later add an embedding model.

Keep the system lean by starting with Option A; only add embeddings if the judge is too slow or inconsistent.

### Step 2.6 — Export to TRL-compatible `pairs.jsonl`

Follow the standard preference schema (explicit prompt):

- `prompt`
- `chosen`
- `rejected`
- `pair_meta` including:
  - `pair_type` (`cross_policy` / `best_vs_worst`)
  - `label_source` (`unlabeled_candidate` / `ai_judge` / later `human`)
  - `axis` (`helpfulness` / `region_alignment`)
  - model/policy/decoding ids

Reference: TRL dataset format best practices  
`https://huggingface.co/docs/trl/main/dataset_formats`

### Step 2.7 — Pair clarity audit (small, required)

Sample ~100 pairs across domains/types:

- reject pairs where “chosen” is only better because it is longer (verbosity bias)
- check that cross-policy pairs are meaningfully different
- check that within-policy pairs are clearly rankable

Update:

- N (samples per prompt)
- decoding params
- judge rubric wording
- pair selection thresholds

---

## Minimal experiments (to validate Phase 2)

- **Divergence rate**: % of prompts where SG vs US answers differ meaningfully.
- **Pair clarity (manual)**: % of sampled pairs where the intended preference axis yields a confident decision.
- **Coverage**: ensure selected pairs are not dominated by a few domains/types.

---

## Definition of done

- `data/runs/<run_id>/pairs.jsonl` exists with:
  - 500–2,000 pair candidates
  - mixed `pair_type` coverage (`cross_policy`, optionally `best_vs_worst`)
  - explicit provenance (`label_source`, policies, model ids, decoding params)
- A short report exists (can be `phase2_report` output) summarizing:
  - divergence rate
  - pair distributions by domain/type
  - audit outcomes + resulting parameter changes

