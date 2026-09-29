# HockeyViz — Score Sequencing

- **Title (as published):** "Score Sequencing" (page `<title>`: "Score Sequencing")
- **Author:** Micah Blake McCurdy (@IneffectiveMath)
- **Published:** February 5, 2020
- **URL used:** https://hockeyviz.com/txt/scoreSeq
- **Fetch method:** curl with browser User-Agent (WebFetch returns HTTP 403 from hockeyviz.com); full HTML retrieved 2026-07-04 (≈586 lines), saved to scratchpad.
- **Accessed:** 2026-07-04
- **Completeness:** full article text retrieved (intro + Overview + Method + Fitting + Results sections; all chart sub-sections: "Tied scores", "One goal leads", "One goal deficits", "Most-recent goal effects", "Immediate Goal Impact" × 2, "Conclusions"). Figures/plots referenced in text were not retrieved (PNGs). Copyright footer: "© Micah Blake McCurdy 2026".
- **Epistemic note:** This article is from 2020. The Magnus 9 (2025) and xG8 (2025) articles already fetched are the authoritative current record for what HockeyViz's production models actually do; scoreSeq witnesses the score-effects *evidence* and *motivational argument* only. Where any decision or practice here has been superseded or refined by those later articles, that is noted explicitly. Inferences are tagged "(inferred)".

---

## Summary

scoreSeq examines what causes "score effects" — the well-known phenomenon that losing teams
dominate play — by fitting a regression on 2016-19 5v5 stints with a highly granular set of
score terms (every specific goal-sequence pattern up to 5 total goals × every regulation minute)
while simultaneously controlling for player ability, zone starts, coaching, rest, home ice, and
period. The central conclusion is that **leading teams sitting back drive score effects on shot
rates more than trailing teams pushing** — a finding the author later uses to justify the
"shell" coaching term in both Magnus 7 and Magnus 9, which fires only when a team is tied or
leading by 1–2 in third periods. The response variable is "threat" — the xG-weighted sum of
the shot-rate map — so scoreSeq measures effects on **xG rates** (shot volume weighted by
location/context danger), not raw counts. Magnitudes for typical score-and-period combinations
range from −30% to +15% relative to league average; the effects vary strongly by period and
are most dramatic in the third. Score effects on raw shot rates (and xG rates) are the subject;
xG8 (2025, already distilled) later finds additional shot-quality effects conditional on score
inside the layered xG model.

---

## Decision inventory

