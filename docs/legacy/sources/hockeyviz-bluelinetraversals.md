# HockeyViz — Blueline Traversals

- **Title (as published):** "Blueline Traversals"
- **Author:** Micah Blake McCurdy (@IneffectiveMath)
- **Article date:** May 1, 2024 (as stated in the article header; original research first presented at the Ottawa Hockey Analytics Conference, 2021; slides and video available; improvements to the off-ice impact computation are new in May 2024)
- **URL used:** https://hockeyviz.com/txt/bluelineTraversals — fetched via curl with a browser User-Agent (WebFetch returns HTTP 403); Wayback fallback not required (full article retrieved directly, 254 KB HTML, article text intact).
- **Accessed:** 2026-07-04
- **Completeness:** full article retrieved. Section inventory (confirmed against raw HTML): Introduction, Overview, Method, Fitting, Structural Results, Skater Results, Off-ice Impacts, Weaknesses. Interactive charts (team-by-team player DONX hexagons, stoppage/shift-end probability plots) are data-driven SVG or canvas — their labels are not recoverable as text but the surrounding prose and headers fully describe the model and results.

---

## Summary

McCurdy's Blueline Traversals model measures each skater's individual impact on whether the puck moves across either blue line during 5v5 play. He frames four directional impacts: exit offence (own zone → NZ), entry offence (NZ → opponent zone), exit defence (keep puck in opponent zone), and entry defence (keep puck out of own zone). These are estimated by two separate logistic regressions — an entry model (one observation per second of 5v5 NZ play; response = 1 if puck enters offensive zone) and an exit model (one observation per second of 5v5 non-NZ play; response = 1 if team exits their zone) — each containing per-skater and per-head-coach terms alongside structural controls for score state, period, home/road, and score×period interaction. All three penalty types use ridge strength 100; score terms are pooled to sum-to-zero at strength 100 million. The model is fit season by season with a season-to-season continuity prior (deviation-from-last-season penalty). Beyond the in-stint player coefficients, the article introduces an **off-ice impact** metric: a Markov-chain simulation of a player's shift using their fitted coefficients finds the steady-state zone-distribution shift the player produces, which is then weighted by the zone-start xG impacts from Magnus to yield an end-of-shift ice-position gain or loss in xG/60 terms. Off-ice impacts are roughly ten times smaller than on-ice impacts in magnitude.

Zone state is imputed from public NHL PBP — the article relies on this imputation throughout but does not describe the specific imputation algorithm. The Weaknesses section acknowledges two distinct omission classes (see below). The article operates exclusively on 5v5 (five-on-five) data; no mention of PP or PK strength states. The terms "Ice Won" and "Ice Lost" do not appear anywhere in the article text; the article names player outputs by the four directional axes (D/O/N/X) and by "offensive and defensive off-ice impacts".

---

## Decision inventory

