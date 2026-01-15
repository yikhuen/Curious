## Roadmap: prompt curation → pairwise responses → preference data

This roadmap is organized to keep the repo **lean and failure-resistant**: every phase produces a concrete artifact and an evaluation signal, and avoids building heavy infra before it’s needed.

---

## Phase 0 — Clarify objectives and label rubrics (1–3 days)

### Requirements

- Define the two core prompt properties as explicit rubrics:
  - **Regional leakage** (prompt contains region hints) — must be minimized.
  - **Regional salience** (prompt invites region-dependent answers) — must be maximized.
- Define what “pairwise preference” means for this project:
  - helpfulness preference (general quality)
  - cultural/region alignment preference (does the answer match the intended regional norm/style?)
  - optional overall trade-off preference
- Decide the initial target regions/models (e.g., SG vs US) and what “region-tuned” means operationally (fine-tune vs system-prompt conditioning).

### Experiments

- Manually write ~30–50 seed prompts, then score them with the rubric; refine rubric until it’s stable.
- Run 2–3 different LLM prompt templates for question generation on 1–2 domains; compare leakage/salience distributions.

### Definition of done

- A written rubric with examples (pass/fail/borderline) for leakage + salience.
- A small “gold seed set” of prompts (`questions_seed.jsonl` or equivalent, even if stored temporarily) tagged with leakage/salience.

---

## Phase 1 — MVP prompt pool generation (region-neutral, region-salient) (3–7 days)

### Requirements

- Produce a first version of `questions.jsonl` with:
  - domain + question_type metadata
  - source tracking (seed vs generate vs evolve)
  - leakage/salience scoring (even if AI-judged initially)
- Implement a minimum viable filtering stack conceptually:
  - explicit leakage (blocklist / NER heuristic)
  - shape constraints (length, is-question)
  - dedup (near-duplicate suppression)

### Experiments

- **Ablation**: measure how many prompts survive when you remove each filter (to detect brittle filters).
- **Distribution sanity**: verify coverage across domains/types and check for collapse (e.g., too many advisory prompts).
- **Human audit**: spot-check a random sample (e.g., 100 prompts) for leakage/salience/naturalness.

### Definition of done

- `questions.jsonl` with at least:
  - 10–15 domains × 5–7 types populated
  - leakage rate below an agreed threshold (e.g., ≤5% in audited sample)
  - a measurable salience rate (e.g., ≥50% salience≥1 in audited sample)

---

## Phase 2 — Pairwise response generation + pair selection (3–7 days)

### Requirements

- For each prompt, generate:
  - at least one response per target region/policy (SG vs US baseline)
  - optionally multiple samples per policy (to enable best-vs-worst pairs)
- Define a **pair selection** method that is stable and cheap:
  - cross-policy disagreement (SG vs US)
  - best-vs-worst within a policy using a judge score
- Create the first `pairs.jsonl` in a standard preference format (`prompt`, `chosen`, `rejected`) with metadata.

### Experiments

- **Divergence proxy**: estimate how often SG vs US answers differ meaningfully (entity differences, embedding distance, or heuristic signals).
- **Pair clarity**: sample ~100 pairs and check if the “better” answer is obvious under your labeling criteria (if not, adjust sampling).

### Definition of done

- `pairs.jsonl` containing at least 500–2,000 candidate pairs covering multiple domains/types.
- A documented pair selection rule and its observed distribution (how many pairs came from each heuristic).

---

## Phase 3 — Preference labeling pilot (human + AI-judge triage) (1–2 weeks)

### Requirements

- Write labeling instructions (short, consistent, with examples) for:
  - helpfulness preference
  - cultural/region alignment preference
  - optional overall preference
- Decide the labeling stack:
  - **human-only** (small but high-quality), or
  - **AI-judge triage + human calibration** (scale with guardrails)
- Store labels with provenance (who/what labeled it, rubric version).

### Experiments

- **Inter-annotator agreement** on a shared slice (to detect rubric ambiguity).
- **AI-vs-human calibration**: compare AI judge labels to human labels on the same slice; measure disagreement and failure modes.
- **Bias audit**: check if labels correlate with superficial style (length/verbosity) rather than substance.

### Definition of done

- A human-labeled preference set (e.g., 1k–5k pairs) with measured agreement.
- A calibrated AI-judge setting (if used) with documented failure cases and a rule for when to defer to humans.

---

## Phase 4 — Scale prompt generation without saturation (ongoing)

### Requirements

- Add **prompt evolution operators** (bounded transformations) to expand the pool without drifting.
- Add **novelty budgeting** within buckets (domain × type × difficulty).
- Maintain a stable “hard set” of high-salience/low-leakage prompts for regression testing.

### Experiments

- **Saturation detection**: track novelty and dedup rates as total prompt count grows.
- **Hard-set win-rate trends**: ensure improvements show up on the hard set, not just easy prompts.
- **Domain expansion**: add new domains and confirm they don’t break neutrality checks.

### Definition of done

- Sustained growth in prompt count (e.g., 10k+) with stable novelty and leakage rates.
- A versioned hard set + metrics dashboard (even if just a simple report) used every iteration.

---

## Phase 5 — Training integration (optional, when data is ready)

### Requirements

- Choose the first optimization approach:
  - **DPO** (simpler pipeline, directly uses preference pairs), or
  - **Reward model + sampling** (more components, more failure modes)
- Define evaluation targets aligned to the project goal (regional alignment, not just generic helpfulness).

### Experiments

- **Baseline**: compare tuned policy vs base policy on the hard set and on a held-out prompt slice.
- **Over-optimization checks**: detect reward hacking / style bias.

### Definition of done

- A trained policy that measurably improves on:
  - cultural/region alignment preference rates
  - without increasing leakage or collapsing helpfulness

