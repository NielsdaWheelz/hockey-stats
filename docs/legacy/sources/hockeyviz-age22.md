# HockeyViz — Age and Decay

- **Title (as published):** "Age and Decay"
- **Author:** Micah Blake McCurdy (@IneffectiveMath)
- **Article date:** November 28, 2022
- **URL used:** https://hockeyviz.com/txt/age22 — fetched directly via curl with a browser
  User-Agent (WebFetch returns HTTP 403 from hockeyviz.com). The HTML (`<title>`: "Age and Decay")
  was retrieved in full (≈36 KB). No Wayback fallback was required.
- **Accessed (fetch date):** 2026-07-04
- **Completeness:** full article retrieved. Sections: Introduction, Method, Imputing Missing Data,
  Fitting, Results (Even-Strength Shot Rate, Special Teams Shot Rate, Penalty Drawing and Taking,
  Goal Impact Stats), Appendix: Positional Breakdown. All text recovered; the positional-breakdown
  appendix links graphs only with no accompanying text (see Open questions).
- **Epistemic note:** this article is a 2022 empirical aging study using survivorship-corrected
  non-parametric regression. It is not a parabolic fit. McCurdy's Magnus 9 (2025) _approximates_
  its findings with a parabola `c(a−24)²` as a practical prior for the isolation model; the parabola
  is Magnus 9's design choice, not a claim in this article. Citations to age22 as "the aging study
  behind the parabolic prior" are compressed shorthand that elides that distinction (see
  Cross-check §C1).

---

## Summary

McCurdy constructs survivorship-bias-corrected aging curves for a cohort of NHL players
(≥1,000 career minutes, 2007–2023, 1,548 skaters + 185 goaltenders) across nine separate
ability dimensions. The key insight is that the observed ability of NHL-active players at any age
is a biased sample: young stars are rushed in because scouts already know they are good, and old
players persist selectively because they remain above the replacement threshold. Both biases
inflate or depress the raw observed age-ability curve. McCurdy handles this by tracking two
latent terms per integer age — the average ability of observed (O_a) and hidden (H_a)
cohort members — and recovering the full-cohort curve C_a = w_a · O_a + (1 − w_a) · H_a,
where w_a is the observed fraction at age a. Hidden-player abilities are imputed by truncated
normal sampling (reject draws above the 75th percentile of the observed distribution), following
the method of Schuckers, Lopez, and Macdonald (preprint). The model is fitted with OLS plus
"fusion" (adjacent-age similarity) penalties rather than diagonal ridge; no parametric
functional form is assumed. Results are presented graphically per skill but peak ages are mostly
not stated numerically. Notable findings: EV defence peaks around age 25 and declines more
slowly than offence; the goaltending curve peaks at approximately age 26; finishing and setting
curves are "very flat" early, suggesting these abilities are already developed when players enter
the league; penalty drawing and taking decline approximately uniformly from youth with no
characteristic peak (attributed to footspeed). The article explicitly flags the biased
observed-data conclusion that EV shot generation peaks at 19–20 as a selection artefact.
Positional breakdowns (forward vs. defender) are available in an appendix, without accompanying text.

---

## Decision inventory