| id | topic | decision | rationale / verbatim quote | article section |
|---|---|---|---|---|
| hockeyviz-bluelinetraversals-D1 | scope / coverage | Model operates on **5v5 (five-on-five) play only**. | "every second of five-on-five play during which the puck is in the neutral zone" (entry model); "every second that the puck is not in the neutral zone" in the exit model, placed in 5v5 context throughout. PP/PK not mentioned. | Method |
| hockeyviz-bluelinetraversals-D2 | two separate models | Entry and exit impacts are estimated by two **separate logistic regression models**, not one joint fit. | "Strictly speaking I measure these impacts with two different but heavily overlapping models." | Method |
| hockeyviz-bluelinetraversals-D3 | entry model unit of observation | One observation per second of 5v5 NZ play, **two rows per second** (home team = offence / road team = offence), response = 1 if offence team moves puck into their OZ that second. | "The entry model has two observations for every second of five-on-five play during which the puck is in the neutral zone. … The response variable is set to 1 if the offence team moves the puck into their offensive zone and 0 if they have not." | Method |
| hockeyviz-bluelinetraversals-D4 | exit model unit of observation | One observation per second of non-NZ play; the team near their own goalie = offence (trying to exit); the team far from their goalie = defence (defending the blue line behind them). Response = 1 if offence team exits. | "The exit model has one observation for every second that the puck is not in the neutral zone. … the team playing near their own goalie is the 'offence' team … the team playing far from their goalie is the 'defence' team." | Method |
| hockeyviz-bluelinetraversals-D5 | four directional impacts | Four player-impact facets measured: exit offence, entry offence, exit defence, entry defence. Entry defence = keeping puck out of own zone; exit defence = keeping puck in opponent zone. | The four-item list in Overview. | Overview |
| hockeyviz-bluelinetraversals-D6 | coach terms included | Each head coach appears in each of the four directional roles as a separate term. | "Furthermore, each team's head coach is included in each of the four senses, to proxy for how they instruct (either directly or indirectly) their players to play." | Method |
| hockeyviz-bluelinetraversals-D7 | structural controls | Both models share: 7 score-state terms (trailing ≥3, trailing 2, trailing 1, tied, leading 1, leading 2, leading ≥3) expressed from the perspective of the team wanting the transition; 3 period terms; 2 home/road terms; 3 score×period interaction terms (tied-in-3rd, leading-1-in-3rd, leading-2-in-3rd). | Explicit enumeration in Method. | Method |
| hockeyviz-bluelinetraversals-D8 | model class | **Logistic regression** (not linear ridge like Magnus). | "This model is fitted as a logistic regression, with three kinds of ridge penalties." | Fitting |
| hockeyviz-bluelinetraversals-D9 | three ridge penalties, each strength 100 | (1) Deviation of every non-constant term from zero (encodes "no one player can dramatically change results alone"); (2) deviation of every term from its value in the **previous season** (encodes "players and sport change slowly"); (3) score terms pooled to zero at strength **100 million** (encodes that aggregate score effects must be neutral). | "One penalty (of strength 100) is applied to every non-constant term's deviation from zero … A second penalty (also of strength 100) is applied to every term's deviation from its value in the previous season … Finally, a third penalty (of strength 100 million) is used to pool the score terms to enforce our knowledge that all the score effects taken together must average to zero." | Fitting |
| hockeyviz-bluelinetraversals-D10 | no aging adjustment | The season-to-season penalty is flat (deviation from last season = 100), not shaped by a player's age. No aging curve is applied. | (inferred from absence; the penalty described is uniform — unlike Magnus which has an age-dependent certainty Λ; the article does not mention aging.) | Fitting |
| hockeyviz-bluelinetraversals-D11 | coefficient interpretation | Logistic regression coefficients are reported as seconds of delay/speed-up to the mean transition time, derived by converting the constant-term probability to an average waiting time, then doing the same with a given term added. | "Each transition (entry or exit) has an associated constant term; converting this to a probability gives the chance of a transition in a given second … Repeating this process with the constant and a given term added lets us compare the two, to quote the effect of that term in seconds." Explicitly notes these times are "strictly speaking, cannot be added together." | Structural Results |
| hockeyviz-bluelinetraversals-D12 | score-effect direction: exits | Trailing → faster exits (shaves ~2 s); leading by 1–2 → adds ~1 s; leading by a lot → "downright leisurely." Third period slows exits; third-period score interactions are strong. Road teams ≈ 2 s harder exit time than home. | "Trailing is associated with shaving around two seconds off the time it takes to get the puck out of your own zone … Road teams have a roughly two-second harder time exiting their zone than home teams." | Structural Results |
| hockeyviz-bluelinetraversals-D13 | score-effect direction: entries | Tied = easiest entries; both leading AND trailing → longer time until entry. Interpretation: leading teams dump-and-change (neutral zone → defend own blue), trailing teams exit easily but can't penetrate. Period and home/road terms are very small for entries; "tied in the third" = specifically clogged neutral zones. | "When the puck is in the neutral zone, the impact of the score is quite different: tied games are the ones where entries are a little easier to come by." | Structural Results |
| hockeyviz-bluelinetraversals-D14 | skater four-way axes | Skater results are displayed on four axes: D (entry defence vs exit defence), O (entry offence vs exit offence), N (entry offence vs entry defence), X (exit offence vs exit defence). | Explicit axis legend in Skater Results section. | Skater Results |
| hockeyviz-bluelinetraversals-D15 | off-ice impacts via Markov chain | Player's coefficients (from both models) are used to build a **Markov chain** that simulates a single player's shift: puck in one of four states (DZ, NZ, OZ, OTF × ongoing/stoppage) at each second; zone transitions use the constant term + the player's term only (four league-average teammates, five league-average opponents assumed). Stoppage and shift-end probabilities use 2018–2024 league-wide averages. | "I simulate a single player's shift with a simple Markov chain … I compute the zone-to-zone transition probability using only the constant term in the relevant transition model and the player's term in that model. This amounts to assuming that the player of interest has been provided with four league average teammates, and five league average opponents." | Off-ice Impacts |
| hockeyviz-bluelinetraversals-D16 | off-ice impact via fixed-point calculation | The simulator S is a map from ℝ⁴ (starting puck-location probabilities) to ℝ⁴ (ending puck-location probabilities). Find fixed point by iteration: α₀ = (11.9% DZ, 12.5% NZ, 13.0% OZ, 62.5% OTF). Validate: "fairly close to league-wide shift-start types." For player p: compute S_p(α₀) − α₀ = net zone-state change attributable to the player. | "Since this map is continuous, it has a fixed point … In this case, the fixed point is α₀ = (11.9%, 12.5%, 13.0%, 62.5%). This distribution is fairly close to league-wide shift-start types, which is an encouraging validation." | Off-ice Impacts |
| hockeyviz-bluelinetraversals-D17 | off-ice impact weighted to xG/60 | The net zone-state shift S_p(α₀) − α₀ is weighted by the zone-start xG impacts from Magnus (−29.4% DZ, −24.8% NZ, +17.3% OZ, +7.4% OTF of league-average xG/60, with OTF split evenly between DZ and OZ), yielding an off-ice impact in xG/60. Scaled to 1,000 following-shift minutes. | "The impact of starting a shift in the defensive zone in my shot rate model is -29.4% of league-average xG/60 … we can form the weighted sum … to obtain the total net impact of ice position gained or lost in xG/60." | Off-ice Impacts |
| hockeyviz-bluelinetraversals-D18 | off-ice impact magnitude | Off-ice impacts span roughly −1% to +1% of league-average xG/60. Off-ice impacts are "about ten times smaller than on-ice impacts." Top players include Tkachuk, Hughes, Fox, MacKinnon plus specialists like Foligno. The two off-ice components (offensive and defensive) correlate at r = −0.40. | "In total magnitude, however, these off-ice impacts are much smaller than on-ice impacts, by a factor of roughly ten. … a player near the top of the league in gaining ice position … can expect to contribute about five goals a season." | Off-ice Impacts |
| hockeyviz-bluelinetraversals-D19 | notional league-average deployment | For weighting off-ice impacts: OTF starts (62.5%) divided notionally into DZ/OZ halves, yielding a "standard" deployment s = 40.5% DZ, 17.5% NZ, 42.0% OZ. | "if we choose to artificially divide those starts into offensive zone and defensive zone starts, we have a 'notional league average' deployment of 40.5% DZ, 17.5% NZ, 42.0% OZ." | Off-ice Impacts |
| hockeyviz-bluelinetraversals-D20 | puck location imputed from public PBP | The model relies on zone-state imputed from NHL public play-by-play. The specific imputation algorithm is **not described** in the article beyond the Weaknesses section's disclosure that some round-trips have no recorded events. | "I have deliberately chosen to work with the nhl's public play-by-play data, from which the puck location at many (but not all) times can be imputed." | Weaknesses |
| hockeyviz-bluelinetraversals-D21 | weakness: DZ→NZ→DZ blind spot | A DZ→NZ→DZ round-trip with no recorded event is treated as continuous DZ time. Effect: "make players and coaches look worse at zone exits and better at entry defence." Omission rate unknown. | "there are times when the puck moves from a defensive zone into the neutral zone and then back into that same defensive zone without an event being recorded; my approach here will treat this as a continuous stretch of play in the defensive zone. The effect of these omissions will tend to make players and coaches look worse at zone exits and better at entry defence." | Weaknesses |
| hockeyviz-bluelinetraversals-D22 | weakness: entry-then-immediate-NZ-return blind spot | Some zone entries are followed by a return of the puck to the neutral zone with no recorded event. Effect: "make coaches and players stronger at entry defence and weaker at zone exits than they actually are." | "there are some number of zone entries which are followed by a return of the puck to the neutral zone without any record; these omissions will tend to make coaches and players stronger at entry defence and weaker at zone exits than they actually are." | Weaknesses |
| hockeyviz-bluelinetraversals-D23 | omission rate unknown for both blindspots | The relative frequency of the two omission classes (D21 and D22) is not estimable. | "I don't know how to estimate how common these two omissions are in order to even guess at a comparison between these two effects." | Weaknesses |
| hockeyviz-bluelinetraversals-D24 | no entry-quality taxonomy | The model does not attempt to distinguish carry-in entries from dump-ins, or controlled exits from chip-and-chase. (inferred from absence and the Weaknesses section: the model's inherent data ceiling is that zone entries are not events in public PBP.) | (inferred) | — |
| hockeyviz-bluelinetraversals-D25 | display: four-axis player charts per team | Skater results shown as interactive hex/dot charts for each team, each season (2007-08 to 2023-24), with DONX axes. Coach terms shown as the first row; smaller magnitude but felt on every entry/exit. | Skater Results section; team-by-team chart structure visible in HTML. | Skater Results |
| hockeyviz-bluelinetraversals-D26 | historical coverage: 2007-08 onward | Charts cover 17 seasons: 07-08 through 23-24, matching Magnus 9's sequential fitting window. | Column headers in interactive charts. | Skater Results |

---

## Model structure sketch

Two separate **logistic regressions** (not linear, not map-valued — these are scalar per-second binary outcome models):

**Entry model:**
- Population: every second of 5v5 play when puck is in the neutral zone.
- Two rows per second (home-attacks and away-attacks observations).
- Response: binary — 1 if the offensive team moves puck into their OZ in that second, 0 otherwise.
- Covariates: per-skater terms (offensive and defensive, for/against); per-head-coach terms (same four directional senses); structural controls (score 7-state, period 3-level, home/road 2-level, 3 score×period interaction indicators).

**Exit model:**
- Population: every second of 5v5 play when puck is NOT in the neutral zone.
- One row per second (team near own goalie = offence; other team = defence).
- Response: binary — 1 if the offensive team moves puck into the NZ in that second, 0 otherwise.
- Same covariates structure as entry model.

**Three ridge penalties (both models):**
1. Strength 100: deviation of every non-constant term from zero (broad talent prior).
2. Strength 100: deviation of every term from the previous season's value (slow-change continuity prior).
3. Strength 100,000,000: pool of all score terms to sum-to-zero (structural constraint).

**Off-ice impact (post-hoc composition, not a fitted model):**
- Markov chain simulator S using player's fitted coefficients and league-average context.
- Fixed-point α₀ computed by iteration; S_p(α₀) − α₀ = player's net zone-distribution shift.
- Weighted by zone-start xG impacts from Magnus → off-ice impact in xG/60 per 1,000 following-shift minutes.
- Two outputs (offensive off-ice impact; defensive off-ice impact); r ≈ −0.40 between them.

Not described anywhere in the article:
- The specific zone-state imputation algorithm from the raw PBP event sequence.
- How stoppages within a second are handled.
- Whether faceoffs are used as zone anchors (not stated in the article).
- How shot/goal events vs faceoff events vs giveaway/takeaway events each anchor zone state.

---

## Full covariate list as stated

Both models share the following terms:

**Player terms:**
- Per-skater: offensive impact (team's entry/exit rates when on ice) and defensive impact (opponent's rates), one coefficient per direction per season.
- Per-head-coach: general attacking and defending pair in each of the four directional senses (8 coach terms per coach).

**Structural terms (both models):**
- Score state × perspective: 7 levels (trailing ≥3, trailing 2, trailing 1, tied, leading 1, leading 2, leading ≥3), from the perspective of the team seeking the transition.
- Period: 3 terms.
- Home/road: 2 terms.
- Score × period interactions: 3 terms (tied-in-3rd; leading-1-in-3rd; leading-2-in-3rd).

**Absent from the model (not mentioned):**
- Shift-start zone type (no per-second zone terms as in Magnus).
- Rest/fatigue terms.
- Penalty shadow terms.
- Any aging adjustment on the prior.

---

## Evaluation protocol and reported results

The article contains no formal held-out evaluation. Validation signals offered:

- **Fixed-point sanity check:** α₀ = (11.9%, 12.5%, 13.0%, 62.5%) is "fairly close to league-wide shift-start types" (actual league typical: 10.3% DZ, 17.5% NZ, 11.7% OZ, 60.5% OTF). Described as "an encouraging validation of our admittedly very simple transition model."
- **Face-validity exhibit:** score-effect direction aligns with known hockey patterns (trailing teams exit faster; tied NZ is clogged in 3rd period).
- **Correlation between off-ice offensive/defensive impacts:** r = −0.40 (expected negative because transitions benefit both sides simultaneously).
- **Off-ice vs on-ice magnitude ratio:** approximately 10× smaller for off-ice. "Very roughly, a player near the top of the league in gaining ice position in this sense who plays a lot of minutes can expect to contribute about five goals a season."
- **Named player face-check:** Brady Tkachuk, Quinton Hughes, Adam Fox, Nathan MacKinnon top the off-ice chart ("known to be exceptionally strong"); Marcus Foligno as a specialist example.
- No repeatability test (year-to-year correlation of coefficients) is reported. No AUC, log-loss, calibration plot, or Brier score is given for the logistic regression.

---

## Outputs / artifacts

- Per-season, per-team interactive charts showing each player's location in the DONX four-axis space (2007-08 to 2023-24). Coach terms shown as the first row in each team chart.
- League-wide scatter plots of off-ice offensive vs defensive impact, by season.
- Per-team off-ice impact breakdowns by player for the current season.
- Structural-term bar charts (score effects for exits and entries, period terms, home/road terms, interaction terms).
- Stoppage probability and shift-end probability tables (2018–2024 league averages, used in the Markov chain).

---

## Linked / companion articles referenced

- Ottawa Hockey Analytics Conference 2021 slides and video (linked but no URL recoverable from article text — McCurdy's OTTHAC 2021 talk is the origin of this research).
- Shot rate model (Magnus) — specifically the zone-start xG impacts (−29.4% DZ, −24.8% NZ, +17.3% OZ, +7.4% OTF) used to weight the off-ice impact.
- No other articles are linked in the body.

---

## Open questions / ambiguities

| id | question | relevance |
|---|---|---|
| OQ-1 | Where do the terms "Ice Won" and "Ice Lost" originate? They are not in the article text. The OTTHAC 2021 slides (linked but not retrieved) are the most likely source; the site's product/tool pages are another. | naming provenance |
| OQ-2 | The imputation algorithm is unspecified. Which PBP event types does McCurdy use as zone anchors? Does he use faceoff zone, event coordinates, nearest stoppage? Are giveaways/takeaways used? Are missed shots used? | source-method ambiguity |
| OQ-3 | Does the entry model's "one observation per second" approach imply a clock-resolution issue—are ties at the same game-second handled, and how? | source-method ambiguity |
| OQ-4 | Is zone start included as a control covariate? The article is silent; the exit-model population is already conditioned on the puck being outside the neutral zone, so the role of a separate start-state control cannot be inferred. | source-covariate ambiguity |
| OQ-5 | Did McCurdy test age-dependent continuity priors? The article describes only flat season-to-season shrinkage and reports no age-dependent alternative or sensitivity comparison. | source-prior ambiguity |
| OQ-6 | What is the magnitude of the two acknowledged reconstruction blind spots? Both omission directions inflate entry-defence and deflate exit estimates, but the article does not quantify either bias. | source-validation limit |
