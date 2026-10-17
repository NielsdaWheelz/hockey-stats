# product roadmap

status: approved intermediate direction and proposed later milestones. version labels describe capabilities, not deadlines, giant releases or model/schema versions. the [brief](brief.md) fixes the destination; the [implementation plan](plan.md) owns current status, assignments and sequencing. the [capability inventory](product-inventory.md) lists components, cards and supporting views. this roadmap does not authorize execution or expand capture scope.

parity scope confirmed 2026-09-29: **complete player analysis**, covering hockeyviz/jfresh skater and goalie cards, components, context, history and comparisons. whole-site parity is not the destination. this means comparable analytical capabilities under our stated definitions, not identical private-model numbers.

## proposed progression

| milestone | what becomes useful | why here / what it needs |
|---|---|---|
| intermediate — private observed results | localhost completed-season table/search, player profile, recorded on-ice 5v5 attempts, matched exposure/rates and game evidence with coverage | [05a](specs/05a-observed-website.md) uses supported source/reconstruction outputs independently of model admission; omit ability and xg. this does not replace v1 |
| v1 — explain a player's 5v5 contribution | completed-season offense/defense estimates and maps, recorded results, league table, name search, compact comparison and game evidence | establish the scientific and product foundation; this is the current plan, not merely the capture slice |
| v2 — compare and share | declared-cohort distributions and percentiles, richer comparisons, a compact downloadable 5v5 player card | get more use from the existing analysis before adding new models; retain magnitude, units, uncertainty and component scope alongside ranks |
| v3 — follow the season | publish current-season estimates whenever the operator runs an update; show incorporated evidence and coverage | requires validated behavior with partial-season evidence, entrants and source corrections; rerunning the full-season recipe is not enough by itself |
| v4+ — broaden the component profile | penalties drawn/taken, power-play offense, penalty-kill defense and finishing, each added separately | each needs its own definition, reference, data support and evaluation; choose the next component from that evidence, not a mandatory bundle |

v2 and v3 are independent after v1. the recommendation favors useful comparison tools first; current-season work can take priority if that is the more pressing use once v1 exists. the cost of the proposed order is delaying current-season analysis while improving the completed-season product. each milestone can ship through several small slices.

source capture, reconstruction and feature preparation support the first product; [the plan](plan.md) owns their current status and study results. [the feature inventory](model-features.md) distinguishes implemented encoders, inactive families and missing source/inference dependencies.

## scientific path to v1

the post-04b direction prioritizes useful spatial signal recovery and scoped uncertainty. [04c](specs/04c-attribution-recovery.md) tested one fixed geometric shape basis against zero and native 04b after diagnosing saved evidence. the user selected broad shape first: complete regional rates and fine cells remain secondary, and nomination would not establish complete player-map accuracy. improvement over 04a alone does not demonstrate recovery beyond zero; [the post-study finding](issues/attribution-spatial-recovery.md) leaves all frozen verdicts intact. numerical checks belong inside the work.

04c's representation traded fine spatial freedom for shared evidence across rink geometry. its known-truth assessment included broad/local and poorly represented patterns, annual transitions and inseparable linemates. its contingent refit-uncertainty and real-point-fit stages were not reached; they do not automatically transfer into later studies. native-grid rendering supplies no independent cell precision, and the 5% meaningful scalar contrast supplies no spatial error budget.

[04c's completed decision](research/attribution-04c/decision.md) fails the mean-recovery gate after all 800 paired datasets. gated uncertainty and real fitting are not reached. [04d's diagnosis](research/attribution-04d/decision.md) separates small broad geometric omission, limited precision and selected-scale suppression; annual carry supports its frozen targets. this motivates one pooling question, not an adopted model.

