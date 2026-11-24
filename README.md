# hockey stats

open the [private player-analysis site](http://127.0.0.1:3000/) on the macbook. choose a skater or goalie, inspect a season, compare two players of the same kind, or download the card and its evidence. the published seasons are 2023–24 through 2025–26.

five card layouts share one local publication. the analytical skater sheet shows where the model assigns offensive and defensive value. the comparative card places seasonal estimates among a named peer group. the goalie sheet shows stopping and subsequent recorded events. the descriptive and microstat cards show supported observations alongside their definitions and coverage. the microstat card marks unavailable tracking fields and includes a separate modeled value strip. [field inventory](docs/product-inventory.md#v1-field-crosswalk-and-card-acceptance) · [delivery evidence](docs/research/application-v1-20/verification.md).

## private observed results

recorded 5v5 results have their own matched counts, minutes and coverage. use the descriptive card, recorded maps or game evidence to inspect them. model estimates describe seasonal level under stated references. the skater headline uses a common workload of 1,000 five-on-five, 100 power-play and 100 penalty-kill minutes. [product choices](docs/brief.md) · [scientific rationale](docs/research/model-direction.md).

## manual cross-version cutover and rollback

the installed application browses its admitted local database with expansion detached. operators can restart the compatible build, preview a candidate and recover the previous publication using the [operator instructions](docs/operations.md). exact file identities, locations and matching git revisions live in [storage](docs/storage.md#serving).

## development

| purpose | owner |
|---|---|
| current status, assignments and sequence | [plan](docs/plan.md) |
| v2 tracks and intended outcomes | [roadmap](docs/roadmap.md) |
| source facts, estimators, publication and application responsibilities | [architecture](docs/architecture.md) |
| numerical inputs and active recipes | [feature repertoire](docs/model-features.md) |
| evidence behind v2, archived decisions and open problems | [release review](docs/research/v1-review.md) · [council](docs/research/council.md) · [release and study evidence index](docs/research/README.md) · [issues](docs/issues/) |
| checked originals and field expectations | [fixture index](fixtures/README.md) |

## chance research review

historical research commands, pinned selections and verdicts stay with the studies. the [v1 command reference](https://github.com/NielsdaWheelz/hockey-stats/blob/9d1b9fa8f77f79730dde112df1316180028fb293/README.md#chance-research-review) is also available offline with `git show 9d1b9fa:README.md`. [chance fixtures](fixtures/chance/README.md) · [historical sources and provenance](docs/legacy/README.md).
