# player-card destination and reference evidence

reviewed 2026-09-29 following the user's explicit clarification: replicating hockeyviz's player cards and components, together with jfresh's cards, is the long-term goal. the first target remains completed-season 5v5 skater chance creation and suppression. this is a reference inventory, not a slice plan or a claim that private models can already be reproduced.

the detailed [capability inventory](../product-inventory.md) now separates components, subskills, descriptive cards, goalie cards, context and optional tracking. the user confirmed dedicated goalie cards for later. this page retains the comparative rationale rather than duplicating that checklist.

2026-10-22 amendment: the dated initial-target ordering below is historical. the [full experimental program](../specs/experimental-player-analysis.md) now specifies all selected core player-analysis families together; its numerical and application contracts supersede earlier "later" placeholders. the comparison evidence remains useful, but private parity and scientific support are not inferred from completion.

## supplied-image review and v1 boundary — 2026-10-22

visually inspected all [eight user-selected images](visual-references/README.md), retained their exact bytes and original filename/hash mapping. s01 establishes a compact percentile-tile card with embedded histories; s02 a grouped microstat card; s07 a dense four-map/subskill/component sheet. s04/s08 establish contour, density legend and evidence-inset forms. s05/s06 expose a distinct many-player scatter gap; s03 adds historical population bands. the index records concrete findings and unknowns; no interactive behavior was tested.

