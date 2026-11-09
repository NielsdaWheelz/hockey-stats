# final spatial probes: bounded saved-review proposal

status: source/protocol proposal only. no helper implemented or changed; no actual or fixture artifact opened, import executed or numeric call made. final producer and existing helpers remain frozen. root separately releases implementation and, after producer exit/canonical validation, any actual saved check. [specification](../../../specs/v1-08-positive-attribution.md#numerical-resolution-and-measured-cost) · [annual saved-history scope](real-spatial-history-audit-protocol.md) · [prior fixture proofs](independent-review.md#proofs)

the smallest useful addition is one temporary final-year saved checker, reusing `unpack`, `check_reference`, `rates`, `compare_rate` and ordered-array digest primitives. it would bind probe evidence and independently reduce all cheaply available standardized movements. it would not call the annual audit, production comparison, reader or evaluator. the existing tiny integration/fixture tools contain fit/strict-reader paths and must not be rerun. their mathematical evidence remains historical.

## prospective reads and bindings

read only the root-pinned final manifest, `annual-baseline-manifest.json`, `probes/baseline.json`, `probes/rows.json`, `probes/requirements.json`, three ordinary head json/npz pairs, current `reference.json` and `projections.jsonl`, and each probe's metadata, coefficient npz, comparison and projection jsonl/npz. rehash these small standalone members. select only `basis.npy` from `design.npz` and `rates.npy` from ordinary `projections.npz`; do not hash or load either full archive. probe projection archives contain only rates and can be rehashed/read one at a time. retain canonical-validation ownership of the two partially read archives, with selected-array digests and semantic checks reported separately.

require the annual baseline's immutable manifest fields to match final state fields, excluding only `files/resources`, and its member records to remain an unchanged subset. independently reproduce the baseline descriptor's canonical-json head-metadata hashes and ordered coefficient digests. verify complete head identities, unchanged prior inputs except recomputed `prior_mean`, packed age coordinates/conditional profiling, saved centers/reference and the prescribed continuation controls; no new gradient gate. preserve incomplete continuation evidence without attempting to qualify an endpoint.

report coefficient maximum/l2 movement between the saved completed baseline and probe vectors, including age coordinates and conditional prior-only completion. these are completed endpoint movements, not a reconstructed raw native step or movement attributable solely to the optimizer. retain native iterations/evaluations/termination and differences of saved likelihood/penalty/total components as descriptive evidence. do not recompute an objective or introduce a movement, improvement or gradient threshold.

check frozen row uniqueness/order, the at-most-256 bound, player/role/kind identities and requirements dispositions/first witnesses within that saved selection. do not claim to prove global first-key selection, complete population coverage or `no_matching_context` from saved keys alone: canonical `select_probe_rows` owns those full-design claims. no reselection occurs. verify every saved context locator belongs to the frozen selected row and has the correct coordinate dimensions/ranges.

## actual comparison inventory

frozen `compare_probe` emits **thirteen** numeric maxima per head, plus `status/reason/maxima/failures` containers. the later fixture review's fifteen replayed table values are five quantities across three heads; historical “15 maxima” prose is not the current schema. enumerate the source's actual names:

| field | independent saved replay | fixed limit |
| --- | --- | --- |
| `standardized_shape_probability` | raw coefficients, centers, offsets and basis; all roster roles/cells | `1e-5` |
| `neutral_shape_probability` | same, neutral reference | `1e-5` |
| `standardized_quality_probability` | same, independent sigmoid arithmetic | `1e-5` |
| `neutral_quality_probability` | same, neutral reference | `1e-5` |
| `standardized_scalar_per_hour` | signed native sum of changed minus baseline saved rates | `1e-4` |
| `standardized_native_map_l1` | native sum of absolute rate differences | `1e-4` |
| `prospective_1000_minute_goals` | contrast xg native sum multiplied by `1000/60` | `1e-3` |
| `shape_probability` | saved magnitude/locator only; actual-context predictor unavailable | `1e-5` |
| `quality_probability` | saved magnitude/locator only; actual-context predictor unavailable | `1e-5` |
| `coalition_scalar_per_hour` | saved magnitude/locator only; sixteen actual-context coalitions unavailable | `1e-4` |
| `coalition_native_map_l1` | same limit of evidence | `1e-4` |
| `allocation_scalar_per_hour` | saved magnitude/locator only; actual-context coalition inputs unavailable | `1e-4` |
| `allocation_native_map_l1` | same limit of evidence | `1e-4` |

for the seven replayable maxima, preserve roster/role/quantity/kind/native-cell order and first c-order argmax ties. independently regenerate standardized maps/scalars for all three variants using the accepted primitive and existing projection tolerances, then reduce the saved rate arrays directly. shape/quality probabilities need a small explicit softmax/sigmoid calculation, since the saved rate archives contain no probability arrays. record replay/saved discrepancies and any rounded tie; retain the original movement limits without adding a tolerance that rescues a threshold crossing.

the six actual-context quantities cannot be replayed from `rows.json` and maxima: `_probe_contexts` needs the selected factual dense context plus actor design, and saves no per-context predictor/coalition/allocation arrays. reading full context/csr or reconstructing source features would exceed this proposal. check their finite nonnegative values, exact limits, locator membership/ranges and reported failure consistency, clearly labeling magnitudes as saved canonical evidence. a failed context comparison can have many per-row failure entries; do not claim to reconstruct that list from its global maximum. `status/reason/failures` must agree with completion and reported limit crossings. actual maxima remain supported by the producer's canonical `_validate_probes` replay, frozen source, prior tiny/captured-fixture arithmetic and [first-real bounded direct-24 allocation proofs](real-first-spatial-saved-review.md), not a new independent real-context replay. the explicit tradeoff is retaining those owners for six actual maxima while adding cheap independent evidence at the immutable-baseline and standardized-rate boundary; there is no present concrete concern justifying a new full-design load.

## release and output

implementation, if approved, should be one direct study script with explicit field inventory and reductions; no runner or new framework. it needs no production imports, fit, objective, gradient, full state reader, source pass, full context/csr, actual adjustment/allocation or extra solver. no repeated fixture/source/math campaign is proposed. a later separately released single saved invocation would use fresh external output/log/true-exit records, bind all inputs/code, retain measured cost and distinguish seven independently replayed maxima from six canonical-only magnitudes. the ordinary final-year history audit remains separate. root owns numerical/annual acceptance and any successor release; this proposal grants neither.
