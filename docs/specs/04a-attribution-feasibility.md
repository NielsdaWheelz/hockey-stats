# pr04a — attribution feasibility and player-consequence sensitivity

status: **stub; not ready for implementation.** material scope preferences are selected below; population/model/uncertainty contracts still require the full specification. research direction is approved independently of chance-model admission. [plan](../plan.md) owns assignment; [04](04-player-attribution.md) retains supported chance-valued player outputs and release requirements.

scope decisions, 2026-10-14: include historical borrowing now, using all five admitted regular seasons, 2021–22 through 2025–26. fit chronologically with separate annual player effects and borrowing from earlier estimates; later-season observations cannot inform earlier fits. the target season is 2025–26. the user chose closer alignment with the intended ability model over a one-season diagnostic, accepting a five-season fitting chain and additional prior/temporal assumptions and verification. borrowing alone does not establish supported ability.

aging decision: begin with age-neutral borrowing. the preceding estimate supplies the expected level, with additional uncertainty for change between seasons; current-season evidence can move it. no age-based mean trajectory or age-dependent borrowing strength is selected here. the full spec must define innovation uncertainty, skipped seasons, starting/entrant priors and a compatible league-relative reference. this baseline can lag systematic development or decline. retain age facts; age-informed borrowing is an explicit [04 follow-up](04-player-attribution.md#decisions-for-the-full-specification), not discarded capability.

resolution decision: a player-effect contrast equal to **5% of the relevant league-average team rate** is worth trying to distinguish, separately for offense and defense. each recorded-rate benchmark uses its own declared numerator, exposure and league reference; report the corresponding attempts per 60 minutes alongside the relative quantity. this is a product-chosen meaningful contrast, not a guaranteed precision, allowed model error, per-cell threshold or expected-goals/player-value budget. it does not require precise adjacent ranks or every player comparison to resolve. uncertainty, perturbation limits and acceptable distortion remain to specify before assessment.

valuation decision: include one provisional comparison of the final 2025–26 unblocked spatial effects using the existing 03n direct and 03o decomposed transfer fits. keep the entire chronological attribution chain and its priors in attempt-rate units. apply the two valuation functions only after fitting, to the same final-season maps under one shared supported reference. no additional historical chance fits or dependency on 03p results follows.

this is location-only valuation sensitivity: marginalize shot type, preceding context and actors under the common reference rather than expanding the attribution response to recover each player's type/context mix. for q × g, average the product over the same joint reference; do not multiply separately averaged components. reference construction and compatible map valuation are new work, not merely reuse of saved factual predictions. the comparison cannot establish complete chance creation, blocked-origin accuracy, historical forecast performance or error relative to truth. both valuation models remain scientifically unadmitted.

## target behavior

test whether genuine 5v5 stint data support understandable player-rate attribution, then identify which upstream errors materially affect player conclusions. outputs are research benchmarks and sensitivity evidence, not admitted chance-creation ability or a 04 handoff.

start from recorded all-attempt rates for scalar benchmarks and recorded unblocked-coordinate patterns for spatial benchmarks. independently define each numerator and compatible exposure; coordinate absence must not unnecessarily exclude scalar attempts. retain time with no events, both goalies, membership ambiguity and selective coverage. block contacts are not release coordinates.

use synthetic known-effect stints to test recovery, correlated deployment and uncertainty behavior under stated assumptions. real deployment patterns may inform simulation; simulated truth stays labeled. define a small named family of probability/location perturbations to assess changes in player magnitudes, signs, comparisons and maps. the selected saved-model valuation comparison supplements these scenarios; its provisional weights are sensitivity inputs only.

## contract and ownership

inputs: attributable interpreted events, separate event/elapsed membership, aligned exposure, identities/history where selected, saved direct/decomposed transfer artifacts, a declared common valuation reference and simulation/perturbation assumptions. outputs: reconciled benchmark populations, fitted research associations, population-specific scalar/spatial accounting, recovery checks, provisional final-season valuation comparison, sensitivity results and consequences for future admission criteria.

each spatial map must reconcile to its own population-matched scalar. the recorded-unblocked spatial benchmark need not equal the recorded all-attempt scalar benchmark: their numerators and populations differ.

reuse reconstruction, corpus, references and feature primitives. python owns attribution/numerics; no effect-side hockey calculation. a simple explicit estimator is the starting candidate; exact model, regularization, historical borrowing and uncertainty belong to the full spec. no generic attribution framework or new source campaign.

content must distinguish observed counts, recorded-rate associations, simulated effects, provisional chance weights and supported ability. keep the fitted count-rate maps and their post-fit valuations separately identified, with explicit units and populations. sensitivity envelopes are not confidence intervals; simulation/repeatability does not establish physical-origin truth or causal separation. a gap between two imperfect valuation models is not a bound on actual error.

## decisions for the full specification

- freeze the recorded all-attempt scalar and recorded-unblocked spatial benchmarks, five-season corpus selections, event-to-exposure rules, reference, units and treatment of entrants/trades/missingness. do not inherit chance-model exclusions mechanically.
- operationalize the selected 5% recorded-rate contrast: freeze reference populations, units, eligibility and how uncertainty and sensitivity determine which comparisons resolve. define spatial conclusions separately; do not apply a 5% threshold to every cell or transfer it mechanically to chance-valued effects.
- specify one bounded attribution design, controls and synthetic recovery cases. align zero-event time, teammate/opponent exposure and deployment covariates; do not control away mechanisms players should receive credit for.
- predeclare source-stratum probability/location perturbations, bounds and reporting. do not choose tolerances from the residuals or intervals needed to rescue a known failure. close the [consequence-budget issue](../issues/player-consequence-budgets.md) only with attributable evidence.
- bind the existing transfer fits and common valuation reference; specify supported cell/type/context/actor handling and exact post-fit projection. retain the chronological count-rate estimand and unchanged prior units. do not treat different model populations as a matched comparison or silently omit unsupported locations.
- state uncertainty conditioning and which claims the evidence cannot support. an assumption envelope supplies no physical-location accuracy claim.
- assign shared-module changes separately from 03p and select a few relevant lasting checks under [07](07-lightweight-testing.md). keep temporary campaign tests/controllers disposable.

completion: population/exposure and each population-matched map/scalar calculation reconcile; synthetic recovery, declared perturbations and the shared-reference final-season valuation comparison are assessed; remaining identification/source limitations and a concrete next decision are recorded. a failed or inconclusive feasibility result is valid. no rejected model is admitted, no final player card is supplied, and the all-attempt product remains the destination.

tradeoff: this branch begins the actual player question earlier at the cost of provisional outputs, parallel research and shared-reference valuation work. the bounded post-fit comparison avoids a historical chance-fitting campaign while omitting player-specific type/context-mix credit. physical origins, supported chance valuation, player robustness and explicit publication remain separate obligations.
