# pr03o — observable conversion decomposition

status: **stub; queued, not ready for implementation.** previously selected after merged 03l (`2bf0e7c`); now follows review of [03m historical admission](03m-historical-corpus.md) and [03n history comparison](03n-history-comparison.md). those results inform the training horizon; neither improvement nor final model admission is a prerequisite for reconsidering this challenger. full specification and implementation/execution assignment remain separate. [plan](../plan.md) · [direction/council](../research/model-direction.md) · [03l decision](../research/chance-03l/decision.md)

## question and selected comparison

does separately modeling recorded net-hitting and scoring improve later goal probabilities and explain conversion errors, compared with the improved direct-conversion model?

`p(goal | unblocked, x) = p(on_net | unblocked, x) × p(goal | on_net, x)`

`x` denotes the same pre-outcome evidence at assessment; the observed outcome defines training labels/applicability, never prediction inputs or product gating.

- baseline: current improved direct conversion with `game_additive,recent_additive,recent_interactions`, historical actor borrowing and existing geometry.
- candidate: two native binary components, on-net versus missed on eligible unblocked attempts; goal versus saved on eligible on-net attempts.
- both use the complete source-eligible unblocked experimental population. stage-specific training applicability is explicit; no sequence-completeness filter or changed source eligibility.
- prove the mapping from existing `source_event.type_key` and `feature_facts.outcome.values.on_net` to labels/masks. preserve observed/inferred meaning, source identities and unavailable evidence. actual outcomes select training labels/masks, never prediction inputs.
- predict both candidate components for every applicable unblocked assessment row and compare their product with the direct baseline on identical keys. do not use the observed on-net result to gate the goal prediction.

retain current geometry, improved immediate context and historical structure; choose one explicit training horizon after 03n, not a horizon × layer matrix. exact stage designs/actor treatment and penalty/reference mapping belong in the full spec. plan six solves: direct baseline plus two candidate components in each existing development/season-transfer window. an exactly compatible 03n control may be reusable only if its frozen inputs, design, numerical contracts and assessment meet this protocol; otherwise fit fresh. the sequence-selected 03l baseline is not a full-population control. existing assessment seasons remain research-exposed.

## boundary and evidence

composed goal proper loss/calibration is the fair primary comparison; per-stage diagnostics locate errors. retain brier, predicted mass, exact applicability denominators and paired conditional game/calendar assessment. the full spec freezes criteria and numerical limits before fitting. a negative/inconclusive result completes developmental research, without admission or automatic integration.

reuse the native encoder, binomial objective/penalties/optimizer, component artifact/quantity contracts, source/cohort accounting and report/resampling primitives. extend explicit quantities/masks; do not build a generic layer engine or duplicate numerics. supported inactive features, including sequence, remain implemented.

no acquisition/hdd dependency, new contextual family, altered geometry/type treatment, freeze/rebound/setter inference, blocked-origin integration, joint em, automated matrix, player estimate or publication. [xg8](https://hockeyviz.com/txt/xg8) motivates decomposition; this two-layer challenger is not its full four-layer model or evidence of current private parity.

## full-spec obligations and costs

settle exact label/applicability contracts, separate stage predictor/actor/penalty meanings, schemas and consumers, dated selections/input identities, paired metrics/intervals, prospective decision/stop rules, measured capacity, manual commands and content. require independent statistical/systems/content challenge. temporary fixture integration/live red → green → refactor → green checks are deleted after verification; retain original failure bundles, facts and scientific tools under the existing policy.

more coefficients and up to six solves buy separate observable targets; compounded probabilities may worsen goal prediction. this is a structural challenger, not a promised calibration repair or a direct measurement of player ability. no automatic execution or generic infrastructure follows.

leading alternative: mirror-pool conversion geometry at the current resolution, sacrificing genuine left/right variation for support. keep it queued, with original penalized-objective meaning preserved; do not combine it with this experiment or schedule it automatically. broader source/measurement and all-attempt opportunity sensitivity still precede supported player claims in 04.
