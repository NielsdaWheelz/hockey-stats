# 03j conversion-scale benchmark protocol

status: implementation and the complete benchmark authorized on 2026-10-08. frozen before any real adjustment fit; executing revision and verification identities are bound below. the final executing copy is external to git/worktrees. [specification](/Users/nnandal/Documents/code/hockey-stats-03j/docs/specs/03j-chance-experiment.md).

## purpose and inputs

test the later-window predictive value of one unpenalized two-parameter adjustment to saved factual unblocked conversion probabilities. the result selects a research priority; it neither admits a model nor authorizes an opportunity correction, native follow-on fit, 04 or publication. historical 03b rejection and 03e/03h withholding remain unchanged. 03h/03i are interpretive context, not runtime inputs. the runtime 03g parent's `scientific_assessment: not_performed` remains separately identified.

start at `/Users/nnandal/Documents/code/hockey-stats-03g-runs/diagnosis/completion.json`. use existing `chance_assessment.load_evidence`, `FROZEN_DIGESTS` and one `reconstruct(..., diagnostic=collector)` call. hash the whole stream during that single pass and reconcile all revised quantities, native bins, games and coverage before any adjustment fit. no acquisition, raw/fitted-parent reopening, preparation, base-model fitting/prediction or population intersection.

| input | sha256 |
|---|---|
| completion | `8f4e098acb1b9b8ece3a989beb5e6a6d631d8ac32e3f7402923b59425d78080b` |
| comparison | `e2d825297f5dd5a02871595a101d4a458a1c0546742f1acb9c8068a9f51e5e3c` |
| composition | `d9c5f3773dfcb803cc7bcd3d41fd0c90025282247bfd3ffcc698eed13040a6d9` |
| attempts | `2830f700f4304c24da332cc34467670b9970f66f7d18de6791d8ca74754daca9` |

## populations and numerical model

training ends 2024-12-31. preserve all 712 selected games, including zero-contribution games, in date/id order. reconcile 85,317 recognized rows: 68,775 eligible, 16,270 outside scope and 272 unavailable; eligible outcomes are 49,014 unblocked, 19,761 blocks and 2,804 goals. only eligible unblocked rows enter the adjustment.

| inclusive window | selected games | unblocked attempts | goals |
|---|---:|---:|---:|
| adjustment fit, 2025-01-01–2025-02-28 | 346 | 23,987 | 1,332 |
| assessment, 2025-03-01–2025-04-17 | 366 | 25,027 | 1,472 |

use exact saved `predictions.revision.candidate_r` complementary logs. define `x = log_p - log_not_p`, `eta = a + b*x`; adjusted logs are `log_expit(eta)` and `log_expit(-eta)`. no probability clipping/floors, features, penalty or slope constraint. identity `(0,1)` reproduces saved row probabilities/losses within `1e-12` and aggregates under native `agrees` (`1e-10` relative/absolute).

minimize weighted mean bernoulli negative log likelihood with `chance.fit_logistic` and analytic gradient. standardize using only nominal fit-window mean `m` and population standard deviation `s`, held fixed in every resample. solve on `[1,(x-m)/s]` from identity initialization `[m,s]`; recover `b=theta_1/s`, `a=theta_0-b*m`. settings: `optimizer_max_iterations=200`, `optimizer_ftol=1e-14`, `optimizer_gtol=1e-10`. reduce the weighted objective and its two gradient components with `math.fsum`; bootstrap assessment metrics retain vectorized weighted sums. independently require finite coefficients/logs, optimizer convergence, scaled-gradient infinity norm at most `1e-8`, positive-definite analytic 2×2 hessian, and objective no worse than identity under `agrees`.

positive fit weight, both labels, rank two and overlapping class ranges are necessary. either ordering/touching of positive-weight class ranges is complete/quasi separation. invalid nominal support or numerical execution fails without completion. unsupported bootstrap samples are retained as explicit missingness; no ridge, retry, redraw, coefficient cap or constant replacement.

## summaries and uncertainty

primary: paired assessment mean log-loss difference, adjusted minus unchanged, nats per eligible unblocked attempt. negative favors adjustment. secondary: brier difference and signed residual `(predicted goals-observed goals)/N`; store residuals as proportions and display percentage points. fit metrics are apparent/in-sample. all nominal binary sums use native helpers, weighted bootstrap metrics use vectorized versions of those same definitions. pool attempts, not equally weighted game ratios.

retain assessment partitions for march/april, none/recent and all six model types `wrist,snap,slap,backhand,tip,other`; retain zeros and contributing games. recentness comes from `previous_event.status`. retain all twenty native bins with different own-predictor memberships and separately matched unchanged-probability cohorts; each family and nominal per-game sums reconcile independently. empty rates remain null. no subgroup intervals, thresholds, admission margins or new calibration gate.

