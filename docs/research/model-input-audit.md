# public methods versus our actual inputs

audited 2026-09-30 against implementation `9132131`, three local game captures, season references and retained 03b evidence. three independent reviewers examined hockeyviz, evolving hockey, and our capture → interpretation → preparation → model path. the drive is detached: fixture presence is not historical completeness. this is a bounded public-method audit, not access to either site's private production system.

current follow-up: [03c is merged](chance-03c/decision.md), with all three seasons admitted locally, expanded fixtures and verified report/landing coverage. the tables below retain the dated chance-1 baseline; their pending source claims are superseded by that evidence. [03d's selected-feature contract](../specs/03d-chance-revision.md#selected-features-and-preceding-context) records the revised candidate's include/assess/omit decisions. no source recovery establishes scientific support.

**we do not use the same complete inputs or features.** `chance-1` is a smaller, rejected candidate. earlier research documented several simplifications, but failed to connect the public-method inventory to every relevant source field. the blocked-shot-type omission is an audit failure, not a necessary consequence of a public-data core.

## reference versions and meaning

- hockeyviz [xg8](https://hockeyviz.com/txt/xg8), published 2025-05-26: four conditional outcomes, type-specific geometry, recent-event/rebound/sequence context, score/time terms, shooter/setter/goalie/coach effects, annual fitting and historical priors; imputed block and some tip locations. its setter imputation uses manually tracked assist proportions from corey sznajder as calibration evidence. that is not complete observed passing in nhl play-by-play.
- hockeyviz [magnus9EV](https://hockeyviz.com/txt/magnus9EV), published 2025-08-27: spatial shot-rate attribution with offensive/defensive players, deployment, coaches and historical/aging structure. this is a different layer from per-attempt probability.
- hockeyviz's [2026–27 preview](https://hockeyviz.com/txt/preview2627) announces rewritten models with explanations forthcoming. it refers to nineteen historical regular seasons. the older public descriptions do not establish the newer production recipe.
- evolving hockey's [xg article](https://evolving-hockey.com/blog/a-new-expected-goals-model-for-predicting-goals-in-the-nhl/) originated in 2018 and was republished in 2021. [public preparation code](https://github.com/evolvingwild/hockey-all/blob/13b713f94324e929aca57789b1363c7bc8f97962/xG/xG_preparation.R) is pinned to its 2018 revision. their [version table](https://evolving-hockey.com/about/) lists xg 2.0 from 2019. exact current feature parity is unknown.

our game captures contain api play-by-play, boxscores, shift charts, pl and gs reports; season inventories and bios are separate references. the historical eh article used nhl rtss data with espn coordinate supplementation; its later version history reports a source change. this is overlapping evidence, not identical acquisition. no espn fallback or private peer dataset is admitted here. [historical acquisition](https://evolving-hockey.com/blog/a-new-expected-goals-model-for-predicting-goals-in-the-nhl/), [version history](https://evolving-hockey.com/about/)

our implemented probability stages use spatial cell, trailing/tied/leading score and shooter identity; conversion additionally uses goalie identity. role × score conditions the origin prior. type is diagnostic only. see [feature construction](../../analysis/src/hockey_stats/chance.py), [preparation](../../analysis/src/hockey_stats/chance_data.py) and [03a's explicit omissions](../specs/03a-chance-workflow.md). knowing that a field exists is not the same as using it.

## feature comparison

| family | published reference | our implemented state / next decision |
|---|---|---|
| geometry and type | xg8: type-specific spatial terms; historical eh: coordinates, distance, angle, seven types | pooled grid; geometric benchmark only. api type diagnostic; report type not structured. 03c repairs evidence, next model decides conditioning |
| preceding event | xg8: short-window rush/cycle, rebound delay and shooter continuity; eh: prior location, time gap, displacement, kind and team relationship | no predictors. much source evidence already interpreted; next model must define ordering, interruptions and missingness |
| extended possession proxy | xg8: shot sequence tied to continuing defending membership | no sequence feature; reconstruction supplies some necessary membership evidence, not continuous possession truth |
| game context | xg8: score/period and period-boundary terms; eh: home, period, game time, detailed score margin | coarse score only; other facts largely retained. assess in next model |
| outcomes | xg8: block, miss, freeze, goal layers; eh: unblocked goal probability | block avoidance × unblocked conversion. can target the same marginal probability as four layers, but does not estimate the same intermediate subskills |
| people | xg8: shooter, setter, goalie, coaches; historical eh xg matrix omits shooter/goalie identity | shooter/goalie terms only; no setter/coach effects. adding them changes both conditioning and standardization |
| inferred geometry | xg8: geometric block imputation and tip relocation | different forward block kernel; tip coordinates remain warned proxies, with no relocation. neither is a replica |
| recording effects | [hockeyviz's historical scorer-bias method](https://hockeyviz.com/txt/scorerBias) constructs coordinate corrections using rink/home-away effects and optimal transport | no rink correction. attacking-frame rotation is not bias correction; current peer deployment remains unverified |
| history | eh's historical training used seven or ten seasons, depending on situation | three admitted seasons; no annual actor evolution in `chance-1`. next model/04 justify history needed for their claims |
| strength | eh has separate even-strength, advantage, shorthanded and empty-net models | genuine 5v5 only is the agreed first scope; special teams and goalie cards remain later |
| player attribution | [eh rapm](https://evolving-hockey.com/glossary/regularized-adjusted-plus-minus/): stint-weighted offense/defense, score, strength, faceoff-zone and rest terms; magnus9EV supplies a spatial alternative | membership/exposure exists; contextual player attribution is unimplemented 04 work, not a hidden capability of the chance model |
| attribution deployment/history | [magnus9EV](https://hockeyviz.com/txt/magnus9EV): recent rest, shift-start zone/time, home × period, score × minute, post-penalty effects, coaching, aging and prior-season estimates | supporting facts partly admitted; 04 must define its own supported contextual terms and priors |
| additional chance context | [topdownhockey's 2026 methodology](https://hockeystats.com/methodology/expected-goals): shooter/opposing-unit shift age, detailed preceding outcomes, displacement/time, lateral crossing and off-wing geometry | candidate definitions absent from our model; existing shifts, reasons, coordinates and bios supply much of the evidence. missing interval links and zero-time gaps remain explicit |

our reference opportunity averages each empirical training shooter–goalie pair's probability product. xg8's weighted effect centering does not establish that same reference operation. pooled static actor effects also differ from annual estimates informed by historical priors. these are estimator/estimand choices, not missing api fields; the next model must justify both. none of the omitted features has yet been shown to repair 03b's failures.

the eh historical predictor groups are explicitly inspectable: `shot_distance`, `shot_angle`, `game_seconds`, `game_period`, `coords_x/y`, previous `coords_x/y`, `distance_from_last`, `seconds_since_last`; categorical home, strength, score, type, previous-event kind and same/opposing team. special-teams recipes add penalty timing/prior-strength context. its selected-event lag is not tracked puck motion. its missing-type-to-wrist rule must not be copied. [pinned code](https://github.com/evolvingwild/hockey-all/blob/13b713f94324e929aca57789b1363c7bc8f97962/xG/xG_preparation.R)

historical eh excludes blocks as focal xg targets; our latent blocked-origin problem is additional work, not something that recipe solves. subsequent gar/spm also uses component-specific selections from observed/on-ice statistics and long-term rapm targets. those belong to later valuation, not indiscriminately to shot prediction. [xg population](https://evolving-hockey.com/blog/a-new-expected-goals-model-for-predicting-goals-in-the-nhl/), [gar process](https://evolving-hockey.com/blog/wins-above-replacement-the-process-part-2/)

## captured facts not fully consumed

this inventory distinguishes interpretation gaps from omitted predictors. full payloads remain preserved; the omissions below have not erased them. not every field is useful, nor do the public references establish that both peers consume it.

| evidence | actual state | next consumer / disposition |
|---|---|---|
| pl shooter/team/type | description only; 111 fixture block types overlooked | 03c structured evidence and unique joins; full-season coverage still to verify |
| pl distance and own-goal wording | raw description, no structured fields | 03c audit examples; next model specifies coordinate/actor semantics. [own-goal issue](../issues/own-goal-attribution.md) |
| turnover `details.playerId` | captured; omitted from event roles | interpretation when a selected context or turnover component needs the actor; team/kind context need not wait |
| stoppage `reason` / `secondaryReason` | primary interpreted; secondary remains raw | next model if defining freeze/rebound outcomes; explicit sequence rules required |
| penalty actors/type/duration / `descKey` | actors/type/duration interpreted; description key raw | later penalty component or a demonstrated context need |
| block/miss reasons and blocker | interpreted, not predictors | source diagnosis/observation model; current outcome cannot predict itself |
| goal credit and assist identities | interpreted; scorer used as shooter; no setter inference | actor-semantics review now; later setting component requires its own evidence/assumptions |
| on-ice lists, situation and shifts | reconstructed membership/exposure, with visible gaps | already define eligibility; 04 attribution; selected next-model sequence features |
| home, clocks, score | retained; only coarse pre-event score modeled | next model feature decision; no post-goal score leakage |
| venue, location, absolute start/timezone | captured, omitted from interpreted game | admit if using rink, neutral-site, travel or precise-rest context; home team is not venue identity |
| birth date and shoots/catches | bios interpreted and corpus-resolved, unused by chance model | next model/04 decide age or handedness use; no new bio feed needed |
| skater boxscore detail | goals/assists/sog/blocks/toi/shifts interpreted; hits, turnovers, pim, faceoff percentage and other totals raw | later observed cards and reconciliation, not postgame shot predictors |
| goalie boxscore detail | saves, shots/goals against, strength splits, starter/decision raw | later goalie cards and reconciliation |
| gs strength/goalie summaries | captured `reference_only`; officials/attendance also present | selected corroboration; reported even-strength is not our genuine-5v5 denominator |
| coaches/scratches | structured `right-rail` and roster report inspected, neither admitted | 04 is the existing owner; move admission earlier only if 03d needs coaches. scratches remain later |
| replay/clip locators | raw `pptReplayUrl` and highlight identifiers | bounded evidence investigation; a locator does not prove usable video access |
| other bio/display fields | physical measurements, birthplace, draft/current affiliation and display metadata mostly raw | later concrete product needs; current affiliation cannot establish historical membership |

inspection anchors: [interpretation fields/roles](../../analysis/src/hockey_stats/interpret.py), [structural report extraction](../../analysis/src/hockey_stats/play_report.py), [bio admission](../../analysis/src/hockey_stats/references.py), [corpus players](../../analysis/src/hockey_stats/corpus.py). reproduce the field inventory from the union of keys in the three `fixtures/captures/*` bodies and their descriptions, then trace the named fields through these modules and chance preparation.

complete passes, screens, player/puck trajectories, entries/exits and paired physical block-release/contact observations are not established inputs here. neither cited xg recipe establishes that these are ordinary public fields we discarded. inferred rushes, setters and origins must remain labeled inference. public-data core does not mean every external calibration dataset is open or reproducible.

## offline audit boundary and remaining inputs

bounded live follow-up, 2026-09-30: gamecenter `landing` supplies a previously uncatalogued goal modifier; `right-rail` supplies structured coaches/scratches. [exact source evidence](source-audit.md#additional-source-evidence-without-the-drive) establishes their distinct uses. [03c](../specs/03c-source-revision.md) now specifies landing capture/interpretation; implementation remains pending. right-rail remains a candidate when coach context is selected. this is additional source evidence, not another model feature guessed from card appearance.

the local field pass covers nineteen bodies across nine source families: thirteen json responses and six html reports. treating array positions as `*`, distinct scalar-or-empty paths number 118 for play-by-play, 173 for boxscores, 20 for shifts, 14 for season games, and 24 each for season metadata, skater bios and goalie bios. these counts describe an enumerated surface, not semantic correctness, all html vocabulary, historical coverage or the universe of upstream fields.

additional raw families now accounted for: source/control flags (`limitedScoring`, regulation/max periods, overtime/shootout flags), root display/clock snapshots, running shot/scorer/assist totals, and bio `firstSeasonForGameType`. do not invent admission rules from undocumented flags or treat post-event totals as pre-event predictors. roster presence establishes reported membership, not actual participation; unused backup goalies are present locally.

clock counterexample: game `2025020001` has api `startTimeUTC: 2025-10-07T21:00:00Z` (17:00 edt), while gs prints start 17:20. game `2025021094` is complete with root clock `04:19` remaining; all three fixtures have `displayPeriod: 1`. source/scheduled timestamps, reported actual start, display snapshots and event clocks are distinct. precise rest/travel needs an explicit time definition; event ordering cannot use the root clock.

recording comparability needs its own decision. [topdownhockey's 2026 account](https://hockeystats.com/methodology/expected-goals) reports changing short-miss frequencies and coordinate distributions, and excludes short misses from its focal shot population. that is a hypothesis and population choice to investigate, not an exclusion to inherit. season differences alone do not separate recording changes from changed play. its prose and pseudocode give inconsistent fold counts, so it is not an executable validation specification. our three seasons do not automatically share measurement semantics.

the remaining product inputs have owners rather than immediate parsers:

| input family | first consumer and boundary |
|---|---|
| territorial/state transitions and post-penalty intervals | 04 deployment where selected; later ice-won/lost components. public events support inference, not tracked possession |
| goalie starts/relief, freezes/rebounds and opportunity exposure | later goalie component; boxscore totals alone do not define event-level denominators |
| eligible comparison cohorts, league environment and reference workload | published comparisons/common-value summaries when implemented; derive from admitted evidence, no new feed implied |
| sampled passing/entry/retrieval observations; skating measurements | optional tracking cards. [jfresh's microstat definitions](https://hockeystats.com/about/microstat-player-cards) distinguish all three zones tracking from nhl edge speed |

allocation: 03c specifies its exact source/field contracts; [03d](../specs/03d-chance-revision.md) retains the revised candidate's input decisions. each selected quantity needs its source path or derivation, observed/derived/imputed status, units/frame/time meaning, join identity, missing/conflicting behavior, information timing and consumer. [03e](../specs/03e-training-assessment.md) owns empirical judgment; [04](../specs/04-player-attribution.md) owns attribution context. no schema registry or universal importer.

finish when every reviewed public-method family and every analytically relevant local field has a disposition, and each genuinely additional source names the missing fact it supplies. do not claim “all possible inputs.” full-corpus vocabulary, missingness by season/outcome, source corrections and scientific adequacy remain unverified until the drive returns. new live samples are new observations, not substitutes for the frozen 03b captures.

## action and tradeoff

03c still implements its bounded source repairs, not all table rows. its decision must record source coverage, the newly recognized coordinate/actor questions, and remaining field omissions. before another fit, the next model specification must give each relevant comparison family a disposition: include, assess, or omit with a reason and owner. distinguish factual predictors, outcome labels, reconstruction evidence and fields averaged out of reference opportunity. specify when each field is knowable and its availability across target outcomes: goal-only assists and next-stoppage evidence cannot automatically predict an earlier outcome.

shot type, rushes and rebounds can describe opportunities a player helps create. valuing those opportunities and then controlling those mechanisms away in 04 changes what the player receives credit for. averaging actor coefficients also does not remove every talent association carried by locations/types/context. declare the reference construction and contribution target; do not claim complete causal isolation.

this is one review table, not a feature store or automatic schema registry. the tradeoff is explicit: small models remain permissible, but their information loss must be justified. unavailable tracking, paid calibration, extra seasons and deferred product families do not become requirements merely because a peer uses them. source facts are admitted when their analytical consumer needs them; known omissions can no longer disappear between source and model specifications.
