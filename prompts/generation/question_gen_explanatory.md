# Question Generator: Explanatory Type

Generate **explanatory** questions that ask about factors, concepts, reasons, or norms.

## Goal
Create questions that are:
1. **Region-neutral** (no country/city names, local institutions, currencies, region-specific acronyms)
2. **Regionally salient** (answers would naturally differ by region without the question revealing where the user is from)

## Domain
{{domain_name}}: {{domain_description}}

## Question type: Explanatory
These questions ask someone to explain factors, concepts, or norms. They typically start with "What factors...", "Why do...", "What are the main considerations...", "How does X work..."

## CRITICAL: Avoid regional leakage

### DO NOT include:
- Country/city names (US, Singapore, London, Tokyo)
- Local institutions (NHS, CPF, 401k, HDB, DMV)
- Region-specific currencies or programs
- Region-coded acronyms (MRT for Singapore transit, HSA for US health savings)
- Implicit cultural markers that strongly signal a region (tipping, prom, Thanksgiving, lunar new year bonus)

### BAD examples (explicit leakage = 2):
- "How does the NHS handle referrals for specialists?" ❌
- "What factors affect 401k contribution limits?" ❌
- "Why do Singaporeans use CPF for housing?" ❌

### BAD examples (implicit leakage = 1):
- "What are the norms around tipping at restaurants?" ❌ (tipping strongly implies US)
- "Why is prom such a big deal for high school students?" ❌ (prom is US-centric)

### GOOD examples (leakage = 0, salience ≥ 1):
- "What factors influence how people choose between public and private healthcare options?"
- "What are typical expectations around after-hours messages from coworkers?"
- "What are common considerations when splitting a restaurant bill with a group?"

## Output format

Return a JSON array of question objects. Each object must have:
- `question`: The question text
- `domain`: "{{domain_id}}"
- `question_type`: "explanatory"

```json
[
  {"question": "...", "domain": "{{domain_id}}", "question_type": "explanatory"},
  {"question": "...", "domain": "{{domain_id}}", "question_type": "explanatory"}
]
```

## Task

Generate {{num_questions}} diverse explanatory questions for the domain "{{domain_name}}".

Focus on topics where the explanation would naturally differ by region (laws, norms, systems, expectations) without revealing any specific region in the question itself.
