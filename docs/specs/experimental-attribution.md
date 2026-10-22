# experimental spatial attribution and player value

implementation appendix to [the complete program](experimental-player-analysis.md). [the plan](../plan.md) alone owns assignment; the parent specification owns seasons, acquisition and publication. [chance/execution](experimental-chance.md) owns inferred origins and reference-execution chance values. this is one coherent initial recipe, not a claim to reproduce private hockeyviz software. frozen studies and their fitted artifacts remain unchanged.

the parent's [coverage amendment](experimental-player-analysis.md#input-and-feature-completeness) also requires concrete retained alternatives for documented finer elapsed context and age/entry/transition-variance behavior. coarse bins and mean drift below remain initial choices, not evidence that those other mechanisms are implemented. finish their equations, exposure/reference semantics and bounded exercise costs before implementing the added alternatives; unrelated baseline and application work need not wait for comparative scientific success.

## populations and response ownership

prepare five annual states chronologically. use corrected source support, actual membership and ordinary regular-season play with both goalies present. `ev` contains two directed observations of genuine 5v5 time. `st` contains one advantaged-side observation of 5v4, 5v3 or 4v3 time; its attacking player terms mean pp offense, defending terms mean pk defense. share those player terms across the three states, retaining separate state baselines. 4v4, 3v3, empty-net and shorthanded offense do not enter these attribution fits; their descriptive/chance evidence retains its own population.