[04e](specs/04e-attribution-pooling.md) specifies two spatial pooling bands within the same representation. new synthetic populations must support at least 25% lower regional error than zero, improvement over unchanged pooling and at least 99% retention of its prediction gain. null behavior stays visible. this slice deliberately tests means/prediction first; calibrated player intervals, real-data evidence and complete rates remain later responsibilities even after a nomination. no real or nested fitting is bundled into it. the private observed website remains independent.

the remaining analytical responsibilities are distinct; their concrete next studies depend on evidence rather than a mandatory bundle:

| responsibility | remaining claim / dependency |
|---|---|
| spatial attribution and complete rates | useful recovery, scoped uncertainty, joint map/scalar accounting and adequate complete-rate behavior; smoothing alone does not guarantee positive intensities |
| deployment adjustment | use justified shift-start/time, score/time, rest and penalty-aftermath facts across all supported exposure, including zero-event time; coach terms require admitted dated evidence |
| temporal ability | annual age-neutral borrowing already exists; assess age-related change, entrant/returner behavior and entry/exit selection against it. older history needs a named temporal consumer |
| chance valuation and downstream consequences | supported integrated opportunity values, block-origin/type/tip sensitivity and common-reference valuation; retain 03p's structural nomination without treating it as admission |
| real-player support | predictive/portability evidence, shared-deployment limitations and justified consequence budgets; synthetic recovery and provisional weights cannot supply these alone |

04a/04b's matched recorded-rate populations and provisional valuation remain research evidence. neither location-only stresses nor agreement between unadmitted weights bounds error against truth. the [04 supported-attribution contract](specs/04-player-attribution.md) preserves the all-attempt chance-valued destination. [model direction](research/model-direction.md) retains alternative chance structures and targeted inactive features; no blanket activation or new acquisition is implied.

[05a](specs/05a-observed-website.md) progresses independently from those model questions using observed evidence. [05](specs/05-publication.md) and [06](specs/06-website.md) later extend its publication/view owners with supported ability, maps and comparisons. selected lasting checks under [07](specs/07-lightweight-testing.md) arrive with their owning boundaries; the whole testing slice is not a prerequisite. [the plan](plan.md) owns assignments.

tradeoff: the intermediate website delivers earlier utility and feedback, with possible schema/view rework when supported estimates arrive. spatial pooling adds a testable smoothness assumption and may lose local detail. neither direction lowers the evidence required for ability publication or changes the first analytical product.

## milestones that need not wait

