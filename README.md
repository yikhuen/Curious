# Curious — Region-Neutral Prompt Generation Pipeline

A pipeline for generating region-neutral prompts that elicit regionally diverse responses, designed for training culturally-aware language models.

## Quick Start: Phase 0 (Judge Calibration)

Before running Phase 1, you need to calibrate the judge model on the seed set.

### Step 1: Start the Model Server

In **Terminal 1**, start the vLLM server (keep it running):

```bash
# Install vLLM if needed
pip install vllm

# Start server (A100-80GB)
vllm serve Qwen/Qwen2.5-32B-Instruct --port 8000 --dtype bfloat16

# Or for A100-40GB, use quantized:
vllm serve Qwen/Qwen2.5-32B-Instruct-AWQ --port 8000
```

The server will download the model (first time only), load it into GPU memory, and start serving on port 8000. **Leave this terminal running.**

### Step 2: Run Calibration

In **Terminal 2**, run the calibration script:

```bash
python scripts/run_judge_calibration.py --base-url http://localhost:8000/v1
```

This will:
- Grade all 60 seed prompts
- Compare predictions to gold labels
- Print accuracy summary
- Write results to `data/runs/phase0_calibration/judge_results.jsonl`
- Exit when complete

**Completion signal**: The script prints a summary and exits. You'll see:
```
============================================================
CALIBRATION SUMMARY
============================================================
Leakage accuracy:  55/60 (91.7%)
Salience accuracy: 52/60 (86.7%)

Results written to: data/runs/phase0_calibration/judge_results.jsonl
```

**Target accuracy**: Leakage ≥85%, Salience ≥75%

### Step 3: Review and Refine (if needed)

If accuracy is below targets:
1. Review mismatches in `judge_results.jsonl`
2. Update `prompts/judges/leakage_salience.md` with clarifications
3. Re-run calibration to verify improvements

---

## Quick Start: Phase 1

This guide walks you through **Phase 1: MVP Prompt Pool Generation** — creating your first scalable set of region-neutral, region-salient prompts.

---

## Prerequisites

### 1. Phase 0 Complete

Ensure Phase 0 artifacts exist:
- `configs/domains.yaml` (12 domains)
- `configs/question_types.yaml` (7 types)
- `configs/llm.yaml` (model: Qwen2.5-32B-Instruct)
- `configs/policies.yaml` (SG/US policies)
- `prompts/judges/leakage_salience.md`
- `data/seeds/questions_gold.jsonl` (60 seed prompts)

### 2. Python Environment

```bash
pip install -r requirements.txt
```

Additional dependencies for Phase 1:
```bash
pip install rouge-score  # For ROUGE-L deduplication
```

### 3. GPU Setup (A100 recommended)

You'll need a model server running. For **Qwen2.5-32B-Instruct** on a single A100:

```bash
# Install vLLM
pip install vllm

# Start the server (FP16, uses ~64GB VRAM)
vllm serve Qwen/Qwen2.5-32B-Instruct --port 8000 --dtype bfloat16

# Or for A100-40GB, use quantized:
vllm serve Qwen/Qwen2.5-32B-Instruct-AWQ --port 8000
```

Keep this server running in a separate terminal.

---

## Phase 1 Workflow Overview

Phase 1 generates, filters, deduplicates, and scores prompts through these stages:

```
1. Generate → questions_raw.jsonl
2. Filter → questions_filtered.jsonl
3. Deduplicate → questions_deduped.jsonl
4. Score → questions_scored.jsonl
5. Accept → questions_accepted.jsonl
```

Each stage is a separate script that reads JSONL and writes JSONL (append-only, restartable).

---

## Step-by-Step: Running Phase 1

### Step 1: Create Generation Templates

First, create question generation templates for each question type:

```bash
# Templates will be created at:
# prompts/generation/question_gen_<type>.md
```

Each template should:
- Include "no region cues" constraints
- Show contrastive examples (good vs leaky from seed negatives)
- Require strict JSON output

**Status**: ⚠️ Templates not yet created — this is the first task.

### Step 2: Generate Initial Batch

Run generation for each (domain × question_type) bucket:

```bash
python scripts/phase1_generate_questions.py \
    --run-id phase1_v1 \
    --base-url http://localhost:8000/v1 \
    --batch-size 20
```

**Output**: `data/runs/phase1_v1/questions_raw.jsonl`

**What to check**:
- Coverage across domains/types
- Early leakage patterns
- Repetitive prompts

### Step 3: Apply Hard Filters

Run cheap filters (blocklists, shape checks, PII):

```bash
python scripts/phase1_filter_questions.py \
    --input data/runs/phase1_v1/questions_raw.jsonl \
    --output data/runs/phase1_v1/questions_filtered.jsonl
```

