# conflicting defending sides leave recorded frames unresolved

status: open; independent frame-provenance follow-up from 03b.

03c verification: [the preserved native fixture](../../fixtures/captures/2023020078/) reproduces the contradiction and unchanged exclusions; its five historical body hashes match 03b. this is a source-semantics limitation, not an unavailable-drive dependency.

in fresh capture `2023020078` (nyr at sea, 2023-10-21), the raw `homeTeamDefendingSide` field reports both sides in every period: period 1 has 51 left / 55 right records, period 2 has 47 / 48, and period 3 has 49 / 49. these are repeated within-period transitions, not missing coordinate fields.

the reviewed reconstruction contract rejects an entire period’s frame when its explicit sides conflict. all 98 timed attempts therefore have `unresolved_frame` with `period reports conflicting defending sides`; preparation retains 86 unavailable and 12 outside 5v5, with no eligible attempts. score accounting is supported. this is a source conflict with the period-frame invariant, faithfully rejected by reconstruction.

03m preserves a distinct ordered switch in [2021020942](../../fixtures/captures/2021020942/), toronto/buffalo at `Tim Hortons Field`, 2022-03-13. p3 has 55 left-side rows, then 62 right-side rows. api `/plays/281` stoppage, event `591`, sort `564`, records `secondaryReason: switch-sides` at `10:00`; next faceoff `/plays/282`, event `685`, sort `567`, changes the reported side. original report `/rows/284[PL-285]` independently says `REFEREE OR LINESMAN,SWITCH SIDES`. the settled guard retains all 36 p3 timed locations as null; 22 attempts are unavailable and 14 known outside scope. the other periods retain 62 eligible unblocked attempts, and timed score stays supported. no source or population policy changed.

a switch marker alone cannot resolve the frame: `2023020078` supplies api markers at `/plays/49,/158,/201,/256` and matching report `PL-53,PL-162,PL-205,PL-260`, yet its periods have further unexplained side transitions. both complete original bundles remain the required counterexamples for any proposed temporal frame contract.

[clean raw receipts, transitions, exact guards and preparation counts](/Users/nnandal/Documents/code/hockey-stats-03b-review/03b-20260930/inputs/development-whole-game-exclusions-clean.json) were verified at clean revision `6a0f6de2073d515921c9533fd58787a43d7234b7`; artifact sha256 `f3ff1a108203f974ef68cc16edb650846075049f39abda049572131ec8e909f8`. the retained local copy matches that digest. the captures alone cannot establish whether the side field is wrong or the coordinates use another convention. neither a physical direction nor a correction is justified.

the next owner is source semantics/provenance research, followed by reconstruction’s frame contract. resolution requires independent evidence establishing the recorded coordinate frame for affected events, a reviewed strict interpretation of ordered transitions that retains unexplained conflicts, and verified readmission/preparation against both original bundles. preserve the conflicting captures and existing exclusions; do not infer sides from period parity, shot majority, zones or a switch marker alone. any changed population requires rerunning the scientific study.