2,000 draws each for whole-game, seven-day and fourteen-day methods. each method initializes one `PCG64` generator with seed `3032026`, generates its complete fit-window sample matrix with `rng.integers`, then its complete assessment-window sample matrix. independently resample windows with replacement at their original unit counts; preserve row pairing and use identical assessment multiplicities for both predictors. whole-game selected counts are 346/366. native `calendar_blocks` anchors separately at each first selected date, retaining empty/final partial units: 9/7 weekly and 5/4 fortnightly. map multiplicities to weights without row duplication.

refit on each fit resample with fixed nominal `m,s` and identity initialization. ordered draw columns: `[a,b,delta_log_loss,delta_brier,unchanged_residual,adjusted_residual]`. retain all draw values and per-statistic missing reasons. zero fit/evaluation mass, one label, rank deficiency and separation yield null affected statistics; unchanged assessment residual may survive unsupported fitting. optimizer/arithmetic failure on supported data is an execution error. any undefined draw makes that statistic's interval null. use pointwise 95% linear percentiles without redrawing or dropping samples. nominal estimates use original populations. every interval record retains selected/contributing unit counts for both windows.

these intervals include adjustment fitting and selected fit/assessment sampling conditional on the saved base model. they omit base-model fitting, adaptive selection, origin assumptions and cross-window dependence. four/five fortnightly units limit that sensitivity. both windows are research-exposed. newer labels give the adjustment more recent information; january–february versus march–april environments, drift, shrinkage, missing mechanisms and measurement error remain competing explanations. chronology supplies no untouched confirmation.

## fixed decision and outputs

in order: `conflicting_or_adverse` if nominal `b <= 0` or any defined paired log-loss interval has lower endpoint strictly above zero; otherwise `scale_priority` if `b > 0`, whole-game upper endpoint is strictly below zero, both calendar intervals are defined and neither has lower endpoint above zero; otherwise `inconclusive`. equality to zero supplies neither strict sign condition. calendar methods assess adverse sensitivity, not independent benefit. secondary findings constrain the hypothesis without changing the rule.

`scale_priority` nominates one native scale/shrinkage/temporal experiment. other results nominate at most one structural challenger or `no_supported_intervention`; failed scale improvement does not identify a structural cause. no follow-on fitting is automatic. intercept `a` is the joint regression intercept, not calibration-in-the-large with varying slope. coefficient equality, lower proper loss and descriptive bins do not establish complete calibration.

write only `conversion-scale.png`, `benchmark.json`, then `completion.json` last under a new exclusive external output. finite json, schema 1, exact benchmark/completion kinds, distinct current and parent execution identities; `model_admission: not_assessed` and historical `withheld`. no model, handoff or adjusted probability stream. completion alone indicates success; valid inconclusive/adverse results exit zero. malformed evidence/numerics or budget breach leaves no completion. rerun this cheap command after interruption; no checkpoint or runner.

the one figure shows unchanged/adjusted columns, own-bin residuals above counts, all twenty midpoints, identical symmetric-log residual scales (linear within ±5 pp, tails through ±100 pp), and identical count scales with linear 0–1 core/logarithmic tails. empty residual markers are absent; zero counts remain visible. reserve caption space and inspect for clipping/overlap. caption states dates, denominators/sign, different memberships, research exposure and descriptive status. nonlinear tail distances trade metric spacing for legibility; exact tables retain all values. this is retrospective observed-cell conversion, not a live pre-release forecast or standardized opportunity.

## resources, verification and execution

one nominal solve plus 6,000 resampled solves, maximum 200 optimizer iterations each. ceilings: 900 seconds wall time and 2 gib peak rss. time the first 20 predetermined draws of every method inside this execution and count them toward 2,000. before remaining draws, project `elapsed_now + sum((2000-20)*prefix_draw_seconds[method]/20)`; stop if projection or memory exceeds the ceiling. check actual resources between phases/solves and before completion; record actual time, rss, bytes, throughput and projections. an engineering repair may change a ceiling only in a newly frozen protocol; never relax the scientific settings after results.

verify synthetic end-to-end behavior before freezing. the single real execution uses temporary in-process verification that retains the collected arrays, checks independent nominal/split/per-game/group/bin arithmetic, all percentiles and the decision, and representative weighted fits/draws across all methods without replaying the stream. temporary control code does not alter the production command's settings; its numerical receipts remain, and the controls/tests/bytecode are deleted at closure. statistical, systems and content reviewers inspect the result and figure. preserve expensive parents and source captures.

