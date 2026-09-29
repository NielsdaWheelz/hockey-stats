# HockeyViz — The Magnus Game Prediction Model, version 8

- **Title (as published):** "The Magnus Game Prediction Model"
- **Author:** Micah Blake McCurdy (@IneffectiveMath)
- **Article date:** September 24, 2025
- **URL used:** https://hockeyviz.com/txt/magnus8GameSim
- **Accessed:** 2026-07-16
- **Index status:** HockeyViz's [`Current Models` index](https://www.hockeyviz.com/) lists this page
  as “Magnus 8 (Game Simulation)” with the same date.
- **Retrieval:** the complete rendered article was retrieved directly. The linked shot-rate,
  penalty-rate, and shooter-goaltender pages are separate component sources; this dossier attributes
  only the assembly and simulation decisions stated on the game-simulation page.
- **Evidence boundary:** the page describes a game-outcome simulator built from separately estimated
  player, coach, shot-rate, penalty-rate, and shot-outcome inputs. The simulator is outside the current
  HockeyViz component-model parity denominator. Its relevant component descriptions are supporting
  evidence or source ambiguities, not new comparator requirements, and none is evidence about sG or a
  player Total.

## 1. Summary

Magnus 8 predicts a game's win probability by repeatedly simulating play from the two rosters,
expected situation-specific ice times, and head coaches. Player shot-rate isolates are assembled into
even-strength, power-play, and penalty-kill team maps; own attack and opponent defence are averaged for
the matchup. Separately estimated penalty draw/take rates determine manpower changes, and a distinct
shooter-goaltender outcome model turns a sampled shot, actor set, location, and goalie into a goal
probability.

The simulation advances one second at a time. It samples penalties, strength state, shot occurrence,
shooter, setter, shot location, and outcome with several deliberate simplifications. In particular,
penalties last a fixed 120 seconds, the penalized player is not removed from the available roster,
several strength states share one map, shot location is independent of shooter and setter, overtime
largely reuses even-strength maps, and shootouts are coin flips. The page says about 10,000 runs are
enough for reported quantities to stabilize, but supplies no held-out game-level accuracy, calibration,
proper score, uncertainty assessment, or benchmark comparison.

Two statements conflict with other reviewed HockeyViz pages. This page selects shooters using a
strength-specific historical on-ice shot fraction weighted by expected ice time, whereas the 2022
`Shootiness` article says its Elo-style conditional probabilities are used for simulated shooter
sampling. It also says the special-teams shot-rate model neglects rest, whereas Magnus 9 ST explicitly
publishes three rest categories and their effects. These are preserved as source ambiguities rather
than silently reconciled or projected onto private current code.

## 2. Decision inventory

