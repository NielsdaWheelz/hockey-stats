# Evolving-Hockey — Expected Goals Model ("A New Expected Goals Model for Predicting Goals in the NHL")

- **Authors:** Josh Younggren & Luke Younggren (EvolvingWild / Evolving-Hockey)
- **Canonical URLs used:**
  - Primary (fetched): https://evolving-hockey.com/blog/a-new-expected-goals-model-for-predicting-goals-in-the-nhl/ — the site republication (dated April 25, 2021) of the original writeup
  - Original (identified via search, not separately fetched): https://rpubs.com/evolvingwild/395136/ (RPubs, originally published June 7, 2018)
  - Companion (fetched): https://evolving-hockey.com/glossary/general-terms/ (glossary xG entry; defers all technical detail to the writeup)
- **Accessed:** 2026-07-03
- **Retrieval note:** the primary article was retrieved via multiple targeted WebFetch extractions of the evolving-hockey.com page. Everything below is sourced from those retrievals; inferences are marked "(inferred)". No newer methodology document was found on evolving-hockey.com — the 2021 blog post appears to be a republication of the 2018 RPubs writeup, and the glossary explicitly points back to it as the model documentation.

## 2. Summary

Evolving-Hockey's expected goals model is a per-shot binary classifier: for every unblocked shot attempt (Fenwick — goals, shots on goal, misses), it predicts the probability the shot becomes a goal ("the response/target variable is either a 1 or a 0"). The model class is gradient boosting — "eXtreme Gradient Boosting – better known as 'XGBoost'" with `objective = "binary:logistic"` — chosen following Peter Tanner's MoneyPuck approach. The headline architectural decision is **four separate models by strength state**: even-strength (5v5/4v4/3v3), powerplay/man-advantage (5v4, 4v3, 5v3, 6v5, 6v4), shorthanded offense (4v5, 3v4, 3v5), and shots at an empty net, motivated by "significant differences in play styles and scoring rates" and confirmed by early testing. Data is NHL RTSS play-by-play scraped with Manny Perry's dryscrape functions: 7 seasons ('10-11–'16-17) for EV/PP, 10 seasons ('07-08–'16-17) for the rarer SH/EN situations. Features are ~15 conceptual variables (43 columns after dummy expansion): distance/angle to the goal, raw coordinates, shot type, score state, period/game time, home indicator, within-model strength dummies, and — instead of explicit rebound/rush classifiers — a family of **prior-event variables** (type of the immediately preceding event for each team, its coordinates, distance travelled since it, and seconds elapsed). Hyperparameters were tuned by a "modified" random search (5-fold CV × 200-run loops, iteratively narrowed ranges, ~16 hours for EV), with AUC as the tuning metric and log loss reported for reference; final evaluation used a held-out 2017-18 season (EV AUC 0.7822 CV / 0.7747 holdout). A Bayesian shooting-talent feature was built but discarded because XGBoost never used it in any tree. The authors flag missing passing data as the dominant limitation, acknowledge CV optimism, and note there is no calibration or future-goals predictivity analysis in the writeup.

## 3. Decision inventory

