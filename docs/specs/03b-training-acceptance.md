# pr03b — training and scientific acceptance

status: research and specification authorized; implementation, bulk acquisition and fitting not started. [03a](03a-chance-workflow.md) is reviewed and merged. the user chose fresh captures of 2023–24 through 2025–26 after the [external audit](../research/external-corpus-audit.md). [brief](../brief.md) · [plan](../plan.md)

## target and boundary

produce a defensible decision about the existing all-attempt chance model: **supported for a declared use**, **insufficient evidence**, or **rejected**. a completed pr may conclude that the candidate is unsuitable. acceptance does not publish results, validate player attribution or establish hockeyviz parity.

reuse capture, corpus admission, preparation, fitting, evaluation and scoring. add one retained scientific comparison script and repair [evaluation/scoring attribution](../issues/chance-artifact-attribution.md). no legacy importer, new estimator family, grid search platform, scheduler, model registry, website or permanent test harness. changing the likelihood, features or fixed five-foot grid requires a reviewed scientific revision first.

## evidence and operation

use native commands with an explicit root such as `/Volumes/Expansion/hockey-stats/`: `references/<season>/`, `captures/<game_id>/`, `corpora/<run>/<season>/`, `chance/<run>/`. within a chance run, keep `inputs/` (selections/configs/evidence), `fits/`, `assessments/`, `scores/` and `review/` as siblings: existing commands reject outputs inside their input parents. verify the drive is mounted before creating directories; no local fallback or storage discovery service. colima is unnecessary. existing local fixtures and eventual published databases support detached operation. old data remains untouched; this pr does not authorize archive deletion.

1. capture each season's four references with `capture-season`. use `hockey-stats-corpus` against the initially empty game directory to obtain the official inventory. ids come from that inventory, not generated numeric ranges or the old database.
2. capture each inventoried game with the existing five-source command in an ordinary sequential operator loop. expect about 19,680 game requests plus twelve reference requests. stop on command failure and inspect it; retain failed receipts and capture retries into a fresh directory. arrange the selected capture at its required game-id path before admission; never move frozen inputs. no batch service or retry framework.
3. admit through the existing corpus command into new output directories. selected `input_error` and `identity_mismatch` prevent fitting; missing captures and unavailable identities remain explicit gaps. do not omit defective games to evade this contract.
4. inspect season/game/source coverage, eligible and unavailable attempts, reconstructed exposure, location and shot-type semantics. hand-check development examples. apply uniform source-integrity rules to confirmation data without consulting fitted performance. substantial selective gaps require a narrower justified claim or insufficient evidence, not merely a percentage badge.

retain exact selections, configs, source identities, completed fits, assessments and costs outside git. keep the protocol, decision and compact figures in git; link external artifacts by path and hash. fresh acquisition costs another download and changes retrieval dates, but avoids projected legacy inputs and a second admission path. corrected historical captures support retrospective analysis, not an as-of-date forecasting claim.

## chronological design

use regular-season whole games only; 03a preparation owns true-5v5 eligibility. selections have `purpose: research` and use the existing schema.

| stage | fit | assess/use |
|---|---|---|
| development | 2023–24 | 2024–25; choose a small candidate set and protocol |
| confirmation | 2023–24 plus 2024–25, frozen recipe | 2025–26 excluding the three development-exposed fixtures |
| final retrospective fit, only after support | all three seasons | score the selected 2025–26 season; these are not confirmation predictions |

exclude `2025020001`, `2025020006` and `2025021094` from confirmation, even after fresh capture. they have already informed development. they may inform additional development checks and the final fit. confirmation therefore contains at most 1,309 games, with actual admitted coverage reported.

this is one expanding recent-window candidate, not proof of the optimal historical horizon. penalties remain numerically fixed; do not silently rescale them between stages. more data changes their relative strength and the empirical conversion reference. pooling assumes sufficiently comparable seasons and persistent nuisance effects; inspect season/source differences and entrants during development. widening the corpus or changing the target is a new decision, not an automatic response to disappointing results.

use a draft `docs/research/chance-03b/protocol.md` during development; commit its frozen version **before confirmation**. record exact selections/digests, exclusion rules, candidate and benchmark definitions, configs, reference weighting, primary comparisons, material tolerances, supported groups/bins and resampling settings. no unresolved numerical acceptance criteria at this boundary. scientific evidence requires an identified clean analysis revision; preserve failed/rejected development runs where they explain selection.