the directed populations and separation of player/context effects follow the public [magnus ev](https://hockeyviz.com/txt/magnus9EV) and [special-team](https://hockeyviz.com/txt/magnus9ST) descriptions. our positive likelihoods, reduced time encoding, priors and seasonal headline are explicit departures.

retain every eligible zero-event interval. if an attempt lacks an essential valid identity, outcome, location/imputation or chance value, remove its affected reconstructed interval's counts **and time** from the shared modeled attempt/chance population. this common support is required for their joint construction; do not intersect unrelated personal, observed or mechanism populations. retain excluded seconds, events and reasons. event membership at a boundary follows the existing corroborated event-assignment rule; it is not guessed from a later lineup.

each eligible attempt supplies native-cell origin mass `o[e,c]`, summing to one. the chance owner supplies `q0[e,c]`, the goal probability at that origin with virtual neutral execution. preserve circumstances and the pre-outcome setter mixture. retain:

```text
attempt location mass: o[e,c]
neutral chance mass:   o[e,c] * q0[e,c]
```

blocks retain inferred release mass; their contact location is never an observed release. neutral chance mass is an estimated quantity, not realized goals. the quality head below regresses these probabilities, not another set of observed bernoulli outcomes. no poisson sampling-uncertainty claim follows.

## elapsed design

`analysis_data.py` extends the reconstruction/feature owners with one all-time design. split eligible intervals at membership, strength, score, live-play reset, regulation ten-minute boundaries and each member's shift-age boundaries `0,10,20,40,60,90` seconds; the last age bin is `90+`. evaluate continuously changing prefix counters at the chunk's left endpoint. this defines a piecewise-constant model: elapsed integration is exact for that declared approximation, not for continuously changing fatigue. events use the corresponding chunk covariates, except their authoritative pre-event score and supported boundary membership. do not discard an otherwise eligible goal merely because subsequent elapsed time has the new score.

[v1-01](v1-01-shared-evidence.md#context-and-labels) owns these factual chunks. elapsed counters include events strictly before the chunk-left clock and participation over preceding half-open time; same-clock events are excluded from that frozen snapshot. execution's separate exact pre-event snapshot may include earlier same-clock records. the spatial producer owns encoding, training-only centering/scaling and its additional valued-response support, not another chronology implementation. dated coach evidence joins separately from v1-02.

the fixed design includes:

- player indicators for the two roles; dated coach indicators for each role, plus coach score deviations for `-2..2` and a third-period tied/one-/two-goal-lead deviation;
- home × period; attacking score clipped to `[-3,3]` × six regulation ten-minute bands; a separate overtime score context without a fabricated regulation clock;
- attacking/defending unit fractions in each shift-start-type × age-bin cell: offensive, neutral, defensive, proved live on-the-fly and unknown;
- unit fractions in each previous-night/second-previous-night played combination; unit means of supported game-prefix and preceding-7/14-day workload counters from `feature_history`;
- the existing supported strength-transition indicator, evaluated over elapsed time through its recorded reset. a membership transition is not automatically a proved penalty expiry.

shift starts require the actual player's coherent shift, not a team-average invented start. `no_same_clock_faceoff` alone does not prove on-the-fly entry: require a start strictly inside a corroborated live episode; ambiguous same-clock starts stay unknown. restart zones and membership use the same source/frame owner as events. score chronology consumes the source-ordered goals: goals use the prior score; elapsed play after them uses the updated score. preserve genuine eligible overtime rather than imposing a third-period cutoff.

numeric context is training-exposure centered and scaled; missing values use that centered zero **plus** an explicit missing indicator. categorical unknowns remain categories. retain partial counters and their completeness flags. source missingness is never overwritten. extraction remains retained when inactive; chance-only event chains are not transplanted into elapsed denominators. 04o's smooth clock curves remain a distinct retained alternative.

## positive volume and forty-mode shape

reuse the 656-cell native geometry and `attribution.build_shape_basis(grid(), uniform_shares)`, retaining all forty graph modes. save the basis once and reuse its exact arrays across years; do not rotate annual eigenvectors independently. this new uniform-reference basis has its own identity. old gaussian coefficients and moments cannot be imported into the new likelihood.

for each `ev|st`, fit count volume, count shape and conditional quality heads:

```text
eta_v(x,s) = log(r[s]) + intercept[s] + x beta
v(x,s) = exp(eta_v(x,s))                         # attempts / hour
eta_c(x,s) = log(pi[s,c]) + B[c,:] dot (intercept_shape[s] + x Theta)
p_c(x,s) = softmax_c(eta_c(x,s))
lambda_A[c](x,s) = v(x,s) * p_c(x,s)            # attempts / hour / cell
Q_c(x,s) = sigmoid(logit(qbar[s,c]) + intercept_q[s] + x beta_q
                   + B[c,:] dot (intercept_qshape[s] + x Theta_q))
lambda_X[c](x,s) = lambda_A[c](x,s) * Q_c(x,s)  # chance / hour / cell

volume loss = sum_chunks E[j]*v(x[j],s[j])
              - sum_events eta_v(x[e],s[e]) + prior
shape loss  = -sum_events,c o[e,c]*log(p_c(x[e],s[e])) + prior
quality loss = -sum_events,c o[e,c] *
  (q0[e,c]*log(Q_c(x[e],s[e]))
   +(1-q0[e,c])*log(1-Q_c(x[e],s[e]))) + prior
```

`E` is hours. every complete cell rate is positive and `lambda_X[c] < lambda_A[c]`; signed player contrasts can be negative. this learns expected neutral opportunity quality conditional on modeled context/location, averaging unmodeled event circumstances through their targets. it is not an independently estimated chance rate, nor a cell-agnostic average xg multiplier. native-cell rates sum directly to each scalar. divide by cell area only when publishing a density and restore that area when integrating. the existing observed-display grid is different: use an explicit mass-preserving transport, never matching unrelated numeric cell ids.

freeze positive annual baseline construction. pool same-family origin mass across states and add one uniform attempt; normalize to `pi_pool`. state spatial shares are `(origin_mass[s,c]+10*pi_pool[c])/(attempts[s]+10)`. pooled rate is `(attempts+1)/(exposure_hours+1)`; set `r[s]=(attempts[s]+pooled_rate)/(exposure_hours[s]+1)`. let pooled quality be `(sum neutral_mass+.5)/(attempts+1)` and `qmean[s]=(neutral_mass[s]+10*pooled_quality)/(attempts[s]+10)`. then `qbar[s,c]=(neutral_mass[s,c]+10*pi[s,c]*qmean[s])/(origin_mass[s,c]+10*pi[s,c])`. these positive rate/interior quality offsets also support zero-event fixtures. the pseudo-hours/attempts are initial smoothing choices, not validated optimal constants. zero-exposure states are explicitly prior-only; they do not acquire fictitious observations.

fit/save raw actor coefficients on stable identity axes; history always carries these raw coordinates. for reporting/projection only, center player roles using that year's eligible role time and coach terms using eligible coach time, transferring constants to the corresponding state intercept/applicability column so factual predictions stay exact. account for actual role counts and unknown-coach applicability; a score-specific coach offset cannot become an unconditional intercept. never carry a changing annual reporting center as if it were raw ability change. categorical context uses fixed contrast coding and centered continuous columns. proper penalties resolve the remaining overlapping context columns; do not make sparse contexts unpenalized.

each annual role axis includes every identified skater in that season's prepared regular-season roster, including skaters with zero exposure in that role. the proper prior supplies their conditional estimate, labeled prior-only with zero role exposure; it does not fabricate specialist evidence. a missing identity or failed fit remains unavailable. full-family completion requires actual fitted evidence, not a collection of prior-only zeros.

### fixed priors and annual meaning

use independent gaussian penalties `0.5*((coefficient-mean)/sd)^2`. scalar player sd is `.25` at first observation and `.10*sqrt(year_gap)` when returning. shape-player prior has the same total root-mean-square log-effect scale, divided by `sqrt(40)` per uniform-orthonormal mode. quality uses these same scales on its scalar and forty spatial log-odds coefficients. coach scalar/shape-rms scales are `.10` initially and `.05*sqrt(year_gap)` on return. context scalar sd is `1`, shape-rms sd `.5`; state scalar-intercept sd is `2`, state shape-intercept rms sd is `1`. the static mean is zero; the returning mean is the most recent earlier fitted coefficient. entrants are not forced to replacement level.

volume player means additionally use the chance appendix's dated `z(age)` and a separately fitted `F/D` age drift: `mean=previous+(z(current)-z(previous)) dot gamma`, ridge `64` on `gamma`. fit this jointly with the annual volume coefficients. absent age/role gives an explicit age-neutral transition. shape, quality, coaches and mechanism priors are age-neutral initially. annual history conditions on earlier means and omits their uncertainty; it can lag reversals. these constants and the limited aging model are disclosed assumptions, not rescued study winners.

minimize with analytic gradients, sparse design multiplication and scipy limited-memory bfgs: history `10`, `maxiter=2000`, `ftol=1e-10`, `gtol=1e-6`. start from the prior mean, retain objective/gradient/convergence evidence and never call a failed solve a successful estimate. use stable log-sum-exp; overflow or underflow that destroys physical positivity is a numerical failure, not an invitation to clip predictions.

compress identical volume-design chunks by summed exposure. process shape/quality events in batches of at most `4096`, forming only batch × forty and batch × 656 arrays; accumulate gradients. never allocate event × cell × feature tensors. this preserves all modes and events while avoiding native-grid work over every zero-event second. six annual heads, across five years, form thirty spatial solves; mechanisms add their declared annual chains, not a recipe sweep. one heavy annual solve at a time; external outputs and ordinary explicit reuse of completed compatible states suffice. no optimizer grid, bootstrap campaign or runner.

## projections and adjustment explanation

the standardized reference is one virtual unit: other player/coach residuals zero, centered elapsed context zero, the relevant state baseline retained. it is **league-centered**, not the arithmetic mean prediction over actual lineups. insert one focal player into the appropriate role, holding everything else fixed:

```text
delta[i,c,s] = lambda_c(focal=i, reference, s) - lambda_c(reference,s)
delta[i,s] = sum_c delta[i,c,s]
```

evaluate this separately for `lambda_A` and the joint `lambda_X=lambda_A*Q`; zeroing only one head is not the complete player contrast. publish both complete maps and signed effects. defensive `delta` means change in chances/attempts against; invert only its value-ledger sign. league eligible-time shares of 5v4/5v3/4v3 define the pp mixture, and the identical shares define reciprocal pk mixtures. no player's own specialty usage chooses their reference basket.

for the actual-context explanation, partition each head's linear predictor into self, teammates, opponents, coaching/other context and baseline. compute exact four-group shapley values over the sixteen subsets of non-baseline groups. substitute each group jointly in volume, shape and quality, then recompute exponential, softmax, sigmoid and the complete rate product; the quality logit is not an additive log-rate contribution. coefficients alone are not rate contributions. group maps/scalars plus baseline close to the factual fitted prediction; numerical residual must meet tolerance and is never attributed to an actor. these are model allocations, not causal effects.

## penalties

following the joint on-ice responsibility question in [magnus penalties](https://hockeyviz.com/txt/magnus7P), fit team awards rather than assigning all responsibility to the named offender. this baseline targets non-offsetting ordinary two-minute minors arising during supported 5v5. retain committed/drawn/served people separately. at a shared clock, cancel ordinary opposing minor pairs; mixed major/double-minor/compound groups without an unambiguous disposition are unresolved, with matched affected exposure excluded. bench minors can supply a known team award without an invented individual offender. delayed-penalty extra-attacker play is outside the population: a 6v5 award cannot be reassigned to earlier 5v5 time by guesswork. retain all other recorded penalty facts and explicit excluded-award classes, including majors, double minors, misconducts and penalty shots; they are inactive model targets, not deleted evidence. label the result **ordinary-minor drawing/taking**, not total penalty minutes or all penalty impact.

one positive volume model has drawing-team player roles and taking-team player roles, full zero-event support and the elapsed context above. add pre-event repeat/switch/none for the preceding eligible award in the game; uncertainty after an unresolved award stays unknown, and a new period does not erase it. reuse the player/coach scalar priors and annual means; penalty age drift is zero. output signed draw/take-rate contrasts, counts and coverage.

value an award as one isolated two-minute power play. in goals/hour, let `a,b` be neutral 5v4 pp/shorthanded scoring rates, and `e_f,e_a` neutral ev rates. obtain `a` from the positive chance-rate reference; estimate `b` from neutral valued shorthanded events divided by matched exposure, without inventing a shorthanded-offense player model. pin `T=2/60` hours:

```text
tau = -expm1(-a*T)/a              # limit T when a tends to zero
V = ((a-e_f) - (b-e_a))*tau
drawn_value_per60 = delta_draw * V
taken_value_per60 = -delta_take * V
drawn_value = (1000/60) * drawn_value_per60
taken_value = (1000/60) * taken_value_per60
```

`delta_draw` and `delta_take` are award-rate contrasts per60 minutes; the two value rates are goals per60 and the final two values are goals over the common 1,000-minute 5v5 workload. the pp goal ends the minor; an sh goal does not. this values an isolated opportunity, omitting overlaps, 5v3 interactions and regulation-end truncation. the valuation uses neutral units, not the focal player's pp/pk coefficients; do not count the resulting additional special-team minutes again.

## shootiness

estimate a season's tendency to take the team's attempts, related to the [published shootiness question](https://hockeyviz.com/txt/shootiness), with an annual conditional multinomial rather than an instant elo state. fit the seven declared ev/pp/pk states together, with one shared player term and state-specific position effects. on each supported attempt, the observed shooter chooses among the actual attacking skaters:

```text
P(i | unit,s) = exp(position_offset[i,s] + b[i]) /
                sum_unit exp(position_offset[.,s] + b[.])
position_offset[F,s] = log((2/3)/n_F) + role_effect[F,s]
position_offset[D,s] = log((1/3)/n_D) + role_effect[D,s]
```

`n_F,n_D` are the present unit's counts; absent groups contribute no candidates. unknown roles use weight `1/unit_size` and retain that status. position effects have zero-sum contrast coding and gaussian sd `1`; player coefficients are position-centered with the offset transferred to preserve factual probabilities. use player gaussian sd `.5` initially, `.2*sqrt(year_gap)` around the previous mean on return. source shooter identity includes tips even when the chance model masks tip execution. known shooter and complete candidate membership are required; no shot outcome is a predictor. shared player coefficients across strengths are an explicit initial pooling assumption.

all mechanism histories, including shootiness, carry raw fitted coordinates. position/role centering is a separate reporting/projection transform with its exact offset transfer; changing annual centers must not alter a returning player's prior mean.

publish probability and change against the same position slot's zero effect in the reference unit below. hypothetical units normalize to one. shootiness allocates modeled execution opportunity under the chance appendix's common reference panel; it is not an additional goal-value term.

## inferred territory and post-shift value

the four roles are exit offense, entry offense, zone retention and entry prevention. this model uses genuine 5v5 with both goalies present only. the [public blueline framework](https://hockeyviz.com/txt/bluelineTraversals) motivates their distinction; the following explicit inference/hazard recipe is ours. no public event feed establishes complete puck possession or tracked entries.

within corroborated continuous 5v5 live episodes, linearly interpolate the puck's longitudinal coordinate between consecutive usable located events. faceoff, shot/miss, block-contact, hit and turnover coordinates are recorded-position proxies; contact is allowed here as contact, never release. split at actual blue lines `x=-25,+25`, lineups and context changes. crossing two lines produces two inferred transitions. no interpolation across strength change, whistle, goal, period, invalid coordinate frame or a source gap; time before the first/after the last anchor is unknown. equal-clock conflicting anchors leave the affected segment unknown. future anchors are used only for retrospective response reconstruction, never predictors. unrecorded out-and-back movement remains invisible.

fit two continuous-time event-rate models, entries and exits, with log-linear player/coach roles, clipped score, period/home and the same scalar priors/history. their rate unit is crossings/second and duration is seconds; the coefficient priors are dimensionless log-rate scales. each known neutral-zone interval supplies exposure to both possible entry directions; each end-zone interval supplies exposure to its exit direction. inferred crossings supply counts, including retained zero-crossing time. four rates form a valid three-zone generator:

```text
Q[D,N]=q_exit_home; Q[N,O]=q_entry_home
Q[N,D]=q_entry_away; Q[O,N]=q_exit_away
Q[z,z]=-sum_other Q[z,other]
loss = sum_exposures duration*q - sum_crossings log(q) + prior
```

`D,N,O` are zones from the home team's attacking orientation. `D→N` uses home exit-offense and away zone-retention terms; `N→O` home entry-offense and away entry-prevention; `N→D` away entry-offense and home entry-prevention; `O→N` away exit-offense and home zone-retention. a focal home skater changes those four edges through their respective four roles; a focal away skater uses the reflected mapping. neutral teammates/opponents and coaches retain zero residuals. increased retention/prevention coefficients increase the opponent's transition hazard before any favorable display-sign inversion.

show each standardized hazard with its actual transition direction. entry/exit offense probabilities are `1-exp(-q*1 second)`; retention/prevention probabilities are `exp(-q_opponent*1 second)`, the complement for the relevant opponent transition. these are conditional one-second subskill summaries, not competing-event outcome probabilities. neutral-zone directions for a complete step come from `expm(Q)`, not two independent bernoulli draws. retain that conditioning and label defensive hazards as opponent exit/entry hazards. the four subskills explain movement and are not four extra value components.

derive ice won/lost from what the player leaves to a successor, not the attempts already credited while on ice. use the fitted zone generator in a finite absorbing shift model. its absorbing start types are `DZ,NZ,OZ,on_the_fly`. estimate league whistle hazards and live shift-ending hazards by current zone/age bin, plus probability of ending at a whistle and the following faceoff-zone matrix. use only supported reconstructed shift/live/stoppage evidence; censor unknown spans. freeze gamma smoothing of `.5` events/`30` seconds for hazards, beta `(.5,.5)` for ending-at-whistle probabilities, and `.5` pseudo-count per restart-zone cell. these are weak stabilizers, not measured physical priors.

the restart matrix `R[z,k]` conditions on the zone at the whistle and gives the following faceoff zone. let `w_z` be whistle hazard, `d_z` live-ending hazard and `h_z` probability of ending at a whistle, all at the current age bin. off-diagonal transient rates are `T[z,k]=Q[z,k]+w_z*(1-h_z)*R[z,k]`; the diagonal is minus their sum minus `d_z+w_z*h_z`. absorbing rates are `w_z*h_z*R[z,k]` into each faceoff type and `d_z` into on-the-fly. same-zone whistle restarts are self-events: they create no spurious probability loss. restarting after a whistle retains the current shift age; only a new shift starts at age zero.

integrate each age-bin generator by matrix exponential and the `90+` tail by its transient fundamental matrix. freeze league start-type frequencies and the supported zone mixture for on-the-fly starts. this initializes the all-neutral process; its non-absorbed mass is the common reference survival curve `S0(t)`. positive ending hazards make absorption total one. compare the absorbing distribution with the focal player's four transition effects inserted against all-neutral players, using the same start distribution and whistle/shift-end behavior: `d_i=end_i-end_0`, with `sum(d_i)=0`.

for each successor start type `z`, integrate the positive spatial model's start-context contrast for **one neutral successor slot**; the other four slots stay neutral. use the same frozen `S0(t)` for every start type, not a newly selected or player-specific survival curve. with `t` in seconds and rates per hour:

```text
G_side[z,c] = integral_0^infinity S0(t) *
  (lambda_X_side[c](slot_start=z, slot_age=t, reference)
   -lambda_X_side[c](reference)) dt / 3600
reference_mean_shift_seconds = integral_0^infinity S0(t) dt
n0 = 60000 / reference_mean_shift_seconds
ice_won_map[c]  = n0 * sum_z d_i[z]*G_for[z,c]
ice_lost_map[c] = n0 * sum_z d_i[z]*G_against[z,c]
```

evaluate against-side start zones in the correctly reflected attacking frame; on-the-fly uses the declared pooled zone mixture. this common survival assumption deliberately excludes start-specific/focal substitution behavior from successor value.

sum cells for goals per basket; against increases are unfavorable. current-player spatial effects hold start context fixed; these terms allocate the induced successor-start difference only. never add raw post-shift outcomes or the four movement subskills again. collapsing live exits to one on-the-fly state loses their specific live-zone imprint. incomplete anchors, interpolation, fixed substitution behavior and the successor-slot approximation remain prominent limits. this is a model-based territorial footprint, not observed possession or measured causal transition skill.

## card projections and shared quantities

publish neutral complete attempt/xg rates beside each focal complete rate and signed contrast from `project_spatial`; use the same context and reference, never an empirical league rate as an interchangeable denominator. the isolated card's four maps are **attempt-rate contrasts** for 5v5 offense, pp offense, 5v5 defense and pk defense. their xg insets are separate projections: signed xg/60 and `100*delta_xg/neutral_complete_xg`. each additive map closes to its own quantity; an attempt map does not integrate to its xg inset. defensive rates keep the against sign, while the contribution ledger reverses that sign explicitly.

produce `pp`/`pk` aggregated maps/scalars using the exact state weights of the common workload ledger below; store these weights/reference identity and retain exact-state detail. these are common-mixture estimates, not the player's actual usage. a missing required state does not become zero or silently re-normalize the mixture. the 5v5 shootiness label is `100*(focal_probability-neutral_probability)` percentage points on its declared common unit, not relative percent. expose both probabilities.

the compact card's penalty grouping is exactly `penalties_drawn+penalties_taken` from the ledger. compute and publish it once in `player_value`; the ten separate contributions remain authoritative. central isolated-card execution distributions use the 5v5 common-panel per100 finishing/setting quantities; their adjacent contribution labels still use the full workload. no percentile, conditional stage or shootiness term is added to the total. [application](experimental-application.md#card-compositions-and-shared-display-rules) owns cohorts, history and physical display.

## ten-term ledger and depth reference

use the [approved common workload](https://hockeyviz.com/txt/sG), with our season-level interpretation. the basket is 1000 minutes 5v5, 100 minutes pp, 100 minutes pk. every term is favorable-positive:

| term | goals per reference basket |
|---|---|
| 5v5 offense / defense | `(1000/60)*delta_xgf`; `-(1000/60)*delta_xga` |
| pp offense / pk defense | `(100/60)*mixture(delta_pp)`; `-(100/60)*mixture(delta_pk_against)` |
| finishing / setting | the common-context, modeled-opportunity formulas below; never actual own-season opportunity shares substituted silently |
| penalties drawn / taken | the isolated-minor formulas above |
| ice won / lost | integrated successor maps; negate the against quantity |

freeze the execution reference units: 5v5 has 3f/2d; 5v4 and 5v3 have 4f/1d; 4v3 has 3f/1d; 4v5 has 2f/2d; 3v5 and 3v4 have 1f/2d. insert the focal player into one slot of their reported position, with all other player deviations zero. unknown role leaves this standardized execution component unavailable, not arbitrarily assigned to forward. these are common hypothetical deployments, not each player's actual role mix.

let `H_s` be reference hours: `1000/60` at 5v5 and the appropriate share of `100/60` for each pp/pk state. let `A_s` be neutral team attempts/hour: the count-model reference for ev/pp, and matched source-pooled attempts/exposure for shorthanded offense, which has no individual creation model here. each state uses the chance appendix's common annual, outcome-blind origin/context panel. for focal player `i`, let `p_i` be their fitted shootiness probability in that unit. for possible shooter slot `j!=i`, let `t(i|j)` be the normalized positional setter weight among the other unit slots, using the chance appendix's fixed forward-shooter `2:1` and defender-shooter `3:1` rules. set

```text
setter_share_i = .8 * sum_{j != i} p_j * t(i|j)
finishing_i = sum_s H_s*A_s*p_i*mean_shooter_contrast(i,s)
setting_i   = sum_s H_s*A_s*setter_share_i*mean_setter_contrast(i,s)
```

the shooter contrast is per potential attempt; the setter contrast is conditional on an assisted opportunity, so the `.8` factor appears only once. integrate conditional-outcome products within each common panel row before averaging. this recipe has no setter×shooter-role interaction and uses one common panel for every slot, so the displayed setter factorization is exact for that reference. chance-owner outputs per100 divide by100 here. modeled shootiness can alter opportunity allocation, but own-season toi or actual personal attempts cannot substitute. this finite common-unit reference excludes former off-ice candidates; the chance fitting/evidence universe still retains them. this is a reference assumption, not denial of observed off-ice assists.

sum these ten values exactly. this is a defined component index: creation×own execution, penalties×own specialty skill and other cross-component interactions are omitted. their absence is a convention, not a numeric “unexplained residual.” per-event shapley accounting remains separate descriptive model evidence. shootiness, conditional outcome stages, coaches and territorial subskills are explanations, not additional addends. no label of gar, war, realized goals or causal total follows.

content example, explicitly synthetic: `5 + 3 + .5 + .3 + 1 + .8 + .4 - .2 + .2 - .1 = 10.9`. the card must show those same signed components and workload, not only the total. no interval exists until an actual uncertainty method supplies it.

the user-selected replacement proxy is team depth. for each season/team, rank forwards and defensemen separately by **all-strength regular-season boxscore toi**, not fitted value or included 5v5 time. a player is depth on that team when below its top 12f/top 6d cutoff; ties at the cutoff remain regulars. use the player's majority-toi reported position group, record mixed/unknown status, and exclude unknown/incomplete ranking inputs rather than silently substitute another denominator. zero-time scratches do not create reference weight.

for player `i`, weight is summed all-strength toi on team stints where that player is depth. pool by position, using this one weight for the player's complete annual ten-component vector; trades do not duplicate that vector. the depth reference is the weighted mean vector. subtract each reference component from its league-relative counterpart; replacement total is their sum. identical weights across components preserve accounting. missing required component values make the complete depth comparison unavailable rather than silently changing its population. report reference members, weights, time and coverage. this proxy reflects injuries, deployment and trades; it is not available replacement labor, a prior for entrants or an exact competitor replacement definition.

## interfaces, ownership and acceptance

`analysis_data.py` owns prepared elapsed/event/mechanism facts and source joins; reuse `reconstruct`, `game_chronology`, `feature_data`, `feature_history` and `scoring_credits`. `spatial_rates.py` owns positive rate objectives, annual states and projections. `player_mechanisms.py` owns penalties, territory and shootiness; `player_value.py` owns references and the sole ten-term ledger. reuse `attribution` geometry/identity helpers, not its incompatible gaussian likelihood. ordinary functions and the parent command suffice:

```text
fit_spatial(prepared, valued_attempts, recipe, previous_state) -> spatial_state
fit_mechanisms(prepared, spatial_state, chance_state, previous_states) -> mechanism_states
project_spatial(state, reference) -> native_maps, scalars, adjustment_groups
compose_value(spatial, execution, mechanisms, depth_reference) -> component_results
```

inputs bind game/event/interval locators, source support, hours, membership, native-cell mass, design/basis and predecessor identities. states bind axes, priors, training cutoff, centers, objectives and numerical status. results bind person/season/state, units/sign, reference, source/model identity, support, inference and absent uncertainty. output complete and signed maps separately. publication transports these values; it does not recompute hockey accounting.

bounded checks independently establish zero-event exposure, source-order goals, same-clock shifts, special-team reciprocity, missingness, origin mass, gradients, centering invariance, strict complete-rate positivity and chance≤attempt rates, native-map/scalar closure, absorbing probability/survival, penalty cancellation/value and traded-player reference weights. independently recompute one small objective/projection per family; the parent specification owns the bounded stricter-tolerance continuation and its comparison thresholds. inspect real skaters, sparse specialists, entrants and traded players; retain poor results with truthful diagnostics. no scientific-success gate or automatic extra campaign. follow the parent red/green/refactor, fixture-preservation and temporary-test deletion policy.
