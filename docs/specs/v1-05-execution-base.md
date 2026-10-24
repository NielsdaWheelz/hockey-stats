# v1-05 — execution base

full implementation handoff under [the program](experimental-player-analysis.md) and [chance appendix](experimental-chance.md). [the plan](../plan.md) owns assignment. this document assigns no implementation, fitting or activation. historical research verdicts remain unchanged.

## outcome and boundary

produce twenty checked annual execution states: `u/q/r/g` for `20212022` through `20252026`, plus one shared probability evaluator. real preparation must have passed [v1-01](v1-01-shared-evidence.md); [v1-02](v1-02-dated-coaches.md) supplies separately bound reported coaches. v1-03 factual reductions are independent. fixture development needs no hdd; complete fitting needs the external prepared evidence and external-only outputs.

this is a computed experimental baseline, not a selection tournament. poor calibration is reported, not grounds for omitting a correctly computed component. wrong support, leakage, invalid probabilities, failed solves or unresolved numerical errors remain defects. no scientific admission follows.

v1-06 owns persisted event values, neutral reference panels, finishing/setting projections, maps, contribution accounting and publication; v1-07 owns the two continuation heads and goalie summaries. no cards, sqlite changes, acquisition, new seasons, attention/rink/origin alternatives, bootstrap campaign or serving changes here. retained inactive features and historical research interfaces survive; no legacy-artifact adapter or duplicate parser.

## owners and composition

| owner | responsibility |
|---|---|
| `analysis_data.py`, `coaches.py` | existing strict prepared/coach readers; source facts and identity binding |
| `execution.py` | new annual execution design, source selection, setter prior, state contract and public probability interface |
| `execution_design.py`, `execution_history.py` | internal source binding/encoding and the one prior-clock history owner shared by preparation and attributed numerical witnesses |
| `execution_fit.py` | cohesive objective/gradient/penalty/em internals; execution-specific mathematics, not a model framework |
| `chance_features.py` | reuse pure family transforms; explicit product encoding over v1-01 facts, preserving strict old research behavior |
| `chance.py`, `shot_origins.py` | reuse `solve_logistic`, native grid/kernel and mirror/map-penalty algebra; extract a genuinely shared primitive only where needed |
| `analysis_cli.py` | thin annual `fit` command; preserve concurrent `prepare/facts/publish` work |
| `docs/research/execution-v1-05/verification.md` | actual input/output identities, coverage, numerical evidence, costs, examples and limitations |

old `chance.py` fits joint-season research models; its `r` is not this recorded-stop head. its feature exclusions and `research/fixture_exercise` artifact schemas are also different. reuse numerical primitives, not misleading old model wrappers. use existing finite-json/numpy writers with the new strict reader below.

implementation boundaries: first settle input/design/state types in `execution.py`; numerical work then owns `execution_fit.py` against that layout, while content/source verification independently supplies checked cases and receipt definitions. the integration owner alone edits shared cli/artifact composition and reconciles any extracted primitives. exercise the complete fixture path before real fitting; real annual/head solves remain sequential. no competing copies of preparation, likelihoods or probability arithmetic.

```text
hockey-stats-analysis fit --family execution --prepared DIR --coaches FILE
  --season ID [--previous DIR] --out NEWDIR

prepare_execution(base_prepared, coaches, recipe, season) -> ExecutionDesign
fit_execution_year(design, previous_state, recipe, output) -> ExecutionState
read_execution_state(path, expected_purpose) -> ExecutionState
read_execution_probe(state, head) -> checked numerical-probe variant
execution_branch_probabilities(state, predictors, origin_cells, neutralize=())
  -> BranchPrediction
```

`ExecutionDesign` is ordinary in-memory training data, not a second persisted feature warehouse. predictors contain pre-outcome circumstances, identified actors/coaches, tip applicability and the setter prior; labels/assist observations are separate. `neutralize` accepts distinct groups from `shooter,setter,goalie,coaching`; it zeros their centered residuals through this same evaluator. default is actual execution; all four gives virtual neutral execution. v1-06 composes this mechanism rather than reconstructing logits.