confirmation cannot choose features, kernels, penalties, exclusions or tolerances. a substantive revision after seeing its results makes those games development evidence; repeated assessment is not fresh confirmation. document that limitation and obtain separately justified evidence before claiming renewed confirmation. [selection-bias research](https://www.jmlr.org/papers/v11/cawley10a.html)

## development and resource limits

first measure preparation, fitting, evaluation and scoring on a deterministic bounded selection of admitted training games. record selection, wall time, peak memory and output sizes. the fixture fit's 184 attempts in 9.605 seconds establishes neither season-scale capacity nor a checkpoint requirement.

start from the existing configuration only as a numerical anchor. investigate a small, named set of existing kernel, origin-prior and penalty alternatives; explain each scientific purpose. do not run an automatic cartesian sweep. specify ranges from development evidence, not the three fixtures or a desired confirmation result.

profile demonstrated costs before optimizing. preserve the estimator while fixing a measured hot path. if a fit's replacement cost warrants recovery, specify a small checkpoint at completed em boundaries/starts with matching input/config/implementation identities before launching costly fits; interrupted inner optimization may restart. no general job engine. record any prerequisite repair in `docs/issues/` rather than concealing it in the research script.

## scientific comparisons and decision rules

**factual probability:** compare unblocked conversion with the saved distance/angle benchmark, and outcome-blind all-attempt prediction with its saved score/role benchmark. standardized reference opportunity values are a different quantity; do not compare them with factual goals as calibrated predictions.

for log loss and brier score, pool per-game sums: `sum(candidate loss − benchmark loss) / sum(attempt count)`. resample games in pairs, recomputing this ratio; never average game means. use 2,000 draws and 95% percentile intervals, recording the numpy generator and fixed seed. if any draw has a zero denominator, that interval is null with an undefined-draw count/reason; never substitute zero, discard draws or redraw until valid. this is sampling uncertainty conditional on the fitted model, using a game-independence approximation. it excludes parameter and latent-origin uncertainty; investigate longer temporal dependence if development diagnostics implicate it.

comparisons require matching game ids, consumed input digests, preparation/prediction definitions and per-game populations/coverage. the within-assessment benchmark shares the candidate population. assessments have no event ledger: establish cross-artifact eligibility equality through identical inputs and the same identified clean preparation implementation, not counts alone or a second reconstruction. regenerate cheap assessments under one revision when needed. incompatible populations are separately named analyses, not paired comparisons.

**calibration:** report predicted-minus-observed rate overall and in the existing fixed probability bins, with counts and game-resampled intervals. lower proper loss does not establish better calibration. predeclare consequential supported bins; sparse bins are unsupported, not successful. show existing subgroup summaries for season, score, role, home/away, stage-specific unseen actors and unblocked shot type. these are aggregate summaries: the current artifacts do not supply per-game subgroup data for clustered subgroup intervals. investigate specific rink/context patterns through bounded additional summaries only when evidence warrants them. [calibration guidance](https://scikit-learn.org/stable/modules/calibration.html)

**origins and values:** compare named alternatives on the same development events, grid and reference definition. freeze a small sensitivity set with the recipe, then refit that fixed set on the confirmation training window and compare on the same 2025–26 confirmation events, without retuning or selecting a new winner. report event-value changes, total values, blocked-origin distribution changes (`0.5 × sum(abs(q₁ − q₂))`) and aggregate spatial opportunity mass, separately for blocked/unblocked attempts. show absolute mass changes as well as shape; do not normalize away changed totals or use separately scaled maps. observed-record likelihood is a same-grid diagnostic, not origin accuracy. distinguish kernel changes, refitting and changed reference weights in calculations and captions.

seek independent blocked-shot evidence, such as attributable replays annotated with location uncertainty. select examples across geometry/source conditions before inspecting fitted maps. record unavailable evidence and selection limits; goal-selected highlights are not a representative blocked-shot sample. masked unblocked locations and plausible geometry cannot establish blocked-origin validity. [hockeyviz's missing-origin discussion](https://hockeyviz.com/txt/xg8) motivates the problem, not our kernel's correctness. unstable or unsupported origins cannot be repaired by silently shipping an unblocked-only product.

the scientific owner freezes material criteria from development precision and hockey meaning, independently of whether the favored candidate passes:

- each primary loss comparison gets a maximum tolerated excess `ε`; use zero if no positive margin is justified. interval upper bound at or below `ε` supports that requirement; lower bound above it rejects; overlap is insufficient evidence.
- calibration gets predeclared symmetric margins and sample-support rules. require the interval to lie within the acceptable region; containing zero alone does not establish adequacy. an interval wholly outside rejects that requirement; boundary overlap is insufficient.
- origin/value sensitivity gets declared practical limits and an explicit evidence judgment. factual calibration cannot overrule unsupported spatial allocation. consequential subgroup failures may narrow scope or prevent acceptance.

the overall decision must address all three claims. missing evidence is not a pass. this protocol deliberately permits insufficient power or an inadequate candidate to stop progress toward 04.

## contracts and files

before research assessments, move the existing executing implementation/dependency identity into all three chance-command outputs, alongside the separate model digest. do not mutate fitted artifacts to claim acceptance; `scientific_assessment: not_performed` still describes what the command itself does. the written scientific decision supplies the judgment.

one entry point, `python research/chance_review.py --evidence /abs/evidence.json --out /abs/newdir`, runs from `analysis/`. it reads saved artifacts and produces comparisons/figures. it does not capture, fit, choose thresholds, publish or issue an automatic verdict.

| input/output | explicit contract |
|---|---|
| `evidence.json` | `schema_version: 1`, `purpose: research`, absolute `protocol` path, `assessments: [{label, path}]`, optional `scores: [{label, path}]`, `resampling: {draws: 2000, seed: integer}`; labels unique within each list; `reference_score` required exactly when scores are supplied and names one supplied score |
| assessment entry | path to an existing 03a evaluation artifact; compare its saved candidate/benchmark metrics; reject fixture-purpose artifacts as scientific evidence |
| score entry | path to `score.json`; verify linked attempts file/hash; require identical ordered selections and lockstep `(game_id, source_index)` keys/statuses; `event_id` may be null; at least two compatible research entries for sensitivity; reject reordered/mismatched streams rather than adding a join engine |
| `comparison.json` | schema 1, executing implementation identity, digests of evidence/protocol/consumed artifacts and their referenced model/selection identities, population definitions, counts, estimates/intervals, calibration/sensitivity results, missing reasons, resampling settings and figure paths |
| failure/output | new output directory only; write final comparison after figures succeed; malformed/nonfinite or incompatible inputs fail visibly; absent evidence remains null with a reason, never zero |

reuse production arithmetic and saved metric sums; do not implement another predictor, eligibility rule or model reader. stream scored rows for sensitivity instead of materializing every event × cell × alternative. use the existing python environment; add a pinned plotting dependency only as needed for the static figures. no generalized schema/experiment framework.

| file/boundary | owner and responsibility |
|---|---|
| `docs/research/chance-03b/protocol.md` | scientist: development choices and frozen confirmation procedure |
| external `chance/<run>/` | operator: selections/configs, fits, assessments, scores, `evidence.json`, comparisons and resource measurements |
| `analysis/research/chance_review.py` | numerical engineer: retained scientific calculations and reproducible figures |
| `analysis/src/hockey_stats/chance_cli.py` | workflow engineer: attribution repair; reuse `artifacts.implementation_identity` |
| `analysis/pyproject.toml`, `analysis/uv.lock`, `README.md` | dependency/operator instructions only where the above work requires them |
| `docs/research/chance-03b/decision.md` and adjacent figures | scientist and content designer: conclusion, evidence, limitations and 04 handoff |

## content and handoff

the content designer owns truthful labels, denominators, units, shared axes/scales and captions explaining what each panel can establish. the decision leads with supported use, insufficient evidence or rejection; then population, reference, cutoffs and exclusions. minimum content: coverage table, paired score table, two calibration panels with counts, common-scale spatial/value sensitivity, and independently attributed origin examples where available. no leaderboard, generic quality percentage or causal claim.

after a supported decision, fit the declared final retrospective model and score 2025–26. its reference is the eligible three-season training mix, not specifically the 2025–26 league average. retain its distinct digest, cutoff and reference weights; compare coverage, convergence and opportunity surfaces with the confirmation fit on the same declared events. withhold the handoff if new instability undermines support. final in-sample results do not replace confirmation. preserve expensive completed work; cheap website builds remain recoverable from git.

04 receives the decision, frozen recipe, confirmation evidence, final model, compatible scored attempts/coverage and consequential sensitivity alternatives. 04 owns player attribution, event/exposure compatibility and downstream map uncertainty. its chronological validation must fit upstream chance models within each permitted training cutoff; using the all-data final chance fit inside earlier folds leaks information.

## completion and verification

1. fresh inventories and every selected game's source/eligibility disposition are attributable; no projected legacy input or fabricated raw receipt enters the corpus.
2. temporary integration checks demonstrate the attribution repair without changing model bytes, mismatched-population rejection, hand-computed pooled comparisons, reproducible paired resampling, and explicit missing/fixture-evidence behavior. red → green → refactor; then delete test code/test-only dependencies. retain scientific scripts, figures and useful facts.
3. real commands and the comparison script run end to end; finite probabilities, existing mass/accounting invariants and declared populations hold. document measured cost rather than extrapolating fixture timing as capacity.
4. the protocol predates confirmation. the decision explains probability performance, origin evidence and sensitivity, including failed requirements. keep the [shot-location issue](../issues/shot-location-evidence.md) open until its evidence criteria are met.
5. supported scope produces the separate final-fit handoff; rejection/insufficiency produces concrete next work in `docs/issues/`. no forced acceptance, publication or archive cleanup.

material limits: three recent seasons restrict historical claims; a small candidate set may miss a better estimator; chronological confirmation sacrifices tuning data; game bootstrap intervals omit fitting/origin uncertainty; the fixed grid and point estimates require downstream sensitivity. tuning values, practical margins and any checkpoint remain empirical development decisions, resolved before their dependent work—not guessed now and not delegated to a preference poll.
