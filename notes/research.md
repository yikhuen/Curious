## Research: how labs curate prompt/question pipelines for pairwise preference data

### What “question generation for preference data” usually means in practice

Across RLHF/DPO-style projects, labs typically treat “questions” (prompts/instructions) as a **first-class dataset** with its own curation loop, because preference labels are only as good as the prompts they’re conditioned on. A common high-level shape:

- **Prompt pool construction**: mix organic prompts (real users / crowdworkers) + synthetic prompts (LLM-generated expansions) + targeted probes (edge cases).
- **Prompt curation**: privacy filtering, deduplication, downsampling overrepresented sources, and stratified sampling to preserve coverage.
- **Candidate response generation**: generate 2–N responses per prompt (often across multiple models, temperatures, or decoding strategies).
- **Preference collection**: humans (or AI judges for triage) compare/rank responses for the same prompt, yielding pairwise records like `(prompt, chosen, rejected)`.
- **Iterate**: use failures from eval/labeling to generate more “hard” prompts and reduce blind spots.

For our project, the key twist is: we want **high regional salience** (different regions plausibly answer differently) while keeping **low regional leakage** (the prompt itself does not name any region or region-specific institution).

---

## Case studies (what they did → what we should copy)

### OpenAI InstructGPT (instruction RLHF with human rankings)

