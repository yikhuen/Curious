# Question Generator: Comparative Type

Generate **comparative** questions that ask users to compare options, weigh pros and cons, or evaluate alternatives.

## Goal
Create questions that are:
1. **Region-neutral** (no country/city names, local institutions, currencies, region-specific acronyms)
2. **Regionally salient** (answers would naturally differ by region without the question revealing where the user is from)

## Domain
{{domain_name}}: {{domain_description}}

## Question type: Comparative
These questions ask someone to compare two or more choices and their trade-offs. They typically include "compare", "difference between", "pros and cons", "versus", "which is better".

## CRITICAL: Avoid regional leakage

### DO NOT include:
- Country/city names (US, Singapore, London, Tokyo)
- Local institutions (NHS, CPF, 401k, HDB, DMV)
- Region-specific currencies or programs
- Region-coded acronyms (MRT for Singapore transit, HSA for US health savings)
- Implicit cultural markers that strongly signal a region (tipping, prom, Thanksgiving, homecoming)

### BAD examples (explicit leakage = 2):
- "What are the differences between HDB and private condos in Singapore?" ❌
- "How does the NHS compare to private healthcare in the UK?" ❌

### BAD examples (implicit leakage = 1):
- "How does tipping at restaurants compare to tipping at bars?" ❌
- "What are the trade-offs between community college and state university?" ❌ (US-specific structure)

### GOOD examples (leakage = 0, salience ≥ 1):
- "What factors should someone consider when choosing between public transit, driving, and cycling for a daily commute?"
- "How do people typically choose between public and private healthcare options?"
- "What are the main differences between vocational training and academic pathways after secondary school?"

## Output format

Return a JSON array of question objects. Each object must have:
- `question`: The question text
- `domain`: "{{domain_id}}"
- `question_type`: "comparative"

```json
[
  {"question": "...", "domain": "{{domain_id}}", "question_type": "comparative"},
  {"question": "...", "domain": "{{domain_id}}", "question_type": "comparative"}
]
```

## Task

Generate {{num_questions}} diverse comparative questions for the domain "{{domain_name}}".

Focus on comparisons where the trade-offs or relative merits differ by region (due to different systems, costs, availability, or norms) without naming any specific region.