| id | topic | source decision or fact | source rationale / limit |
|---|---|---|---|
| hockeyviz-magnus8gamesim-D1 | game-level estimand | Estimate a team's single-game win probability as its win share across repeated simulations initialized by both rosters, expected ice-time distributions, and head coaches. | This is a game-prediction product, not a player-component estimator or player Total. |
| hockeyviz-magnus8gamesim-D2 | game-result procedure | Simulate 3,600 regulation seconds, then up to 300 overtime seconds if tied; unresolved overtime becomes a 50/50 shootout result. | The page describes this result mechanism but does not validate it against a richer overtime/shootout process. |
| hockeyviz-magnus8gamesim-D3 | lineup units | Group skaters into situation-specific units at 5v5, power play, and short handed before constructing team inputs. | Sensible unit grouping is the only change from Magnus 7 highlighted in the introduction. |
| hockeyviz-magnus8gamesim-D4 | team shot-map assembly | Weight individual shot-rate isolates by expected ice time to produce separate even-strength, power-play, and penalty-kill team maps; apply recent-game fatigue at this assembly stage. | The source does not estimate fatigue-driven roster decisions. |
| hockeyviz-magnus8gamesim-D5 | special-teams role boundary | Use isolated player effects for power-play offence and penalty-kill defence, while treating power-play defence and short-handed offence as league average for every player. | This mirrors the directional omission documented by the special-teams component model. |
| hockeyviz-magnus8gamesim-D6 | special-teams rest conflict | State that the special-teams shot-rate repetition of the 5v5 method neglects rest while retaining the other terms. | Magnus 9 ST explicitly displays rested, normal, and tired categories; the public pages therefore do not support one unambiguous current statement. |
| hockeyviz-magnus8gamesim-D7 | opponent combination | Average the shooting team's attack map with the opponent's corresponding allowance map for each game situation. | The example averages home power-play offence with road penalty-kill defence. |
| hockeyviz-magnus8gamesim-D8 | penalty-rate assembly | Weight each skater's isolated draw/take impacts by expected all-situations ice time, then average one team's take rate with the opponent's draw rate to obtain the simulated call rate. | Penalty-rate estimation is upstream; the simulator composes the two opposing directions. |
| hockeyviz-magnus8gamesim-D9 | penalty eligibility | Exclude majors, misconducts, offsetting minors, goaltender penalties, and bench minors from the simulation input. | This is the simulator's event boundary, not a complete definition of the separate penalty-rate model or player value. |
| hockeyviz-magnus8gamesim-D10 | penalty and strength dynamics | Sample penalties by second at uniform rates, reduce the penalized team's skater count for a fixed 120 seconds, leave the penalized player in the roster pool, and coarsen even and advantaged strength states. | The source calls this treatment simplistic; it does not distinguish 5v5 from 4v4/3v3 or 5v4 from 5v3/4v3 for shot maps. |
| hockeyviz-magnus8gamesim-D11 | active game context | Use the evolving simulated score for leading/trailing effects, include coach-specific third-period tied/leading tactics, and apply time/venue structural shot-map terms. | Every team otherwise receives league-average score response; the article also notes higher home and second-period shot danger. |
| hockeyviz-magnus8gamesim-D12 | shot-event process | For every second, sample no shot, a home shot, or a road shot from the current team shot-rate estimates. | This is a discrete simulation mechanism; a rate of 42 shots/hour becomes probability `42/3600` per second. |
| hockeyviz-magnus8gamesim-D13 | shooter-choice conflict | Choose the shooter with weights formed from that player's historical fraction of team on-ice shots in the current EV/PP/PK state multiplied by expected ice time in that state. | The separate `Shootiness` page instead says an Elo-style on-ice conditional distribution is used in game simulation; the page does not explain the replacement, coexistence, or vintage. |
| hockeyviz-magnus8gamesim-D14 | setter sampling | Assign no setter with probability 20%; otherwise choose a teammate with role weights under which forwards are twice as likely as defenders to set for forwards and three times as likely to set for defenders. | The weights are described as a simple approximation to observed hand-tracked passing rather than an estimated player setting propensity. |
| hockeyviz-magnus8gamesim-D15 | location/actor independence | Sample shot location from the team shot-rate map independently of the selected shooter and setter. | The weaknesses section explicitly says real players occupy and shoot from different locations and that the simulator does not represent this dependence. |
| hockeyviz-magnus8gamesim-D16 | shot-outcome service | After shooter, location, and goalie are known, call a separate shooter-goaltender model for goal probability. | The game-simulation page does not restate that component's fitting or actor-layer details. |
| hockeyviz-magnus8gamesim-D17 | overtime and shootout approximation | Reuse 5v5 shot maps during overtime, mark 3v3 only in the goal-outcome model, and resolve an unscored overtime with an unweighted shootout coin flip. | The source names both approximations as weaknesses. |
| hockeyviz-magnus8gamesim-D18 | Monte Carlo stabilization | Report that approximately 10,000 simulations stabilize game win probability, expected team goals, and similar quantities of interest. | No convergence plot, tolerance, seed sensitivity, or Monte Carlo interval is supplied. |
| hockeyviz-magnus8gamesim-D19 | omitted hockey mechanics | Do not explicitly simulate icing, faceoffs, timeouts, bench minors, fatigue-related roster choices, player-specific penalty-box absence, or realistic overtime and shootout differences. | The page distinguishes simplifications that concern the author from those considered low priority; this is an observation ceiling, not component evidence. |
| hockeyviz-magnus8gamesim-D20 | first-principles composition | Treat the overarching game process as a first-principles hockey simulation whose component weights arise from game duration, skater counts, and event rates rather than one loss-optimized aggregate predictor. | Upstream talent and rate inputs are still statistical models; only the composition layer is characterized this way. |
| hockeyviz-magnus8gamesim-D21 | game-level evaluation boundary | Publish no held-out game prediction loss, calibration, benchmark comparison, or formal test that the chosen approximations improve game forecasts. | Interpretability and mechanistic coherence are defended philosophically, not established as predictive superiority. |
| hockeyviz-magnus8gamesim-D22 | reported output family | Produce game win probability and quantities such as expected goals for each team from the simulated result distribution. | The page names these outputs but does not expose a fitted artifact, simulation trace, or uncertainty contract. |
| hockeyviz-magnus8gamesim-D23 | version claim | Identify situation-specific player-unit grouping as Magnus 8's headline improvement over Magnus 7 while otherwise retaining the predecessor's structure. | This is a descriptive version statement, not evidence that all upstream component versions changed together. |