| id | topic | decision | rationale / verbatim quote | article section |
|---|---|---|---|---|
| evolving-hockey-xg-D1 | target definition | xG framed as binary classification per unblocked shot: 1 if the Fenwick shot is a goal, else 0 | "the response/target variable is either a 1 or a 0 … 1: a fenwick shot resulted in a goal // 0: a fenwick shot was not a goal"; `is_goal = 1 * (event_type == 'GOAL')` | Modeling process |
| evolving-hockey-xg-D2 | shot universe | Blocked shots excluded from the target universe (Fenwick only) | "Only unblocked shots will be included (as the coordinates for blocked shots are recorded based on where the shot was blocked – not where it was taken)" | Data preparation |
| evolving-hockey-xg-D3 | data source | NHL RTSS play-by-play scraped with Manny Perry's dryscrape functions; RTSS data made public on Corsica | "NHL's RTSS data, scraped using Manny Perry's dryscrape functions" | Data preparation |
| evolving-hockey-xg-D4 | event stream | Underlying event stream filtered to GOAL, SHOT, MISS, BLOCK, FAC, HIT, GIVE, TAKE (blocks/faceoffs/hits/give/take retained as *prior-event* context even though only Fenwick events are scored) | filter list in code; prior-event dummies cover exactly these types | Data preparation |
| evolving-hockey-xg-D5 | layer boundary / model split | Four separate models by strength state: EV (5v5, 4v4, 3v3), PP/man-advantage (5v4, 4v3, 5v3, 6v5, 6v4), SH offense (4v5, 3v4, 3v5), empty net | "Given the significant differences in play styles and scoring rates … it seemed like a good idea to build four separate models … we determined that there was a benefit to creating separate models" | Modeling process |
| evolving-hockey-xg-D6 | PP pooling | Goalie-pulled offense (6v5, 6v4) pooled into the PP/man-advantage model rather than its own state | strength-state list for the PP model includes 6v5, 6v4 | Modeling process |
| evolving-hockey-xg-D7 | training windows | EV & PP: 7 seasons ('10-11–'16-17); SH & EN: 10 seasons ('07-08–'16-17) — longer window for rare states, shorter for common ones due to compute; pooled unweighted (no recency weighting — code-verified, see §10) | "the main reason being computational time to train the models"; "short-handed and empty net shots occur much less frequently than EV or PP attempts" | Data preparation |
| evolving-hockey-xg-D8 | exclusions | 6v3, penalty shots, and shootouts excluded | "We decided to exclude the above to improve the accuracy of measuring the most important situations for skater evaluation. The 6v3 state occurs so infrequently, we deemed this unnecessary (and potentially problematic due to a class imbalance)" | Data preparation |
| evolving-hockey-xg-D9 | missing data | Shots with missing coordinates (shot or prior event) dropped (`!is.na(coords_x)` etc.); per-season missing rates reported (0.0128–0.0284 as retrieved — proportions, ~1.2–2.8%; unit resolved and range corrected to 0.0118–0.0284 by the §10 code check) | "here are the total number of fenwick shots that were missing coordinates for the shot or prior event" | Data preparation |
| evolving-hockey-xg-D10 | model class | XGBoost (gradient boosted trees), `objective = "binary:logistic"`, for all four models | "We used an algorithm called 'eXtreme Gradient Boosting' – better known as 'XGBoost' – for all four of these models" | Modeling process |
| evolving-hockey-xg-D11 | rebound/rush handling | NO explicit rebound or rush-shot classifier features; prior-event variables (type/coords of last event, distance_from_last, seconds_since_last) carry that information implicitly — adopted from MoneyPuck | "Rather than using rebound and rush shot classifiers, he [Peter Tanner] used prior event variables in his model. His use of a gradient boosting algorithm and prior event variables was something we drew heavily on" | History / Modeling process |
| evolving-hockey-xg-D12 | distance construction | shot_distance = sqrt((89 − \|x\|)² + y²) — Euclidean distance to the goal line plane at x = 89 | formula given in code | Feature construction |
| evolving-hockey-xg-D13 | angle construction | shot_angle = abs(atan(y / (89 − \|x\|)) · 180/π) | formula given in code | Feature construction |
| evolving-hockey-xg-D14 | long-shot correction | Event descriptions parsed for recorded distance/zone; "long shots" (recorded distance > 89 ft, i.e. behind-net/wrong-end coordinates) identified and distance+angle corrected | "Since the distance and angle calculation assumes any shot was taken from 89 feet or less, we will identify 'long shots' and correct the distance and angle" | Data preparation |
| evolving-hockey-xg-D15 | zone correction | Defensive-zone BLOCK events re-labelled offensive zone (`event_zone == 'Def' & event_type == 'BLOCK' → 'Off'`) | code quote in cleaning section | Data preparation |
| evolving-hockey-xg-D16 | penalty-shot cleanup | Strength state and skater counts corrected for penalty shots during cleaning (the shots themselves then excluded from modeling) | "we will correct the strength state and count of skaters for penalty shots" | Data preparation |
| evolving-hockey-xg-D17 | raw coordinates as features | Raw coords_x/coords_y included as predictors *alongside* derived distance/angle, letting the trees learn location effects beyond the two derived geometry features | feature list includes coords_x, coords_y and shot_distance, shot_angle | Feature construction |
| evolving-hockey-xg-D18 | prior-event features | Last-event coords (coords_x_last, coords_y_last), distance_from_last = Euclidean distance between shot and prior event, seconds_since_last; plus dummies for prior event type × {same team, opposing team} over SHOT/MISS/BLOCK/GIVE/TAKE/HIT, and prior_face for faceoffs | feature list | Feature construction |
| evolving-hockey-xg-D19 | shot type | 7 shot-type dummies (wrist, deflected, tip, slap, backhand, snap, wrap-around); missing shot type defaults to Wrist | "defaulting to 'Wrist' when missing" | Feature construction |
| evolving-hockey-xg-D20 | score state | 9 score-differential dummies from score_down_4 to score_up_4, relative to the shooting team (i.e. score effects handled *inside* the model as features, not by post-hoc adjustment) | feature list | Feature construction |
| evolving-hockey-xg-D21 | within-model strength dummies | Even-strength model gets state_5v5 / state_4v4 / state_3v3 dummies (strength split is two-level: separate models by regime + dummies within regime) | feature list | Feature construction |
| evolving-hockey-xg-D22 | venue | is_home dummy (home/away shooter) is the only venue feature; no rink/scorekeeper coordinate-bias correction is described | feature list | Feature construction |
| evolving-hockey-xg-D23 | time features | game_seconds and game_period both included as continuous features | feature list | Feature construction |
| evolving-hockey-xg-D24 | feature counting | 43 dummy-expanded columns ≈ 15 conceptual features; authors prefer the 15-count | "Technically we're using 43, but the 8 groups of dummy variables are intrinsically connected … more accurate to say we've used 15 features" | Feature construction |
| evolving-hockey-xg-D25 | shooter talent | Bayesian (empirical-Bayes-inspired) shooting-talent feature built and offered to the model, but XGBoost never split on it in any tree → dropped; authors admit their construction may have been flawed | "This variable (in each model) was never used in any decision tree that was generated"; "Of course there's the chance our method was flawed" | Modeling process |
| evolving-hockey-xg-D26 | identical feature set across models | All four strength-state models use the identical feature set; only training data and tuned hyperparameters differ (writeup claim — contradicted by the code: UE/SH add `prior_event_EV` + `pen_seconds_since`, see §10) | "four separate models" trained independently with identical inputs | Modeling process |
| evolving-hockey-xg-D27 | hyperparameter search | "Modified" random search: 5-fold CV run in a 200-iteration loop, parameter ranges narrowed iteratively between loops; ~16 hours for the EV model; each model tuned separately | "5-fold cross validation run in a loop 200 times"; "we'd get an idea of where the 'best' runs were coming in … bring the ranges for each parameter in bit by bit" | Modeling process |
| evolving-hockey-xg-D28 | tuning metric | AUC used to train/tune; log loss reported "to reference" only | "AUC was used to train and tune the final model parameters – Log Loss was included to reference" | Modeling process |
| evolving-hockey-xg-D29 | early stopping | early_stopping_rounds = 25 during CV | code quote | Modeling process |
| evolving-hockey-xg-D30 | nrounds/seed sensitivity | Final tree count fixed by re-running CV 20+ times because "the rounds/seed did change, often significantly"; final EV: nround = 189, set.seed(556) | quoted; `xgb.train(data = full_xgb, params = param_7_EV, nround = 189)` | Modeling process |
| evolving-hockey-xg-D31 | final EV hyperparameters | eta=.068, gamma=.12, subsample=.78, max.depth=6, colsample_bytree=.76, min_child_weight=5, max_delta_step=5 | parameter block quoted verbatim | Modeling process |
| evolving-hockey-xg-D32 | evaluation protocol | K-fold CV metrics + a fully held-out future season (2017-18) as out-of-sample test | results table reports "AUC – CV" and "AUC – '17-18" per strength state | Results |
| evolving-hockey-xg-D33 | overfitting caveat | Authors explicitly flag CV optimism relative to the holdout season | "As with any model, even the best K-fold cross validated test set is often, to varying degrees, overfit. You can see that here" | Results |
| evolving-hockey-xg-D34 | calibration | NO calibration analysis (no reliability plots, no summed-xG-vs-goals comparison, no post-hoc calibration step) — evaluation is discrimination-only (AUC + log loss) | (inferred from absence) + authors' own admission they did not run Sprigings/Toumi- or Shomer-style predictive validation: "we used AUC for our evaluation metric and have not currently performed a method like Dawson & Asmae/Harry – this could be explored in the future" | Results / Discussion |
| evolving-hockey-xg-D35 | limitation: passing data | Missing pre-shot passing data is the flagged dominant limitation; cross-crease and stretch-pass shots are believed undervalued | "Both of us are fairly confident that any xG model would benefit somewhat significantly from knowing where a pass came from and when it occurred… and we haven't even touched on zone entries/exits" | Discussion |
| evolving-hockey-xg-D36 | feature-importance interpretation | Variable-importance charts shown per model but explicitly caveated as not regression coefficients; shot distance dominates in every strength state | "Clearly, shot distance is the most 'important' variable in the model, regardless of strength state"; "these are not coefficients from a linear regression" | Results |
| evolving-hockey-xg-D37 | empty-net model | Empty-net shots get their own XGBoost model (10 seasons, 3,680 Fenwick shots, same feature set); no EN evaluation metrics reported | "shots directed towards an empty net" as fourth model | Modeling process |
| evolving-hockey-xg-D38 | output artifact | Per-shot xG appended as a column on every Fenwick event in the play-by-play | "This will add a column for every fenwick event that gives its corresponding xG value" | Results |
| evolving-hockey-xg-D39 | implementation | Sparse model matrix (`Matrix(..., sparse = TRUE)`) → `xgb.DMatrix`; R/xgboost stack | code quotes | Modeling process |
| evolving-hockey-xg-D40 | future work | Flagged: Shomer-style two-stage shooter-talent xG; future-goals predictive validation; incorporating publicly tracked passing/zone data; separate penalty-shot/shootout models | quotes in Discussion ("This is a method we would like to potentially explore in a future version") | Discussion |

