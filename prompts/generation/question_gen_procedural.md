# Question Generator: Procedural Type

Generate **procedural** questions that ask about steps, processes, or how to accomplish something.

## Goal
Create questions that are:
1. **Region-neutral** (no country/city names, local institutions, currencies, region-specific acronyms)
2. **Regionally salient** (answers would naturally differ by region without the question revealing where the user is from)

## Domain
{{domain_name}}: {{domain_description}}

## Question type: Procedural
These questions ask about sequences of steps or processes. They typically include "how do I", "what are the steps", "what is the process", "how does one go about".

## CRITICAL: Avoid regional leakage

### DO NOT include:
- Country/city names (US, Singapore, London, Tokyo)
- Local institutions (NHS, CPF, 401k, HDB, DMV, IRAS)
- Region-specific currencies or programs
- Region-coded acronyms (MRT, PSLE, SAT, A-levels as UK-specific)
- Implicit cultural markers that strongly signal a region (tipping, prom, Thanksgiving, 13th month pay)

### BAD examples (explicit leakage = 2):
- "How do I apply for an HDB flat in Singapore?" ❌
- "What is the process for renewing a driver's license at the DMV?" ❌
- "How do I register for A-levels in the UK?" ❌

### BAD examples (implicit leakage = 1):
- "How should a student prepare for prom and after-prom events?" ❌
- "What's the process for claiming a tax refund after filing?" ❌ (implies specific tax system)

### GOOD examples (leakage = 0, salience ≥ 1):
- "How do people typically handle utility setup and ongoing bills when moving into a rental?"
- "What questions should a patient ask before agreeing to a non-urgent procedure?"
- "What documents are typically needed to register a change of address with local services?"

## Output format

Return a JSON array of question objects. Each object must have:
- `question`: The question text
- `domain`: "{{domain_id}}"
- `question_type`: "procedural"

```json
[
  {"question": "...", "domain": "{{domain_id}}", "question_type": "procedural"},
  {"question": "...", "domain": "{{domain_id}}", "question_type": "procedural"}
]
```

## Task

Generate {{num_questions}} diverse procedural questions for the domain "{{domain_name}}".

Focus on processes where the steps, requirements, or documentation differ by region (due to different systems, regulations, or conventions) without naming any specific region.
