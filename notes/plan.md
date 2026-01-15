## Question → pairwise responses pipeline (region-neutral prompts with regional salience)

### Goal

Generate a **region-neutral** prompt set that tends to elicit **regionally different** answers when answered by models tuned on different cultural contexts (SG, US, JP, …), and package the resulting responses into a **preference-ready pairwise dataset**.

### Core constraint (make explicit)

- **Low regional leakage**: prompts must not name specific countries/cities, region-specific institutions, currencies, benefits programs, etc.
- **High regional salience**: prompts should still invite region-dependent choices/norms (e.g., transit habits, etiquette, schooling, housing, healthcare decision-making).

Think of this as optimizing for **salience without leakage**.

### Quick review of the previous plan (strengths + gaps)

- **Strengths**
  - Clear goal/constraint and a sensible generate→filter→validate loop.
  - Explicit diversity axes (domain + question type) and staged filtering.
  - Traceability mindset (metadata in outputs).
- **Weak points we address in this revision**
  - The plan stops right before the key deliverable: **pairwise responses + preference labels**.
  - “Neutrality” is treated as one check; in practice we need two distinct scores: **leakage** vs **salience**.
  - Validation metrics were a bit over-specified early; we want a minimal set that drives iteration.
  - No explicit strategy for scaling without saturation (near-duplicates / drift).

For supporting references and reusable external assets, see `research.md`.

---

## Data products (stable artifacts)

Keeping artifacts stable prevents overengineering and makes every step restartable.

### `questions.jsonl` (prompt pool)

Minimal required fields:

- `id`
- `question` (string)
- `domain` (string)
- `question_type` (string)
- `source` (e.g., `seed`, `llm_generate`, `llm_evolve`, `external_seed`)
- `leakage_score` (0–2) and `salience_score` (0–2)
- `filters` (booleans + notes)
- `provenance` (generator model, run id, timestamp)

### `pairs.jsonl` (preference-ready pairwise responses)

Follow the common TRL/HH-style convention so we can reuse existing tooling:

- `prompt` (the question, optionally with prior turns if multi-turn later)
- `chosen` (assistant response A)
- `rejected` (assistant response B)
- `pair_meta` (model ids, sampling params, annotator/judge source, label type)
- Optional: separate axis labels (e.g., `helpfulness_preference`, `cultural_alignment_preference`, `overall_preference`)

---

## Lean pipeline (end-to-end)

### Step 0: Define scope + budgets (coverage without bloat)

- **Domains**: start with ~10–15 “high salience” domains, expand later.
- **Question types**: keep 5–7 types (explanatory, comparative, advisory, procedural, hypothetical, reflective, trade-off).
- **Budgets**: set target counts per (domain × type), and a “hard set” budget (see Step 6).

### Step 1: Build a seed prompt pool (don’t start from zero)

Use multiple sources, but keep them separable via `source`:

- **Manual seeds**: small curated set that exemplifies “salience without leakage.”
- **External seeds (optional)**: existing prompt corpora as raw material (filter aggressively).
- **Synthetic expansion**:
  - **Generate**: produce new questions conditioned on (domain, type) with contrastive good/bad examples.
  - **Evolve**: mutate accepted questions with bounded operators (add constraint, deepen trade-off, multi-turn conversion) while preserving neutrality constraints.

### Step 2: Cheap hard filters (fast failure)

Run cheap checks first:

- **Explicit leakage**: blocklists + named-entity heuristics for regions, institutions, currencies, benefits programs, etc.
- **PII / personal data**: remove anything that looks like it.
- **Shape**: length bounds, “is a question”, language, no obvious prompt injection artifacts.

### Step 3: Deduplicate + enforce diversity (prevent saturation)

- Embedding-based near-duplicate removal within (domain × type) buckets.
- Quotas/balancing so one domain/type can’t dominate.
- Track novelty scores so scaling doesn’t just add paraphrases.

### Step 4: Audit for “leakage” vs “salience” (separate signals)

Use an LLM-as-judge (or rules + judge) to assign two independent scores:

- **Leakage score (0–2)**: 0 = no region cues, 1 = borderline/implicit, 2 = explicit.
- **Salience score (0–2)**: 0 = likely universal answers, 1 = sometimes region-dependent, 2 = strongly region-dependent without naming regions.

Gatekeeper rule (initially): keep prompts with **leakage ≤ 0** and **salience ≥ 1**.

### Step 5: Sample-based human audit (calibration, not full labeling)

Every batch (e.g., each 500 prompts):

- Spot-check a random sample for leakage/salience/naturalness.
- Use findings to update: blocklists, judge rubric, and generation prompts.

### Step 6: Generate candidate responses (for pairwise comparisons)

For each accepted prompt:

- Generate responses from two “policies” (e.g., SG-tuned vs US-tuned), and/or multiple samples per policy.
- Prefer **multi-completion** so you can form informative pairs (best-vs-worst, or cross-policy disagreements).

### Step 7: Choose which pairs to label (maximize signal per label)

Pair selection heuristics (start simple):

- **Cross-policy disagreement**: pairs where SG vs US answers differ in salient entities/assumptions.
- **Best-vs-worst** within a policy: use a judge score to pick extremes for clearer preferences.
- Maintain coverage quotas so labels aren’t all from one domain.

### Step 8: Collect preferences (human-first, AI-assisted)

Lean recommendation:

- **Human labels** on a small, high-value slice to anchor the project.
- **AI judge triage** for scale (use as proposal labels, calibrated against human).
- Store everything in `pairs.jsonl` with explicit label provenance.

---

## Minimal metrics that actually drive iteration

- **Leakage pass rate**: how many generated prompts survive hard filters + audit.
- **Novelty/dup rate**: how much of the batch is new vs near-duplicate.
- **Coverage**: fraction of (domain × type) buckets filled.
- **Divergence rate**: % of prompts where region policies diverge meaningfully (proxy: embedding distance or detected entity differences).
- **Label agreement** (when humans label): inter-annotator agreement on the slice.

---

## Extensibility (avoid “question exhaustion”)

Prioritize extensions that preserve the same artifacts (`questions.jsonl`, `pairs.jsonl`):

- **Multi-turn prompts**: store prompt as message history; keep chosen/rejected as the final assistant turn.
- **New axes**: add `difficulty`, `format`, `safety_sensitivity`, `language` without changing the core loop.
- **Hard-set loop**: keep a dedicated “regional divergence hard set” that evolves as you scale.

Roadmap and phased definitions of done are in `roadmap.md`.