| id | topic | decision | rationale / verbatim quote | article section |
|---|---|---|---|---|
| hockeyviz-age22-D1 | cohort definition | Cohort = skaters and goaltenders with ≥1,000 minutes of NHL regular-season hockey over the 2007–2023 window. 1,548 skaters + 185 goaltenders. | "This minute threshold serves no technical purpose … but instead focusses attention on the kind of players of greater interest to me, namely the ones with non-trivial careers." | Method |
| hockeyviz-age22-D2 | age grid | Integer ages 18–49. "Any discrete set of ages can be used." | Chosen for definiteness; not principled. | Method |
| hockeyviz-age22-D3 | O/H two-covariate design | For each age a, two model covariates: O_a (mean ability of cohort members observed in NHL at age a) and H_a (mean ability of those not observed). | The full-cohort curve C_a = w_a · O_a + (1 − w_a) · H_a recovers unbiased aging from the biased observable. | Method |
| hockeyviz-age22-D4 | year classification | Each player-season is classified as an entry year (first NHL season), departure year (last NHL season), or middle year. Entry/departure encoding pulls O_a and H_a together at ages of high roster churn. | Players may have more than one entry/departure year if they have multi-stint careers. | Method |
| hockeyviz-age22-D5 | middle-year encoding | Middle years: fractional age splits (e.g., 0.75 in O_28, 0.25 in O_29 for a player who was 28 for 75% of that year). Response Y = observed ability. | Straightforward fractional assignment. | Method |
| hockeyviz-age22-D6 | departure-year encoding | Y_38 is encoded as H_39 + O_38 − O_39, "synthesizing both information about the player's performance in their departure year itself and the fact that it is a departure year." | Replaces the missing Y_39 with the hidden-cohort value; penalises the gap between O_a and H_a at departure ages. | Method |
| hockeyviz-age22-D7 | entry-year encoding | Dual of departure: Y at age a encoded as H_{a-1} + O_a − O_{a-1}. | "Pulls O_a towards the observed results for players of that age but also pulls the estimates of O_a and H_a more tightly together for ages in which more players enter or depart." | Method |
| hockeyviz-age22-D8 | imputation: model of gatekeepers | Hidden-player ability is modelled not as random absence but as active selection by "a vast network of persons—scouts, stat-keepers, managers, and so on—endeavouring to put the very best players into the NHL." | The 75th-percentile truncation encodes "if the player's ability were so high, we assume that they would somehow be put into the league." | Imputing Missing Data |
| hockeyviz-age22-D9 | imputation: truncated normal, 75th-percentile cap | Hidden-player ability imputed by drawing from N(mean_observed, sd_computed) and rejecting values above the 75th percentile of that distribution. "This method, as well as the rejection threshold, are both taken from the preprint of Schuckers, Lopez, and Macdonald." | Moving the cap lower = gatekeepers are better; raising it arbitrarily = no quality distinction between in-league and out-of-league. | Imputing Missing Data |
| hockeyviz-age22-D10 | imputation SD | The SD of the imputation distribution is "computed from the standard deviation of the observed abilities and the fraction of the cohort which is observed at the age at hand, again following their method." | (inferred: follows Schuckers-Lopez-Macdonald formula for adjusting observed SD for partial selection.) | Imputing Missing Data |
| hockeyviz-age22-D11 | iterative two-step fitting | Step 1: impute missing data using mean observed values → fit model. Step 2: discard, re-impute using full-cohort estimated means → fit again. Method taken from Schuckers, Lopez, and Macdonald. | Allows the cohort mean estimate to condition the imputation, rather than using the biased observed mean. | Fitting |
| hockeyviz-age22-D12 | fitting procedure: OLS + fusion penalties, no diagonal ridge | "fitted using ordinary least squares fitting, but with three kinds of ridge penalties … here, we do not use any such penalties [diagonal], and instead use so-called 'fusion' penalties." | No prior toward zero; smoothness achieved by adjacent-age fusion, not global shrinkage toward a parametric form. | Fitting |
| hockeyviz-age22-D13 | O-fusion penalty | O_a fused to O_{a+1} with strength proportional to the fraction of cohort members shared between those two ages. | Ensures adjacent observed curves move together where the cohort overlaps. | Fitting |
| hockeyviz-age22-D14 | H-fusion penalty | H_a fused to H_{a+1} analogously to the O-fusion. | Same rationale. | Fitting |
| hockeyviz-age22-D15 | C-fusion penalty | C_a = w_a · O_a + (1 − w_a) · H_a fused to C_{a+1}. "We expect that C_a will vary smoothly as a function of a, since we know that the physical changes that occur in the adult human body as it ages are gradual." | The full-cohort curve (the target) is the object required to be smooth, not the raw O or H separately. | Fitting |
| hockeyviz-age22-D16 | penalty constant | All fusion penalties are multiplied by 50,000. "empirically chosen to give a suitably smooth result." | Ad hoc; no cross-validation or theoretical derivation cited. | Fitting |
| hockeyviz-age22-D17 | data range used | 2008–09 through 2021–22. The 2007–08 season excluded ("labourious to determine which players are entering") and 2022–23 excluded ("in progress"). | Cohort membership and entry/departure status is determined from all 2007–2023 data; the fitted model uses the inner range. | Fitting |
| hockeyviz-age22-D18 | ability measure: isolated impact | The response Y is McCurdy's isolated individual ability from his separate shot-rate or xG models, not raw on-ice statistics. "the framework described above will be appropriate for any ability for which we have a measurement that we trust is suitably isolated to the individual." | Isolation is a precondition; raw rates would conflate aging with context effects. | Results |
| hockeyviz-age22-D19 | selection-bias finding (EV offence) | Without survivorship correction, observed EV shot-generation curve peaks at ~19–20. McCurdy calls this erroneous: "players of that age who play in the league do so almost entirely because their coaches and managers are already quite sure that they will be very good." | The O/H correction moves the curve's peak to an older, unspecified age. | Results — EV Shot Rate |
| hockeyviz-age22-D20 | defence peaks later and higher than offence (EV) | "Not only does defensive suppression peak later, it is, comparing like ages, always higher than offensive creation and falls off much more slowly as players age." Defence peaks around age 25. | Consistent pattern repeated across all skill families below. | Results — EV Shot Rate |
| hockeyviz-age22-D21 | special teams: later peaks than EV | PP shot generation and SH shot suppression peak at later ages than the equivalent EV abilities. "the peak ages are later." | Attributed partly to stronger selection pressure: "older players with established power-play ability routinely continue to play such minutes even as they lose even-strength resources." | Results — Special Teams |
| hockeyviz-age22-D22 | special teams: late-career uptick (PP) | PP shot-generation shows an uptick in late career. "may be a modelling artifact, or it may be players deliberately honing their powerplay skills late in their careers in order to remain in the league." | Flagged honestly as ambiguous. | Results — Special Teams |
| hockeyviz-age22-D23 | penalty draw and take: uniform decline, no peak | Both penalty drawing and taking "decline more or less uniformly as players age" with no characteristic peak. "the 'typical' shape of the aging curve is absent." | "I have a suspicion that this is because the most important factor, both to drawing penalties and to making sure that one does not commit them, is footspeed." | Results — Penalty |
| hockeyviz-age22-D24 | penalty draw/take: constant gap | "the difference between the two curves appears to be constant over most ages" — drawing ability is consistently above not-taking ability, with roughly constant offset. | Pattern is consistent with a single underlying physical attribute (footspeed) driving both. | Results — Penalty |
| hockeyviz-age22-D25 | finishing and setting: already fully developed at entry | "The early part of the finishing and settings curves are both very flat, suggesting that by the time skaters enter the league their goal threat abilities are more or less already fully developed." | Contrasts with shot-rate abilities, which show clear development arcs. | Results — Goal Impact Stats |
| hockeyviz-age22-D26 | goaltending peak age ~26 | "The goaltending curve has the most 'typical' shape, with a peak age at 26, older than the peak of most skater abilities." | Only explicit numerical peak age stated in the article. | Results — Goal Impact Stats |
| hockeyviz-age22-D27 | defensive aspect always dominates across skill families | Across EV, special teams, and penalty: "the defensive ability … is above the offensive ability once again." Pattern is general. | The goaltending result is discussed with the same framing (most typical shape). | Results (all sections) |
| hockeyviz-age22-D28 | positional breakdown provided but not narrated | The appendix repeats the O/H/C analysis separately for forwards and defenders for each of the eight skater abilities, but the article provides no text description of the positional results. | Only the graphs are linked; no commentary. | Appendix |
| hockeyviz-age22-D29 | future work: richer imputation | "In a future version … I mean to replace this imputation method with a more sophisticated one, possibly considering … the specific age they happen to be, their nationality, the pathway their previous career has taken, their positions, perhaps even their family kinship to previous NHL players or their ethnicity." | Flagged as "a more delicate matter than the somewhat drier work of modelling on-ice behaviour only." | Imputing Missing Data |