preexecution numerical review found supported synthetic refits can terminate abnormally near floating-point resolution. correctly rounded reduction improves summation accuracy but does not remove this limitation; its measured 24,000-row callback cost is about five times the ordinary numpy reduction. the same prefix projection and strict failure rule remain authoritative. [the issue](/Users/nnandal/Documents/code/hockey-stats-03j/docs/issues/conversion-refit-convergence.md) and numerical receipts preserve failures; successful synthetic identity exercises are not evidence that all real refits converge.

the following identities were frozen after reviewed green implementation was committed cleanly, before any real adjustment fit.

## frozen execution identity

- freeze time: `2026-10-08T23:27:34.522202+00:00`
- clean executing git revision: `864ba1ef5283e558097064665fc2777faa402603`
- preexecution verification sha256: `c9009b0c07f2acc16ff8ff75485314f7dce6cc6f25f689aa1131a315c46fcf8a`
- interpreter: `UV_PYTHON=3.14.8`; locked dependencies unchanged.

| source | sha256 |
|---|---|
| `docs/specs/03j-chance-experiment.md` | `b898aeb1e8912796742976dde02b1a2baef23834f91d0eed8653122a222b34f5` |
| `analysis/research/chance_conversion_scale.py` | `26fd60ad0098a3a8eccf183b463a21794164de5b67c374bd2cbca427b4d438db` |
| `analysis/research/chance_assessment.py` | `471ca9bed5d1027cb8d2e45c7cb2644f0215e129011c28a8406d2a602f31b9d9` |
| `analysis/research/chance_residual_diagnosis.py` | `41533256b05bca5e6480498c2bc93ecb7c2f24332b475a9916795069821facf0` |
| `analysis/research/chance_review.py` | `c04fa47b432a8e96fb8230c8c4e5f9013511df7b1beee81cd141e0e174257a74` |
| `analysis/research/chance_development.py` | `d3717bd4276c2284cce1967bade055847a9e94a41e66720fddd51c1a2ca4124f` |
| `analysis/src/hockey_stats/chance.py` | `7ce67e8aefb8efad6915271dc581a86c3d375ccff5408bfecd440081e7e655b6` |
| `analysis/src/hockey_stats/chance_evaluation.py` | `2d6ea0b86589e99f4651888ca81a4b76bd6f9947c4bc896a80757e2844f5afd5` |
| `analysis/src/hockey_stats/chance_cli.py` | `4baba0c79a9cbee0d23e961e88cb093bcd6ab6ba02dbd050445918fab83e779a` |
| `analysis/src/hockey_stats/artifacts.py` | `b8600cec329389cda3fe1f5a589d1127ace7b407c57a8fc7abf54e004e37f184` |
| `analysis/uv.lock` | `bae38095f3dea6bdb860501eca311b1c33390c7a1e8b7aae76966572f118acdd` |
| `analysis/pyproject.toml` | `353897b8a614132c9d0d001ab5b67cc661d42077b8b96e7dbaa02a9b55d392c5` |
| `analysis/.python-version` | `922fe0c3de073b01988e23348ea184456161678c5e329e6f34be89be24383f93` |

| temporary verification control | sha256 |
|---|---|
| `/Users/nnandal/Documents/code/hockey-stats-03j-runs/verification/one_real_run.py` | `1c77e408237c441fa208c6a7b58a35238b76b863425a973503aba0dbc9ce3778` |
| `/Users/nnandal/Documents/code/hockey-stats-03j-runs/verification/audit_outputs.py` | `43e16c7271b24f8381666f4d0379ae0a266b6fd7a775cbf85ced5f287576e29f` |

production command from the clean worktree root:

```sh
UV_PYTHON=3.14.8 uv run --locked --project analysis python analysis/research/chance_conversion_scale.py --completion /Users/nnandal/Documents/code/hockey-stats-03g-runs/diagnosis/completion.json --protocol /Users/nnandal/Documents/code/hockey-stats-03j-runs/inputs/protocol.md --out /Users/nnandal/Documents/code/hockey-stats-03j-runs/benchmark
```

the authorized execution below calls that same `run` once with unchanged arguments/settings, captures its arrays for the required independent checks, and prohibits raw/base-model calls. it leaves an external failure receipt if the strict command aborts.

```sh
UV_PYTHON=3.14.8 uv run --locked --project analysis python /Users/nnandal/Documents/code/hockey-stats-03j-runs/verification/one_real_run.py /Users/nnandal/Documents/code/hockey-stats-03g-runs/diagnosis/completion.json /Users/nnandal/Documents/code/hockey-stats-03j-runs/inputs/protocol.md /Users/nnandal/Documents/code/hockey-stats-03j-runs/benchmark /Users/nnandal/Documents/code/hockey-stats-03j-runs/verification/real-run.json
```
