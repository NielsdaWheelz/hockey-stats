# HockeyViz — The Magnus Prediction Model, version 8 (penalties)

- **Title (as published):** "The Magnus Prediction Model — Estimating Individual Impact on
  Penalty Rates, version 8"
- **Author:** Micah Blake McCurdy (@HockeyViz.com)
- **Article date:** March 27, 2026
- **URL used:** https://hockeyviz.com/txt/magnus8P
- **Accessed:** 2026-07-15
- **Index status:** the direct URL is live and is the latest accessible penalty-method page found, but
  HockeyViz's [`Current Models` index](https://www.hockeyviz.com/), checked 2026-07-16, still lists
  Magnus 7 Penalty Rates dated August 9, 2023. “Latest directly accessible” is therefore not treated
  as “site-declared current.”
- **Retrieval:** complete live HTML retrieved directly. The visible article runs through the
  score/venue/time, rest, zone, game-number, penalty-history, and rejected-pressure results. Several
  later distribution/result sections are retained in HTML comments from an older model and are excluded
  from current-version evidence.
- **Evidence boundary:** this page models rates of non-offsetting minor penalties drawn and taken. It
  does not price a penalty in goals, model penalty severity/type, or by itself define the penalty term in
  sG/Total.

## 1. Summary

Magnus 8 Penalties is a map-free linear isolation model for non-offsetting minor-penalty rates. Every
substitution-free passage of regulation play produces two rows, one for each team's penalty-drawing rate.
Skaters and head coaches receive paired draw/take terms; between-game rest receives paired terms as well.
The drawing side additionally receives manpower, score-by-venue-by-minute, shift-start-zone, game-number,
and penalty-history context. The penalty-history family distinguishes calls that would make the game's
absolute net penalty differential converge toward zero from calls that would make it diverge farther.

The model is fitted in two stages: one global generalized-ridge fit over 2007-08 through 2025-26, followed
by per-season fits shrunk toward the global coefficients. Structural families are centered on league
average; the score/venue/minute curves also receive within-period smoothness/constancy penalties and
weaker cross-period continuity. The article says the full 840-term score/venue/time construction predicts
out of sample substantially better than a two-term standings-pressure representation, but publishes no
numeric score, uncertainty, actor repeatability, or actor-penalty tuning details.

The page's March 2026 date and direct availability make it the newest accessible penalty write-up in
this review, but the site's current-model index still points to Magnus 7. This dossier records Magnus 8
as direct evidence without projecting it onto the indexed production model.

## 2. Decision inventory

| id | topic | source decision or fact | source rationale / limit |
|---|---|---|---|
| hockeyviz-magnus8p-D1 | estimand | Estimate adjusted rates at which a team draws and takes non-offsetting minor penalties. | The units are penalties per 1,000 minutes, centered at league average. |
| hockeyviz-magnus8p-D2 | observation unit | Encode every substitution-free passage of regulation play twice: once for the home team's draw rate and once for the road team's draw rate. | Opposing on-ice actors supply the matching penalty-taking side of each row. |
| hockeyviz-magnus8p-D3 | skater terms | Give every skater one draw-impact term and one take-impact term, treating every on-ice player as able in principle to affect a call. | Credit/blame is diffuse across the on-ice unit rather than assigned only to the penalized or fouled player. |
| hockeyviz-magnus8p-D4 | coach terms | Give every head coach one draw-impact term and one take-impact term. | The article does not separate staff roles or claim causal head-coach effects. |
| hockeyviz-magnus8p-D5 | rest terms | Include paired draw/take effects for tired (played last night), rested (played neither prior night), and normal (all other cases). | Each rest family is centered; observed effects are reported as small. |
| hockeyviz-magnus8p-D6 | structural perspective | Apply manpower, score/venue/minute, zone, game-number, and penalty-history context from the penalty-drawing team's perspective. | Skater, coach, and rest families instead occur as draw/take pairs. |
| hockeyviz-magnus8p-D7 | manpower | Mark 5v5, 5v4, 4v5, 4v4, 5v3, and 3v5 from the drawing team's perspective; coarsen 3v4 with 4v5 and 4v3 with 5v4; leave other extremely rare states unmarked. | The source's separate 6v4/4v6 sentence names labels absent from its own list; see Open Questions. |
| hockeyviz-magnus8p-D8 | score/venue/clock | Fit `7 score states x 2 venues x 60 regulation minutes = 840` context terms. | This is intended to proxy changing player/coach behavior and, in the interpretation, referee behavior across game situations. |
| hockeyviz-magnus8p-D9 | zone start | Include offensive-zone, neutral-zone, defensive-zone, and on-the-fly shift-start terms for the drawing side. | These terms are centered; the page reports on-the-fly starts with the highest draw rate and NZ faceoff starts with the lowest. |
| hockeyviz-magnus8p-D10 | season game number | Include game-number terms, 1 through 82 in modern seasons. | The family proxies within-season adjustment by skaters, coaches, and referees; calls are reported to be most frequent early and mostly settle by about game 30. |
| hockeyviz-magnus8p-D11 | penalty history | Encode the absolute game penalty differential that would follow a call and whether the call would make the differential converge or diverge. | Diverging calls become harder as imbalance grows; the author argues the long-history pattern is more plausibly referee-mediated than a short player reaction. |
| hockeyviz-magnus8p-D12 | two-stage fit | First fit one global model on 2007-08 through 2025-26, then fit the same model separately by season. | The per-season model is descriptive/smoothed; its prior uses a global fit containing the full historical window rather than only earlier seasons. |
| hockeyviz-magnus8p-D13 | ridge targets | In the global generalized-ridge fit, bias terms toward zero/league average; in each seasonal fit, bias terms toward their global estimates. | Exact actor penalty strengths and tuning procedure are not supplied in the visible article. |
| hockeyviz-magnus8p-D14 | reference and units | Express coefficients in penalties per 1,000 minutes relative to zero = league average. | The article reports the league baseline falling from just under 70 to roughly 45-50 per 1,000 minutes across the era. |
| hockeyviz-magnus8p-D15 | centered structural families | Enforce time-weighted zero sum for the six named manpower terms with a `10^12` penalty; center rest, zone, game-number, and penalty-history families as well. | Centering avoids an arbitrary one-hot reference and lets every term read relative to league average. |
| hockeyviz-magnus8p-D16 | smooth clock curves | Center the 840 score/venue/minute terms; apply `10^6` within-period smoothness and constancy penalties and `10^5` continuity penalties across period boundaries. | Exact matrix constructions for “smoothness” and “constancy” are not printed. |
| hockeyviz-magnus8p-D17 | special-teams call-rate result | Further calls are less frequent once manpower is already unequal; a team already advantaged is least likely to draw another call. | The author offers both hockey-structure and referee-threshold explanations. |
| hockeyviz-magnus8p-D18 | score/clock result | Penalty behavior varies strongly over score, venue, and minute; early tied play is conservative and call rates decline broadly during third periods. | The broad third-period decline across incentives is interpreted as suggestive of referee influence, not identified causality. |
| hockeyviz-magnus8p-D19 | rest/zone result | Tired players take slightly more and draw slightly fewer penalties; faceoff starts damp draw rates relative to on-the-fly starts. | Rest effects are described as very small; all terms remain adjusted associations. |
| hockeyviz-magnus8p-D20 | penalty-history interpretation | Converging versus diverging call patterns remain after the other context controls and are attributed tentatively to officials' aversion to perceived imbalance. | Referee identities are not model terms, so the mechanism is interpretive rather than isolated. |
| hockeyviz-magnus8p-D21 | pressure challenger | A two-term standings-points pressure representation was tested and rejected because the 840 context terms predicted out of sample substantially better. | No numeric loss, folds, margin, or multiplicity rule is reported. |
| hockeyviz-magnus8p-D22 | actor-output boundary | The live article defines skater and coach marginals but its old distribution/player-result appendix is commented out. | Current public actor artifacts cannot be inferred from commented older HTML; sibling card/sG sources provide separate product evidence. |
| hockeyviz-magnus8p-D23 | uncertainty and validation | No uncertainty, calibration, repeatability, residual diagnostic, complete OOS score, or actor null-recovery result is published. | The sole explicit challenger result is the qualitative pressure comparison. |
| hockeyviz-magnus8p-D24 | value boundary | The response is call rate, not goals, wins, or state/severity-specific expected value. | Any goal price and allocation into sG is a separate downstream model decision. |
| hockeyviz-magnus8p-D25 | causal ceiling | Player, coach, and structural terms are adjusted associations; unmodeled officials and tactical behavior may drive observed context patterns. | The article itself distinguishes plausible referee mechanisms from player/coach behavior without identifying them. |