- **What they did**
  - **Prompt sourcing**: a mixture of **API customer prompts** and **labeler-written prompts** (to increase diversity when organic prompts are sparse). Prompts are privacy-filtered and deduplicated; they cap prompts per organization to avoid overrepresentation. ([paper](https://arxiv.org/abs/2203.02155))
  - **Pairwise/ranking labels**: for each prompt, generate multiple completions (reported as 4–9), then have humans **rank** them; pairwise preferences are derived from the ranking. ([paper](https://arxiv.org/abs/2203.02155))
- **Why it matters for our direction**
  - **Prompt pool is a product**: treat prompts as versioned data with explicit provenance and caps (prevents one source dominating).
  - **Multi-completion is the default**: generate multiple answers per prompt so you can pick informative pairs (not just “two random samples”).
  - **Generalization split idea**: they split by org/user; for us, an analogue is splitting by **prompt source** (seed vs evolved vs mined) so we don’t overfit to one generation style.

### OpenAI WebGPT (preference data with prompts from an existing question dataset)

- **What they did**
  - **Prompt sourcing**: use an existing open question distribution (ELI5-style longform questions) rather than inventing prompts from scratch. ([blog](https://openai.com/blog/webgpt/), [paper](https://arxiv.org/abs/2112.09332))
  - **Pairwise labels**: humans compare model answers to the *same* question to create preference data for reward modeling. ([paper](https://arxiv.org/abs/2112.09332))
- **Why it matters for our direction**
  - **Bootstrapping strategy**: we can start from existing prompt corpora (then filter for “region-neutral”) instead of generating everything.
  - **Task-shaping**: if we later want *evidence-grounded* regional answers, WebGPT is a blueprint for “add evidence fields without breaking the preference schema.”

### Anthropic HH-RLHF (helpfulness/harmlessness preference pairs)

- **What they did**
  - **Data format**: release a canonical pairwise schema with `chosen`/`rejected` responses for a shared prompt. ([dataset](https://huggingface.co/datasets/Anthropic/hh-rlhf))
  - **Collection pattern**: generate candidate responses (including via rejection sampling / iterative improvement), then collect human preferences; keep separate helpfulness vs harmlessness tracks. ([paper](https://arxiv.org/abs/2204.05862))
- **Why it matters for our direction**
  - **Two-axis thinking**: our analogue is “**helpfulness**” vs “**cultural/region alignment**” (or “neutrality compliance”). Multi-axis labels help avoid optimizing one dimension while breaking another.
  - **Schema compatibility**: adopting HH-style `chosen/rejected` makes us interoperable with existing tooling and reduces bespoke code.

### Anthropic Constitutional AI / RLAIF (AI-assisted preference labeling and revisions)

- **What they did**
  - **Scale feedback** using an explicit “constitution” (principles) so an AI model can critique/revise outputs and can also act as a judge to produce preference labels (RLAIF). ([paper](https://arxiv.org/abs/2212.08073))
- **Why it matters for our direction**
  - **Lean scaling path**: use AI-judging for *triage* (screening, clustering, “hard prompt” discovery), then reserve human labeling for calibration and high-value pairs.
  - **Principle-driven evaluation**: we can encode “no explicit region references”, “works in any region”, “invites region-specific choices” as a lightweight “constitution” for automated audits.

### DeepMind Sparrow (targeted human judgments + adversarial probing)

- **What they did**
  - Collect **targeted judgments** (preference + rule compliance) and use **adversarial probes** to stress safety rules; train separate models for preference and rule violations. ([paper](https://arxiv.org/abs/2209.14375), [blog](https://deepmind.google/blog/building-safer-dialogue-agents/))
  - The full dataset is not publicly released, but the pattern is well described.
- **Why it matters for our direction**
  - **Targeted judgments** map well to our needs: “does this prompt leak region?” is different from “is this prompt good?”
  - **Adversarial prompts** are a scalable way to uncover failure modes in region-neutrality filters (e.g., subtle institution names, holidays, seasonal assumptions).

### LMSYS Chatbot Arena (organic prompts + pairwise votes at scale)

- **What they did**
  - **Prompt sourcing**: real users submit prompts; models respond; users vote which answer they prefer (pairwise). ([paper](https://arxiv.org/abs/2403.04132))
  - They downsample overly common prompts and curate “hard prompts” subsets for evaluation. ([hard prompts post](https://lmsys.org/blog/2024-05-17-category-hard/))
- **Why it matters for our direction**
  - **Reality check**: organic prompts include lots of noise (greetings, duplicates, ambiguous asks). You need downsampling + stratification or your dataset collapses into “small-talk preference data.”
  - **Hard-subset pattern**: create a “regional-divergence hard set” (high salience, low leakage) to track progress while scaling.

### Stanford SHP (preferences inferred from Reddit outcomes)

- **What they did**
  - Build preference pairs from Reddit by using **score + timestamp** heuristics to infer which comment is preferred for a post. ([dataset](https://huggingface.co/datasets/stanfordnlp/SHP))
- **Why it matters for our direction**
  - **Cheap preference signal**: demonstrates a way to get pairwise preference supervision without running your own labeling operation.
  - **Caution**: domain and demographic skew is strong; for “regional differences,” SHP may primarily encode Western internet norms—useful for tooling/bootstrap, risky as a target distribution.

### OpenAssistant OASST1 (tree-structured prompts + rankings)

- **What they did**
  - Crowdsource prompts and multi-turn conversation trees; when multiple assistant replies exist to the same node, collect **rankings** among siblings. ([dataset](https://huggingface.co/datasets/OpenAssistant/oasst1))
- **Why it matters for our direction**
  - **Multi-turn extensibility**: this is the clearest open reference for how to store and rank multi-turn data without forcing everything into single-turn.
  - **Operational insight**: separating “growth” from “ranking” as distinct tasks is a clean way to structure human work.

### UltraFeedback (synthetic multi-response + judge scores → preference pairs)

- **What they did**
  - For each instruction, collect multiple model responses and have a strong model (e.g., GPT-4) score across axes; derive pairwise preferences from score differences. ([repo](https://github.com/OpenBMB/UltraFeedback))
- **Why it matters for our direction**
  - **Practical scaling**: multi-response per prompt + (AI) judging yields a lot of preference pairs quickly.
  - **Bias risk**: judge preferences can imprint on the dataset; we should treat AI-judged labels as a *proposal* until calibrated with a small human set.

### PKU-SafeRLHF (explicitly multi-axis preference data)

- **What they did**
  - Provide preference data with safety annotations and both “dual-preference” (helpfulness + harmlessness separately) and “single-preference” (trade-off) labels. ([paper](https://arxiv.org/abs/2406.15513))
- **Why it matters for our direction**
  - **Label decomposition**: we can mirror this by collecting (a) “which is more helpful?” and (b) “which better matches region/culture expectations?” separately, plus an optional combined label for downstream training.

### Self-Instruct + Evol-Instruct (prompt expansion loops)

- **What they did**
  - **Self-Instruct**: iterative generate→filter loop starting from a small seed set; novelty filtering to reduce duplicates. ([paper](https://arxiv.org/abs/2212.10560), [repo](https://github.com/yizhongw/self-instruct))
  - **Evol-Instruct / WizardLM**: mutate/evolve instructions to increase complexity/diversity (add constraints, deepen reasoning, broaden topics) with elimination filters. ([WizardLM repo](https://github.com/nlpxucan/WizardLM), [WizardCoder paper](https://arxiv.org/abs/2306.08568))
- **Why it matters for our direction**
  - **Anti-exhaustion mechanism**: prompt mutation operators + novelty filtering are a scalable way to generate “new” prompts without drifting into nonsense.
  - **Controlled diversity**: evolution steps can be constrained to preserve region-neutrality while increasing “regional salience.”

### AlpacaFarm (preference-data simulation for fast iteration)

- **What they did**
  - Provide a framework to **simulate preference feedback** with LLM judges so you can iterate on pipeline + training methods before paying for large-scale human labels. ([repo](https://github.com/tatsu-lab/alpaca_farm), [paper](https://arxiv.org/abs/2305.14387))
- **Why it matters for our direction**
  - **Lean experimentation**: we can prototype “regional alignment preferences” with simulated judges, then validate on a small human-labeled slice.
  - **Avoid overbuilding**: simulation lets us test pipeline decisions (prompt distribution, pair sampling) before building a heavy annotation stack.

---

## Existing repos / datasets to build on (mapped to pipeline stages)

The goal here is **reuse without coupling**: we should borrow *formats, prompt sources, and reference implementations* without turning our repo into a fragile dependency graph.

### Recommended “lean” reuse pattern

- **Adopt a standard pairwise schema** (`prompt`, `chosen`, `rejected`) so tooling compatibility is free.
- **Ingest external datasets as optional inputs** (not hard dependencies): treat them as “seed prompt sources” and filter them to our constraints.
- **Keep pipeline stages as restartable transforms** over JSONL artifacts (append-only), so each step can be rerun independently.

### Practical mapping table

| Resource | What it gives you | Pipeline stage(s) | How we’d use it (lean) | Notes / risk |
|---|---|---|---|---|
| InstructGPT paper | Prompt mixture patterns + ranking setup | Design reference | Copy patterns: source caps, dedup, multi-completion per prompt | Not a dataset release |
| `Anthropic/hh-rlhf` | Canonical pairwise format | Preference schema | Mirror the `chosen/rejected` structure to stay interoperable | Different objective (help/harmless) |
| TRL dataset formats | Widely used preference schema conventions | Data interface | Follow TRL’s explicit `prompt/chosen/rejected` best practices | Helps avoid schema bugs ([docs](https://huggingface.co/docs/trl/main/dataset_formats)) |
| `stanfordnlp/SHP` | Huge preference pairs “for free” | Baseline RM / tooling | Use for smoke-testing RM/DPO data loaders and analysis | Popularity bias, domain skew |
| `lmsys` Arena convos | Organic prompts + pairwise votes | Prompt sourcing / evaluation | Mine prompts, then apply region-neutrality filters; build a “hard subset” | Privacy/moderation considerations; distribution mismatch |
| `OpenAssistant/oasst1` | Multi-turn trees + rankings | Multi-turn extensibility | Use as reference structure for multi-turn prompt packaging | Not region-focused |
| `OpenBMB/UltraFeedback` | Multi-response per prompt + judge labels | Synthetic preference bootstrap | Use to validate multi-response handling, pair selection logic, multi-axis scoring | Judge bias (AI-labeled) |
| `PKU-SafeRLHF` | Multi-axis preferences + safety categories | Annotation design reference | Borrow idea: separate labels per axis + trade-off label | Safety objective differs |
| `yizhongw/self-instruct` | Generate→filter loop code | Prompt expansion | Reuse the loop structure + novelty filtering, but swap in our neutrality/salience audits | Filtering must be adapted |
| `nlpxucan/WizardLM` (Evol) | Evolution/mutation operators | Prompt expansion | Reuse “operators” (add constraints, deepen) bounded by neutrality constraints | Needs careful elimination rules |
| `tatsu-lab/alpaca_farm` | Simulated preference feedback harness | Experimentation | Use to prototype “regional preference” judges and pair sampling before human labeling | Simulation ≠ ground truth |

---

## Extensibility: how to scale prompts without “running out of questions”

In practice, you won’t exhaust the space of possible prompts; you’ll hit **saturation** (near-duplicates, low novelty, or drifting off-task). The extensions below prevent that while keeping the system lean.

### 1) Add explicit “novelty budgeting”

- Maintain an embedding index of accepted prompts.
- A new prompt must clear a novelty threshold **within its bucket** (domain × type × difficulty), not just globally.
- This prevents “transportation advisory” from saturating while other buckets stay empty.

### 2) Use mutation operators instead of unconditional generation

Borrow from Evol-Instruct: apply bounded transforms to existing high-quality prompts:

- **Deepen**: add one constraint (budget, accessibility, trade-offs) while keeping region-neutral.
- **Broaden**: ask for multiple perspectives (e.g., “consider different household types”) without naming regions.
- **Counterfactualize**: “what changes if X constraint flips?”
- **Multi-turn convert**: generate a follow-up question that depends on a plausible first answer.

This produces novelty with controllable drift.

### 3) Build a “hard prompt” discovery loop

Borrow from Arena/Sparrow:

- Run prompts through your region-tuned models.
- Flag prompts where:
  - region neutrality checks are borderline (possible leakage),
  - responses diverge strongly (high salience),
  - or the models produce systematic failures (bias, refusal, hallucination).
- Feed these back as seeds for more prompts in the same neighborhood.

### 4) Support new “axes” without rewriting everything

Design your metadata so you can add new dimensions later:

- **Difficulty**: shallow vs deep reasoning.
- **Format**: single-turn, multi-turn, tool-augmented, constrained-output.
- **Language**: English-first, then multilingual.
- **Safety/ethics**: disallowlists, red-teaming prompts, and “sensitive-but-benign” categories.

### 5) Keep artifacts stable; swap validators and generators

To avoid overcomplication:

- Keep the core artifacts stable (`questions.jsonl`, `pairs.jsonl`).
- Allow swapping components (generator model, embedding model, judge model) via config.
- Make every step restartable from disk outputs.

