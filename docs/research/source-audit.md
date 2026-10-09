# source audit for reconstruction and later models

date: 2026-09-29, local time. purpose: account for useful public evidence before choosing another inference rule. this is a bounded audit, not a claim that every nhl endpoint has been surveyed. source availability is not historical coverage or scientific validation.

## corrected omission

the [archived catalogue](https://github.com/NielsdaWheelz/hockey-stats-legacy/blob/1d45312ed4a2d797150e377c87ecdba231b5ebfc/docs/design/data-sources.md) already named the official play-by-play report as the source of explicit event on-ice lists. we failed to carry that requirement into the new source selection. separating interpretation from reconstruction was appropriate; assuming the four captured sources would suffice was not. the [boundary audit](../../fixtures/README.md#manually-corroborated-exposure-and-boundary-facts) supplies concrete counterexamples.

the user confirmed adding this report to pr2b. use reported event membership and reconstructed elapsed exposure as separate quantities. no blanket endpoint convention, automatic shift fallback or inference presented as observation.

## inputs and their next consumer

| evidence | useful fact / decision | limit and cost |
|---|---|---|
| [official play report](https://www.nhl.com/scores/htmlreports/20252026/PL020001.HTM) | added in merged 02b: event player lists, clock/type/description and strength observations | one additional capture and focused parser; ambiguous cross-source matches remain unavailable |
| existing play-by-play/boxscore bodies | exposed game-scoped sweater numbers and team abbreviations in 02b; preserved period markers, goalie/situation evidence, event order and locations | these facts needed no new feed |
| [season bios audit](corpus-reference-audit.md) | 02c: bulk skater/goalie reports supply birth date and shoots/catches; 03–04 own analytical use | exact filtered requests establish scope; rows do not echo season/type. missing fields remain null; current affiliation is not historical membership |
| [player landing](https://api-web.nhle.com/v1/player/8473419/landing) | documented direct bio source; bulk reports replace per-player acquisition in 02c | no automatic fallback or extra command. use later only for a demonstrated missing fact; derive age at an analytical date, not retrieval time |
| [season inventory audit](corpus-reference-audit.md) | 02c: game collection plus season metadata establish expected-game identities and missing-capture denominators | checks collection totals and identity; no manufactured ids or fixed games-per-team rule |
| [weekly schedule](https://api-web.nhle.com/v1/schedule/2025-10-07) | selected corroboration; direct season inventory replaces week stitching in 02c | a captured week does not establish a season denominator |
| [playing roster](https://www.nhl.com/scores/htmlreports/20252026/RO020001.HTM) | corroborates coaches/scratches; inspected `right-rail` is a structured candidate for the same facts. prospective admission: 03k preparation or 04; attribution use remains 04 | this report does not provide handedness. scratch status does not establish injury reason; reported coach names need attributed identity handling. no roster-report parser dependency for 02b, chance-1 or 03c |
| [event summary](https://www.nhl.com/scores/htmlreports/20252026/ES020001.HTM), [visitor shifts](https://www.nhl.com/scores/htmlreports/20252026/TV020001.HTM), [home shifts](https://www.nhl.com/scores/htmlreports/20252026/TH020001.HTM) | 02b: selected manual fixture checks; 02c: selected corpus corroboration. no planned duplicate production parser | overlapping nhl exports, not independent ground truth. reported even-strength totals need not equal genuine 5v5 with both goalies present; add a parser only for a demonstrated missing fact |
| [moneypuck downloads](https://moneypuck.com/data.htm) | later comparator for features, counts, opportunity values and sensitivity | transformed data and another model, not raw evidence or an oracle. shot downloads omit blocks; use the stated credit/noncommercial terms, and examine other use before publication |
| [nhl edge](https://www.nhl.com/nhl-edge/nhl-edge-whats-new) | later descriptive skating, shooting and zone-time context | public summaries do not establish access to complete movement trajectories or tracked passing/entries. preserve their population/units rather than turn descriptive percentiles into ability effects |
| [documented goal replays](https://rentosaijo.github.io/nhlscraper/reference/replay.html) | candidate later movement/coordinate spot checks | public tooling describes goal-event puck/player snapshots. our direct sprite request returned 403; access and coordinate semantics remain unverified. outcome-selected clips cannot supply representative shot training data |

the schedule sample returned seven days and 48 games, including the three opening-day regular-season games. player profiles and the additional reports were read directly; no new source has been admitted to the production fixture corpus in this research phase. the goal-replay candidate comes from the package author's documentation and [implementation](https://github.com/RentoSaijo/nhlscraper/blob/main/R/Event.R), not a successful local capture.

these are the boundaries in the [v1 plan](../plan.md), not postponed wholesale to v2. [02c](../specs/02c-corpus.md) is reviewed and merged; its [follow-up source audit](corpus-reference-audit.md) selects direct season inventory and bulk bios. [03a](../specs/03a-chance-workflow.md) specifies the chance workflow; 03b admitted real training evidence and assessed it. prospective 2026-10-08 ownership: 03k may admit coach facts for the retained repertoire even before a candidate activates them; 04 owns whether/how they enter attribution. fact preparation does not preselect a coach coefficient or public coach product. scratch availability views remain outside v1.

## consume existing evidence before adding sources

[the field-to-feature audit](model-input-audit.md), 2026-09-30, compares published hockeyviz/evolving hockey methods with actual capture, interpretation and model use. it records further unused source facts and deliberate feature omissions; it does not establish current private-system parity. the amendment below replaces its first-active-consumer admission rule prospectively.

prospective amendment, 2026-10-08: [03k's retained feature preparation](../specs/03k-feature-repertoire.md) is now an explicit consumer of reviewed available facts, including currently inactive families. reuse complete admitted captures; extend interpretation where useful fields remain raw. 03k now covers the full local repertoire without acquisition. absent feeds, including coach/scratch evidence, require a separate admission assignment, potentially with their component, rather than implicit fetching or duplicate exports. 04 still owns attribution semantics. [the feature inventory](../model-features.md) replaces first-active-fit demand as the only reason to prepare a useful fact; it does not admit inaccessible tracking or mandate new parsers for redundant reports.

03c correction, 2026-09-30: the official report's descriptions carry shot types even when the api omits them for blocks. all 111 fixture blocks have explicit report types; 249 matched unblocked records agree across feeds. [the attributed audit](chance-03c-source-audit.md) records counts and limits. [03c](../specs/03c-source-revision.md) admits structured report participants/types and uses supported constraints for repeated-clock joins. no additional feed is needed for these facts; independent physical-origin evidence remains a separate problem.

the captures retain full responses. selecting a smaller interpreted schema has not destroyed omitted upstream fields. score/time, preceding events, faceoffs and shift starts can support later feature construction without another feed. distinguish pre-event score from a goal's post-event snapshot; distinguish all shift starts from faceoff starts. their precise analytical features belong in 03–04, not a speculative feature store in 02b.

no newly inspected source supplies a representative set of blocked shooting origins or complete passing/entry/exit tracking. those remain inference or separately sourced tracking problems. do not call a normalized block location a shooting origin, or derive a tracked action merely because a card has a slot for it.

the review rule is small: each next slice identifies the facts it needs, checks whether a direct source already supplies them, then names the source or the inference and its limits. this is a design question, not a new ingestion framework. 02b pays for one necessary source/parser; future reference and corpus work stays with its actual consumers.

## additional source evidence without the drive

checked 2026-09-30, 16:39–16:41 utc, with read-only `GET` requests and user agent `hockey-stats-source-audit/0.1`. the sampled responses returned 200 at the requested urls. these were live inspections, not admitted captures or replacements for 03b snapshots.

gamecenter `landing` is not wholly redundant with play-by-play: `summary.scoring[].goals[].goalModifier` supplies additional goal semantics. each sampled response identifies the requested game, season `20252026` and game type `2`.

| source | landing goal path | modifier | matching play-by-play identity |
|---|---|---|---|
| [2025020282](https://api-web.nhle.com/v1/gamecenter/2025020282/landing) | `/summary/scoring/2/goals/0` | `own-goal` | event `162`, `/plays/282`, period 3, `13:44` |
| [2025020307](https://api-web.nhle.com/v1/gamecenter/2025020307/landing) | `/summary/scoring/0/goals/0` | `own-goal` | event `74`, `/plays/14`, period 1, `01:50` |
| [2025020184](https://api-web.nhle.com/v1/gamecenter/2025020184/landing) | `/summary/scoring/1/goals/1` | `awarded` | event `104`, `/plays/158`, period 2, `09:10` |

those play-by-play records lack both `goalModifier` and `shotType`. the awarded record nevertheless contains coordinates `(85,2)`, credited scorer `8477492`, goalie `8482137` and situation `1551`. its [play report](https://www.nhl.com/scores/htmlreports/20252026/PL020184.HTM), row `PL-162`, has ordinary goal wording, a four-foot distance and both five-skater-plus-goalie lists. the modifier is additional evidence; it does not by itself prove that no physical shot occurred. [03d physical-action treatment](../specs/03d-chance-revision.md#source-and-population-contract)

the three fixture-game landings contain nineteen scoring rows, each uniquely matching an existing play-by-play goal id: eighteen modifiers `none`, one `penalty-shot`. the latter is `2025021094`, event `153`, `/plays/164`. `none` also labels the shootout winner in `2025020006`, event `823`, `/plays/370`; it does not establish an ordinary timed attempt. missing, unmatched or unfamiliar modifiers must not default to `none`. historical vocabulary, completeness and cross-retrieval agreement remain unverified.

[03c now specifies landing admission](../specs/03c-source-revision.md): preserve complete responses through existing capture primitives; validate game identity; match unique event ids with period/time/team/credited-player corroboration; retain exact modifier values and source locators with explicit unavailable/conflict states. pass the observation through for diagnosis and enforce the existing penalty-shot exclusion on positive matched evidence; 03d owns own/awarded physical-attempt treatment. cost: one additional response per game—3,936 for the current complete corpus—plus bounded interpretation. preserve the five existing captures and actual new retrieval dates; no bulk download is authorized or started.

contract check, 2026-09-30: landing's `isHome` is a boolean team-side observation; `playerId` is credited scorer; `periodDescriptor` belongs to the enclosing scoring group. landing lacks `gameOutcome`. in the shootout fixture it includes the winning scoring-summary event, not all successful shootout attempts. it therefore cannot replace existing result accounting or require a one-to-one count across all api goal records. explicit event-id joins and untimed-period handling remain necessary.

[right-rail for 2025020001](https://api-web.nhle.com/v1/gamecenter/2025020001/right-rail) provides `/gameInfo/awayTeam/headCoach/default` and its home equivalent, naming jeff blashill and paul maurice, plus scratch player ids and officials. it lacks a top-level game id in this sample, so admission needs explicit request binding and available contextual corroboration. prefer evaluating this structured candidate before committing to an html coach parser; retain roster html as corroboration. this does not add a coach source to 03c.

right-rail also links ten reports/charts. additionally inspected [shot summary](https://www.nhl.com/scores/htmlreports/20252026/SS020001.HTM), [faceoff summary](https://www.nhl.com/scores/htmlreports/20252026/FS020001.HTM) and [faceoff comparison](https://www.nhl.com/scores/htmlreports/20252026/FC020001.HTM) supply aggregate shot/strength/period checks and zone/strength/opponent faceoff comparisons. no new physical origin or independent tracking evidence was established. no production parser is justified for these exports now.
