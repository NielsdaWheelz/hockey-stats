# repeated method notes in history exports

## problem

the shared selected-field svg/png export repeats json-shaped method limitations and findings for each annual record. findings substantially repeat the limitations, obscuring the distinctions between years. the responsible owner is the [shared history/export renderer](../../app/src/web/analysis-history.tsx), rather than a goalie-specific renderer.

## impact

the output is cumbersome to read and compare. the one inspected real goalie png is long but legible and complete against the supplied [v1-07 content contract](../specs/v1-07-goalie-continuation.md#content-contract-and-acceptance); no clipping or contradictory claim was visible. that contract sets no arbitrary height budget, so repetition alone is an explicit editorial tradeoff rather than a demonstrated v1-07 blocker. this review establishes neither all-image acceptance nor resolution of the separate network-guard rejection. compact full-card composition remains separate v1-19 work.

## evidence

the inspected download is [the three-season stopping history png](/Volumes/Expansion/hockey-stats/runs/goalies-v1-07-20261108-01/real/acceptance-final-g-st-01/browser-03/003-normal-goalie.ev.stopping_goals_per100_on_net.png), 1200×6385. each annual section repeats long limitations/findings arrays. raw values and units, annual cohorts, support, method, conditioning and assessed/unassessed sensitivity remain visible; the footer disclaims confidence or ability separation from percentiles.

## resolution criteria

the shared history/export owner presents repeated caveats once where their applicability is unchanged, in readable prose. retain meaningful unique caveats and every annual distinction in support, conditioning, reference and sensitivity. verify the affected selected-field svg/png with actual downloads: all required content remains legible, correctly associated with its year and unclipped. no fixed height target or compact-card redesign is implied.

## implementation and remaining proof

v1-10's shared owner now renders support reasons and uncertainty as readable text, converts interval bounds to display units once, and groups identical note text with its applicable years. distinct caveats, annual sensitivity, support, conditioning, references and uncertainty remain separate. [bounded mechanism/goalie renderer controls](../research/mechanisms-v1-10/product/history-human-text-controls.json) pass; csv structured evidence remains unchanged.

this issue remains open. actual final real mechanism and goalie svg/png downloads must still prove legibility, complete caveats and correct annual association under the integrated application. temporary renderer controls and earlier fixture downloads do not close that criterion.
