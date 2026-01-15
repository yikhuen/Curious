## Phase 2 — Progress checklist (responses + pair selection)

### Status

- [ ] Not started
- [ ] In progress
- [ ] Blocked
- [ ] Done

---

## Checklist

### Setup

- [ ] Confirm `data/questions.jsonl` (or equivalent accepted prompt pool) exists
- [ ] Confirm `configs/policies.yaml` exists (SG/US policies; no explicit self-location)
- [ ] Confirm Qwen model choice for response generation (up to 72B) in `configs/llm.yaml`
- [ ] Decide N samples per prompt per policy (start with N=1; scale to N=4 if stable)

### Response generation

- [ ] Generate responses for SG policy
- [ ] Generate responses for US policy
- [ ] (Optional) Generate multiple samples per policy (N>1)
- [ ] Save `responses.jsonl` with full provenance (prompt_id, policy_id, decoding, model_id)

### Pair construction

- [ ] Build cross-policy pairs (SG vs US for each prompt)
- [ ] (Optional) Score within-policy responses for helpfulness (judge) to enable best-vs-worst
- [ ] Build best-vs-worst pairs (within-policy) with explicit `label_source=ai_judge`

### Prioritization (spend labels efficiently later)

- [ ] Compute divergence proxy for cross-policy pairs (judge-scored or simple heuristic)
- [ ] Flag high-divergence pairs for Phase 3 labeling priority

### Export format (compatibility)

- [ ] Export TRL-compatible `pairs.jsonl` with explicit:
  - [ ] `prompt`
  - [ ] `chosen`
  - [ ] `rejected`
  - [ ] `pair_meta` (pair_type, label_source, axis, policies, model/decoding)

### Audit + report (required)

- [ ] Sample ~100 pairs across domains/types
- [ ] Check verbosity bias (chosen isn’t just longer)
- [ ] Check cross-policy pairs differ in region-relevant ways
- [ ] Check within-policy pairs are clearly rankable
- [ ] Write `run_manifest.json` + short Phase 2 report (divergence rate, distributions, fixes)

---

## Definition of done (Phase 2)

- [ ] `pairs.jsonl` exists with 500–2,000 pair candidates
- [ ] Pair provenance is explicit (pair_type + label_source + axis + policy ids)
- [ ] Divergence rate is measured and tracked (not necessarily “high” yet, but visible)
- [ ] Pair clarity audit completed and used to adjust parameters/templates

