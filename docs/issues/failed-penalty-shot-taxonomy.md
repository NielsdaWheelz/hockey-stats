# failed penalty shots erase whole-game score support

status: open; interpretation-contract follow-up from 03b.

the fresh development captures contain `typeCode: 537`, `typeDescKey: failed-shot-attempt`, which interpretation does not classify. one such timed row makes both `timed_goals` checks unavailable under the reviewed completeness rule. preparation then requires matching checks and rejects any timed row whose kind cannot exclude an unaccounted goal. the implementation follows those guards; the source taxonomy contract is incomplete.

raw play reports explicitly record unsuccessful penalty shots in games `2023020955` (api source index 342, period 3/19:57, `PL-346`), `2023020974` (203, 2/17:05, `PL-207`), and `2023021224` (252, 3/04:19, `PL-256`). each report labels the outcome `MISS` / `Penalty Shot, Failed Attempt`. manually counted ordinary goals agree with both sources’ finals: 3–4, 1–6, and 4–3. no conflicting goal total was found.

all three games lose score support: 384 recognized attempts, including 316 unavailable and 68 outside 5v5. preserve those exclusions in this study. [clean raw receipts, rows, exact guards and preparation counts](/Volumes/Expansion/hockey-stats/chance/03b-20260930/inputs/development-whole-game-exclusions-clean.json) were verified at clean revision `6a0f6de2073d515921c9533fd58787a43d7234b7`; artifact sha256 `f3ff1a108203f974ef68cc16edb650846075049f39abda049572131ec8e909f8`.

the next owner is interpretation’s source taxonomy. resolve this by establishing strict non-goal semantics for this source code from attributed evidence, reviewing the interpretation contract, and verifying complete goal accounting on these captures and contradictory/unknown-event cases. then readmit and rerun preparation and the scientific study. do not bypass completeness, recode preserved payloads, or reuse fits from the changed population as unchanged evidence.
