## Phase 2 — Pairwise response generation + pair selection (3–7 days)

### Why this phase matters (1–2 lines)

This phase converts “just prompts” into **preference-ready pair candidates** by generating multiple responses per prompt and selecting pairs that are most informative for later preference labeling.

### Decisions (optimized for efficiency + aligned with objective)

- **Use explicit `prompt` + `chosen/rejected` formatting (even for candidates)**
  - **Why**: keeps us compatible with common trainers and avoids reformatting later.
  - **Reference**: TRL recommends explicit `prompt` and not duplicating prompt text in `chosen/rejected` ([TRL dataset formats](https://huggingface.co/docs/trl/main/dataset_formats)).

- **Generate multiple completions per prompt (multi-completion)**
  - **Why**: enables “best-vs-worst” and strong-margin pairs; better signal per label than random pairs.
  - **Reference**: InstructGPT used multiple completions per prompt (ranked by humans) to train preference models (`notes/research.md`).

- **Best-of-N / rejection sampling as a selection primitive**
  - **Why**: cheap way to create clear preference contrasts without human labeling at full scale.
  - **Reference**: OpenRLHF exposes “best-of-n” generation and rejection-sampling style workflows ([OpenRLHF docs](https://openrlhf.readthedocs.io/en/latest/non_rl.html)).

- **Prefer cross-policy disagreement for “regional salience” evaluation**
  - **Why**: the objective is regional divergence from region-neutral prompts; pairs should highlight that divergence.

### Step-by-step plan

- **Step 2.1 — Define “region policies” for answer generation**
  - Start lean: one base model + two system prompts (“Answer as someone from Singapore…”, “Answer as someone from the US…”).
  - Record policy definitions as text (so runs are reproducible).
  - **Later extensibility**: swap policies to actual region-tuned models without changing data formats (see `notes/plan.md` stable artifacts).

- **Step 2.2 — Generate responses (N per prompt per policy)**
  - For each accepted prompt in `questions.jsonl`:
    - produce at least 1 response per policy
    - optionally produce N samples per policy (e.g., N=4) to enable best-vs-worst within-policy pairs
  - Store metadata needed for audits:
    - model id, temperature/top_p, max tokens, policy id, timestamp, prompt id
  - **Reference**: multi-completion is the default pattern in RLHF data collection (InstructGPT; `notes/research.md`).

- **Step 2.3 — Compute cheap “divergence proxies” (for pair selection)**
  - Examples of low-cost proxies:
    - named-entity/keyword differences between policies (local terms appearing)
    - embedding distance between responses (optional if embeddings available)
    - length/style mismatch flags (to avoid trivially preferring verbosity)
  - **Why**: prioritizes pairs likely to yield informative preference signal.

- **Step 2.4 — Build pair candidates (two complementary sources)**
  - **Cross-policy pairs**:
    - Pair SG-policy response vs US-policy response for the same prompt.
    - Primary purpose: maximize salience signal and prepare region-alignment preference tasks.
  - **Best-vs-worst pairs (within-policy)**:
    - For each policy, select the highest-scoring and lowest-scoring response under a judge rubric (helpfulness or coherence).
    - Primary purpose: create clear “chosen vs rejected” training pairs (strong margin).
  - **Reference**: UltraFeedback-style “multi-response + judge → preference pairs” is a known scaling path (`notes/research.md`), with the caveat that judge bias must be calibrated later.

- **Step 2.5 — Decide what “chosen vs rejected” means for Phase 2 outputs**
  - To stay honest about label provenance:
    - if chosen/rejected is determined by an AI judge → mark as `label_source=ai_judge`
    - if it is a placeholder for later human labeling → mark as `label_source=unlabeled_candidate`
  - **Efficiency note**: avoid inventing multiple schemas; add provenance fields instead.

- **Step 2.6 — Sample-based “pair clarity” audit**
  - Review ~100 pairs across domains/types:
    - are pairs non-trivial (not just “one is longer”)?
    - do cross-policy pairs actually differ in region-relevant ways?
    - do best-vs-worst pairs look clearly rankable?
  - Use findings to adjust:
    - N (samples per prompt)
    - divergence proxy thresholds
    - judge rubric prompts

### Experiments (minimal but decisive)

- **Divergence rate**: % of prompts with meaningful cross-policy differences.
- **Pair clarity score** (manual): % of sampled pairs that an annotator can confidently choose between on the intended axis.
- **Domain coverage check**: ensure the selected pairs are not dominated by 1–2 domains.

### Definition of done

- **Pair dataset produced**: a first `pairs.jsonl` (or equivalent) containing:
  - at least 500–2,000 pair candidates
  - balanced coverage across domains/types (no single bucket dominates)
  - explicit provenance for how each pair was formed (`cross_policy` vs `best_vs_worst`, and label_source)
- **Selection rule documented**: written description of:
  - N used for sampling
  - divergence proxy used
  - how pairs were chosen (heuristics + thresholds)
- **Readiness for Phase 3**: a concrete plan for how humans (or AI+human calibration) will label:
  - helpfulness preference
  - region alignment preference

