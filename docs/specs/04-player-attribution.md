# pr04 — season-level player contribution

status: **stub; not ready for implementation.** expand after [03e](03e-training-assessment.md) establishes a supported chance-value contract. [brief](../brief.md) · [architecture](../architecture.md) · [input audit](../research/model-input-audit.md)

## target and boundary

estimate each skater's underlying offensive chance creation and defensive chance suppression across the selected completed regular season, informed by justified historical evidence. publish spatial effects, comparable scalar summaries and supported uncertainty relative to a declared league reference. observed season/game results remain separate. this is genuine 5v5 with both goalies, not total player value or season-end form.

inputs: attributable valued attempts/origin distributions from 03, compatible reconstructed event membership and elapsed exposure, game/season identities, player references and justified history. outputs: explicit player-season estimates, spatial payloads, uncertainty/support, reference/units, coverage, model identity and observed game/season evidence for [05](05-publication.md). unavailable exposure is not zero; numerators and denominators must support the same claim.

python owns attribution and scientific assessment under `analysis/src/hockey_stats/`; reuse reconstruction, corpus, reference and numerical primitives. effect serving owns no duplicate hockey calculation. no public refitting, forecast, replacement-level total or generalized player-model framework.

## decisions for the full specification

- select the spatial attribution model, units, prior-season/aging treatment, regularization and uncertainty claims. correlated deployment limits isolation; prediction checks do not prove causality.
- assess teammate/opponent, home/score/time, rest, shift-start zone and post-penalty context. decide which mechanisms the player should receive credit for: chance context used upstream must not automatically be controlled away again here.
- decide whether coach terms are justified. if 03d has not admitted coaches, evaluate structured `right-rail`, game/coach identity and roster-report corroboration here. do not build both parsers by default. scratch views remain later.
- establish analytical eligibility, selective-gap treatment, historical sufficiency, entrants and traded-player handling. retain team-specific observed evidence without fragmenting the selected season-level ability target.
- specify map-to-scalar accounting, observed game-to-season reconciliation and a meaningful assessment protocol. split implementation and real assessment further only if this selected work warrants it.

completion requires supported claims and coherent output contracts, not merely a converged regression. temporary software checks follow red/green/refactor then deletion; scientific diagnostics and useful artifacts remain. the content designer owns labels that distinguish estimates, observations, reference values and unavailable evidence. richer adjustment costs computation and can change the attribution question; justify each term rather than copy a peer's list.