prediction returns ordered origin cells and setter branches with their prior probabilities, `u,q,r,g`, and the five terminal probabilities. `u/q/r` are setter-independent and may be stored once per origin. callers provide explicit origin cells; origin weights are separately identified, never inferred from an outcome inside the evaluator. unknown ids or unavailable heads give explicit errors/status, not neutral substitutes. available prior-only actors remain evaluable with their support status. no source access or mutation during prediction.

## input population and targets

validate the prepared selection and coach binder, then consume only the requested year's game/people members and its exact predecessor. bind corpus hashes, season/game/date/team, prepared member hashes and coach identities. no newest-file discovery. later-year facts cannot affect dictionaries, means, candidates, centers or age terms. earlier-date workload already prepared by v1-01 is permitted; retain its source identity.

use supported ordinary physical attempts in regular-season states with `3..6` skaters per side, one opposing goalie and zero or one attacking goalie. exclude shootouts, penalty shots, empty opposing nets and unsupported focal identity/team/membership/shooter/type/frame/location/outcome. chronology uncertainty excludes a head only when it prevents that head's target or core focal state: an unknown later successor withholds stop-dependent labels, while missing predecessor context remains optional. resolved event membership need not have matched elapsed time. missing optional shift/context evidence is encoded, not a reason to erase such attempts. never replace reported location or actor uncertainty with a convenient category. every recognized attempt receives keyed inclusion/exclusion dispositions.

| head | included target rows | binary response |
|---|---|---|
| `u` | supported blocks/misses/saves/goals | block `0`, others `1` |
| `q` | supported unblocked attempts | miss `0`, save/goal `1` |
| `r` | on-net attempts with known immediate-stop label | recorded immediate stopped save `0`, goal/continuing save `1` |
| `g` | on-net attempts known not stopped | continuing save `0`, goal `1`; auxiliary setter label only where supported |

use v1-01's exact `recorded_goalie_stop` definition, not the historical longer-span stop flag. unknown stop status withholds only `r/g` labels. no outcome-label availability indicator enters predictors. target eligibility, predictor availability and rate-denominator support remain distinct.

reuse all 656 native cells and the fixed kernel with distance `20` feet/direction strength `4`. unblocked observations use their recorded proxy cell; blocks use `w(h)=K(b|h)/sum_k K(b|k)`. preserve every cell. candidate geometry uses origin `h`, never substitutes contact `b`. tips retain their proxy location and have no residual shooter contribution in any head.

at each origin/setter branch:

```text
block       = 1-u
miss        = u*(1-q)
stopped     = u*q*(1-r)
continuing  = u*q*r*(1-g)
goal        = u*q*r*g
```

these sum to one before and after integration. imputed blocked-attempt goal opportunity can be positive; it is not a factual forecast conditional on observing that block. no claim of measured release location follows.

## fixed design

each annual head has an unpenalized intercept, a mirrored native base map plus five type-deviation maps using the existing six-type order/reference, selected circumstance columns, and applicable actors. expand tied coordinates to the native grid before evaluating the original map penalties; sum gradients back to tied coordinates. do not halve mirrored edge contributions or add fitting sum-to-zero constraints. only the spatial maps are tied: off-wing/history may still produce asymmetric full predictions.

all heads select, in canonical order:

```text
game_additive, recent_additive, recent_interactions, recent_geometry, off_wing,
sequence, shift_age, shift_start, workload, calendar_rest, strength_transition
```

reuse the existing fixed transforms/scales, with these explicit product adaptations:

| encoding | contract |
|---|---|
| exact strength | 32 fixed categories `(attacking_skaters,defending_skaters,attacking_goalie)`; reference `(5,5,1)`, 31 contrasts. derive from supported membership, not source pp/pk labels |
| recent geometry/off-wing | candidate-origin transforms; no recent event is structural absence, uncertain predecessor/hand is unavailable. retain `reported_hand_stable_trait` |
| shift age/workload | `opposing_unit`, with every actual member required for a complete aggregate; preserve old min/mean/max and scaling. no known-members-only means |
| shift start | known `on_the_fly` is reference; faceoff offensive/neutral/defensive contrasts; unknown is unavailable. preserve last-faceoff zone/age terms |
| strength transition | existing return to genuine 5v5 after unequal strength; no generic even-strength or penalty-expiry interpretation |
| actors | shooter in all heads, masked on tips; goalie in `q/r/g`; setter in `g`; separate attacking/defending coaches in all heads |

