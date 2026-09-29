# HockeyViz — The Magnus Prediction Model, version 9 (special teams)

- **Title (as published):** "The Magnus Prediction Model, version 9 — Estimating Individual
  Impact on NHL Special Teams Shot Rates"
- **Author:** Micah Blake McCurdy (@hockeyviz.com)
- **Article date:** September 8, 2025
- **URL used:** https://hockeyviz.com/txt/magnus9ST
- **Accessed:** 2026-07-15
- **Companion required by the source:** [Magnus 9 EV](https://hockeyviz.com/txt/magnus9EV),
  already preserved in [`hockeyviz-magnus9ev.md`](hockeyviz-magnus9ev.md). The special-teams page
  says it is strictly separate but otherwise similar and documents only its differences.
- **Other linked method companions:** [Magnus 8 xG](https://hockeyviz.com/txt/xg8) and
  [fabric xG](https://hockeyviz.com/txt/fabricxg), already covered by sibling dossiers.
- **Later conflicting description:** the September 24, 2025
  [Magnus 8 game-simulation page](https://hockeyviz.com/txt/magnus8GameSim) says its special-teams
  shot-rate repetition neglects rest, although this page explicitly displays three rest categories.
  The conflict is preserved rather than reconciled across component vintages.
- **Retrieval:** the complete rendered article was retrieved directly. No substantive method text is
  hidden in HTML comments.

## 1. Summary

Magnus 9 ST is a separate map-valued isolation model for advantaged-team shot creation and
disadvantaged-team shot suppression during 5v4, 5v3, and 4v3 stints. It deliberately does not estimate
short-handed offence or power-play defence. The page inherits the Magnus 9 EV architecture by reference:
stint rows, player and context terms, xG-weighted half-rink shot-rate maps, generalized-ridge isolation,
and league-average interpretation. It then documents two simplifications: head coaches receive only a
general attacking/defending pair rather than score-specific terms, and score receives seven state terms
rather than the EV model's score-by-minute foliation.

The displayed structural context also includes home/away by period, three between-game rest states, and
shift-start-zone effects that decay across 35 indexed seconds (`0` through `34`). Player, teammate,
opponent, score, zone, and coach decompositions are shown. The article reports qualitative results, not a
formal held-out evaluation or uncertainty product.

A game-simulation description published sixteen days later says the special-teams shot-rate model
neglects rest. Because this page directly names and plots rested, normal, and tired terms, the two public
descriptions cannot both be treated as one unambiguous current dependency manifest.

## 2. Decision inventory

| id | topic | source decision or fact | source rationale / limit |
|---|---|---|---|
| hockeyviz-magnus9st-D1 | service boundary | Fit special teams as a model strictly separate from Magnus 9 EV. | The page explicitly calls it separate while reusing the EV architecture. |
| hockeyviz-magnus9st-D2 | observation population | Create a row for every special-teams stint at 5v4, 5v3, or 4v3; the team with more skaters is always the attacking team. | These are the only strength configurations named as included. |
| hockeyviz-magnus9st-D3 | directional roles | Estimate power-play offence and penalty-kill defence; do not estimate short-handed offence or power-play defence. | The author says those mirror directions might be considered someday but records no plan. |
| hockeyviz-magnus9st-D4 | inherited architecture | Use the same model columns as Magnus 9 EV except for the simplifications stated on the ST page. | Exact fitting, priors, response construction, player columns, and penalties are not restated; claims about them must resolve through the EV companion. |
| hockeyviz-magnus9st-D5 | map response | Every coefficient is a half-rink shot-rate map expressed as xG relative to the season's league-average special-teams baseline. | The display also prints each map's aggregate xG-rate effect relative to baseline PP xG. |
| hockeyviz-magnus9st-D6 | coach terms | Include one general attacking/defending pair per head coach, attached to the head coach as a proxy for the wider staff. | Unlike EV, the ST model has no score-specific coach terms. |
| hockeyviz-magnus9st-D7 | score terms | Include seven score states from trailing by at least three through leading by at least three. | Unlike EV, these terms are not crossed with game minute. The results prose later calls them six, a source inconsistency. |
| hockeyviz-magnus9st-D8 | venue and period | Display six home/away-by-period game-state maps. | Home advantage appears in every period; the second period is more dangerous for both teams and the third less dangerous after score adjustment. |
| hockeyviz-magnus9st-D9 | rest | Use rested, normal, and tired categories based on games played on the previous two nights. | Reported PP rest effects are small relative to PK rest effects; the later Magnus 8 game-simulation page's claim that ST neglects rest is a cross-source conflict. |
| hockeyviz-magnus9st-D10 | zone-start decay | Estimate shift-start-zone effects across 35 displayed indices, `0` through `34`. | Offensive-zone benefit decays; on-the-fly changes are negative in ST, unlike EV. |
| hockeyviz-magnus9st-D11 | player reference | Player marginals are shown relative to the special-teams league-average xG-rate map. | The article notes a right-skew toward stronger offensive generators and discusses replaceability as intuition, not as an above-replacement transform. |
| hockeyviz-magnus9st-D12 | decomposition | Publish raw on-ice, player marginal, teammate, opponent, score, zone, and coach views. | Coach impact on players and the general coach terms are shown separately. |
| hockeyviz-magnus9st-D13 | role/position display | Show forwards and defenders separately within the player-marginal results. | The article reports forwards as somewhat stronger PP generators and slightly stronger PK defenders per minute in that season. |
| hockeyviz-magnus9st-D14 | evaluation evidence | Report qualitative structural and distribution findings but no held-out loss, calibration, repeatability, uncertainty, or model-version comparison. | Any general Magnus regularization-tuning evidence belongs to the EV companion; the ST page supplies no ST-specific numeric gate. |
| hockeyviz-magnus9st-D15 | publication surface | Publish context maps, 35 per-second zone-map links, player distributions, decomposition panels, and coach summaries. | The page does not expose a fitted artifact or machine-readable coefficient table. |
| hockeyviz-magnus9st-D16 | observation ceiling | The model isolates associations within recorded special-teams stints and public event/shift context; it does not identify unrecorded tactics or assign causal responsibility to individual coaches. | This follows from the response/covariate design and the head-coach proxy language. |

## 3. Model structure

```text
special-teams stint at 5v4, 5v3, or 4v3
  attacking side = team with more skaters
  defending side = team with fewer skaters
        |
        v
Magnus 9 EV map-valued isolation architecture
  + PP-offence / PK-defence player roles
  + one general attack/defence pair per head coach
  + seven score-state terms (not score x minute)
  + home/away x period
  + three rest states
  + shift-start zone decay, indices 0..34
        |
        v
half-rink xG-rate maps relative to league-average ST xG
```

The article does not say whether 5v4, 5v3, and 4v3 receive distinct indicator terms inside the shared
fit. Inclusion of all three populations must not be upgraded into evidence of within-model strength-state
separation.

## 4. Evaluation and outputs

The source supplies face-validity observations: home advantage, second-period danger, small PP rest
effects, larger PK rest effects, a decaying offensive-zone-start benefit, and negative on-the-fly ST
changes. It also publishes player/context decompositions. It does not report:

- out-of-time or out-of-sample probability/map loss;
- a same-population baseline;
- calibration or spatial residual tests;
- year-over-year player/coach stability;
- support by 5v4/5v3/4v3 state;
- confidence/credible bands or empirical interval coverage; or
- an admission rule for the omitted mirror roles.

## 5. Open questions and source ambiguities

1. **Six versus seven scores.** Seven states are enumerated, but the results section says "six score
   terms." The enumerated design is retained and the later count is treated as a likely typo.
2. **Strength-state indicators.** All three advantaged configurations enter the population, but the page
   does not say whether they share one baseline or receive distinct terms.
3. **Inherited details.** The response's exact attempt universe, blocked-origin handling, estimation
   fabric, ridge penalties, sequential priors, aging, and centering are not restated. The Magnus 9 EV and
   xG dossiers are authoritative for those shared details; ST-specific deviations may be undocumented.
4. **Zone index convention.** ST links `0` through `34`, while the EV dossier describes seconds `1`
   through `35`. Both contain 35 terms, but whether this is merely zero-based display indexing is unstated.
5. **Coach attribution.** The head-coach column intentionally proxies for staff and system effects. It is
   an adjusted association, not a causal estimate of one person's instructions.
6. **Private/current implementation.** The article documents the 2025 public method. It does not expose
   private operational changes after publication.
7. **Game-simulation rest conflict.** The September 24 game-simulation description says its ST method
   neglects rest, while this September 8 source explicitly publishes rest terms. The pages may bind
   different component vintages, but neither provides a versioned dependency manifest proving that.