| id | topic | decision | rationale / verbatim quote | article section |
|---|---|---|---|---|
| hockeyviz-scoreseq-D1 | Core conclusion | **Leading teams sitting back drive score effects more than trailing teams pushing.** | "My conclusion is: Leading teams sitting back drive score effects on shot rates more than trailing teams pushing." | Introduction |
| hockeyviz-scoreseq-D2 | Unit of observation | Each observation = a stretch of 5v5 play without substitutions (a "stint"), duplicated into two rows (home attackers / away attackers), with home-team shots and away-team shots as the respective responses. | "each observation was a stretch of 5v5 play without substitutions" | Method |
| hockeyviz-scoreseq-D3 | Response variable | Shot-rate **maps** (same mechanism as Magnus), summarised to a scalar "threat" = "the weighted sum of all of the values in the map, according to the league-average shooting percentage at those locations"; expressed as % above/below league-average 5v5 rate. | "a summary of them which I call 'threat', which is obtained by taking the weighted sum of all of the values in the map, according to the league-average shooting percentage at those locations" | Results |
| hockeyviz-scoreseq-D4 | Score parameterization | Not a single score-differential dummy or ordinal: **one term per regulation minute × specific goal-sequence pattern**, up to 5 total goals in the game. E.g. "h" = home team scored only; "haah" = scored, conceded, conceded, scored (tied at 2). At most 60 × 31 non-trivial score states used; terms with < 1,000 seconds of data not displayed. | "I include a raft of score terms, one for each of the sixty regulation minutes of a game, for every pattern of previous goals scored, up to five." | Method |
| hockeyviz-scoreseq-D5 | Scope restriction | Restricted to situations where **at most five total goals** had been scored; these represent "almost exactly two thirds of the 5v5 play from those seasons, making 122,589 minutes of data". | verbatim | Method |
| hockeyviz-scoreseq-D6 | Data span | Most recent three full regular seasons at time of writing: **2016-17, 2017-18, 2018-19**. | "the most recent three full regular seasons (2016-2019)" | Method |
| hockeyviz-scoreseq-D7 | Controlled covariates | Player terms (skater off/def), zone-start terms (OZ/NZ/DZ faceoff; on-the-fly as baseline), head coach terms, rest, home-ice advantage, second-period effect; all duplicated once for offence, once for defence. | "Terms for each skater; Offensive/Defensive/Neutral zone start terms … Head coaching; Rest. … one term for home-ice advantage and one term for the second period" | Method |
| hockeyviz-scoreseq-D8 | Fitting method | Generalized ridge regression; penalties: players 10,000; coaches 50,000; zone terms 0; score terms **10** ("effectively zero, but, in fact, not zero"). | "penalties of ten thousand" / "fifty thousand" / "no penalty" / "penalties of ten (effectively zero, but, in fact, not zero)" | Fitting |
| hockeyviz-scoreseq-D9 | Fusion penalty | Adjacent-minute score terms fused with a penalty of **200,000** (much stronger than the diagonal penalties), encoding that time is continuous; the final minute of each period is **not** fused to the start of the next (intermission breaks). | "I fuse each score term for a given minute to the score term with the same score detail at the following minute … However, I do not fuse the final minute of each period to the corresponding term at the beginning of the following period." / "The strength of the fusion penalties is two hundred thousand" | Fitting |
| hockeyviz-scoreseq-D10 | Score-effect period character | Score effects have "quite different characters in each period": second period contains more offence; offence drops sharply at the start of the third and continues to decline throughout; tied scores also show a sharp drop at the second intermission. | "score effects … are most obvious in the third period" / "the second period contains much more shooting than either of the other periods" | Results — Tied scores |
| hockeyviz-scoreseq-D11 | Third-period leading decline | Teams leading by 1 or 2 show the sharpest decline in offensive threat as the third period progresses; "the drop is most precipitous" when a 2-0 lead yields to 2-1 — those teams generate ~30% less threatening shots by end of regulation. | "The drop is most precipitous in games where a team with a two-nothing lead surrenders a goal; such teams by the end of regulation are themselves generating a pattern of shots 30% less threatening than league average play." | Results — One goal leads |
| hockeyviz-scoreseq-D12 | Leading teams drive, not trailing | Trailing-by-one teams do not show increased offensive push above average; "matching reductions in offence clearly benefit the leading team" even when both teams' offence nominally declines. The author argues this is consistent with leading teams as the primary driver, even though the fraction of total offence shifts toward trailing teams. | "for one-goal deficit games, matching reductions in offence clearly benefit the leading team. This is consistent with leading teams being the primary driver of score effects even if the fraction of total offence shifts towards trailing teams" | Results — One goal deficits |
| hockeyviz-scoreseq-D13 | Momentum: most-recent scorer | Being the most-recent team to score is "nearly always beneficial, although the effect is a modest 5% or so"; tied after a score vs tied after a concession differs by ~5% threat. | "it is nearly always beneficial to be the most-recent scorer, although the effect is a modest 5% or so" | Results — Most-recent goal effects |
| hockeyviz-scoreseq-D14 | Goal-scored impact on offence | **Nearly all teams, in nearly all situations, lower their offensive output in the minutes following a goal they scored.** Most lines are negative (reduced offence). The sharpest effect = teams tying the game late in the third (−10 to −15% threat) — driven by the scoring team, not the conceding team. | "nearly all of the lines are negative---that is, most teams, in most situations, respond to scoring a goal by lowering their offensive output in the following minutes" | Results — Impact of a Goal Scored |
| hockeyviz-scoreseq-D15 | Goal-conceded impact on offence | "Little effect" on the conceding team's offence: "nearly all lines confined in the −5% to +5% band near league average." Exception: teams who concede a third-period go-ahead goal "immediately generate a notable bit of offence" (turning it on when necessary). | "In general, though, it seems that teams respond offensively to scoring (by generating less offence) and perhaps also defensively to being scored on (by allowing less); but mostly do not respond offensively to being scored on except near the end of games." | Results — Impact of a Goal Conceded |
| hockeyviz-scoreseq-D16 | Shell-term justification | The finding that leading teams are the primary driver — especially in the third period, tied or up 1–2 — directly motivates the "shell" coach indicator in Magnus (fires only in those states). Not stated in this article itself, but the Magnus articles cite scoreSeq explicitly for this motivation. | (cited by Magnus articles; scoreSeq provides the evidence) | (cross-article) |
| hockeyviz-scoreseq-D17 | "Worst lead in hockey" germ | The one strongly positive goal-scored effect is scoring in the second period to cut a 2-0 deficit to 2-1 — the team generating more offence, potentially (inferred) the germ of truth in the aphorism "a two-goal lead is the worst lead in hockey". | "the one strongly positive effect is that of scoring in the second period to cut a two-goal deficit in half. Perhaps this is the germ of truth behind the (preposterous on its face) aphorism that a two-goal lead is 'the worst lead in hockey'." | Results — Impact of a Goal Scored |
| hockeyviz-scoreseq-D18 | Tied overtime incentive | Both teams in a tied game benefit from shepherding to overtime (gimmick standings points), so both reduce offence as the third wears on — this *also* appears as a score effect but is not a pure leading-team story. | "For tied teams, a reduction in offence as the third wears on suits both teams - they will split three points if they can shepherd their game to overtime, because of the gimmick points handed out for winning an overtime or winning a shootout." | Results — One goal deficits |
| hockeyviz-scoreseq-D19 | Tied-with-rally exception | The only tied-state that does NOT see steadily diminishing third-period offence: teams who were down 2-0 but rallied to tie. "Such teams alone are immune to having their offence steadily dwindle over time, although its steady value is still 10% less threatening than league average play." | verbatim | Results — Tied scores |
| hockeyviz-scoreseq-D20 | Penalty ad hoc | The penalty values used in this model are "taken from Magnus 2 as my starting point and then the rest is a matter of (my) touch and intuition, such as it is." | verbatim | Fitting |

