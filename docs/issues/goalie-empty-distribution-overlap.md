# absent goalie distribution text overlaps

the actual season-absent full-sheet png on `63b49e6` overlaps “no finite distribution” with the following cohort/reference text. it occurs in the core rug and all six subskills. `goalieCardSvg` draws the first line at `top+30` but advances its cursor from `top`, placing the next baseline three pixels above that line.

evidence: [independent actual pixel review](../research/application-v1-19/receipts/real-export-pixel-independent-review.json) and the retained absent png/svg under `/Volumes/Expansion/hockey-stats/runs/application-v1-19-20261114-01/real/exports/attempt-03/cases/absent/`. unavailable values and reasons are correct; their text is hard to read.

resolve by advancing from the drawn baseline before rendering the next paragraph, preserving every reason and font size. verify the actual final absent download and the remaining complete sheets after the same-candidate build/start. no numerical or publication work is required.
