# HockeyViz — Shootiness

- **Title (as published):** "Shootiness"
- **Author:** Micah Blake McCurdy (@IneffectiveMath)
- **Article date:** September 13, 2022
- **URL used:** https://hockeyviz.com/txt/shootiness
- **Accessed:** 2026-07-15
- **Index-date conflict:** HockeyViz's [`Current Models` index](https://www.hockeyviz.com/), checked
  2026-07-16, labels the same page September 13, 2023. The rendered article body says September 13,
  2022; this dossier preserves
  the body date and does not infer which index field is mistaken.
- **Retrieval:** the complete rendered article was retrieved directly. The linked general Elo-method
  article was not required because the HockeyViz page supplies its own initialization, expectation,
  and update equations.
- **Later companion:** the September 24, 2025
  [Magnus 8 game-simulation page](https://hockeyviz.com/txt/magnus8GameSim) describes a different
  shooter-selection weight; that conflict is preserved below and in
  [`hockeyviz-magnus8gamesim.md`](hockeyviz-magnus8gamesim.md).
- **Evidence boundary:** this page documents a conditional shooter-choice/share model and two uses of
  its output. It does not document an expected-goals, finishing, shot-creation, or additive player-value
  model. The dossier therefore does not treat `Shootiness` as any of those estimands.

## 1. Summary

HockeyViz `Shootiness` estimates which on-ice skater will take a team shot, conditional on the team
having generated that shot and on the set of skaters on the ice. It is an online Elo-style model with a
pairwise logistic comparison inside a normalized multi-player expectation. Every observed regular-season
shot since 2007-08 updates the shooter upward and every non-shooting on-ice teammate downward, with a
larger update when the shooter was less expected. Forwards and defenders begin from different baselines
chosen so that a typical five-skater unit allocates two-thirds of shots to its three forwards and one-third
to its two defenders.

The latent rating is used in two places described by the article: as the shooter-sampling distribution in
game simulation, and as an interpretable summary-card probability against a fixed synthetic group of
position-balanced, baseline-rated teammates. The page does not say that this quantity is added to sG or
any other Total. It also reports no out-of-sample validation, calibration, uncertainty, decay, season reset,
or sensitivity analysis for its two empirically chosen constants.

The later Magnus 8 game-simulation page instead says simulated shooters are selected from each
player's historical fraction of team on-ice shots in the current EV/PP/PK state, weighted by expected
ice time. Neither source explains whether that raw propensity replaced the Elo distribution, coexists
with it, or describes a different simulator path. The current public simulation-use claim is therefore
ambiguous even though this page's Elo equations and card use are explicit.

## 2. Decision inventory

| id | topic | source decision or fact | source rationale / limit |
|---|---|---|---|
| hockeyviz-shootiness-D1 | estimand | Estimate the probability/share that each member of the current on-ice skater set takes a team shot, conditional on a shot occurring. | The article defines a high rating as greater likelihood of taking the team's shots. |
| hockeyviz-shootiness-D2 | model class | Use an Elo-style online update built from a logistic function with scale `d = 100`. | Elo is presented as a streamlined logistic-regression construction; `d` is called empirically determined. |
| hockeyviz-shootiness-D3 | position baseline | Initialize a player at `r0 = -d log(n/p - 1)`, with `(n,p) = (2,1/3)` for defenders and `(3,2/3)` for forwards. | This makes each defender's initial share `1/6` and each forward's `2/9`, which sum to one for a conventional 2D/3F unit. |
| hockeyviz-shootiness-D4 | training population | Process every regular-season shot from 2007-08 onward in event order. | The article does not state an end date for the fit separate from the displayed 2007-2023 graph. |
| hockeyviz-shootiness-D5 | multi-player expectation | For each skater `a` in on-ice set `A`, average pairwise logistic expectations against every other member, scaled so the expected shares sum to one. | The article explicitly states `sum(e_a) = 1`. |
| hockeyviz-shootiness-D6 | online update | After player `q` shoots, update every on-ice player by `k (|A|-1) (1[p=q] - e_p)`, with `k = 1`. | The shooter always rises, teammates always fall, and surprising outcomes move ratings more; `k` is called empirically determined. |
| hockeyviz-shootiness-D7 | temporal policy | Ratings accumulate sequentially from the initial value; no season reset, aging, injury adjustment, exposure-dependent shrinkage, or recency decay is documented. | This is an evidence limit, not a claim that private/current code has no such handling. |
| hockeyviz-shootiness-D8 | simulation use | Convert the on-ice ratings to `e_a` and sample the simulated shooter from those probabilities. | This is one of this page's two stated uses; the 2025 Magnus 8 game-simulation page instead documents strength-specific historical shot fractions weighted by expected ice time. |
| hockeyviz-shootiness-D9 | fixed synthetic basket | For a defender, compare against one baseline defender and three baseline forwards; for a forward, compare against two baseline defenders and two baseline forwards. | This standardizes teammate context by position rather than using a player's actual linemates. |
| hockeyviz-shootiness-D10 | card output | Display an interpretable change in shooter probability under the fixed synthetic basket rather than the latent rating. | The prose says to difference a probability from `r0`, which mixes units; the intended probability-scale baseline is ambiguous. |
| hockeyviz-shootiness-D11 | mechanism boundary | The quantity reallocates a generated team shot among on-ice skaters; it does not estimate whether the team generates a shot or whether that shot scores. | This follows directly from conditioning on an already-generated shot and is an inference from the documented estimand. |
| hockeyviz-shootiness-D12 | Total membership | Neither stated use adds `Shootiness` to sG or another player Total. | Absence from this page is not proof about an inaccessible private product; the separate sG/isolate dossier supplies the complementary public-output evidence. |
| hockeyviz-shootiness-D13 | tuning and validation | No loss function, held-out comparison, calibration check, repeatability statistic, or uncertainty estimate is reported for the model or for `d = 100` and `k = 1`. | The source labels both constants empirical without describing their selection experiment. |
| hockeyviz-shootiness-D14 | published artifacts | The page shows a league distribution for skaters who shot during 2007-2023 and points to season-end values on player summary cards. | The figure is descriptive; no downloadable rating history or model artifact is linked. |
| hockeyviz-shootiness-D15 | observation ceiling | The model learns only from recorded shots and recorded on-ice skater sets; it does not observe unrecorded passing options, possession choices, or off-puck shot opportunities. | This is an inference from the documented input and conditional target. |

## 3. Model structure

For on-ice set `A`, define

\[
l(x)=\frac{1}{1+\exp(-x/d)}, \qquad d=100,
\]

and

\[
e_a=\frac{2}{|A|(|A|-1)}\sum_{p\in A\setminus\{a\}}l(r_a-r_p).
\]

The source states that the `e_a` values sum to one. After observed shooter `q`, ratings update as

\[
r_p \leftarrow r_p+k(|A|-1)(\mathbf 1[p=q]-e_p), \qquad k=1.
\]

The model is therefore competitive: on every observed shot one skater receives positive surprise credit
and the other on-ice skaters receive negative updates. It is not a collection of independent player shot
counts.

## 4. Evaluation and output evidence

The article offers interpretability and face-validity examples but no formal predictive evaluation. It
contrasts players whose raw on-ice shot shares are affected by shoot-first or pass-first teammates, which is
the confounding the competitive rating is meant to address. The published output is a probability-scale
summary-card value and a historical league distribution, plus the latent probability used by the separate
game simulator.

The page reports no:

- chronological or player-held-out loss;
- probability calibration;
- baseline comparison against observed share or a multinomial model;
- hyperparameter sensitivity;
- year-over-year stability;
- interval or posterior uncertainty;
- proof that the displayed probability difference is additive with any value component; or
- reconciliation with the later game-simulation page's different shooter-selection weights.

## 5. Open questions and source ambiguities

1. **Probability-versus-rating subtraction.** The display paragraph says the derived probability is
   differenced from `r0`, but `r0` is a rating while the derived quantity is a probability. The intended
   baseline is plausibly `l(r0) = p/n`, but that correction is not stated and is not silently imposed here.
2. **Irregular on-ice sets.** The expectation formula accepts arbitrary `|A|`, but the initialization and
   card basket assume ordinary forward/defender compositions. Extra-attacker, short-handed, and missing
   on-ice configurations are not discussed.
3. **Temporal freshness.** The training description starts in 2007-08 but gives no decay or reset. How
   quickly the rating adapts to role, team, injury, or aging changes is not evaluated.
4. **Shot universe.** The article says "shot" without enumerating goal/save/miss/block categories. It does
   not establish whether blocked attempts or only unblocked attempts drive the live rating.
5. **Current implementation.** The source is dated 2022 and its graph ends in 2023. Its equations remain
   the latest public methodology found, but this dossier does not project them onto inaccessible current
   private code.
6. **Simulation-use conflict.** The 2025 Magnus 8 game-simulation page uses a strength-specific raw
   on-ice shot fraction multiplied by expected ice time. It does not say whether this supersedes the
   Elo distribution, is an implementation shorthand, or applies to a separate simulation path.
