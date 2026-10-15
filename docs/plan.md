# implementation plan

this page owns current status, assignment and sequencing. the [brief](brief.md) owns product choices; [architecture](architecture.md) owns system responsibilities; [model direction](research/model-direction.md) owns scientific rationale. [roadmap](roadmap.md) and [capability inventory](product-inventory.md) own the destination. study folders retain exact protocols, decisions and verification.

## current boundary

01–03p are reviewed and merged; 03o merged in `0f863ec`, and 03p in `c0efc7d` through [pr #20](https://github.com/NielsdaWheelz/hockey-stats/pull/20). no model has been admitted and the website is unbuilt. software completion is separate from scientific support. 03b remains rejected, 03e/03h withheld, and [03o](research/chance-03o/decision.md) records `decomposed_direction,no_supported_representation,null,not_admitted`; all six primary intervals cross zero.

on 2026-10-14 the user approved two research tracks: **attribution feasibility and consequence-based sensitivity, alongside one structural chance-model experiment with its numerical check included**. the user subsequently assigned the entire [03p](specs/03p-chance-structure.md) implementation and bounded execution, with adversarial review and temporary red/green/refactor verification, on branch `work/03p-chance-mirror`. the user has now assigned the entire [04a](specs/04a-attribution-feasibility.md) implementation and bounded execution on branch `work/04a-attribution-feasibility`, in a separate worktree, with subagent implementation, adversarial review at each boundary and temporary integration checks deleted after closure. no acquisition, model adoption or publication is assigned.

03p is complete and merged: [its decision](research/chance-03p/decision.md) is `within_budget,nominate_mirror,mirror_y,not_admitted`. four controls replay exactly, all four mirror fits succeed, both assessments reconcile and all eight capped probes pass the specified stability rule. this developmental structure nomination leaves calibration, all-attempt/player claims and historical verdicts unchanged. 04a's matched-population boundary is independently reviewed in `74472db`, its annual model and simulator in `d1f672f`, and native projection in `a053f80`. assessment software and figures are also independently reviewed. protocol freeze, bounded real execution and evidence review follow; no scientific result has yet been accepted.

research-only 04a may precede chance admission. supported chance-valued player outputs still require the relevant probability, measurement and player evidence; 04a cannot supply that handoff merely by completing. 05–06 may separately develop with clearly labeled fixtures. observed-rate benchmarks and fixtures do not replace the agreed all-attempt player product.

## next slices

| slice | owner / output | dependency and unresolved choice |
|---|---|---|
| [04a attribution feasibility](specs/04a-attribution-feasibility.md) | separate matched populations, two five-season annual model chains, synthetic recovery and provisional final-season valuation sensitivity | assigned and in progress; existing five-season corpus/transfer artifacts, external drive for real execution. population → model → projection → real evidence → closure, with independent review at each boundary; no chance-admission or 03p-result prerequisite |
| [04 supported player attribution](specs/04-player-attribution.md) | season-level 5v5 chance creation/suppression, coherent maps/scalars, uncertainty and observed evidence | supported chance inputs and player robustness; learn from 04a without promoting its provisional estimates |
| [05 publication](specs/05-publication.md) | python sqlite export, effect reads, explicit activation and one rollback file | agreed analytical/view contract; labeled fixtures can precede final scientific outputs |
| [06 website](specs/06-website.md) | league table/search, profiles/maps, comparisons and full-season/game evidence | 05; real analytical release needs supported 03–04 results |
| [07 lightweight testing](specs/07-lightweight-testing.md) | a few lasting checks for stable contracts; publication/browser checks added when those boundaries exist | specify selected source/numerical checks with their owning work now; no prerequisite to finish all of 07 first |

03p and 04a share source and numerical primitives but answer different questions. 03p owns constrained chance fitting and its shared component/comparison mechanisms; 04a owns exposure-matched attribution, annual priors and projections. interpretation of chance-weight sensitivity depends on the named weights and their limitations. future claim-based criteria may use 04a's evidence without making it a mandatory precursor to every exploratory chance experiment.

the headline choices were settled before execution: mirror pooling and a 99% predictive-gain retention policy for 03p; the 04a choices below. 03p's frozen evidence retains its exact populations, rules, compute limits and identities. 04a specifies a bounded linear annual model, full player covariance, conditional uncertainty, synthetic recovery and unit stresses. these stresses supply no truth-error bounds. do not invent margins from residuals or intervals a favored model needs to pass.

the 04a interview has selected all five admitted seasons with chronological annual borrowing, an age-neutral starting design, a meaningful recorded-rate contrast of 5% of the relevant league-average team rate, and a provisional final-season valuation comparison using existing direct/decomposed transfer fits. [04a](specs/04a-attribution-feasibility.md) owns the exact choices: the attribution history stays in count-rate units, valuation happens afterward, and the 5% contrast is not an error or chance-value budget. age-informed borrowing is queued within later [04 attribution work](specs/04-player-attribution.md#decisions-for-the-full-specification), after the baseline and before any age-specific claim; no separate aging campaign is assigned now.

the user selected matched spatial exclusion: unusable unblocked coordinates remove affected spatial counts and time together, preserving otherwise valid scalar evidence. 04a therefore has separate population references and explicit selective-coverage limitations. its requested temporary red/green/refactor checks are deleted after verification; no lasting suite is selected for this slice. the broader 07 policy remains unchanged.

## completed studies

| slice | retained result / evidence |
|---|---|
| [01](specs/01-capture.md), [02a](specs/02-interpretation.md), [02b](specs/02b-reconstruction.md), [02c](specs/02c-corpus.md) | raw capture, interpretation, separate event/elapsed membership and corpus/reference admission |
| [03a](specs/03a-chance-workflow.md), [03b](research/chance-03b/decision.md) | workflow and real training/assessment; declared all-attempt use rejected |
| [03c](research/chance-03c/decision.md), [03d](research/chance-03d/verification.md) | source repairs/full three-season audit; revised chance implementation |
| [03e](research/chance-03e/decision.md) | three development recipes fail declared calibration; dependent work stopped, no handoff |
| [03f](research/chance-03f/decision.md) | context interactions improve component losses; history ablation worsens them; no admission |
| [03g](research/chance-03g/decision.md), [03h](research/chance-03h/decision.md), [03i](research/chance-03i/decision.md) | saved integration, withholding and localization; spatial/calibration limitations remain |
| [03j](research/chance-03j/decision.md) | all 6,000 adjustment refits complete; no supported intervention |
| [03k](research/features-03k/verification.md) | full retained local repertoire and sixteen numerical families; software verification, not automatic scientific activation |
| [03l](research/chance-03l/decision.md) | four sequence-comparison fits; mixed direction, conditional intervals cross zero, sequence inactive |
| [03m](research/corpus-03m/verification.md) | external cutover, scoped predecessor disposal, five-season/6,560-game audit and detached verification |
| [03n](research/chance-03n/decision.md) | four fits; expanded history worsens both windows, conditional short nomination for this estimator |
| [03o](research/chance-03o/decision.md) | two exact reused controls/four new fits; tiny decomposed direction, no supported representation or admission |
| [03p](research/chance-03p/decision.md) | four exact reused controls/four mirror fits; both windows retain at least 99% predictive gain under the selected conditional policy and pass bounded numerical sensitivity; developmental mirror nomination, no admission |

these are completed questions, not a queue to rerun. their linked protocols and verification records preserve exact populations, code revisions, artifacts and historical test deletion. the older restricted-avoidance proposal remains a [recorded alternative](specs/03j-chance-experiment.md#queued-avoidance-experiment), not an automatic next fit.

## shared rules and first-product completion

- preserve historical decisions and research exposure. an inconclusive study can complete; a new direction does not erase a failed criterion or supply untouched confirmation.
- retain correct inactive features. the [feature inventory](model-features.md) distinguishes extraction, encoding, population support and actual scientific use. selecting another family requires its own availability/cutoff contract.
- extract mature shared execution, artifact and paired-evaluation helpers when assigned work needs them; leave study-specific rules with each study. no blanket rewrite, historical migration or experiment platform.
- retain explicitly selected fast source/numerical regression checks under [07](specs/07-lightweight-testing.md); delete temporary campaign checks/controllers. preserve original fixtures and scientific tools. no whole-corpus fitting in routine checks.
- keep native local processing, external-only expensive outputs, accepted manual reruns and bounded detached evidence. preserve current-project raw/fits/frozen paths; add no vm, drive-investigation gate, storage framework or runner.
- publish explicitly: one completed sqlite database, one previous valid database, manual stop/copy/restart. rebuild website code from git.
- each full spec names quantities, population, owners, verification, content meaning and material tradeoffs. no generic feature/model framework follows from broad research capability.

the first product explains supported 5v5 player contribution with coherent maps/scalars, uncertainty, observed game evidence and visible gaps. browsing works without python or the drive. software checks, supported analysis and explicit publication remain separate requirements.
