# research and delivery evidence

start with the [post-v1 review](v1-review.md) for findings and comparisons, [model direction](model-direction.md) for the limits of the evidence, or the [plan](../plan.md) for current work. a study's decision, protocol and receipts retain the population, recipe and verdict of that study. a later delivery can exercise a previously deferred journey while the original result remains part of the record.

## v1 delivery

| released boundary | implementation contract | evidence to open first |
|---|---|---|
| shared event and elapsed evidence | [01](../specs/v1-01-shared-evidence.md) | [five-season reconciliation, coverage and preparation cost](evidence-v1-01/verification.md) |
| dated head coaches | [02](../specs/v1-02-dated-coaches.md) | [source evidence and reported roles](coaches-v1-02/verification.md) |
| factual card reductions | [03](../specs/v1-03-factual-card-reductions.md) | [real three-season facts](facts-v1-03/real/verification.md) |
| public skating source | [04](../specs/v1-04-skating-source-feasibility.md) | [feasibility limit](skating-v1-04/verification.md) · [deferred follow-up](skating-v1-04-follow-up/source-audit.md) |
| execution base and scoring | [05](../specs/v1-05-execution-base.md) · [06](../specs/v1-06-execution-scoring.md) | [original annual fits](execution-v1-05/verification.md) · [original scoring](execution-v1-06/verification.md) · [corrected five-season chain](spatial-v1-08/receipts/real-final-score-completion.json) |
| goalie continuation | [07](../specs/v1-07-goalie-continuation.md) | [numerical and integrated evidence](goalies-v1-07/verification.md) |
| positive 5v5 attribution | [08](../specs/v1-08-positive-attribution.md) | [source and fit](spatial-v1-08/verification.md) · [volume sensitivity and experimental use](spatial-v1-08/experimental-use-decision.md) |
| special teams | [09](../specs/v1-09-special-teams.md) | [physical states, projections and limitations](spatial-st-v1-09/verification.md) |
| penalties and shootiness | [10](../specs/v1-10-penalties-shootiness.md) | [source, numerical and integration receipts](mechanisms-v1-10/verification.md) |
| territory and successor value | [11](../specs/v1-11-territory-successor-value.md) | [proxies, hazard sensitivity and publication](territory-v1-11/verification.md) |
| value ledger | [12](../specs/v1-12-value-ledger.md) | [common workload, depth members and missing totals](value-v1-12/verification.md) |
| publication and shared views | [13](../specs/v1-13-typed-publication.md) · [14](../specs/v1-14-history-cohorts-exports.md) | [typed publication](publication-v1-13/verification.md) · [history, cohorts and exports](application-v1-14/verification.md) |
| comparative and descriptive cards | [15](../specs/v1-15-comparative-card-discovery.md) · [16](../specs/v1-16-descriptive-card-context.md) | [comparative](application-v1-15/verification.md) · [descriptive and source-backed fixture](application-v1-16/verification.md) |
| microstat and analytical skater cards | [17](../specs/v1-17-microstat-cards.md) · [18](../specs/v1-18-analytical-skater-sheet.md) | [microstat](application-v1-17/verification.md) · [analytical sheet](application-v1-18/verification.md) |
| goalie sheet and discovery | [19](../specs/v1-19-goalie-card-discovery.md) | [sheet, comparison and native exports](application-v1-19/verification.md) |
| whole-card closure and delivery | [20](../specs/v1-20-whole-card-closure.md) | [dispositions, real exports, costs, failed switches, rollback and accepted localhost switch](application-v1-20/verification.md) |

## studies and sources

| question | records |
|---|---|
| what do the sources, reports and elapsed lineups support? | [original reconstruction audit](source-audit.md), [season references](corpus-reference-audit.md), [five-season corpus](corpus-03m/verification.md), [02d exposure correction](source-02d/decision.md) and the [fixture evidence index](../../fixtures/README.md) |
| how were the earlier chance models assessed? | [03b](chance-03b/decision.md), [03c](chance-03c/decision.md), [03d](chance-03d/verification.md), [03e](chance-03e/decision.md), [03f](chance-03f/decision.md), [03g](chance-03g/decision.md), [03h](chance-03h/decision.md), [03i](chance-03i/decision.md), [03j](chance-03j/decision.md), [03k features](features-03k/verification.md), [03l](chance-03l/decision.md), [03n](chance-03n/decision.md), [03o](chance-03o/decision.md) and [03p](chance-03p/decision.md) |
| what evidence bears on separating players and predicting rates? | the [scientific decision index](model-direction.md) links the 04a–04o questions, including adequacy, known-truth recovery, deployment information, annual borrowing and held-out recorded rates |
| what was the foundation for observed cards? | [05a](observed-05a/verification.md), [05b](observed-05b/verification.md), [05c](observed-05c/verification.md), [05d](observed-05d/verification.md), [05e](observed-05e/verification.md), [05f](observed-05f/verification.md), [05g](observed-05g/verification.md) and [05h](observed-05h/verification.md) |
| where did the desired fields, charts and designs come from? | [public method/input audit](model-input-audit.md), [reference inspection](player-card-references.md), [eight supplied images](visual-references/README.md), [current field and view inventory](../product-inventory.md) |
| how did earlier decisions change? | [council history](council-through-v1.md), [storage consolidation](storage-consolidation-20261118/verification.md), [frozen legacy source manifest](../legacy/README.md) |

## reading older evidence

the preparation writer hashes the exact bytes at the [v1-01 specification path](../specs/v1-01-shared-evidence.md) into its policy identity. moving or editing that file changes a numerical input contract. see the [writer](../../analysis/src/hockey_stats/analysis_data.py).

dated plans and operating instructions remain available with `git show 9d1b9fa:<path>`. a file/line reference can require the producer's git revision. absolute local evidence links use the original machine. the [storage guide](../storage.md#historical-input-locators) explains how to resolve a relocated input and where the retained files live. some checks intentionally removed their controllers, scratch paths and old runtimes after saving evidence.

- the two 03e biography citations open a [historical pointer](../issues/historical-bio-dating.md) to the exact note and the verified 03k interpretation.
- the [historical spatial-checker issue](https://github.com/NielsdaWheelz/hockey-stats/blob/30874973fb62ee9736a677293121a3d43d7658be/docs/issues/spatial-history-audit-bindings.md) and its [second saved review](spatial-v1-08/reviews/real-spatial-history-20222023-02-saved-review.md) explain the retired checker link. the surviving [actual-context issue](../issues/spatial-actual-context-extremes.md) is the destination of the short relative path in the historical disclosure review.
- the four disposable v1-08 operator paths are recorded in the [fixture preparation](spatial-v1-08/receipts/replacement-final-first-fixture-preparation.json) and [runtime release](spatial-v1-08/receipts/real-detached-runtime-release.json) receipts. read v1-10 source line locators against [the recorded source](https://github.com/NielsdaWheelz/hockey-stats/tree/17263785fe2a72dc3ac9e10485db5cae766376c3).
- the 03a specification's original [fixture exercise](https://github.com/NielsdaWheelz/hockey-stats/blob/9b4c37aad4b01134637ba1fce3b6a67249e37c88/fixtures/chance/README.md#software-verification-record--2026-09-29) predates the current chance fixture index. the v1-13 foundation fixture and [v1-16 coherent expectations](../../fixtures/publication-v1-16/README.md) retain their separate uses. the [former fixture issue](https://github.com/NielsdaWheelz/hockey-stats/blob/9d1b9fa8f77f79730dde112df1316180028fb293/docs/issues/descriptive-fixture-consistency.md) records the original discrepancy.