retain `game_detail,recent_detail,action_windows,zone_run,historical` inactive. no duplicate recent encoding, unrestricted cross-products or new alternative campaign.

### approved prior-clock history — 2026-10-24

for `recent_additive,recent_interactions,recent_geometry`, reset-dependent strength transition and setter history, admit a historical record only when its verified source order precedes the focal record **and** its supported period/game clock is strictly earlier. exclude every same-clock record uniformly before examining its kind, validity, faceoff, review or reset meaning. never reorder event ids or recover a physical release order. preserve exact focal membership and the existing sequence, deployment, shift-start, exposure, event-prefix workload, calendar-rest and label contracts.

the recent families use the last allowed record, with the same categories, scales and geometry transforms. unknown clock/order/kind is an explicit history barrier, not permission to skip to a convenient predecessor. supported earlier resets/anchors restore their corresponding support. evaluate strength history through the shared native-interval algebra strictly before the focal clock: a return at `r<t` counts even without an intervening recorded event; a return at `r=t` does not. known absence remains zero, distinct from unavailable evidence.

setter history is a **coarsened recorded prior-clock phase proxy**, not recovered physical uninterrupted play. its candidates are current supported attacking teammates plus supported participants in the selected prior-clock phase, excluding the shooter. a known absent phase contributes an empty known history, so a supported current unit alone gives a complete proxy universe. unknown or censored history gives `.2` none/`.8` unknown. a same-clock faceoff is excluded like every other same-clock record; an older phase may therefore persist in the proxy. retain the cutoff, phase status and reason. preparation and attributed resolution witnesses share this timing owner. [approval and tradeoffs](../research/execution-v1-05/timing-amendment.md) records the accepted loss of within-clock rebound/setup detail. the new literal recipe hash requires a fresh fixture and real chain; previous evidence remains historical.

`q/r/g` add `goalie_workload` and `goalie_calendar_rest`. from v1-01's opposing-goalie facts, use prefix `toi_all_seconds/3600`, prefix `on_net_faced/30`, preceding `days_7/days_14.shots_against/30`; then `prior_appearance_exists,calendar_gap_days,prior_one_date,prior_two_date,games_days_7,games_days_14` with the existing unscaled calendar convention. prefix counters include all supported earlier actions, including earlier penalty shots, not merely training-eligible attempts. prior-day reported shots and event-prefix on-net counts remain differently named proxies. no current-date total substitutes for an event prefix. `u` has neither goalie workload nor goalie identity.

numeric optional columns use each head's training mean over available applicable transformed values, weighted by origin mass where necessary. known zero participates; unavailable contributes zero centered value and an unavailable indicator. structural absence contributes zero centered value and its declared category/existence indicator, distinct from unavailable; add a named applicability indicator only when that absence is otherwise unrepresented. derived columns sharing one availability condition share its indicator. save the exact ordered columns, conditions and means. categorical missingness gets a distinct unavailable level. all-missing/constant indicator columns have zero fixed effect and explicit training support; do not silently invent a learned contrast. core-invalid facts remain exclusions. use supported selected field values, never partial `known_*` sums; unrelated missing counters do not invalidate a supported field.

the strict strength-transition query returns one supported record: a known return has both side and age; known absence makes both structurally absent; unknown history makes both unavailable. the two previous-strength contrasts and return-age column therefore share the single `strength_transition` availability condition and unavailable indicator. no separate age-missing indicator may duplicate that column and dilute its precision. recent fields likewise share `preceding_status`; independently supported sequence/workload fields keep separate conditions.

unknown coach has no individual coefficient, an explicit unavailable circumstance indicator and no fallback identity. known-coach applicability controls reference centering. fixed circumstance categories seen only at scoring remain explicit zero-prior contrasts, with training support zero; actor priors follow the separate entry/carry rule and need not be zero. no unknown core strength/type is permitted.

