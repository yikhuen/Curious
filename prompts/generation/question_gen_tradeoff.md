# Question Generator: Tradeoff Type

Generate **tradeoff** questions that explicitly ask about what is gained and lost when choosing between options.

## Goal
Create questions that are:
1. **Region-neutral** (no country/city names, local institutions, currencies, region-specific acronyms)
2. **Regionally salient** (answers would naturally differ by region without the question revealing where the user is from)

## Domain
{{domain_name}}: {{domain_description}}

## Question type: Tradeoff
These questions focus on evaluating explicit trade-offs between choices. They typically include "trade-offs", "what do you gain/lose", "cost vs benefit", "sacrifice", "balance".

## CRITICAL: Avoid regional leakage

### DO NOT include:
- Country/city names (US, Singapore, London, Tokyo)
- Local institutions (NHS, CPF, 401k, HDB, DMV)
- Region-specific currencies or programs
- Region-coded acronyms (MRT, HSA, Roth IRA)
- Implicit cultural markers that strongly signal a region (tipping, prom, Thanksgiving, homecoming)

### BAD examples (explicit leakage = 2):
- "What are the trade-offs of choosing an HDB vs a condo?" ❌
- "What do you sacrifice by maxing out your 401k early?" ❌

### BAD examples (implicit leakage = 1):
- "What are the trade-offs of tipping generously vs tipping the minimum?" ❌
- "What do you gain and lose by attending a community college first?" ❌

### GOOD examples (leakage = 0, salience ≥ 1):
- "What trade-offs should a person consider when choosing between debit, credit, and cash for daily purchases?"
- "How can a student decide whether to pursue higher education immediately or work first?"
- "What are the trade-offs between living closer to work versus in a more affordable area?"

## Output format

Return a JSON array of question objects. Each object must have:
- `question`: The question text
- `domain`: "{{domain_id}}"
- `question_type`: "tradeoff"

```json
[
  {"question": "...", "domain": "{{domain_id}}", "question_type": "tradeoff"},
  {"question": "...", "domain": "{{domain_id}}", "question_type": "tradeoff"}
]
```

## Task

Generate {{num_questions}} diverse tradeoff questions for the domain "{{domain_name}}".

Focus on trade-off scenarios where the relative costs, benefits, or priorities differ by region (due to different economic conditions, social norms, or available options) without naming any specific region.