the analytical release path is supported outcome/opportunity measurement, including blocked-origin/type/location sensitivity → spatial stint attribution with exposure (including zero-shot time), teammate/opponent/deployment context and history → useful profiles/maps/observed game evidence → broader cards and component families. per-shot conversion is upstream valuation, not player creation/suppression. [magnus9](https://hockeyviz.com/txt/magnus9EV) motivates that distinction. richer historical claims need an explicitly admitted historical corpus; nineteen peer seasons are not a prerequisite for the first useful profile. research-only attribution feasibility can investigate the downstream model earlier, as described above.

05a may deliver real source-supported observed results privately once fully specified and assigned; it needs no chance-model handoff. later analytical views can be designed with labeled fixtures, but real ability release requires supported analysis. neither path permits withheld fitted effects under an observed or fixture label.

- **public website:** publish once the personal product is useful and ready to share. hosting and data-publication details get their own small specification then. full cards are not a prerequisite. fitting stays local; hosting does not create an update schedule.
- **historical player analysis:** publish prior-season profiles/cards, maps, component explanations, recorded results and trajectories when comparable outputs exist. define supported seasons and visible gaps through corpus admission. historical training data alone does not supply these outputs; historical season rows in the active publication do not require archived website builds or publication revisions.
- **goalie cards:** confirmed later as a separate analytical family. begin with stopping and its evidence, then add spatial/type/danger detail, supported subskills, workload and history. choose their place after v1 according to value and available evidence; they need their own validation, not completion of every skater component first.

## longer-term destination

the [card references](research/player-card-references.md) describe the intended combination: hockeyviz-style spatial explanation and inspectable components, with jfresh-style concise comparative cards, history and sharing. fuller cards add setting, shooting tendencies and transition contributions as their estimates become defensible. publicly available event data may support inferred components without supporting claims of directly tracked passing or entries; optional enrichment remains separate from the public-data core.

a common-value summary follows only if the components support coherent accounting and a declared reference. no sum of percentile ranks, double-counted contributions or premature total-player-value label. replicating capabilities is the destination; numerical parity with a private model is not an acceptance test.

## player-analysis completion checkpoints

these were missing or underspecified in the milestone outline. they are later capability targets, not one additional giant release. the inventory owns the detailed checklist.

| capability | completion means | dependency / cost |
|---|---|---|
| explain results versus ability | expose supported teammate, opponent, coaching/deployment and other context behind the adjustment; show a residual only where its meaning is defined | needs published explanatory model outputs; contributions add only where the model supplies valid accounting; residual is not a synonym for luck |
| descriptive statistics workspace | individual/on-ice/workload tables, season rows, game evidence, useful count/rate views and downloadable tables | reuses interpreted evidence and publications; selections must not silently change an estimate's fitted population |
| personal and contextual detail | personal shot maps; together/apart results and maps; replacement context; deployment and teammate/opponent comparisons | additional published summaries and exposure; shared deployment still prevents a causal-chemistry interpretation |
| full component detail | spatial special-teams effects, transition subskills, finishing/setting explanations and shooting/goalie outcome detail by supported type/danger | separate scientific validation; exact states, bins and field definitions belong to each slice |
| historical and broader recorded coverage | navigable historical profiles; traded-player team evidence alongside season estimates; later playoff and other strength-state results clearly separated | source admission and backfilled outputs; displaying playoff results does not authorize pooling them into regular-season ability fits |

these targets follow the public hockeyviz [career](https://hockeyviz.com/player/matthau97) and [season](https://hockeyviz.com/player/mcdavco97/EDM/2425) surfaces, jfresh's [historical-card offering](https://hockeystats.com/cards/historic-player-cards), and the current [player-statistics workspace](https://hockeystats.com/players/jackson-lacombe). historical archive access and full interactive workflows were not verified. exact earliest seasons remain evidence-dependent. preseason recorded views remain candidates; no preseason ability model is selected.

## deliberate differences and excluded site families

hockeyviz describes ability at a [particular instant](https://hockeyviz.com/howto/isolate); jfresh describes [predictive war and scoring](https://hockeystats.com/about/player-cards). our headline describes underlying level across a season. current-season updates do not change that estimand. forecast outputs or a point-in-time state estimate would require a separately selected target; matching layouts cannot establish scientific equivalence. similarly, a common-value summary does not establish replacement-based valuation until that reference is defined.

arbitrary date ranges remain excluded; tracked microstats remain optional; contract context remains unselected. these are explicit differences from parts of the references. the cost is narrower functionality in exchange for retaining the settled product meaning and public-data core.

whole-site exclusions include team/league dashboards, game/series reports, coach evaluations, game/playoff forecasts, scenario/roster builders, prospects, scouting and other leagues. these are substantial additional products, evidenced by hockeyviz's [team page](https://hockeyviz.com/team/TOR/2526) and [tool offerings](https://hockeyviz.com/subscribe), and hockey stats' [broader product](https://hockeystats.com/). their existence does not expand the selected player-analysis destination. operator-run publication also makes no promise of either site's live delivery cadence.

## scope discipline

retain the same operating model throughout: local batch analysis, saved expensive fits, sqlite publication and an ordinary website. add a feature's concrete contract and implementation slices when it becomes next. no future-proofing framework or full future backlog now.

prospects, fantasy tools, contracts, lineup simulation, arbitrary date-window fits and paid services are not implied by this roadmap. ordering and candidate details remain proposals; the confirmed skater/goalie destination and agreed v1 scope stay fixed.
