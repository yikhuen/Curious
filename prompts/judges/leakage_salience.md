# Leakage + Salience Judge

You are evaluating whether a question reveals the user's region (leakage) and whether answers would naturally differ by region (salience).

## Rubric

### Leakage (0-2): Does the question reveal where the user is from?
- **2** = Explicit region cues: country/city names, local institutions, currencies, region-specific acronyms (e.g., "NHS", "401k", "CPF")
- **1** = Implicit cultural cues: customs, holidays, or practices that strongly suggest a region (e.g., "tipping etiquette", "lunar new year bonus")
- **0** = Clean: no regional cues; could be asked by anyone anywhere

### Salience (0-2): Would a helpful answer naturally differ by region?

**Key distinction between 1 and 2:**
- **Score 2**: The *approach or framework* itself differs fundamentally by region. You cannot give useful general advice without knowing the region.
- **Score 1**: The *general approach* is similar worldwide, but *specific details* (names, providers, exact steps) vary. Generic advice would still be helpful.
- **Score 0**: Answers would be essentially identical worldwide.

## Examples

**Example 1 (Salience = 2):**
Question: "What are my options for paying for university tuition?"
Rationale: The *entire framework* differs — some countries have free university, others have loans, grants, or payment plans. Cannot give useful advice without knowing region.

**Example 2 (Salience = 1):**
Question: "How can I plan a reliable commute route with unpredictable delays?"
Rationale: The *approach* is universal (check schedules, have backup routes, leave buffer time). Specific transit apps or services vary, but the general advice works anywhere.

**Example 3 (Salience = 2):**
Question: "What should I know about tipping at restaurants?"
Rationale: The *entire practice* differs — mandatory in US, offensive in Japan, optional elsewhere. No universal advice exists.

**Example 4 (Salience = 1):**
Question: "How do I set up utilities when moving to a new apartment?"
Rationale: The *process* is similar (contact providers, schedule setup, provide ID). Specific providers and requirements vary, but generic steps apply everywhere.

**Example 5 (Salience = 0):**
Question: "What are effective ways to stay focused while studying?"
Rationale: Focus techniques (breaks, quiet space, limiting distractions) are universal. No regional variation.

**Example 6 (Salience = 2):**
Question: "How do cultural norms affect giving feedback in group settings?"
Rationale: The *norms themselves* are fundamentally different (direct vs indirect, public vs private criticism). The answer IS the regional variation.

**Example 7 (Salience = 1):**
Question: "What should I ask before agreeing to a medical procedure?"
Rationale: The *questions* are universal (risks, alternatives, recovery). Specific healthcare systems vary, but the approach to informed consent is similar.

## Output format

Return JSON only:
```json
{"leakage_score": <0-2>, "salience_score": <0-2>, "rationale": "<brief explanation>"}
```

## Question to evaluate

{{question}}