---

## Model / method structure sketch

```
Cohort (≥1,000 min, 2007–2023)
    ↓  classify each player-season as entry / middle / departure
    ↓  fractional age-split encoding
    ↓  hidden-player imputation (truncated normal, 75th-pct cap, 2-step iterative)
    ↓
Design matrix X:  age-32 O_a columns + age-32 H_a columns
Response Y:       isolated ability measurement (from McCurdy's separate shot-rate / xG models)
    ↓
OLS + three fusion penalties (O-adjacent, H-adjacent, C-adjacent; const = 50,000)
    ↓
Fitted terms: O_a, H_a for a ∈ {18…49}
    ↓
Derived output: C_a = w_a·O_a + (1−w_a)·H_a   (the "aging curve")
```

Key properties:
- **Non-parametric** — no parabola, spline, or other fixed functional form is assumed; smoothness
  is achieved through fusion penalties on C.
- **Survivorship-corrected** — the O/H framework and truncated imputation explicitly model the
  selection mechanism of the "gatekeepers" who decide NHL roster composition.
- **Response = isolated ability** — the aging study inputs McCurdy's own isolation model outputs,
  not raw rates; aging and context confounding are separated by construction.
- **No per-season or per-team effects** — the model is purely cross-sectional in age; year-level
  variation is collapsed into the individual-season ability measurements supplied as input.
