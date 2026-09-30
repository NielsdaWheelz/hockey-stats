# pr03d — revised chance model

status: **stub; not ready for implementation.** this reserves a review boundary, not a selected estimator or permission to fit the real corpus. expand after [03c](03c-source-revision.md) settles source contracts and reports revised coverage. [plan](../plan.md) · [input audit](../research/model-input-audit.md)

## purpose and inherited meaning

revise the existing chance workflow to produce defensible candidate opportunity values and spatial allocations for genuine 5v5 attempts, including blocked attempts through origin distributions. 04 will estimate season-level player creation/suppression from scientifically supported values and compatible exposure. this slice does not estimate those player effects.

the [03b rejection](../research/chance-03b/decision.md) remains unchanged. its failures motivate a new candidate; they do not prove that every public-method feature is necessary or that adding shot type repairs calibration. all three studied seasons are exposed development evidence. fixtures establish software behavior, not scientific support.

## ownership and boundaries

| existing home | owned work |
|---|---|
| `chance_data.py` | selected feature derivations, analytical eligibility, attributed actor/location/modifier handling and missingness |
| `chance.py`, `shot_origins.py` | one coherent revised estimator, benchmarks, origin distributions and explicit reference valuation |
| `chance_evaluation.py`, `chance_cli.py` | predictions, comparable diagnostics, saved-artifact validation and existing fit/evaluate/score commands |
| interpretation/reconstruction source owners | additional facts only when the selected candidate requires them; no duplicate parser inside model preparation |

inputs are attributable 03c corpus/envelopes, references, selections and configuration. outputs are a reviewed numerical contract, revised workflow/artifact definitions and labeled fixture examples with verification evidence. reuse the current modules and local batch operation. real training and scientific judgment belong to [03e](03e-training-assessment.md); publication, player attribution and later card components remain separate. no parallel modeling platform, universal feature store or presumed tracking dependency.

## decisions before a full specification

- give each relevant [input family](../research/model-input-audit.md) an include, assess or omit disposition with reasons. prioritize demonstrated measurement problems and plausible mechanisms; do not turn the comparison table into a mandatory feature list.
- define the physical event/population being valued: reconciled types, own/awarded goals, tip-location proxies, missing evidence and any preceding-attempt linkage. separate credited scorer from physical actor without inventing either.
- specify selected context's information timing and availability across outcomes. distinguish predictors, outcome labels and retrospective reconstruction evidence; missingness cannot silently encode the outcome being predicted.
- settle the coherent likelihood, type/context/origin dependence, numerical fitting, regularization, history treatment and benchmarks. name remaining empirical choices for 03e rather than inventing validated constants.
- distinguish factual probabilities from standardized opportunity. define the averaging population and operation, spatial accounting, and what 04 should attribute rather than control away. conditional origin estimates are not verified physical locations; interpretable coefficients are not causal isolation.

completion means the reviewed workflow implements those contracts, preserves provenance and missingness, and passes meaningful temporary integration/numerical checks. delete temporary test code afterward; retain useful fixtures and scientific evaluation routines. completion permits assessment, not a supported model claim. the tradeoff is explicit: richer conditioning costs computation and changes interpretation; justify that cost before implementation.

content design owns command/artifact labels distinguishing fixture verification, factual probability, standardized opportunity and conditional origins; scientific owners define those quantities.
