## Phase 1 — MVP prompt pool generation (3–7 days)

### Why this phase matters (1–2 lines)

This phase creates the first **scalable prompt pool** that is both **region-neutral** and **region-salient**, proving we can generate quantity *without* leaking region cues or collapsing into near-duplicates.

### Decisions (optimized for efficiency + aligned with objective)

- **Batch generation by (domain × question_type), not “generate 1000 diverse questions”**
  - **Why**: avoids diversity collapse; “explicit diversity axes” is the core lesson behind Self-Instruct-style loops.
  - **Reference**: Self-Instruct’s generate→filter loop and explicit task pool growth (`notes/research.md`).

- **Start with cheap novelty filtering (ROUGE-L) before heavier semantic clustering**
  - **Why**: lexical novelty checks are fast and reduce obvious duplicates early; we only pay for embeddings if needed.
  - **Reference**: Self-Instruct uses ROUGE-L novelty filtering with a threshold around **0.7** ([Self-Instruct](https://github.com/yizhongw/self-instruct), summarized in `notes/research.md`).

- **Introduce “evolution operators” early, but keep elimination rules strict**
  - **Why**: evolution is the cheapest way to create new, more complex prompts without drifting off-objective.
  - **Reference**: Evol-Instruct/WizardLM uses bounded operators + elimination rules to avoid meta-contamination and no-op evolutions (summarized in `notes/research.md`).

- **Two-step scoring: leakage gate first, then salience**
  - **Why**: leakage failures are hard failures; salience can be optimized gradually. This ordering maximizes throughput.

### Step-by-step plan

- **Step 1.1 — Define the “prompt pool schema” (minimal fields)**
  - Use the `questions.jsonl` schema from `notes/plan.md` (id, question, domain, question_type, source, leakage_score, salience_score, filters, provenance).
  - **Efficiency note**: stable artifacts prevent downstream rework (OpenAI InstructGPT treats prompts as a curated dataset; `notes/research.md`).

- **Step 1.2 — Build generation templates (with contrastive examples)**
  - One template per question_type, parameterized by domain.
  - Include:
    - explicit “no region cues” constraints + bad examples (leakage)
    - “salience” instruction (invite region-dependent choices without naming regions)
    - JSON output requirement (for parseability)
  - **Reference**: contrastive prompting is a practical way to reduce leakage (pattern seen across dataset generation pipelines; see `notes/research.md` case studies).

- **Step 1.3 — Generate the first batch (coverage-first)**
  - For each (domain × type) bucket, generate a small batch (e.g., 10–30 prompts) to fill coverage quickly.
  - Track generator settings in `provenance`.
  - **Why**: early coverage reveals which domains/types are “leakage-prone” without overspending tokens.

- **Step 1.4 — Apply hard filters (fast failure)**
  - **Leakage blocklist**: explicit region terms, institutions, currencies, benefits programs, region-coded acronyms.
  - **Shape checks**: length bounds, must be a question, language checks.
  - **PII guard**: drop anything that resembles personal data.
  - **Reference**: InstructGPT-style prompt filtering and dedup principles (`notes/research.md`).

- **Step 1.5 — Deduplicate and enforce novelty**
  - **Pass 1 (cheap)**: ROUGE-L novelty gate (reject if similarity ≥ 0.7 with an accepted prompt).
  - **Pass 2 (conditional)**: if audits show many paraphrases, add embedding-based dedup within buckets (domain × type).
  - **Why**: prevents “prompt saturation” early (ties to “question exhaustion” discussion in `notes/research.md`).

- **Step 1.6 — Score leakage + salience (judge rubric)**
  - Apply the Phase 0 rubric to assign:
    - leakage_score (0–2)
    - salience_score (0–2)
  - **Gate**: accept prompts where leakage=0 and salience≥1.
  - **Efficiency note**: keep borderline prompts but quarantine them into a “review” pool instead of discarding—useful for improving filters.

- **Step 1.7 — Human spot-check (calibration slice)**
  - Sample ~100 accepted prompts + ~50 rejected prompts.
  - Check:
    - false negatives (good prompts rejected)
    - false positives (leaky prompts accepted)
  - Use results to update blocklists and judge instructions.

### Experiments (minimal but decisive)

- **Filter ablation**: remove one filter at a time; measure leakage rate jump.
- **Prompt distribution report**: counts by domain/type/source; dedup rejection rate.
- **Salience reality check**: for a small subset, ask two different “region policies” to answer (system prompts) and see if answers differ meaningfully (early proxy before Phase 2).

### Definition of done

- **Prompt pool produced**: an initial `questions.jsonl` with:
  - coverage across 10–15 domains × 5–7 types
  - at least 500–2,000 accepted prompts (enough to feed Phase 2)
- **Quality thresholds hit (audited)**:
  - leakage ≤ 5% in the accepted audited sample
  - salience≥1 on ≥ 50% of accepted audited sample (tunable threshold, but must be tracked)
- **Reproducible knobs documented**:
  - generation templates used
  - filter rules (blocklists + novelty threshold)
  - scoring rubric version (from Phase 0)

