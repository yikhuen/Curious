## Phase 0 - Calibration note (seed set)

Date: 2026-01-15

### Method
- Manual rubric walk-through on the seed set to anticipate judge failure modes.
- Model-based calibration run is still pending.

### Expected failure modes
- **Implicit cultural cues** (tipping, prom, Thanksgiving) may be mis-scored as leakage=0 unless the judge is strict about borderline leakage.
- **Institution names vs concepts**: prompts about public/private healthcare or schools can be misread as explicit leakage even when no institution is named.
- **Salience drift**: generic prompts (budgeting, return policy) may be scored as salience=0 by default; add examples of region-dependent norms to anchor salience=1.

### Rubric tweaks to consider after model run
- Add a short list of “borderline” cues directly in the leakage rubric prompt.
- Emphasize that “public vs private” is not explicit leakage unless a program or institution is named.
- Require a short rationale that cites the specific cue that triggered leakage=1 or 2.