**Output**: `questions_filtered.jsonl` with filter reasons

**Filters applied**:
- Explicit leakage blocklist (countries, institutions, currencies)
- Shape checks (is-question, length bounds, language)
- PII heuristics

### Step 4: Deduplicate

Remove near-duplicates using ROUGE-L:

```bash
python scripts/phase1_dedup_questions.py \
    --input data/runs/phase1_v1/questions_filtered.jsonl \
    --output data/runs/phase1_v1/questions_deduped.jsonl \
    --rouge-threshold 0.7
```

**Output**: `questions_deduped.jsonl` with novelty scores

**Threshold**: ROUGE-L similarity ≥ 0.7 → reject (Self-Instruct standard)

### Step 5: Score with Judge

Run leakage/salience scoring:

```bash
python scripts/phase1_score_questions.py \
    --input data/runs/phase1_v1/questions_deduped.jsonl \
    --output data/runs/phase1_v1/questions_scored.jsonl \
    --base-url http://localhost:8000/v1
```

**Output**: `questions_scored.jsonl` with `leakage_score`, `salience_score`, `rationale`

**Gate**: Accept if `leakage_score == 0` AND `salience_score >= 1`

### Step 6: Generate Final Accepted Set

```bash
python scripts/phase1_accept_questions.py \
    --input data/runs/phase1_v1/questions_scored.jsonl \
    --output data/runs/phase1_v1/questions_accepted.jsonl
```

**Output**: `questions_accepted.jsonl` (final prompt pool)

### Step 7: Audit & Report

Sample and audit quality:

```bash
python scripts/phase1_report.py \
    --run-dir data/runs/phase1_v1 \
    --audit-sample-size 100
```

**Output**: 
- `run_manifest.json` (config + counts)
- Distribution report (domain×type coverage)
- Audit samples for manual review

---

## Expected Outputs

After completing Phase 1, you should have:

```
data/runs/phase1_v1/
├── questions_raw.jsonl          # ~2,000-5,000 prompts
├── questions_filtered.jsonl     # ~1,500-4,000 (after filters)
├── questions_deduped.jsonl      # ~1,000-3,000 (after dedup)
├── questions_scored.jsonl       # ~1,000-3,000 (with scores)
├── questions_accepted.jsonl     # ~500-2,000 (final pool)
└── run_manifest.json            # Metadata + counts
```

**Quality targets**:
- Coverage: 10-15 domains × 5-7 types
- Quantity: 500-2,000 accepted prompts
- Leakage: ≤5% in audited sample
- Salience: ≥50% with salience≥1

---

## Troubleshooting

### Model Server Not Responding

```bash
# Check if server is running
curl http://localhost:8000/v1/models

# Restart if needed
vllm serve Qwen/Qwen2.5-32B-Instruct --port 8000 --dtype bfloat16
```

### Out of Memory

- Use quantized model: `Qwen2.5-32B-Instruct-AWQ`
- Reduce batch size in generation script
- Process in smaller chunks

### High Leakage Rate

1. Check filter blocklist coverage
2. Review generation templates (add more negative examples)
3. Audit judge scoring (run calibration script from Phase 0)

### Low Acceptance Rate

1. Check salience scores — may need to adjust generation templates
2. Review dedup threshold (may be too strict)
3. Check filter false positives

---

## Next Steps

After Phase 1 is complete:

- **Phase 2**: Generate pairwise responses using region policies, then collect preferences
- See `notes/implementation/phase2.md` for details

---

## Script Status

⚠️ **Phase 1 scripts not yet implemented**. The scripts referenced above need to be created:

- [ ] `scripts/phase1_generate_questions.py`
- [ ] `scripts/phase1_filter_questions.py`
- [ ] `scripts/phase1_dedup_questions.py`
- [ ] `scripts/phase1_score_questions.py`
- [ ] `scripts/phase1_accept_questions.py`
- [ ] `scripts/phase1_report.py`

See `notes/implementation/phase1.md` for detailed implementation plan.

---

## Configuration

All configs live in `configs/`:

- **`llm.yaml`**: Model IDs, decoding params, cache settings
- **`domains.yaml`**: Domain definitions + budgets
- **`question_types.yaml`**: Question type definitions
- **`policies.yaml`**: Region policy system prompts (for Phase 2)

---

## Project Structure

```
.
├── configs/              # YAML configs (domains, types, models, policies)
├── prompts/
│   ├── judges/          # Judge prompt templates
│   └── generation/      # Question generation templates (Phase 1)
├── data/
│   ├── seeds/          # Phase 0 gold seed set
│   └── runs/           # Phase 1+ run artifacts
├── scripts/            # Pipeline scripts
├── schemas/            # JSON schemas for data formats
└── notes/              # Planning + implementation docs
```

