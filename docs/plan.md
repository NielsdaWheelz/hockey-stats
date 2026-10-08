# implementation plan

the [brief](brief.md) fixes the product; [architecture](architecture.md) fixes settled system boundaries. this page owns sequencing. detailed decisions live in the linked slice specs and research, not a second specification here. [roadmap](roadmap.md) and [capability inventory](product-inventory.md) retain the later player-analysis destination.

completed and merged: [01 capture](specs/01-capture.md), [02a interpretation](specs/02-interpretation.md), [02b reconstruction](specs/02b-reconstruction.md), [02c corpus](specs/02c-corpus.md), [03a chance workflow](specs/03a-chance-workflow.md), [03b training/assessment](specs/03b-training-acceptance.md), [03c source revision](specs/03c-source-revision.md) and [03d chance revision](specs/03d-chance-revision.md). 03d merged in `af95c88`; [its verification](research/chance-03d/verification.md) establishes software behavior. 03c's [decision](research/chance-03c/decision.md) records the full source audit. 03b's [scientific decision](research/chance-03b/decision.md) remains rejected; completion does not imply scientific support.

## next slices

03e merged in `a8b1de8`; [software verification](research/chance-03e/verification.md) and the bounded study are complete, with a [withheld decision](research/chance-03e/decision.md) and no handoff. [03f](specs/03f-model-development.md) merged in `9c5f3dc`; [its decision](research/chance-03f/decision.md) recommends context interactions and retaining history, with calibration unresolved and no admission. 03g is reviewed and merged in `42e1ef7`; [its decision](research/chance-03g/decision.md) recommends `assess_integrated`, without admission or handoff. **03h is reviewed and merged in `d828085`:** [verification](research/chance-03h/verification.md) records independent reviews and deleted temporary tests; [decision](research/chance-03h/decision.md) is `withheld`. **03i is reviewed and merged in `d3d1b92`:** [verification](research/chance-03i/verification.md) binds the saved diagnosis and review/deletion closure; [decision](research/chance-03i/decision.md) retains its historical avoidance recommendation. the user approved [conversion-first direction and retained features](research/model-direction.md) on 2026-10-08. 03j's full specification is ready for handoff; 03k and 04–07 remain stubs. implementation/fitting and publication require separate assignment.

| slice | responsibility | dependency / completion boundary |
|---|---|---|
| [03e training/assessment](specs/03e-training-assessment.md) | completed bounded development/assessment; `withheld` | all three development recipes failed declared all-attempt calibration; no handoff |
| [03f model development](specs/03f-model-development.md) | completed diagnosis and context/history screen in two observable components | twelve completed cells, two exact reused baselines and ten converged solves; context recommended for research, history ablation not recommended; no admission |
| [03g integration/spatial diagnosis](specs/03g-chance-assessment.md) | completed saved conversion integration and observable spatial diagnosis | no new fits; diagnosis and next recommendation, not a 04 handoff |
| [03h saved-candidate assessment](specs/03h-chance-revision.md) | completed inherited necessary calibration checks on saved overall/own-bin probabilities | one reconciled saved-stream pass; two required failures, `withheld`, no handoff |
| [03i localization/composition](specs/03i-chance-revision.md) | completed revised-bin localization and full/common/standardized spatial diagnosis | one saved pass; negligible composition relief; one proposed avoidance-only experiment, no fit/admission |
| [03j conversion-scale benchmark](specs/03j-chance-experiment.md) | fit two adjustments to saved conversion predictions; january–february fit, march–april assessment with adjustment-refit uncertainty | exact saved 03g rows; diagnostic decision about native revision, no production patch/admission; no feature preparation dependency |
| [03k retained feature repertoire](specs/03k-feature-repertoire.md) | prepare reviewed source-backed families and explicit per-stage selection; retain correct inactive implementations | [inventory](model-features.md); reviewable preparation batches, explicit additional-source dependencies; no real fit campaign |
| [04 player attribution](specs/04-player-attribution.md) | history-informed 5v5 creation/suppression, spatial effects, uncertainty and observed evidence | supported chance-model research handoff; compatible exposure and player robustness across admitted alternatives before publication |
| [05 publication](specs/05-publication.md) | python sqlite export, effect read contract, explicit activation and one rollback database | agreed analytical/view contract; labeled fixture outputs can precede scientific acceptance |
| [06 website](specs/06-website.md) | league table/search, profiles/maps, comparisons and complete-season/game evidence | 05; real analytical release needs supported 03–04 outputs |
| [07 lightweight testing](specs/07-lightweight-testing.md) | tiny lasting integration/live suite using maintained fixtures | stable end-to-end path, before first-product completion; fixture collection already belongs to 03c and subsequent slices |

05–06 can develop against explicitly labeled fixture publications once their shared contract is specified. serving and development remain independent of the hdd; numerical processing remains local. later components get their own specs when selected from the roadmap, not speculative numbered prs now.

## current discussion versus implementation

03i completes general saved-evidence localization: composition supplies little relief and both failed probability bands overpredict broadly. on 2026-10-08 the user approved a change of priority. 03j's full specification is ready for separate implementation/real-execution assignment; a gain selects further native research, not model admission. its later assessment rows and fitting rows are all research-exposed, and new labels provide more recent information than the unchanged model. historical verdicts stand.

03k independently builds the [retained repertoire](model-features.md), including available families with no immediate recipe use. then choose one native experiment from the benchmark and existing evidence; specify its discriminating comparison before fitting. retain 03i's restricted avoidance test and its level/allocation/direct-objective improvements in the [03j backlog](specs/03j-chance-experiment.md#queued-avoidance-experiment). no repeated general diagnosis or automatic ablation matrix.

tradeoffs: conversion scaling is cheap but does not identify a mechanism or validate reference-standardized opportunity. broad retained features cost code/upkeep before predictive value is demonstrated. restricted avoidance cannot change no-recent predictions or conversion and may miss broader spatial underfit. measurement, origin-law and player-conclusion robustness remain separate obligations; 04 concerns supported player claims, not private-model numerical parity.

feature preparation is now an explicit consumer of available source facts; it need not wait for a model to activate a family. additional feeds still require explicit admission, not fallback. coach facts may be admitted in 03k or 04; attribution use remains 04. later goalie/penalty/territorial targets and optional tracking retain their own component contracts. [source evidence](research/source-audit.md) records candidates and limits.

## shared rules and first-product completion

- reuse existing primitives; hard-cut superseded derived contracts without legacy readers or silent fallbacks. preserve source bytes, expensive fits and 03b's historical verdict.
- retain correct source-backed feature implementations when recipes disable them; explicit per-stage selection and refitted ablation follow [the feature policy](model-features.md).
- initial slices use temporary integration/live red/green/refactor checks, then delete test code and test-only dependencies. retain useful fixtures/facts. 07 defines the later lasting suite; scientific assessment tools remain analytical work.
- each full spec names contracts, module owners, verification, content rules and material tradeoffs. no generic importer, model platform, scheduler or release manager follows from this plan.
- publish explicitly: one completed sqlite database, one previous valid database, manual stop/copy/restart. rebuild website code from git.

the first product explains supported 5v5 player contribution with coherent maps/scalars, uncertainty, observed game evidence and visible gaps. it serves without python or the drive. software verification and scientific support must both justify a real analytical release.
