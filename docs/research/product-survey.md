# product survey and council findings

date: 2026-09-29

status: research and candidate directions; no product scope or architecture is locked.

the objective is a useful hockey statistics website. learning will happen through building it; a curriculum, teaching interface, or exercise system is outside the present brief. the strongest common principle in the references is inspectable evidence: a useful answer has a defined question, intelligible measurements, and a path back to its supporting data.

## what to borrow, and why

these are complementary exemplars, not a measured ranking of products. observations below come from public pages and method descriptions. subscription interfaces were not exhaustively tested. the interpretation column is our judgment.

| reference | verified capability or method | interpretation and useful principle |
| --- | --- | --- |
| [hockeyviz game simulation](https://hockeyviz.com/txt/magnus8GameSim) | estimates abilities separately, then simulates shots, penalties, and outcomes. micah explicitly values interpretability because he wants to understand and explain hockey. | mechanisms matter alongside prediction. design outputs that help answer why a result emerged. |
| [hockeyviz shot-rate model](https://www.hockeyviz.com/txt/magnus9EV) | estimates spatial patterns while accounting for players, coaching, deployment, score, venue, and fatigue. estimates can be decomposed. | preserve spatial structure and distinguish observed results from adjusted estimates. a scalar can erase the interesting hockey. |
| [evolving hockey overview](https://evolving-hockey.com/evolving-hockey-overview/) | connects tables, charts, gar/xgar, rapm, career views, contracts, projections, and live-game tools. | multiple coherent views are more useful than disconnected widgets. valuation gains meaning through decomposition and comparison. |
| [evolving hockey model history](https://evolving-hockey.com/about/) | publishes model versions, release dates, and changes. | numbers have biographies. distinguish changes in evidence or method from changes in players. |
| [money puck methods](https://www.moneypuck.com/about.htm) and [glossary](https://moneypuck.com/glossary.htm) | describes shot probabilities, rebounds, shooting talent, flurry adjustments, and game probabilities. its deserve-to-win measure is a hypothetical replay calculation, distinct from a prediction of the actual game's outcome. | attach probability to a recognizable question, then specify exactly which question the number answers. evocative naming needs precision. |
| [all three zones](https://www.allthreezones.com/about.html) and [card guide](https://www.allthreezones.com/player-cardsfaq.html) | tracks passes, entries, exits, retrievals, and other microstats; groups cards by hockey skills and discusses tactical context. | measure actions that produce outcomes. organize around hockey concepts rather than the accidental shape of a feed. |
| [hockey-reference glossary](https://www.hockey-reference.com/about/glossary.html) | documents definitions, units, historical conventions, and incomplete-data notation. | reference work succeeds by making ordinary lookups dependable. coverage belongs beside the number. |
| [nhl edge 2.0](https://www.nhl.com/nhl-edge/nhl-edge-whats-new) | combines daily stories, tracking visualizations, and comparisons. | give people a reason to return without requiring a database question. |
| natural stat trick | direct pages failed to load during this audit. [secondary documentation](https://www.datapunkhockey.com/free-data-sources/) describes detailed filters, player comparisons, and csv exports. | preserve analyst agency through precise filtering and export. this observation needs a later firsthand interface check. |

the hockeyviz philosophy is especially relevant: its simulation description explicitly prefers interpretable mechanisms, while acknowledging accuracy as desirable. that is an objective choice, not proof that an interpretable model is necessarily correct. evolving hockey supplies a complementary ambition: comparable valuation across players and situations. all three zones reminds us that better measurement can matter more than a more elaborate model.

## evidence of user friction

these anecdotes generate design hypotheses. they do not establish prevalence, current interface quality, or statistical truth.

- a [money puck reader](https://www.reddit.com/r/SanJoseSharks/comments/tb6oxr/statistics_clarification_on_moneypuck/) confused goal share with scoring probability and mistook the `x` prefix for formatting. implication: explicit names, denominators, and compact definitions near the result.
- a [pairing discussion](https://www.reddit.com/r/SanJoseSharks/comments/mo6rcf) compared raw pair results with adjusted individual impacts; a reader struggled to inspect recent splits on mobile. implication: visible time windows, clear analytical context, and shareable filter state.
- a [discussion of money puck revisions](https://www.reddit.com/r/hockey/comments/1q3q5li/moneypuckcom_weve_made_a_tweak_to_our_xgoals/) requested before/after comparisons and debated missing shot context. implication: publish revision notes and measurement limits. the comments do not establish which model is correct.

## product principles

1. begin each view with a real question. “who is good?” conceals distinct questions about observed performance, adjusted contribution, future performance, and value under a particular role or baseline.
2. keep season or date window, strength state, exposure, unit, and comparison baseline visible. label observations and estimates distinctly.
3. make charts and tables agree because they describe the same selection. retain a path from aggregate to supporting records.
4. preserve decomposition. a combined rating should not become the only available explanation.
5. expose uncertainty when it changes interpretation. avoid presenting a small sample as a settled player attribute.
6. use consistent rink orientation, comparable scales, legible units, and color with an explicit meaning. visual consistency supports correct comparison.
7. retain data provenance and model versions. explain revisions that materially change conclusions.

the design trade-off is fewer simultaneous metrics in exchange for faster interpretation. preserve detailed access rather than deleting it. do not copy difficult conventions merely because respected products use them, or add ornamental interaction that makes comparison harder.

## council agreement and disagreement

this is a synthesis of expert perspectives, not an endorsement by the named researchers.

the product perspective wants an immediate useful answer; the statistical perspective wants defensible inference. resolve this by choosing questions the available measurements can answer, with explicit limits. do not wait for an ambitious model before providing any value.

the hockey analyst wants passing and transition context; the data engineer wants comprehensive automated coverage. ordinary public event data and tracked microstats support different questions. accepting broad event coverage trades away some tactical detail; neither clever modeling nor interface language should hide that loss.

the architect wants stable contracts; research needs changing hypotheses. commit early to identities, units, provenance, and dataset boundaries. defer speculative model families and service topology. this keeps change possible without pretending scientific uncertainty can be designed away.

the predictive modeler may prefer opaque accuracy gains; an explanatory product may prefer inspectable mechanisms. state the objective before choosing between them. either still requires appropriate evaluation.

## candidate first product slices

the first question remains open. plausible candidates are a completed-game explorer, a team comparison, or a narrowly defined player comparison.

a game explorer offers compact real value: final score, cumulative attempts, a rink plot, and an event table for one selection. it also forces agreement between records and aggregates before advanced estimates obscure discrepancies. acceptance would require reconciled counts, explicit event definitions, and consistent filters across views. adding strength or score-state filters must change the relevant denominator as well as the displayed events.

the trade-off is delayed season-wide rankings and trained models. the benefit is a small usable surface that exercises shared data responsibilities. this is a candidate, not a pedagogical mandate or settled roadmap.

before choosing, determine which recurring need matters most: postgame analysis, team tendencies, player evaluation, or goaltending; which team or game anchors the first useful result; and whether personal research may use paid inputs or published results must be reproducible from openly accessible data. resolve these before specifying the first implementation slice.