## 3. Model structure

```text
substitution-free regulation passage
  -> home drawing-rate row
  -> away drawing-rate row

paired terms:
  skater draw / take
  head-coach draw / take
  rest draw / take

drawing-side context:
  manpower
  score x home/away x regulation minute
  shift-start zone
  season game number
  converging/diverging penalty-history state

global generalized ridge, 2007-08..2025-26
  -> seasonal generalized-ridge fits anchored to global coefficients
  -> penalties per 1,000 minutes relative to league average
```

This architecture separates rate isolation from value. It can estimate that a context or player changes
call frequency without determining the expected goal value of the ensuing special-teams state.

## 4. Evaluation and output evidence

The article's only explicit out-of-sample comparison is feature-family admission: the detailed
score/venue/minute representation beats a two-term standings-pressure model. The structural plots also
offer face-validity and historical-pattern checks. It does not disclose the scored rows, fold construction,
metric, margin, or uncertainty for that comparison.

The visible page publishes structural histories and current-season context figures for the baseline,
manpower, score/venue/time, rest, zone, game number, and penalty history. Older raw/player/teammate/
opponent/coach/residual panels remain in HTML comments and are not counted as Magnus 8 public outputs.

## 5. Open questions and source ambiguities

1. **6v4/4v6 labels.** The article says 6v4 is encoded as 6v5 and 4v6 as 5v6, but neither 6v5 nor 5v6
   appears in the six-term list. This may be a typo for 5v4/4v5 or evidence of omitted labels; the dossier
   does not choose between them.
2. **Penalty-event universe.** “Non-offsetting minor” is the only event definition. Bench minors,
   goaltender penalties, delayed calls, double minors, penalty shots, coincidental details, and data
   corrections are not discussed.
3. **Actor penalty strengths.** The live text promises term-specific fitting details but supplies no
   numeric player/coach ridge values or actor continuity/tuning evidence.
4. **Global-to-season prior.** The seasonal target uses the all-years global fit. This is coherent for a
   retrospective smoothed description but cannot be treated as a rolling-origin present-talent forecast
   without a different fit protocol.
5. **Referee mechanism.** Official identity and officiating crew are absent. The source's referee
   explanations are plausible interpretations of residual structure, not causal estimates.
6. **Severity and downstream price.** No penalty duration, strength transition value, leverage price, or
   PP/PK execution interaction is modeled on this page.
7. **Current actor publication.** Commented older distributions cannot establish that Magnus 8 player or
   coach penalty marginals are currently served, even though the live model definition contains them.
8. **Direct-page versus index currentness.** The Magnus 8 URL is live and newer than the indexed
   Magnus 7 page, but it is absent from HockeyViz's `Current Models` list. Public evidence does not
   resolve whether this is an index omission, a preview, or a method that is not production-declared.
