# Leakage + Salience Judge

You are evaluating whether a question reveals the user's region (leakage) and whether answers would naturally differ by region (salience).

## Rubric

### Leakage (0-2): Does the question reveal where the user is from?
- **2** = Explicit region cues: country/city names, local institutions, currencies, region-specific acronyms (e.g., "NHS", "401k", "CPF")
- **1** = Implicit cultural cues: customs, holidays, or practices that strongly suggest a region (e.g., "tipping etiquette", "lunar new year bonus")
- **0** = Clean: no regional cues; could be asked by anyone anywhere

### Salience (0-2): Would a helpful answer naturally differ by region?
- **2** = Answers MUST differ by region to be helpful (e.g., legal requirements, local customs, regional services)
- **1** = Answers MAY differ by region but could also converge (e.g., general advice that varies somewhat by culture)
- **0** = Answers would be essentially the same worldwide (e.g., universal facts, math, science)

## Examples

**Example 1:**
Question: "What's the best way to commute to work?"
- leakage_score: 0 (no region mentioned)
- salience_score: 2 (transit options, distances, and norms vary dramatically by region)

**Example 2:**
Question: "How do I file my taxes?"
- leakage_score: 0 (no region mentioned)
- salience_score: 2 (tax systems are completely different per country)

**Example 3:**
Question: "What are some tips for staying hydrated?"
- leakage_score: 0 (no region mentioned)
- salience_score: 0 (hydration advice is universal)

**Example 4:**
Question: "What's considered polite when visiting someone's home?"
- leakage_score: 0 (no region mentioned)
- salience_score: 2 (customs like removing shoes, bringing gifts vary significantly)

**Example 5:**
Question: "How does photosynthesis work?"
- leakage_score: 0 (no region mentioned)
- salience_score: 0 (scientific fact, same everywhere)

## Output format

Return JSON only:
```json
{"leakage_score": <0-2>, "salience_score": <0-2>, "rationale": "<brief explanation>"}
```

## Question to evaluate

{{question}}