## 4. Model structure sketch

Single-layer per-shot classifier, replicated four times by strength regime; no hierarchical/latent structure.

```
NHL RTSS PBP (dryscrape)
  └─ clean: parse descriptions, long-shot distance/angle fix, Def-zone BLOCK→Off,
     penalty-shot strength fix, drop missing-coords, drop 6v3/PS/SO
      └─ Fenwick shots only (blocks excluded as targets, retained as prior events)
          ├─ EV model   (5v5,4v4,3v3;   '10-11–'16-17, 537,519 shots) ─┐
          ├─ PP model   (5v4,4v3,5v3,6v5,6v4; '10-11–'16-17, 113,573) ─┤ XGBoost
          ├─ SH model   (4v5,3v4,3v5;   '07-08–'16-17, 23,714)        ─┤ binary:logistic
          └─ EN model   (empty net;     '07-08–'16-17, 3,680)         ─┘
                → per-shot P(goal) column on the PBP
```

Conditioning: everything conditions only on the shot row + the single immediately preceding event (type, team parity, location, elapsed time/distance). Score and within-regime strength are features, not adjustments. No shooter identity, no goalie identity, no on-ice skaters, no passing sequence. Each of the four models is trained and hyperparameter-tuned independently on its own regime's shots with — per the writeup — the identical feature set (in code the UE/SH models carry two extra predictors, see D26/§10).

