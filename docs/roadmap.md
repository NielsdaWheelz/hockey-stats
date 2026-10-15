# product roadmap

status: proposed order beyond the agreed first product. version labels describe capability milestones, not deadlines, giant releases or model/schema versions. the [brief](brief.md) fixes the destination; the [implementation plan](plan.md) divides v1 into slices. the [capability inventory](product-inventory.md) lists components, cards and supporting views with explicit scope status. this roadmap does not expand the current capture specification.

parity scope confirmed 2026-09-29: **complete player analysis**, covering hockeyviz/jfresh skater and goalie cards, components, context, history and comparisons. whole-site parity is not the destination. this means comparable analytical capabilities under our stated definitions, not identical private-model numbers.

## proposed progression

| milestone | what becomes useful | why here / what it needs |
|---|---|---|
| v1 — explain a player's 5v5 contribution | completed-season offense/defense estimates and maps, recorded results, league table, name search, compact comparison and game evidence | establish the scientific and product foundation; this is the current plan, not merely the capture slice |
| v2 — compare and share | declared-cohort distributions and percentiles, richer comparisons, a compact downloadable 5v5 player card | get more use from the existing analysis before adding new models; retain magnitude, units, uncertainty and component scope alongside ranks |
| v3 — follow the season | publish current-season estimates whenever the operator runs an update; show incorporated evidence and coverage | requires validated behavior with partial-season evidence, entrants and source corrections; rerunning the full-season recipe is not enough by itself |
| v4+ — broaden the component profile | penalties drawn/taken, power-play offense, penalty-kill defense and finishing, each added separately | each needs its own definition, reference, data support and evaluation; choose the next component from that evidence, not a mandatory bundle |

v2 and v3 are independent after v1. the recommendation favors useful comparison tools first; current-season work can take priority if that is the more pressing use once v1 exists. the cost of the proposed order is delaying current-season analysis while improving the completed-season product. each milestone can ship through several small slices.

source capture, reconstruction and feature preparation support the first product; [the plan](plan.md) owns their current status and study results. [the feature inventory](model-features.md) distinguishes implemented encoders, inactive families and missing source/inference dependencies.

## scientific path to v1

the user approved two research tracks after 03o. [03p](specs/03p-chance-structure.md) specifies mirror pooling with its bounded numerical check; [04a](specs/04a-attribution-feasibility.md) remains an attribution/sensitivity stub with settled preferences. exact execution contracts belong to the full specs; documentation does not authorize execution.

04a does not require chance-model admission for its recorded-rate/synthetic claims. provisional chance-weight sensitivity retains its input limitations; it cannot admit rejected models or supply published ability. supported opportunity measurement, coherent spatial player attribution and player robustness still precede real analytical release.

the selected provisional comparison values only the final-season unblocked spatial effects after the count-rate fits, using existing direct/decomposed transfer models under a shared reference. this provides location-only sensitivity evidence without additional historical chance fits; it does not capture player-specific shot-type/context mix or depend on 03p results. [04a](specs/04a-attribution-feasibility.md) owns its scope and limitations.

age-informed historical borrowing remains an explicit attribution follow-up under [04](specs/04-player-attribution.md#decisions-for-the-full-specification). 04a starts with age-neutral annual borrowing across the five admitted seasons. later work must evaluate age-related development/decline and changeability against that baseline, including entry/exit selection and uncertainty. deferral avoids an additional aging model in 04a; it accepts possible lag in systematic development or decline, not a claim that age is irrelevant.

future representation selection may value useful components within a prospectively justified prediction-cost budget. player-effect resolution should make upstream error tolerances relevant to the intended use; historical criteria and verdicts remain unchanged. numerical checks are bounded parts of model work, not a new serial research programme.

the selected structural experiment is mirror pooling within shot type in both on-net and goal-given-on-net components. wrist/snap analytical pooling, temporal structure, targeted unused features, tip policy and further outcome layers remain alternatives in [model direction](research/model-direction.md), not a mandatory campaign. more historical acquisition needs a concrete consumer. the [capability inventory](product-inventory.md#analytical-dependencies) records the remaining model/product gaps.

05–06 can separately exercise a clearly labeled fixture publication/profile. a few lasting source/numerical checks under [07](specs/07-lightweight-testing.md) can precede the website; browser/publication checks arrive with those boundaries. current assignments and order live only in [the plan](plan.md).

tradeoff: parallel research provides earlier evidence about player consequences and product meaning, while adding provisional outputs and limited coordination. it does not lower the evidence required for release or expand the first product.

## milestones that need not wait

the analytical release path is supported outcome/opportunity measurement, including blocked-origin/type/location sensitivity → spatial stint attribution with exposure (including zero-shot time), teammate/opponent/deployment context and history → useful profiles/maps/observed game evidence → broader cards and component families. per-shot conversion is upstream valuation, not player creation/suppression. [magnus9](https://hockeyviz.com/txt/magnus9EV) motivates that distinction. richer historical claims need an explicitly admitted historical corpus; nineteen peer seasons are not a prerequisite for the first useful profile. research-only attribution feasibility can investigate the downstream model earlier, as described above.

05–06 may independently settle publication/view semantics and presentation using labeled fixtures once separately specified/assigned. final scientific 04 outputs need not precede that development; real release still requires supported analysis. this is optional visible product work, not an added mandatory phase.

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