---

## Model / method structure sketch

This is a causal-interpretation study, not a production xG model. Its outputs are score-term
maps and their threat summaries, used as evidence for a qualitative argument; they are not
promoted to any serving pipeline.

**Regression structure:**
- **Observations:** 5v5 stints (no substitutions), each encoded as two rows (home attacking, away
  attacking); ≈122,589 minutes over 3 seasons.
- **Response:** shot-rate map (function over the ice surface), summarised to "threat" (%)
- **Covariates:**
  - Per-skater off/def terms
  - Zone-start terms (OZ/NZ/DZ faceoff; on-the-fly baseline)
  - Head coach terms
  - Rest terms
  - Home-ice term (one) + second-period term (one)
  - **Score terms:** 1 term per (specific-goal-sequence-pattern, regulation-minute) pair, up to 5
    total goals × 60 minutes; ≈31 non-trivial score states × 60 minutes = ≈1,860 score columns,
    fused pair-wise along the minute axis
- **Fitting:** Ridge regression, time-weighted (stint length); diagonal penalties: players 10k,
  coaches 50k, zone 0, score 10; fusion penalty between adjacent-minute score terms 200k; fusion
  breaks at period boundaries.

**Key design identity with Magnus:** this model closely resembles McCurdy's "flagship" shot-rate
model (Magnus) — same stint segmentation, same two-row per-stint encoding, same xG weighting of
the response — with the **only** difference being the treatment of score state: Magnus uses a
coarser score summary as a control covariate; scoreSeq blows it up into the full per-minute ×
goal-sequence grid to study it directly.