- **Uncertainty not reported** — the article publishes fitted C_a curves as point estimates; no
  confidence bands or credible intervals are shown or described.

---

## Evaluation protocol

**No formal evaluation protocol is reported.** The article is a methodology writeup with
graphical result exhibits. Specific evaluation absences:

- No cross-validation or out-of-sample predictive test.
- No likelihood, AIC/BIC, or goodness-of-fit statistic.
- No sensitivity analysis on the 75th-percentile imputation threshold or the penalty constant 50,000.
- No stated uncertainty on the derived C_a curves.
- The penalty constant is described as "empirically chosen to give a suitably smooth result" with
  no further diagnostic.

Face-validity observations offered by McCurdy:
- The uncorrected observed peak at ages 19–20 (a known artefact of star-rookie selection) is shown
  to be corrected.
- The late-age upward bias in raw observed rates (survivorship of better players) is also
  corrected in the C_a curve.
- The goaltending result (peak ~26) is presented as consistent with the "most typical shape."

---

## Open questions / ambiguities in the source

1. **Exact numerical peak ages for offence and defence are not stated.** The article says defence
   peaks "until the age of 25" (defence description) and that EV offence peaks later than the
   erroneous 19–20 raw-observed peak, but the corrected EV offence peak age is never given
   numerically. (inferred from graph description: somewhere in the early-to-mid 20s, but
   unspecified.)
2. **Appendix positional breakdown is graph-only.** Separate forward/defender curves are shown for
   all eight skater abilities, but no text describes the differences. Whether forwards and defenders
   peak at different ages, and by how much, is left to visual inspection of the plots.
3. **Ability response variable details.** The article says "my even-strength shot rate model" is used
   for shot generation/suppression and "my xG model" for finishing/setting/goaltending, but doesn't
   specify which version of each model was current at the time of writing (November 2022; Magnus 8
   was the prevailing isolation model then). The isolation quality (and thus aging-curve quality)
   depends on the model vintage. (inferred: likely Magnus 7 or 8 for the shot-rate abilities.)
4. **No stated relationship to the parabolic prior used in Magnus 9.** The article never mentions
   or derives a parabola. Magnus 9 (2025) says its parabola c(a−24)² is "broadly consistent with
   previous aging work"; this article is the cited prior work, but how the continuous non-parametric
   curve was approximated as a parabola, and why vertex 24 was chosen, is stated only in Magnus 9
   (as a conceded lack of theoretical justification). The age22 article provides no such fit.
5. **No discussion of positional entry priors or position-specific cohort centring.** The positional
   recentring in Magnus 9 (D31) is not discussed here; the article treats skaters as one pool.
6. **Whether the curves have been or will be updated.** The data covers through 2021–22; there is no
   indication in the article whether it will be periodically re-run. Magnus 9 (2025) uses the
   parabolic prior as a summary, suggesting these curves may not be regularly updated.
7. **Graphical accuracy.** All quantitative findings (except goaltending peak ~26) rest on reading
   plots that are not provided as data files. Numbers in this distillation labelled "(from graph)"
   are estimates only.
8. **SD formula for the truncated-normal imputation** is attributed to Schuckers-Lopez-Macdonald
   but not reproduced here. The exact formula is unverified in this distillation.

---