the user selected the complete hockeyviz player-card families/components and both jfresh skater cards for v1, with available microstats and explicit inaccessible fields. richer standalone scatters/history bands/context tools can follow. [release checklist](../product-inventory.md#v1-card-completion-boundary--2026-10-22) owns this distinction. no supplied goalie/descriptive-card image closes their remaining field audit. a screenshot's private thresholds, projection or implied attribution cannot become our estimator by copying labels.

the [microstat guide](https://hockeystats.com/about/microstat-player-cards), read for this review, identifies manual tracking and separate skating measures. the [sample field crosswalk](visual-references/README.md#microstat-field-coverage) distinguishes available event facts, independent expected quantities and missing observations. completeness of the v1 format does not establish inaccessible tracking parity. no paid acquisition is assigned.

## visual reference sweep — 2026-10-22

the user requires comprehensive publicly documented player-analysis visual capability. [the visual inventory](../product-inventory.md#visual-coverage-inventory--2026-10-22) owns required rows and delivery status; this page owns reference evidence. this pass re-read public page text/guides below. it did not inspect every image, exercise subscription controls or capture rendered screenshots. retrieved pages include cached older content; access date does not establish current production behavior.

| public reference | evidence from this pass / remaining inspection |
|---|---|
| [hockeyviz isolated guide](https://hockeyviz.com/howto/isolate) | documents spatial panels, skill distributions and a component-value diagram; screenshot geometry and interactions still need inspection |
| [skater career](https://hockeyviz.com/player/matthau97) / [season](https://hockeyviz.com/player/matthau97/TOR/2526) | career lists summaries, histories, subskills and type/danger/breakdown links; season lists shot/context panels, replacements, spider, wowy, deployment and appearances. headings prove panel existence, not complete axis semantics |
| [descriptive guide](https://hockeyviz.com/howto/skaterCard) | explains scoring/workload bars, on/off scatter, shift/score deployment and teammate/opponent groups. its adjusted and multiseason meanings must not be copied onto our unadjusted season results |
| [wowy guide](https://hockeyviz.com/howto/wowy) | distinguishes together, focal-away and counterpart-away rates and exposure; our current focal/group contract does not cover all three populations |
| [goalie career](https://hockeyviz.com/player/helleco93) | lists results, isolated subskills, annual type/danger detail and value; linked images/quantities need their own inspection |
| [jfresh skater preview](https://hockeystats.com/cards/player-cards) | exposes component/context percentiles, history labels, identity/usage/contract metadata and download. preview access does not establish other-player controls or export behavior |
| [jfresh goalie preview](https://hockeystats.com/cards/goalie-cards) | exposes strength/danger, start-quality, rebound/consistency, history and observed/expected-save labels; exact formulas and rendered interactions remain unverified |

finish the bounded sweep using representative skater/goalie and season/career pages, the linked detail images/guides, and public table/comparison/history/export surfaces. pin each distinct view's example url, access/method date and screenshot or image when accessible, plus observed controls and access limits. record actual interaction checks separately from a visible control. inaccessible pages remain unknown; do not infer missing panels or bypass access. existing public-profile references in the inventory remain leads, not newly exercised evidence.

map every distinct panel/form/control to an inventory row, shared equivalent or explicit scope decision. a duplicate visual skin can share one implementation; a different analytical question or population needs its own contract. resolve unknown definitions through [the reference issue](../issues/card-reference-definitions.md); track missing display/interaction contracts in [visual coverage](../issues/experimental-visual-coverage.md). this sweep is specification work, not a scientific prerequisite or a claim of exhaustive private-product parity.

## hockeyviz

the public [isolated-impact guide](https://hockeyviz.com/howto/isolate) combines 5v5 offense/defense maps, power-play offense, penalty-kill defense, finishing, setting, shootiness, penalties drawn/taken, and transition contributions. its synthetic-goals summary places component estimates in a common playing-time context. the example is dated december 2024; linked model descriptions may have newer versions.

the corresponding long-term target is a card whose spatial and skill components can be inspected individually and interpreted together. 5v5 maps begin that path. additional components need their own evidence and valid accounting before being included in a total. a missing component must remain visibly unavailable rather than be replaced by an unlabeled proxy. detailed grid dimensions, smoothing, priors, and adjustment terms are methodological choices to investigate, not adopted merely because a reference uses them.

the [descriptive skater-card guide](https://hockeyviz.com/howto/skaterCard) supplies a separate family of scoring, usage and on/off results. [goalie pages](https://hockeyviz.com/player/helleco93) distinguish observed stopping results, isolated subskills and history. these complement the isolated skater card. public methods span versions: the [2026–27 preview](https://hockeyviz.com/txt/preview2627) announces model rewrites with explanations forthcoming.

## jfresh and the current hockey stats product

jfresh's [2022 explainer](https://jfresh.substack.com/p/2022-nhl-player-cards-explainer) attributes the underlying model to patrick bacon and explains its use of percentiles, component summaries, deployment context, and career plots. it also identifies a cost of percentiles: distances between elite performances can disappear when everything is expressed as rank. the article is historical documentation, not a complete current specification.

the current [hockey stats player-card page](https://hockeystats.com/cards/player-cards) provides a public preview with offense, defense, special teams, finishing, penalties, scoring, teammate/opponent context, percentile histories, and a card-download control. it labels the estimates as three-year weighted data and identifies the comparison cohort. the public [founder overview](https://hockeystats.com/about/overview) identifies both patrick bacon and jfresh. only the public preview and documentation were inspected; subscription interactions were not tested.

the corresponding long-term target is a compact, shareable comparative card with component percentiles, declared cohorts, useful context, and change over time. retain the underlying magnitude and units alongside percentile access, so the reader can distinguish ranking from effect size. do not combine percentile ranks as though they were additive contributions.

semantic correction: the current [official explanation](https://hockeystats.com/about/player-cards) describes a predictive model, including projected scoring rates. our selected-season ability target remains different. borrowing its layout does not authorize relabeling our estimate as projected war. the [goalie preview](https://hockeystats.com/cards/goalie-cards) provides a distinct later reference; several current field definitions remain [unresolved](../issues/card-reference-definitions.md).

## historical initial target, explicit model identity

| capability | destination | initial target |
|---|---|---|
| spatial offensive/defensive influence | hockeyviz-style inspectable rink maps | included for 5v5 skaters |
| broader component profile | special teams, finishing/setting, penalties, tendencies, and transition context | added incrementally after separate validation |
| compact comparative card | jfresh-style component comparison and concise context | visual detail and exact percentile scope specified later |
| historical context | player trajectories with method and time windows visible | not needed to complete the first fixed-season target |
| coherent overall summary | a declared reference and non-overlapping contribution accounting | deferred; first target is not total player value |
| shareable artifact | readable exported card with selection/method context | later product specification determines format and timing |

the chosen scientific direction remains hockeyviz-style interpretability and history-informed ability estimation. replicating card capabilities does not by itself choose patrick bacon's war formulation or make synthetic goals interchangeable with war. if multiple model families are eventually offered, label them and preserve their distinct assumptions. the model behind a card must always be identifiable.

the current expanded contracts supersede the initial target column above. extend the existing architecture's explicit outputs and shared view owners; no abstract universal card engine follows. required reference examples, meanings, data dependencies and acceptance evidence belong in the current program, with missing contracts visible before their implementation.