## setter likelihood

the [appendix's candidate/weight definition](experimental-chance.md#setter-inference), with the approved prior-clock proxy above, is normative: current attacking teammates and supported earlier phase participants, excluding shooter; fixed none mass `.2`, remaining `.8` role-weighted; unknown/censored universe `.2` none/`.8` unknown. include off-ice earlier participants. never enlarge candidates after inspecting a goal assist.

`g(h,s)=sigmoid(base(h)+setup*I[s!=none]+setter[s])`. unknown/goalie setter uses the fixed training-candidate-weighted linear mean of current skater setter coefficients, not a frozen constant; include its derivative. no supported weights means explicit prior-only zero. setup is an annual circumstance coefficient. source-supported primary assist/unassisted labels constrain only the likelihood; missing credit or an assistant outside the candidate universe leaves it marginalized with the discrepancy retained.

```text
L(known goal setter s) = pi(s)*g(h,s)
L(unknown goal)       = sum_s pi(s)*g(h,s)
L(continuing save)    = sum_s pi(s)*(1-g(h,s))
objective            = sum_i sum_h w_i(h)*[-log L_i(h)] + penalty
```

for `u/q/r`, substitute their ordinary Bernoulli likelihood. this is a weighted sum of log losses, NOT the log of an origin-marginalized probability. each source attempt has total weight one; blocked expansion occurs only in `u` training. `q/r/g` training origins are points.

deterministic em: known setter responsibilities are one-hot; otherwise normalize `pi*g` for goals or `pi*(1-g)` for continuing saves. each m-step optimizes the weighted logistic objective plus one penalty. re-evaluate the exact penalized observed-mixture objective after every update. likelihoods use stable log arithmetic; never clip bad probability arithmetic into apparent validity. scoring always uses pre-outcome `pi`, never the auxiliary label or posterior responsibilities.

## annual priors and references

the user selected **entry penalty OR carry penalty**, preserving the declared prior mean:

```text
first supported observation:  .5 * lambda * b_y^2
returning actor:               .5 * kappa * (b_y-m_y)^2
m_y = b_last + (z(age_y)-z(age_last)) dot gamma_role
z(a) = ((a-27)/10, ((a-27)/10)^2)
```

| block | fixed penalty |
|---|---|
| native base/type maps | ridge `.25/1`; neighbor smoothing `4` |
| circumstances, strength, missingness, setup | ridge `4`, no carry |
| shooter/setter | entry `4`, carry `16` |
| goalie | entry `16`, carry `64` |
| each coach direction | entry `256`, carry `1024`, no age drift |
| each applicable annual actor-role age curve | ridge `64` |

age is february-1 `age_days/365.2425`. use separate curves per actor block/head/role. apply age drift only when both ages are known and supported roles agree in `F/D/G`; otherwise retain age-neutral carry with a reason. no role-change history reset. jointly fit current actor and age coefficients; no supported transitions means zero age terms. coaches are always age-neutral. no additional level ridge on returning actors: that would impose the rejected automatic 20% decay. no prior-fit uncertainty is propagated.

current actor axes cover supported current participants/candidates, including identified actors without applicable head labels. retain their source support, likelihood support and prior-only status separately. solve zero-likelihood actor terms analytically at their entry/carry mean after estimating age terms. genuinely absent actors are ledger entries, not invented current observations. retain each head/block's last likelihood-supported raw coefficient, season, role and age; copy it through absent/prior-only years. only a completed likelihood-supported estimate updates it. setter mean coupling counts as actual design support; candidate reference weights alone do not. first supported observation means source-first, not true rookie.

center each head's raw actor effects using its included training rows: non-tip shooter opportunities, applicable goalie faced opportunities, separate known attacking/defending coach opportunities, and fixed pre-outcome supported skater setter weights. exclude none/unknown/goalie candidates from setter-center weights. origin weights sum one per attempt; no assists or responsibilities choose centers. zero total weight gives center zero with prior-only status. store centers separately from raw coefficients and the history ledger.

residuals are raw minus center. transfer offsets through the exact applicability terms: non-tip shooter, known coach direction, goalie and setup. actual logits must remain unchanged. unknown/goalie setter's centered deviation is zero by construction. virtual neutral execution zeros all actor residuals while preserving these offsets, circumstances and setup mixture. this is reference execution, not an average over actual matchups or causal isolation.

## state and operation

fixed recipe `experimental-v1`, execution version `execution-v1-05-1`; hash the literal design/target/penalty/origin/missingness/history definition, not just its name. `real/fixture` purposes must agree across inputs. the real chain starts at `20212022`; a fixture chain starts at its earliest selected season, explicitly source-first. first season forbids `--previous`; each later season requires the immediately preceding annual state, preserving the ledger's actual last observations. fixture chains also require consecutive selected years. reject skipped/mismatched years, wrong source/recipe identities, extra/ignored flags and occupied output directories.

annual output contains `manifest.json`, `coverage.json`, `heads/<u|q|r|g>.json`, `.npz` arrays for completed heads and compact diagnostic/probe members. no pickle or arbitrary serialized objects. reuse existing contained-relative-path, finite-json, array-shape/dtype and sha256 checks.

| record | required contents |
|---|---|
| manifest | exact keys `schema_version:1,kind:"execution-state",purpose,season,recipe,implementation,prepared,coaches,previous,training_cutoff,heads,files,resources`; input refs bind resolved locator/hash and selected member identities; `previous=null` only first year |
| `heads` | four ordered records `{head,status,metadata_path,arrays_path}`; status `complete|unavailable`; unavailable has `arrays_path=null`; `files` uniquely binds each actual member `{path,sha256}` |
| head metadata | exact keys `head,target,design,actors,priors,centers,ledger,origin,arrays,starts,selected_start,diagnostics,resolution,status,reasons`; design owns ordered feature/map/actor axes, transforms/means/flags, mirror expansion and exact penalties; arrays bind named finite float64 shapes and axes |
| actor/prior/ledger rows | block/id, dated role/age, current source and likelihood support, center weight, prior-only flag, prior mean/precision and last-supported state; no current estimate for an absent actor |
| starts/diagnostics | requested/deduplicated starts, completion, termination, iterations/evaluations/objectives, em responsibility change and accepted-objective trace; selected completed minimum with deterministic zero-start tie break |
| resolution | separate from solver status: earlier years `not_applicable`; final year `pending|passed|failed`, with probe member identities and comparisons. `pending/failed` is inspectable but does not complete the numerical handoff |
| coverage | every selected game and recognized attempt key, per-head inclusion/disposition, source/label/candidate completeness, strength/type/class totals and optional-feature missingness; located reasons and input pointers |
| resources | actual dimensions, origin/candidate branch counts, solve counts, wall time, peak memory and bytes; no estimated completion percentage |

unavailable head metadata sets `arrays,selected_start,centers=null`, requires reasons/diagnostics and preserves the incoming ledger without a new fitted estimate. incomplete optimizer endpoints may be retained separately as diagnostic members, never as fitted arrays. the reader rejects missing/duplicate/cross-wired members, invalid axes, nonfinite coefficients, malformed priors, mismatched internal identities and false completion claims. it validates the state and its own member bytes; input locators are provenance, not instructions to reopen raw files or traverse old sources. fit/score boundaries explicitly bind supplied prepared/coaches/predecessor objects to these identities. saved prediction needs no originals.

manifest head records, metadata head/array references and member hashes/axes must identify the same coefficient files. reject orphan or multiply addressed fitted arrays. ledger ancestry follows the exact predecessor hash, never a compatible-looking name.

save each final-year tightened head's arrays, recalculated prior-only values/centers/offsets, exact unchanged design/input/penalty bindings and solve/em diagnostics. bind these as resolution members, not a new recipe or a copied annual family. to avoid a digest cycle, freeze a contained `resolution/baseline.json` descriptor before continuations: it binds the unchanged input/recipe identities, each baseline head metadata definition excluding resolution, and the baseline coefficient-member hashes. probes bind this descriptor hash; the final manifest binds the descriptor, probes and final head metadata, and is written last. the strict reader reconciles the descriptor against that final family. `read_execution_probe` returns a variant tagged `usage="numerical_probe"`, with the frozen baseline descriptor hash, final annual manifest hash, changed head and probe hashes; the same evaluator accepts it. ordinary predecessor/producer selection rejects probe variants. v1-06 uses them for propagation without rerunning the fits or silently promoting tighter coefficients under the baseline identity. complete numerical handoff requires four passed final-head probes.

write the annual manifest last. interrupted output has no readable completion manifest; keep expensive pieces and diagnosis, use a fresh destination after repair. an explicitly unavailable head has no consumable fitted probabilities. other head results remain preserved, but a partial family is not completed delivery or a substitute predecessor; no silent old-head fallback. completed compatible annual families are the reuse unit.

use `chance.solve_logistic`: `maxiter=2000,ftol=1e-14,gtol=1e-6`. try zero and current-coordinate prior-mean starts, with all other terms initially zero; deduplicate identical starts and record both requested labels. do not copy old circumstance coefficients across changed annual centers. select the lower completed exact objective. em allows at most 100 updates; every accepted m-step must complete its optimizer. recompute observed objective and responsibilities afterward, requiring relative objective change `abs(new-old)/(1+abs(old))<=1e-8` and maximum responsibility change `<=1e-6`. record every increase; one exceeding `1e-10*(1+abs(old))` fails that start, not an opportunity to relax the criterion. an inner failure cannot become outer convergence. local completion is not a global-optimum claim. empty/single-class heads cannot fit an unpenalized finite intercept: record unavailable, never a finite saturation endpoint as success.

stopping amendment approved 2026-10-22: the baseline uses `ftol=1e-14` and its tenfold-tighter continuation uses `1e-15`. the original relative-loss stopping completed solves while the four probability probes failed; a single preview with these stricter values passed the unchanged `1e-5` margin. the native algorithm, objective, priors, other solver/em options and `1e-10*(1+abs(old))` increase allowance remain unchanged. optimizer completion does not assert that its alternative raw-gradient tolerance was reached. preserve the failed chains and preview as historical evidence; acceptance requires a fresh full chain under the new recipe hash. [amendment review](../research/execution-v1-05/stopping-amendment-review.md).

measure one representative real design/fit before completing the five-year sequence; it counts toward delivery if exact and complete. one heavy fit at a time, within 64 gb. chunk `u`'s full origin expansion and ragged setter evaluation; no whole-corpus attempt×cell×feature tensor. record honest costs without changing populations/modes/tolerances to hit an invented deadline. no runner, checkpoint engine, local fit mirror or automatic retry campaign.

## content and acceptance

the content reviewer owns a compact season×head receipt: precise conditioning, counts/exclusions, strength/type support, source versus inferred quantities, prior-only populations, missingness, computation status and costs. include labeled in-sample class fractions, mean predicted probabilities and mean imputation-weighted head negative log likelihood. report the `g` auxiliary-mixture likelihood separately from its outcome-only binary diagnostic. reliability bins have edges `0,.05,...,1`, last bin including1: integrate each attempt's head probability over its frozen origin/prior branches, then count that physical attempt once with its observed binary target and expected mass. outcome-dependent imputation means these are not honest unconditional all-attempt forecast scores. no physical-origin validation, holdout or admission gate follows. model coefficients are logit terms, not yet per100 card skills.

| acceptance boundary | independent evidence |
|---|---|
| source/design | exact prepared/coach join; original attempts partition; optional gaps survive; supported no-elapsed event retained; workload prefixes exclude focal/future events; changing only later-year evidence in a valid selection cannot alter earlier numerical design/results, though lineage hashes change |
| objective | hand-solvable/finite-difference checks for three binary heads, weighted block loss, native/mirror penalties, age coupling, known/unknown/goalie setters and unknown-setter mean derivative; exact em objective identity/monotonicity |
| history/reference | source-first, zero-label actor, gap returner, role/age conflict and coach change; ledger updates and entry/carry priors; tip/coach/setup centering preserves logits; actual/neutral branching and five-way closure |
| software path | fixture selection→annual cli→strict reader→probabilities; save/read equality; wrong identity/shape/extra fields/occupied output rejected; empty/single-class/failed solve remain unavailable; touched old numerical/feature behavior preserved |
| real completion | all five seasons, twenty completed heads and every selected game reconciled; diagnostics and adverse cases retained; source/prepared/coach files unchanged; no fit completion inferred from a fixture |
| numerical resolution | four final-season continuations of the identical objective with tolerances tenfold tighter, including em stopping where applicable; record parameter/gradient/objective changes and maximum branch/terminal probability change `<=1e-5` on the frozen probe set below |

freeze a bounded probe set before continuations: up to 256 keyed real final-season attempts with all individual identities required by the shared branch evaluator. retain u-only training attempts lacking individual goalie identity, but list their joint probability-probe context as unavailable; never substitute a neutral unknown goalie. among eligible contexts, select probes covering marginal strength levels, then types, then outcomes, then missing context, tips, off-ice/incomplete setters and sparse actors; no Cartesian-product coverage claim. within each requirement choose the first source key, then fill unused slots by source key; define sparse as the least supported identified actor in each applicable block, ties by id. retain the selector/list. real blocks evaluate all 656 origins, unblocked attempts their point. add explicitly synthetic geometry probes at every native cell for each of the six types under the first supported probe's frozen context, actual and fully neutral execution. compare each head and terminal probability using identical origins and pre-outcome priors. absent source cases use attributed fixtures, never invented real witnesses. excessive numerical differences require a responsible repair or explicit incomplete delivery. v1-06 later owns common-panel/per-hour/basket propagation checks; do not implement those consumers merely for this slice.

a source-present prior-only shooter can lack a real focal attempt. its attributed fixture may be explicitly synthetic under a checked source context where that actor is actually on the attacking unit. rebuild that actor's deployment, workload, rest, reported-hand transform, predecessor-shooter relation and outcome-blind setter prior through the source owner; retain the original member/key, changed fields and synthetic reason. this tests numerical behavior without creating an observed attempt. a requirement without a real or valid attributed-fixture witness remains uncovered and cannot pass resolution. report coverage completeness separately from the probability-change comparison.

when no actual incomplete-setter context exists, use a named synthetic source-evidence projection: withhold the last eligible prior-clock record's supported kind in a copy of an actual joint-probability context, then rebuild history, circumstances and the setter prior through their source owners. retain the original member/hash/key, exact prepared-event pointer and true-to-false support change, synthetic reason and expected `.2 none/.8 unknown` prior. preserve actual focal identity and membership. this probe creates neither an observed attempt nor a source correction; it changes no training row, fitted recipe or numerical criterion.

temporary integration/live red→green→refactor→green checks precede acceptance; independent mathematics, systems/source and content reviewers examine final evidence. delete campaign tests/controllers and test-only dependencies afterward; retain useful attributed fixtures, checked expectations and receipts. no new retained harness is selected. stop expanding checks once required behavior and concrete concerns pass.

## tradeoffs and handoff

the baseline trades unknown physical release geometry for a fixed imputer; some source selectivity for explicit core validity; missing optional circumstances for declared imputation; left/right spatial differences for pooling; observed passes for a latent setup assumption; and calibrated/full-history uncertainty for annual point-prior computation. exact strength has 31 penalized contrasts rather than a cheaper additive-count assumption. shot-count scaling affects shrinkage and is fixed, not optimized. two-start em may find only a local optimum. preserving the carried prior mean deliberately differs from simultaneous level-plus-change shrinkage. none of these choices establishes private-model parity.

the four-layer organization, tip masking and actor placements are informed by [hockeyviz xg8](https://hockeyviz.com/txt/xg8). our origin grid/law, earlier-participant candidates, mixture likelihood, stop proxy, annual priors and penalties are independent definitions. no model-admission or public-launch claim is made.

handoff gives v1-06/07 exact annual manifests, public reader/evaluator, coverage and numerical receipts. v1-06 can be specified/developed against the contract while fitting runs; real scoring waits for checked states. factual reductions and card work can proceed independently in isolated worktrees. no second heavy fit should compete for this mac.