## 3. Simulation structure

```text
rosters + expected EV/PP/PK ice time + head coaches
  -> situation-weighted player shot isolates
  -> own-attack/opponent-defence team maps
  -> situation-weighted penalty draw/take isolates

for each simulated second
  -> sample penalty and current skater-count state
  -> apply score, venue/time, coach, and fatigue context
  -> sample no shot / home shot / road shot
  -> sample shooter from strength-specific propensity x expected ice time
  -> sample setter from no-setter and position-role weights
  -> sample location independently from the team map
  -> separate shooter-goaltender model supplies goal probability

regulation -> overtime if tied -> coin-flip shootout if still tied
many simulations -> win probability and expected-score summaries
```

The page's “first principles” label applies to this composition layer. It does not turn the upstream
shot-rate, penalty-rate, actor-choice, or shooter-goaltender estimators into non-statistical models, and
it does not establish that the simulator is causal.

## 4. Evaluation and output evidence

The only quantitative simulation adequacy statement is that roughly 10,000 iterations stabilize the
reported quantities. That is a Monte Carlo precision claim, not predictive validation. The article
does not report:

- chronological game-level log loss, Brier score, calibration, or discrimination;
- a comparison with Magnus 7, a market baseline, or a simpler statistical forecast;
- ablations for lineup units, actor choice, setting, strength coarsening, or location independence;
- uncertainty separating Monte Carlo error from component-model and roster uncertainty; or
- replay artifacts sufficient to reproduce a published game probability.

The named output family includes game win probability and expected goals. None of those outputs is a
player-level sG component, a player Total, or evidence that the simulation mechanics belong in the
current component-model parity denominator.

## 5. Open questions and source ambiguities

1. **Shooter-choice vintage.** The 2022 `Shootiness` page assigns its Elo-derived conditional
   probabilities to simulation, while this 2025 page documents a raw strength-specific historical
   propensity weighted by expected ice time. Which is current, or whether both are used in different
   simulator paths, is not stated.
2. **Special-teams rest.** This page says rest is omitted from the special-teams shot-rate model;
   Magnus 9 ST, published sixteen days earlier, explicitly shows three rest categories. The pages may
   describe different component vintages, but neither says so.
3. **Component vintages.** The model is named Magnus 8 while its linked component families have their
   own version schedules. The article does not publish a dependency manifest or immutable fit IDs.
4. **On-ice unit realization.** Expected situation ice time and “sensible units” are inputs, but the
   rules for changing units by second, handling injuries/scratches, and representing line matching are
   not specified.
5. **Penalty process.** Uniform per-second rates, fixed durations, no goal-terminated minors, and no
   penalized-player removal leave material hockey-state dependence outside the simulator.
6. **Actor/location dependence.** Shooter and setter identities do not affect location. The source
   calls this a weakness but supplies no candidate correction or validation data.
7. **Predictive evidence.** Stabilization after 10,000 runs addresses simulation noise only. The page
   gives no evidence for game-level accuracy, calibration, or comparative value.
