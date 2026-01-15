## Phase 0 — Low-level implementation plan (rubrics, schemas, seed set)

### Objective

Lock down **what we are optimizing** (salience without leakage), **how we measure it** (rubrics), and **what artifacts we will produce** (schemas), so Phase 1 generation doesn’t create unusable data.

This plan is derived from `notes/plan.md`, `notes/research.md`, and `notes/roadmap.md`.

---

## Model choice (current constraint: up to 72B, prefer Qwen2.5/Qwen3)

### Default models

- **Generator**: `Qwen2.5-72B-Instruct`
- **Judge** (leakage/salience + response scoring): same as generator for consistency (72B reduces rubric drift)

### Efficiency guardrails

- Use an **OpenAI-compatible interface** in the eventual implementation (works with vLLM/TGI/hosted endpoints) to avoid writing provider-specific code.
- Cache all LLM calls by `(prompt_template_version, model_id, decoding_params, input_hash)` so reruns are cheap.

---

## Repo structure (lean, restartable artifacts)

We will keep the core pipeline restartable by writing append-only artifacts to disk (no DB).

Planned structure (to be created gradually in Phase 0/1):

- `configs/`
  - `domains.yaml`
  - `question_types.yaml`
  - `llm.yaml` (model ids + decoding params)
  - `policies.yaml` (region policy system prompts)
- `prompts/`
  - `judges/leakage_salience.md`
  - `judges/response_helpfulness.md`
  - `judges/region_alignment.md`
  - `generation/question_gen_<type>.md`
  - `generation/question_evolve_<operator>.md`
- `data/`
  - `seeds/` (hand-curated + negative examples)
  - `runs/<run_id>/...` (Phase 1+ artifacts)

---

## Schemas (define now to prevent rework)

### Prompt pool record (`questions.jsonl`)

Minimum fields (from `notes/plan.md`), finalized in Phase 0:

- `id` (recommend ULID/UUID)
- `question`
- `domain`
- `question_type`
- `source` (`seed`, `llm_generate`, `llm_evolve`, `external_seed`)
- `leakage_score` (0–2)
- `salience_score` (0–2)
- `filters` (object: booleans + notes)
- `provenance` (object: model id, prompt template version, timestamp, run_id)

### Pairwise preference record (`pairs.jsonl`)

Adopt TRL-preferred explicit prompt format:

- `prompt`
- `chosen`
- `rejected`
- `pair_meta` (policy ids, model ids, decoding params, label_source, axis)

Reference: TRL dataset format guidance (explicit `prompt`, `chosen/rejected` as completions)  
`https://huggingface.co/docs/trl/main/dataset_formats`

---

## Rubrics (prompt-level + response-level)

### 1) Prompt leakage rubric (0–2)

- **2 (explicit)**: names a country/city/region, region-specific institution/program/currency, or region-coded acronym (e.g., “NHS”, “MRT”, “401k”).
- **1 (borderline)**: heavy implicit cultural assumptions (e.g., tipping norms, specific holidays, season-coded chores) that break “works anywhere.”
- **0 (clean)**: no regional cues; reasonable in many contexts.

### 2) Prompt salience rubric (0–2)

- **2 (strong)**: likely to elicit region-dependent entities/norms *without* naming regions.
- **1 (moderate)**: sometimes region-dependent; answers may converge.
- **0 (weak)**: likely universal answers.

### 3) Preference axes (response-level; defined now, collected later)

Use separate axes to avoid conflation (pattern consistent with HH-RLHF / multi-axis datasets in `notes/research.md`):

- **Axis A — Helpfulness**: “Which response better answers the prompt?”
- **Axis B — Region alignment**: “Assume a rater from region X. Which response feels more natural/appropriate for region X?”
- **Optional Axis C — Overall trade-off**: if we later need a single combined label.

---

## Step-by-step tasks

### Step 0.1 — Finalize initial domains and question types

- Produce `configs/domains.yaml` with 10–15 high-salience domains (daily life + systems).
- Produce `configs/question_types.yaml` with 5–7 types (as in `notes/plan.md`).
- Add per-bucket budgets (how many prompts per domain×type for Phase 1).

### Step 0.2 — Define “region policies” for Phase 2 (system prompts)

Create `configs/policies.yaml` with at least two policies:

- `policy_sg`: answer naturally from SG context **without explicitly stating the region**
- `policy_us`: answer naturally from US context **without explicitly stating the region**

Rationale: we want content-level divergence, not “In Singapore…” disclaimers.

### Step 0.3 — Create judge prompts (leakage + salience + response scoring)

Write:

- `prompts/judges/leakage_salience.md` (scores 0–2 each + short rationale)
- `prompts/judges/response_helpfulness.md` (pairwise comparison rubric)
- `prompts/judges/region_alignment.md` (pairwise comparison rubric conditioned on a region label)

Design rule: keep outputs **machine-parseable JSON** to minimize downstream fragility.

### Step 0.4 — Build a “gold seed set” + negatives

Create `data/seeds/questions_gold.jsonl` with:

- 30–50 **gold** prompts (leakage=0, varying salience)
- 20–30 **negative** prompts (explicit leakage=2, borderline leakage=1, salience=0)

Purpose:

- calibrate judge prompts
- regression-test filters in Phase 1

### Step 0.5 — Calibration exercise (small, decisive)

Run the judge model on the seed set and record:

- confusion patterns (e.g., false “leakage=0” on subtle cues)
- rubric text refinements needed

Keep this small; don’t scale until rubrics are stable.

---

## Definition of done

- `configs/` contains initial **domains**, **question types**, and **two region policies**.
- `prompts/judges/` contains finalized, parseable judge templates for:
  - leakage+salience scoring
  - helpfulness comparison
  - region-alignment comparison
- `data/seeds/questions_gold.jsonl` exists with gold + negative examples, each labeled with leakage/salience.
- A short calibration note exists (can live in the Phase 0 PR/notes) documenting judge failure modes and rubric updates.