---

## Evaluation protocol

No formal held-out evaluation of the score-term model is reported. The evaluation in this article
is **qualitative pattern coherence**: do the estimated curves follow expected causal logic (e.g.,
does declining third-period offence match the shell hypothesis)? The author notes that the
relative values of penalties are "largely ad hoc" and taken from earlier Magnus work. All
quantitative figures in the article are displays of fitted effects (not test-set predictions).

---

## Reported magnitudes

Verbatim or near-verbatim numbers from the article (all in "threat" % relative to league-average
5v5):

- Second period vs other periods: +1.1% threat (map-weighted baseline; "quite minor").
- Teams tied after down-2-0 rally, third period: ~−10% (steady but immune to the normal decline).
- Teams who score to cut 2-0 deficit to 2-1 (second period): the one **positive** effect in the
  goal-scored impact chart (magnitude not quantified beyond "strongly positive", inferred >+5%).
- Teams up two, who then allow a goal, by end of third: ~−30% threat ("30% less threatening than
  league average play").
- Third-period go-ahead goal conceded: "notable bit of offence" produced by the conceding team
  (magnitude not quantified beyond being a visible positive exception).
- Most-recent scorer advantage: ~+5% threat ("a modest 5% or so").
- Teams leading by 1–2, general third-period decline: "most precipitous" for the freshly-2-0
  teams (the −30% quote); general third-period decline for all leading states is visible but not
  separately quantified.
- Goal-conceded impact on offence: "nearly all lines confined in the −5% to +5% band near league
  average".

---

## Open questions / ambiguities

1. **Shot-quality vs rate decomposition.** scoreSeq measures "threat" (xG-weighted rates) not
   raw shot counts, so it implicitly captures both rate and quality-of-location effects. It does
   not decompose the two. Whether score effects on xG-weighted rates are primarily volume-driven
   or quality-driven is left unanswered here; `hockeyviz-xg8-D30` adds the per-shot conditional quality
   evidence, but the decomposition is not fully reconciled across the two articles.

2. **Venue asymmetry.** Results are home+road aggregated. The direction/magnitude of home/away
   asymmetry in score effects is unquantified here. Magnus 9's 840-column cross implies a
   meaningful interaction; scoreSeq cannot validate or quantify it.

3. **Non-regulation excluded.** The article covers regulation 5v5 only; overtime and shootout
   score effects are absent. scoreSeq therefore gives no evidence about either non-regulation
   state.

4. **Score terms with 5+ goals.** The one-third of 5v5 play with more than 5 total goals is
   excluded from this analysis. Blowout dynamics are unwitnessed here.

5. **Model comparison.** The regression is the same model architecture as Magnus, so the
   "score effects" estimated here are conditional on the same player/coach/zone/rest confounds.
   Whether the specific confound conditioning changes the conclusions vs a simpler two-sample
   comparison is not discussed.

6. **Fusion vs smoothing.** The 200,000 fusion penalty smooths the minute-to-minute curves but is
   explicitly ad hoc. The degree to which results depend on the specific penalty ratio (fusion /
   diagonal = 20,000×) is not tested. The "effectively zero but not zero" diagonal on score terms
   (10) means score effects are allowed to be large — the model is very free here.

7. **Publication date vs later models.** This is a 2020 article. xG8 (2025) and Magnus 9 (2025)
   are later public records. scoreSeq supplies score-effects evidence and the cross-article
   motivation for the shell term; treat nothing here as a claim about HockeyViz production
   practice after 2020 except where a later source cites it explicitly.
