# player-card destination and reference evidence

reviewed 2026-09-29 following the user's explicit clarification: replicating hockeyviz's player cards and components, together with jfresh's cards, is the long-term goal. the first target remains completed-season 5v5 skater chance creation and suppression. this is a reference inventory, not a slice plan or a claim that private models can already be reproduced.

## hockeyviz

the public [isolated-impact guide](https://hockeyviz.com/howto/isolate) combines 5v5 offense/defense maps, power-play offense, penalty-kill defense, finishing, setting, shootiness, penalties drawn/taken, and transition contributions. its synthetic-goals summary places component estimates in a common playing-time context. the example is dated december 2024; linked model descriptions may have newer versions.

the corresponding long-term target is a card whose spatial and skill components can be inspected individually and interpreted together. 5v5 maps begin that path. additional components need their own evidence and valid accounting before being included in a total. a missing component must remain visibly unavailable rather than be replaced by an unlabeled proxy. detailed grid dimensions, smoothing, priors, and adjustment terms are methodological choices to investigate, not adopted merely because a reference uses them.

## jfresh and the current hockey stats product

jfresh's [2022 explainer](https://jfresh.substack.com/p/2022-nhl-player-cards-explainer) attributes the underlying model to patrick bacon and explains its use of percentiles, component summaries, deployment context, and career plots. it also identifies a cost of percentiles: distances between elite performances can disappear when everything is expressed as rank. the article is historical documentation, not a complete current specification.

the current [hockey stats player-card page](https://hockeystats.com/cards/player-cards) provides a public preview with offense, defense, special teams, finishing, penalties, scoring, teammate/opponent context, percentile histories, and a card-download control. it labels the estimates as three-year weighted data and identifies the comparison cohort. the public [founder overview](https://hockeystats.com/about/overview) identifies both patrick bacon and jfresh. only the public preview and documentation were inspected; subscription interactions were not tested.

the corresponding long-term target is a compact, shareable comparative card with component percentiles, declared cohorts, useful context, and change over time. retain the underlying magnitude and units alongside percentile access, so the reader can distinguish ranking from effect size. do not combine percentile ranks as though they were additive contributions.

## common product, explicit model identity

| capability | destination | initial target |
|---|---|---|
| spatial offensive/defensive influence | hockeyviz-style inspectable rink maps | included for 5v5 skaters |
| broader component profile | special teams, finishing/setting, penalties, tendencies, and transition context | added incrementally after separate validation |
| compact comparative card | jfresh-style component comparison and concise context | visual detail and exact percentile scope specified later |
| historical context | player trajectories with method and time windows visible | not needed to complete the first fixed-season target |
| coherent overall summary | a declared reference and non-overlapping contribution accounting | deferred; first target is not total player value |
| shareable artifact | readable exported card with selection/method context | later product specification determines format and timing |

the chosen scientific direction remains hockeyviz-style interpretability and history-informed ability estimation. replicating card capabilities does not by itself choose patrick bacon's war formulation or make synthetic goals interchangeable with war. if multiple model families are eventually offered, label them and preserve their distinct assumptions. the model behind a card must always be identifiable.

the next architecture should accommodate adding analytical outputs through explicit contracts. this destination does not justify implementing an abstract universal card engine or the entire model catalogue now. when a component becomes the next target, pin its reference example, intended meaning, data requirements, and acceptance evidence before implementing it.
