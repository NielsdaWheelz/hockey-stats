# implementation plan

the [brief](brief.md) fixes the product; [architecture](architecture.md) fixes settled system boundaries. this page owns sequencing. detailed decisions live in the linked slice specs and research, not a second specification here. [roadmap](roadmap.md) and [capability inventory](product-inventory.md) retain the later player-analysis destination.

completed and merged: [01 capture](specs/01-capture.md), [02a interpretation](specs/02-interpretation.md), [02b reconstruction](specs/02b-reconstruction.md), [02c corpus](specs/02c-corpus.md), [03a chance workflow](specs/03a-chance-workflow.md), [03b training/assessment](specs/03b-training-acceptance.md), [03c source revision](specs/03c-source-revision.md) and [03d chance revision](specs/03d-chance-revision.md). 03d merged in `af95c88`; [its verification](research/chance-03d/verification.md) establishes software behavior. 03c's [decision](research/chance-03c/decision.md) records the full source audit. 03b's [scientific decision](research/chance-03b/decision.md) remains rejected; completion does not imply scientific support.

## next slices

03e merged in `a8b1de8`; [software verification](research/chance-03e/verification.md) and the bounded study are complete, with a [withheld decision](research/chance-03e/decision.md) and no handoff. [03f](specs/03f-model-development.md) merged in `9c5f3dc`; [its decision](research/chance-03f/decision.md) recommends context interactions and retaining history, with calibration unresolved and no admission. 03g is reviewed and merged in `42e1ef7`; [its decision](research/chance-03g/decision.md) recommends `assess_integrated`, without admission or handoff. **03h is reviewed and merged in `d828085`:** [verification](research/chance-03h/verification.md) records independent reviews and deleted temporary tests; [decision](research/chance-03h/decision.md) is `withheld`. **03i's saved-evidence diagnostic specification is ready for handoff.** 03j and 04–07 remain stubs; implementation/diagnosis and publication require the user's progression decision.

| slice | responsibility | dependency / completion boundary |
|---|---|---|
| [03e training/assessment](specs/03e-training-assessment.md) | completed bounded development/assessment; `withheld` | all three development recipes failed declared all-attempt calibration; no handoff |
| [03f model development](specs/03f-model-development.md) | completed diagnosis and context/history screen in two observable components | twelve completed cells, two exact reused baselines and ten converged solves; context recommended for research, history ablation not recommended; no admission |
| [03g integration/spatial diagnosis](specs/03g-chance-assessment.md) | completed saved conversion integration and observable spatial diagnosis | no new fits; diagnosis and next recommendation, not a 04 handoff |
| [03h saved-candidate assessment](specs/03h-chance-revision.md) | completed inherited necessary calibration checks on saved overall/own-bin probabilities | one reconciled saved-stream pass; two required failures, `withheld`, no handoff |
| [03i localization/composition](specs/03i-chance-revision.md) | localize the two revised failed bins; compare full/common/standardized spatial residuals | one saved pass, no fit or admission; one proposed experiment or explicit insufficiency |
| [03j selected chance experiment](specs/03j-chance-experiment.md) | select one bounded intervention and retain remaining claim-specific assessment | 03i evidence; expand before work; only complete support can supply a conditional handoff |
| [04 player attribution](specs/04-player-attribution.md) | history-informed 5v5 creation/suppression, spatial effects, uncertainty and observed evidence | supported chance-model research handoff; compatible exposure and player robustness across admitted alternatives before publication |
| [05 publication](specs/05-publication.md) | python sqlite export, effect read contract, explicit activation and one rollback database | agreed analytical/view contract; labeled fixture outputs can precede scientific acceptance |
| [06 website](specs/06-website.md) | league table/search, profiles/maps, comparisons and complete-season/game evidence | 05; real analytical release needs supported 03–04 outputs |
| [07 lightweight testing](specs/07-lightweight-testing.md) | tiny lasting integration/live suite using maintained fixtures | stable end-to-end path, before first-product completion; fixture collection already belongs to 03c and subsequent slices |

05–06 can develop against explicitly labeled fixture publications once their shared contract is specified. serving and development remain independent of the hdd; numerical processing remains local. later components get their own specs when selected from the roadmap, not speculative numbered prs now.

## current discussion versus implementation

current: 03g is reviewed and merged; its composed losses improve while calibration/spatial errors remain. [03h](specs/03h-chance-revision.md) is reviewed and merged without rescoring or fitting; [its decision](research/chance-03h/decision.md) withholds the saved composition after conversion bin 3 and all-attempt bin 2 fail required calibration checks. independent statistical, systems and content reviews passed; all temporary tests are deleted. [03i](specs/03i-chance-revision.md) now specifies revised-own-bin localization and a shared month/type spatial comparison. full raw/common-support raw/standardized views distinguish exclusion from weighting. this is the final general saved-evidence localization before one proposed experiment or explicit insufficiency; no cause or remedy is predetermined. [03j](specs/03j-chance-experiment.md) retains the structural backlog and remaining assessment/sensitivity ownership. origin-law sensitivity remains relevant even if observable spatial fit is good. 03i implementation/diagnosis, 03j, 04 and publication are not authorized; 03e's artifacts/verdict and 03b's rejection remain preserved, and the product brief is unchanged.

tradeoff: 03i adds one cheap, finite localization before an expensive repair; it cannot uniquely establish a cause or admit the withheld candidate. fixed composition can leave calendar intervals undefined; disclose that rather than change the target. 03j owns selected intervention/remaining assessment, without an automatic fitting campaign. 04 remains about supported player claims, not numerical parity or proof of every imputed physical origin.

additional inputs belong to the first model/component that requires them. coach admission remains with 04; optional tracking and later goalie/penalty/territorial inputs remain with their own components. [source evidence](research/source-audit.md) records candidates and limits.

## shared rules and first-product completion

- reuse existing primitives; hard-cut superseded derived contracts without legacy readers or silent fallbacks. preserve source bytes, expensive fits and 03b's historical verdict.
- initial slices use temporary integration/live red/green/refactor checks, then delete test code and test-only dependencies. retain useful fixtures/facts. 07 defines the later lasting suite; scientific assessment tools remain analytical work.
- each full spec names contracts, module owners, verification, content rules and material tradeoffs. no generic importer, model platform, scheduler or release manager follows from this plan.
- publish explicitly: one completed sqlite database, one previous valid database, manual stop/copy/restart. rebuild website code from git.

the first product explains supported 5v5 player contribution with coherent maps/scalars, uncertainty, observed game evidence and visible gaps. it serves without python or the drive. software verification and scientific support must both justify a real analytical release.