## 5. Full feature/covariate list (as stated)

Continuous (10): shot_distance; shot_angle; game_seconds; game_period; coords_x; coords_y; coords_x_last; coords_y_last; distance_from_last; seconds_since_last. (The article's own count treats these plus the 8 dummy groups as "15 features"; the continuous list above is 10 items as retrieved — the §10 code check confirms exactly these 10 continuous + 33 dummies = 43 EV predictors, resolving §9.9.)

Boolean/dummy (33, in 8 intrinsically-connected groups):
- Strength (EV model): state_5v5, state_4v4, state_3v3
- Score state: score_down_4, score_down_3, score_down_2, score_down_1, score_even, score_up_1, score_up_2, score_up_3, score_up_4
- Shot type: wrist_shot, deflected_shot, tip_shot, slap_shot, backhand_shot, snap_shot, wrap_shot (missing → Wrist)
- Prior event, same team: prior_shot_same, prior_miss_same, prior_block_same, prior_give_same, prior_take_same, prior_hit_same
- Prior event, opposing team: prior_shot_opp, prior_miss_opp, prior_block_opp, prior_give_opp, prior_take_opp, prior_hit_opp
- prior_face (faceoff immediately preceding)
- is_home

Constructions: shot_distance = sqrt((89 − |x|)² + y²); shot_angle = abs(atan(y/(89 − |x|))·180/π); distance_from_last = sqrt((x − x_last)² + (y − y_last)²).

Considered and excluded: Bayesian shooting-talent variable (never used by any tree; dropped).

Total: "Technically we're using 43, but … more accurate to say we've used 15 features."

## 6. Evaluation protocol and reported results

Protocol: AUC as the tuning/selection metric on 5-fold CV (200-run modified random search per model, early_stopping_rounds=25); log loss reported for reference; final out-of-sample check on the held-out 2017-18 season. No calibration analysis; no out-of-sample future-scoring predictivity test (explicitly deferred to future work).

| Strength state | AUC – CV | AUC – '17-18 | LogLoss – CV | LogLoss – '17-18 |
|---|---|---|---|---|
| EV | 0.7822 | 0.7747 | 0.1847 | 0.1897 |
| PP | 0.7183 | 0.7018 | 0.2716 | 0.2817 |
| SH | 0.7975 | 0.8369 | 0.2148 | 0.2035 |
| EN | (not reported) | (not reported) | (not reported) | (not reported) |

Authors' own reading: CV numbers are mildly optimistic vs. the holdout ("even the best K-fold cross validated test set is often, to varying degrees, overfit"); SH holdout > CV is shown without further comment in the retrieved text.

## 7. Outputs / artifacts

- Per-shot xG probability (0–1) appended as a column to every Fenwick event in the PBP.
- Variable-importance charts for the EV, PP, and SH models (distance dominant everywhere).
- Example tables of highest-xG shots (goal, date, game time, xG value, video links) and example videos/GIFs of high/low-xG shots.
- AUC/log-loss evaluation tables (CV + 2017-18 holdout).
- Downstream (from the glossary/site, descriptive only): the model feeds site stats (xGF/xGA, later xGAR/RAPM); no maps or spatial surfaces are produced by this model — it is a per-shot scalar.

## 8. Linked / companion articles referenced

Fetched companions (1 of 2 allowed): https://evolving-hockey.com/glossary/general-terms/ (defers to the writeup; adds only the stance that xG is preferred over scoring-chance buckets because it "evaluates goal probability on a continuous level, does not introduce arbitrary assumptions into the data").

References cited in the article (not fetched):
- Alan Ryder, Shot Quality (2004): http://hockeyanalytics.com/Research_files/Shot_Quality.pdf
- Alan Ryder, Product Recall for Shot Quality (RTSS data issues): http://hockeyanalytics.com/Research_files/Product_Recall_for_Shot_Quality.pdf
- Ken Krzywicki, distance-adjusted shot quality: http://hockeyanalytics.com/Research_files/SQ-DistAdj-RS0809-Krzywicki.pdf and http://hockeyanalytics.com/Research_files/SQ-RS0910-Krzywicki.pdf
- Michael Schuckers, DIGR: http://www.hockeyanalytics.com/Research_files/DIGR_Schuckers.pdf ; follow-up: https://www.arcticicehockey.com/2011/6/15/2224920/a-look-at-shot-quality
- Tom Tango, Weighted Shots Differential: http://tangotiger.com/index.php/site/comments/introducing-weighted-shots-differential-aka-tango
- Brian MacDonald, Sloan 2012 NHL Expected Goals: http://www.sloansportsconference.com/wp-content/uploads/2012/02/NHL-Expected-Goals-Brian-Macdonald.pdf (+ video https://www.youtube.com/watch?v=zlQKg1_NPls)
- Dawson Sprigings & Asmae Toumi (2015): https://hockey-graphs.com/2015/10/01/expected-goals-are-a-better-predictor-of-future-scoring-than-corsi-goals/
- Emmanuel Perry, Corsica xG Part I: http://www.corsica.hockey/blog/2016/03/03/shot-quality-and-expected-goals-part-i/
- Peter Tanner, MoneyPuck: http://moneypuck.com/ and http://moneypuck.com/about.htm (the direct methodological ancestor: gradient boosting + prior-event variables)
- Cole Anderson, open-source logistic xG: https://rstudio-pubs-static.s3.amazonaws.com/311470_f6e88d4842da46e9941cc6547405a051.html
- Matthew Barlowe, open-source xG: http://www.crowdscoutsports.com/game-theory/expected-goal-xg-model/
- Harry Shomer, GBM xG + shooter-talent two-stage + evaluation: http://fooledbygrittiness.blogspot.com/2018/01/expected-goals-model.html , .../2018/03/shooter-talent-and-expected-goals.html , .../2018/03/evaluating-my-shooter-xg-model.html
- Data/code: Manny Perry dryscrape/corsica: https://github.com/mannyelk/corsica/tree/master/modules and .../models ; NHL RTSS HTM example: http://www.nhl.com/scores/htmlreports/20172018/PL020672.HTM
- XGBoost/GBM background: https://xgboost.readthedocs.io/en/latest/model.html ; https://homes.cs.washington.edu/~tqchen/pdf/BoostedTree.pdf ; Breiman http://statistics.berkeley.edu/sites/default/files/tech-reports/486.pdf ; Friedman https://statweb.stanford.edu/~jhf/ftp/trebst.pdf ; Laurae++ parameter guide https://sites.google.com/view/lauraepp/parameters ; David Robinson empirical Bayes http://varianceexplained.org/r/empirical_bayes_baseball/
- Model code (identified via search, evolvingwild GitHub): https://github.com/evolvingwild/hockey-all/tree/master/xG

(hockeyviz.com/howto/isolate and /howto/shotMap intentionally skipped — covered by sibling agents.)

## 9. Open questions / ambiguities in the source (as retrieved)

*(2026-07-03: items 1, 5, 6, and 9 — and the substance of 2 — are resolved by the §10 code check; item 8's what-is-public half is answered there too.)*

1. **Missing-coordinate rate units:** retrievals reported the per-season missing-coordinate figures as both "0.0128 to 0.0284" (proportions, ~1.3–2.8%) and "0.0128% and 0.0284%". The proportion reading is more plausible for RTSS but the unit was not resolvable from the retrieved text. *(Resolved: proportions — §10.)*
2. **PP/SH/EN hyperparameters:** only the final EV parameter block (`param_7_EV`, nround=189) was retrieved; whether the article prints the tuned parameters for the other three models is unconfirmed. *(Resolved in substance: all four blocks are in the public code — §10.)*
3. **EN model evaluation:** no AUC/log-loss row for the empty-net model appears in the retrieved results table; unclear if the article reports EN performance at all.
4. **game_seconds definition:** one retrieval glossed it as elapsed time "within the game period", which conflicts with also including game_period; likely total game elapsed seconds (inferred), unresolved from retrieval.
5. **Score-state capping:** whether score_down_4/score_up_4 absorb differentials beyond ±4 is not stated. *(Resolved: capped at ±4, the end dummies absorb — §10.)*
6. **Prior-event window:** no time cutoff is stated for what counts as the "prior event" — apparently simply the immediately preceding event with seconds_since_last carrying recency; whether extreme gaps are truncated is not stated. *(Resolved: untruncated raw per-period lag — §10.)*
7. **No rink/scorekeeper coordinate-bias adjustment is mentioned** anywhere in the retrieved text (notable given Ryder's cited "Product Recall" concerns and known arena-recording bias); absence of the adjustment is (inferred from absence).
8. **2018 vs 2021 versions:** the evolving-hockey.com post (April 25, 2021) appears to be a straight republication of the June 7, 2018 RPubs writeup; whether the production model behind the current site stats (xGAR era) still matches this documented version is not stated anywhere found.
9. **Feature count arithmetic:** the article claims 43 columns / 15 conceptual features; the retrieved continuous list has 10 items and dummies 33, which does not obviously reconcile to 43 without assumptions — exact accounting unresolved from retrieval. *(Resolved: 10 + 33 = 43 EV predictors exactly — §10.)*
10. **Calibration:** entirely absent (no reliability analysis, no post-hoc calibrator, no summed-xG audit); the authors only acknowledge not having run *predictivity* validation, and do not discuss probability calibration as a concept.

## 10. Code check (2026-07-03, evolvingwild GitHub) — code-derived addendum

**This section is derived from the model's public training CODE, not from the article.** The only public EH xG training code is https://github.com/evolvingwild/hockey-all/tree/master/xG (`xG_preparation.R`, 779 lines; `xG_modelling.R`, 310 lines; all commits 2018-06-08 — the code behind this writeup; the repo was last pushed 2021-08-02 but the xG folder is untouched since 2018). `github.com/evolvingwild/evolving-hockey` returns HTTP 404 (removed or private — the old EH scraper lived there), and nothing else public on the account carries xG training code: the account's only other repos are `wPAR` (their 2017 pre-xG WAR-family model) and non-hockey `miscellaneous`, and `hockey-all`'s sibling folders (`NHL_Awards`, `wPAR`, `draw_rink.R`) are not xG code. Every verdict below is therefore scoped to the 2018 model; the current production (xGAR-era) model is not public and §9.8 stands. **Epistemic ordering (2026-07-04):** treat this code as a witness to the 2018 lineage, never as truth about EH-current — a repo dormant since 2018 almost certainly trails their private production by years (the newer repo's 404 shows the public record contracting, not tracking, their work). Where a claim concerns what EH does *today*, their most recent public writeups/glossary govern; code-only facts (the UE/SH extra predictors, random folds, drop mechanics) date to 2018 and must not be projected forward.

- **Recency weighting / season half-life: affirmatively absent.** `xgb.DMatrix` is built with `data` + `label` only (xG_modelling.R:54-61; same for `xgb.cv` at :118-125/:187-193 and `xgb.train` at :217-220) — no `weight` argument, no `setinfo`, no decay or half-life or season term anywhere in the modelling script ("season" never appears in xG_modelling.R; the only "weight" hits are `min_child_weight`, an XGBoost regularizer). Training pools 7 seasons (EV/UE) or 10 (SH/EN) with equal weight. Hardens D7 from inferred-from-absence to code-verified: any "EH-style in-training season half-life" attribution is contradicted by all public EH xG training code.
- **Feature sets are NOT identical across the four models — D26 is false in code.** `fun.model_prep` (xG_preparation.R:488-495) gives the EV model exactly 43 predictors — resolving §9.9's arithmetic: 10 continuous + 33 dummies, precisely the §5 list — and the writeup's published list matches the EV code exactly (every writeup feature is in code). But the UE (PP) and SH models add two code-only predictors the writeup never mentions (xG_preparation.R:548-549, 601-602): `prior_event_EV` (last event occurred at even strength) and `pen_seconds_since` (seconds since the penalty started within `pen_index`, oddly capped ≥300 s → 120; :291-293, :349-351). EN omits both. Predictor counts: EV/EN 43, SH 45, UE 47 — each model carries its own strength dummies (EV/SH/EN 3, UE 5: state_5v4/4v3/5v3/6v5/6v4), so UE = 43 − 3 + 5 + 2 and SH = 43 − 3 + 3 + 2; the state-dummy variation is writeup-disclosed (D21), the two extra predictors are not.
- **Missing-coordinate drop rates are PROPORTIONS — §9.1 resolved.** The code drops Fenwick shots when shot coords are NA, prior-event coords are NA, or coords are (0,0) with recorded pbp_distance ≠ 90 (anomaly filter; xG_preparation.R:224-227, 242-243). The writeup's table header literally says "Percentage", but the values are proportions of Fenwick shots — 1.18–2.84% per season (true min 0.0118 in 2015-16, so "0.0128–0.0284" slightly misquotes the range; 2017-18 = 0.0128, 2007-08 = 0.0284, earliest season worst as expected). A literal-percent reading (~10–22 dropped shots/season out of ~78k) is impossible given documented whole-game RTSS/ESPN coordinate-feed outages (one dead-feed game ≈ 60 Fenwick shots already exceeds it) and the code's own anomaly machinery.
- **Prior-event window — §9.6 resolved: untruncated.** `seconds_since_last = game_seconds − lag(game_seconds)` within (season, game_id, game_period) (xG_preparation.R:231) — no time cutoff, no cap, no stoppage reset (STOP/PENL are simply excluded from the 8-event lag universe; FAC is retained as `prior_face`). In particular there is NO rebound classifier and NO rebound time window/constant of any kind in the code; the only time capping anywhere is the UE/SH `pen_seconds_since` ≥300→120 rule.
- **Score-state capping — §9.5 resolved:** score differential is capped at ±4 before dummying (xG_preparation.R:455-463), so score_down_4/score_up_4 do absorb larger differentials.
- **Non-EV hyperparameters — §9.2 resolved in substance:** the final tuned parameter blocks for all four models (EV/UE/SH/EN) are in the public code (xG_modelling.R:231-304), whatever the article prints.
- **CV fold construction: plain random row-wise folds.** Every CV call is bare `xgb.cv(..., nfold = 5)` (xG_modelling.R:118-125, :187-193) — no `folds=` argument, no game/season grouping, no stratification, no chronological ordering; shots from the same game (including rebound chains sharing prior-event context) can straddle train/validation folds. The writeup's CV-vs-holdout optimism (D33) is consistent with this leakage-prone fold design.
- **EN model:** the code comments that the empty-net model is used only for game charts and "probably should just be removed" (xG_modelling.R:293) — consistent with §9.3's missing EN metrics.
