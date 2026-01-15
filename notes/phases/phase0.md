## Phase 0 — Clarify objectives + rubrics (1–3 days)

### Why this phase matters (1–2 lines)

This phase prevents “good-looking” prompts from becoming unusable data by defining **what success means** (leakage vs salience) and **what we will label later** (preference axes), before we scale generation.

### Decisions (optimized for efficiency + aligned with objective)

- **Separate two prompt properties: leakage vs salience**
  - **Why**: “neutrality” is not one thing; we need **low regional leakage** *and* **high regional salience** (see `notes/plan.md`).
  - **How**: 0–2 scale for each, with hard gating later (leakage must be 0; salience ≥ 1).

- **Adopt a standard pairwise preference schema early (`prompt`, `chosen`, `rejected`)**
  - **Why**: keeps the repo interoperable and avoids bespoke formats.
  - **Reference**: TRL dataset format best practices recommend explicit `prompt` and keeping `chosen/rejected` as completions only ([TRL docs](https://huggingface.co/docs/trl/main/dataset_formats)).

- **Multi-axis preference labeling (design now, label later)**
  - **Why**: avoids optimizing “helpfulness” while accidentally destroying “regional alignment.”
  - **Reference**: multi-axis preference design patterns appear in HH-RLHF and PKU-SafeRLHF (summarized in `notes/research.md`).

- **Lean “region policy” definition for Phase 2**
  - **Decision**: start with **prompt-conditioned regional personas** (system prompts) to simulate SG/US answering policies, before building/using fully fine-tuned region models.
  - **Why**: cheaper + faster iteration; still produces divergence signals needed to validate prompt salience (mirrors AlpacaFarm-style “simulation first” iteration in `notes/research.md`).

### Step-by-step plan

- **Step 0.1 — Lock the objective and success metrics**
  - **Define**: “salience without leakage” as the primary objective (from `notes/plan.md`).
  - **Choose minimal metrics** to track in Phases 1–2:
    - leakage pass rate
    - novelty/dup rate
    - coverage by (domain × question_type)
    - divergence rate between region policies (proxy)

- **Step 0.2 — Write the leakage rubric (prompt-level)**
  - **Leakage = 2 (explicit)**: names a country/city, institution, currency, national program, or region-coded acronym (e.g., “NHS”, “MRT”, “401k”).
  - **Leakage = 1 (borderline/implicit)**: heavy cues like “tipping”, “spring cleaning”, “prom”, “Thanksgiving”, etc. (culture-coded assumptions).
  - **Leakage = 0 (clean)**: no region cues; understandable in many contexts.
  - **Efficiency note**: keep this rubric short and operational; every ambiguous rule increases disagreement later.

- **Step 0.3 — Write the salience rubric (prompt-level)**
  - **Salience = 2 (strong)**: likely to elicit region-dependent entities/norms while staying region-neutral (transport habits, housing norms, education pathways, etiquette).
  - **Salience = 1 (moderate)**: sometimes region-dependent, but answers may also converge.
  - **Salience = 0 (weak)**: likely universal answers regardless of region.

- **Step 0.4 — Define the preference labeling tasks (response-level)**
  - **Axis A (helpfulness)**: “Which answer better addresses the prompt?”
  - **Axis B (region alignment)**: “Assume a rater from region X. Which answer feels more natural/appropriate for region X?”
  - **Optional axis C (overall)**: trade-off label if needed later.
  - **Reference**: separating axes avoids conflation (HH-RLHF / PKU-SafeRLHF patterns in `notes/research.md`).

- **Step 0.5 — Choose initial domains + question types (small but high-signal)**
  - **Domains**: start with 10–15 high-salience “daily life + systems” domains (transport, food, housing, healthcare decision-making, education, workplace norms, finance basics, etiquette, family norms, shopping, leisure).
  - **Question types**: keep 5–7 types (from `notes/plan.md`) to avoid diversity collapse.
  - **Efficiency note**: smaller domain set with strong coverage beats a huge taxonomy early (LIMA-style “quality over quantity” intuition; cited in your older plan).

- **Step 0.6 — Build a tiny gold seed set (for calibration)**
  - Create ~30–50 “gold” prompts with leakage=0 and varying salience scores.
  - Include **negative examples** (leakage=2, leakage=1, salience=0) to anchor later automated judges.
  - **Reference**: seed sets are the backbone of generate→filter loops (Self-Instruct in `notes/research.md`).

### Definition of done

- **Rubrics complete**: written leakage+salience rubric with at least:
  - 10 explicit-pass examples
  - 10 borderline examples
  - 10 explicit-fail examples
- **Preference tasks defined**: written labeling instructions for helpfulness + region alignment (even if no labeling happens yet).
- **Seed set exists**: 30–50 gold prompts + negatives, each tagged with leakage and salience.
- **Phase 1 inputs ready**: agreed initial domain list, question types, and target per-bucket budgets.

