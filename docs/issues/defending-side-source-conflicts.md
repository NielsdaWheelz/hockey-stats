# conflicting defending sides leave a whole game’s frame unresolved

status: open; independent frame-provenance follow-up from 03b.

in fresh capture `2023020078` (nyr at sea, 2023-10-21), the raw `homeTeamDefendingSide` field reports both sides in every period: period 1 has 51 left / 55 right records, period 2 has 47 / 48, and period 3 has 49 / 49. these are repeated within-period transitions, not missing coordinate fields.

the reviewed reconstruction contract rejects an entire period’s frame when its explicit sides conflict. all 98 timed attempts therefore have `unresolved_frame` with `period reports conflicting defending sides`; preparation retains 86 unavailable and 12 outside 5v5, with no eligible attempts. score accounting is supported. this is a source conflict with the period-frame invariant, faithfully rejected by reconstruction.

[clean raw receipts, transitions, exact guards and preparation counts](/Volumes/Expansion/hockey-stats/chance/03b-20260930/inputs/development-whole-game-exclusions-clean.json) were verified at clean revision `6a0f6de2073d515921c9533fd58787a43d7234b7`; artifact sha256 `f3ff1a108203f974ef68cc16edb650846075049f39abda049572131ec8e909f8`. the captures alone cannot establish whether the side field is wrong or the coordinates use another convention. neither a physical direction nor a correction is justified.

the next owner is source semantics/provenance research, followed by reconstruction’s frame contract. resolution requires independent evidence establishing the recorded coordinate frame for affected events, a reviewed strict interpretation, and verified readmission/preparation. preserve the conflicting captures and existing exclusions; do not infer sides from period parity, shot majority, or zones. any changed population requires rerunning the scientific study.
