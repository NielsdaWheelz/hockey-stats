# HockeyViz — How to read Shot Maps

- **Title (as published):** "How to read Shot Maps" (page `<title>`: "Shot Maps")
- **Author:** Micah Blake McCurdy (site footer: "© Micah Blake McCurdy 2026")
- **URL used:** https://hockeyviz.com/howto/shotMap — fetched directly (WebFetch returned HTTP 403; retrieved via curl with a browser user-agent). A Wayback Machine copy (`web.archive.org/web/2026/https://hockeyviz.com/howto/shotMap`) was fetched as a cross-check and contains the identical article text.
- **Accessed:** 2026-07-03
- **Completeness:** the full article was retrieved (it is short: one intro section + four team-chart subsections; heading inventory verified against the raw HTML: h1 "How to read Shot Maps", h2 "Team Charts", h3 "5v5 Offence" / "5v5 Defence" / "5v4 Offence" / "4v5 Defence"). No sections were unretrievable.

## Summary

This is a reader's guide to HockeyViz's team shot maps, written by the site author. The unit of analysis is the unblocked shot (missed, saved, or scored); blocked shots are excluded only because public location data for them does not exist. The maps do not show absolute shot rates — because every team shoots mostly from the net-front and the points, absolute maps are uninteresting — instead each location is coloured by how much more or less often the team shoots from that spot than an NHL-average team in the same season. Offence maps put the net at the top; defence maps put it at the bottom. 5v5 maps use a red/white/blue diverging scheme; power-play and penalty-kill maps use a deliberately different orange/purple scheme with a doubled scale (PP shot-rate variance is larger). Because location alone understates or overstates shot danger, each shot is weighted by the ratio of its full expected-goal value (from the site's xG model, deferred to /txt/fabricxg) to a "simplified" location-plus-strength-only model called xG0, so that low-volume/high-danger teams compare fairly against high-volume/low-danger teams. Each map is decorated with the minutes it summarizes (a sample-size honesty device) and a neutral-zone headline: total xG rate in goals per hour plus percent above/below that season's league-average xG rate. xG values assume league-average shooting and goaltending talent, which the author uses to explain why Washington's Ovechkin-driven PP outscored its computed xG. The author also cautions that the spread of team performance in the NHL is small — even one of the better 5v5 offences generates only about one excess shot per hour from the red slot region.

## Decision inventory

| id | topic | decision | rationale / verbatim quote | article section |
|---|---|---|---|---|
| hockeyviz-shotmap-D1 | shot definition (target data) | "Shot" = any unblocked shot: missed, saved, or scored (i.e., Fenwick events). | "I use 'shot' to mean any unblocked shot; that is, a shot which is missed, saved, or scored." | How to read Shot Maps (intro) |
| hockeyviz-shotmap-D2 | blocked shots | Blocked shots excluded solely for data availability, not principle; author would include them if location data existed. | "If I had access to shot location data for blocked shots I would almost certainly include them also, but I do not." | intro |
| hockeyviz-shotmap-D3 | display encoding: relative not absolute | Maps encode the difference between the team's per-location shot rate and the league-average per-location shot rate, never the absolute rate. | "Since every team shoots primarily from close to the net and the points, charts that show absolute rates of shots are not very interesting." | 5v5 Offence |
| hockeyviz-shotmap-D4 | baseline: same-season league average | The comparison baseline is "an NHL average team in that same season" — i.e., season-matched, so league-wide drift doesn't contaminate the map. | "how much more often (or less often) a team shoots from a given spot than an NHL average team in that same season" | 5v5 Offence |
| hockeyviz-shotmap-D5 | baseline: strength-state-matched | Each strength state is compared against its own league average (PP maps vs the 5v4 average, not an all-strength average). | "The notion of 'average' here of course is 5v4 average" | 5v4 Offence |
| hockeyviz-shotmap-D6 | colour scale, 5v5 | 5v5 maps: diverging red (above league average) / white (at average) / blue (below average). | Regions above league-average shot rate "are shown in red"; below "in blue"; at average "in white". | 5v5 Offence |
| hockeyviz-shotmap-D7 | colour scale, special teams | PP/PK maps use a distinct orange (above average) / purple (below average) scheme so they cannot be misread as 5v5 charts. | "they are easy to distinguish from the 5v5 charts because of their different colour schemes: here orange means 'more than average', while purple means 'less than average'" | 5v4 Offence, 4v5 Defence |
| hockeyviz-shotmap-D8 | special-teams scale doubling | The colour scale on PP/PK maps is doubled relative to 5v5 maps. | "the scale is also doubled, since the variance in power-play shot rates is larger than in 5v5 shot rates" | 5v4 Offence |
| hockeyviz-shotmap-D9 | orientation encodes off/def | Net at TOP of chart = offence (shots taken by the team); net at BOTTOM = defence (shots taken by opponents). | "Charts like this, with the net at the top, show offence"; "with the net at the bottom, show defence" | 5v5 Offence / 5v5 Defence |
| hockeyviz-shotmap-D10 | unit of measurement | The map quantity is a shot RATE (worked example expresses excess as shots per hour of 5v5 play), not a count. | "For maps like this, the natural unit of measurement is the rate of shots." | 5v5 Offence |
| hockeyviz-shotmap-D11 | magnitude-reading aid | Every map carries a reference circle for area (bottom right) so a reader can convert a coloured region's area × rate-difference into excess shots. | "the red area in the slot is perhaps around 200 square feet (notice the reference circle for area in the bottom right)" | 5v5 Offence |
| hockeyviz-shotmap-D12 | sample-size handling | Every shot map is decorated with the number of minutes it summarizes, because some chart variants rest on few minutes. | "Because some of the later charts can be based on relatively few minutes, I decorate every shot map with the number of minutes shown" | 5v5 Offence |
| hockeyviz-shotmap-D13 | danger weighting via xG/xG0 ratio | Each shot in the map is weighted by ratio = xG (full model) / xG0 (simplified model), folding non-location danger into the spatial display. | "I use these ratios to weight the shots in the map, so that teams who consistently take fewer but more dangerous shots can be properly compared with teams that take more but less dangerous shots." | 5v5 Offence |
| hockeyviz-shotmap-D14 | xG0 definition | xG0 is a second, deliberately impoverished expected-goals model containing ONLY skater strength state and shot location. | "another expected goals model, without these non-location factors; including only the skater strength state and the shot location. I call this 'simplified' expected goals model 'xG0'." | 5v5 Offence |
| hockeyviz-shotmap-D15 | typical ratio range | The xG/xG0 weight for a relatively dangerous shot (e.g., a rebound) runs "perhaps as high as 1.5 or so"; a less dangerous shot from the same spot "perhaps as low as 0.7 or thereabouts". | verbatim values given in text | 5v5 Offence |
| hockeyviz-shotmap-D16 | display vs estimation boundary | Non-location danger factors (shot type, rebound, rush, "and so on") are judged not directly displayable on a 2-D map; the ratio weighting is the chosen workaround rather than extra map layers. | "these non-location factors are not so easy to display in a simple two-dimensional map" | 5v5 Offence |
| hockeyviz-shotmap-D17 | talent-free xG | Expected-goal values assume league-average shooting and goaltending talent; shooter/goalie skill is deliberately outside the map's xG numbers. | "Crucially, the expected goal values are computed assuming league average shooting and goaltending talent." | 5v4 Offence |
| hockeyviz-shotmap-D18 | headline number | Total expected-goal rate is printed in the neutral zone of the map, together with the relative (percent) change from that season's league-average xG rate. Example: S.J 2.55 xG/hour, +3% vs league. | "The total expected goal rate is shown in the neutral zone, together with the relative change from league average xG rate for the league that season." | 5v5 Offence |
| hockeyviz-shotmap-D19 | strength-state chart set | Team charts are produced per strength state: 5v5 offence, 5v5 defence, 5v4 (power-play) offence, 4v5 (penalty-kill, shots allowed) defence. | section structure of the article | Team Charts (all subsections) |
| hockeyviz-shotmap-D20 | full-xG model deferral | The full expected-goal model (the numerator of the weighting ratio) is defined elsewhere: /txt/fabricxg ("Magnus 3: xG, Shooting, and Goalie-ing"). | "I have created such an expected goal model, described here [/txt/fabricxg]" | 5v5 Offence |
| hockeyviz-shotmap-D21 | caveat: small performance spread | Author warns excess-shot magnitudes are small even for good teams (~1 excess shot/hour from a ~200 sq ft slot region for one of the season's better offences). | "one must also keep in mind that the spread of performance results in the NHL is quite small." | 5v5 Offence |
| hockeyviz-shotmap-D22 | caveat: observed vs xG divergence | When a team's shots are concentrated in one elite shooter, observed goals can legitimately exceed the (talent-free) xG; used explicitly to explain WSH's 2017-18 PP (xG 6.48, "a little worse than league average"). | "very nearly all of the shots in the left-circle blob are taken by Ovechkin himself... which explains why the Washington observed goal rates considerably exceed the computed xG" | 5v4 Offence |

## Model structure sketch

The article describes a display pipeline, not a fitted map-model, with two estimation objects feeding it:

1. **Event layer** — unblocked shots (missed/saved/scored) with locations, split by strength state (5v5, 5v4, 4v5) and by team-for vs team-against.
2. **Danger layer (two xG models):**
   - **xG (full)** — the site's expected-goals model with non-location factors (shot type, rebound, rush, "and so on"); defined in the companion article /txt/fabricxg; computed assuming league-average shooter and goalie talent.
   - **xG0 (simplified)** — same target but covariates restricted to {skater strength state, shot location}.
   - Per-shot weight = xG / xG0 (≈0.7–1.5 in practice). This conditions the spatial display on non-spatial danger without adding display dimensions.
3. **Comparison layer** — the team's (weighted) per-location shot rate minus the same-season, same-strength league-average per-location rate. Sign/magnitude of this difference drives the colour.
4. **Display layer** — diverging colour surface (red/white/blue at 5v5; orange/purple at doubled scale for PP/PK), net-at-top/bottom orientation for offence/defence, minutes decoration, area reference circle, and a neutral-zone headline (total xG rate in goals/hour + % vs league-average xG rate).

Not described anywhere in the article: how the per-location rate surfaces are smoothed/estimated (no kernel, bandwidth, grid, or smoothing method is stated) — see Open questions.

## Full feature/covariate list as stated

For the **maps** themselves (per shot):
- shot location (x, y on the rink; coordinate conventions not stated)
- skater strength state (5v5, 5v4, 4v5 are the charted states)
- team identity and for/against orientation
- season (baseline is season-matched)
- per-shot weight xG/xG0

For **xG0** (exhaustively stated): skater strength state + shot location, nothing else.

For **xG (full)**: not enumerated in this article beyond examples — "shot type, if it was or was not a rebound or on the rush, and so on"; the full list is deferred to /txt/fabricxg.

## Evaluation protocol and reported results

**No evaluation protocol is given.** The article is a reading guide: it contains no train/test split, calibration measure, likelihood, or benchmark for either the maps or the xG/xG0 models (those presumably live in /txt/fabricxg, not fetched in depth here). Numbers reported are worked examples, not evaluations:
- San Jose 2017-18 5v5 offence: 2.55 expected goals per hour, +3% vs league average; slot excess ≈ 1 shot per hour of 5v5 over a ~200 sq ft region; point blob attributed to right-side defenders, "especially Brent Burns".
- Minnesota 2017-18 5v5 defence: large blue (below-average) regions near the net = "excellent 5v5 team defence".
- Washington 2017-18 5v4 offence: xG 6.48 (per hour, inferred), "a little worse than league average", with observed goals exceeding it due to Ovechkin's shooting talent (talent excluded from xG by design).
- New Jersey 2017-18 4v5: fewer shots allowed than league-average PK from directly in front of the net; small increase in the high slot.

## Outputs / artifacts

- Team shot-location maps (PNG, e.g. `/static/img/team/shotLoc/1718/teamShotLoc-1718-S.J-off.png`) in four flavours: 5v5 offence, 5v5 defence, 5v4 offence ("-off-PP"), 4v5 defence ("-def-PK").
- On each map: the relative-rate colour surface (danger-weighted), minutes-shown decoration, area reference circle (bottom right), neutral-zone total xG rate (goals/hour) + percent vs season league-average xG rate.
- Implied upstream artifacts: the full xG model and the xG0 model (per-shot scores), and same-season league-average shot-rate surfaces per strength state.
- The intro says the author makes "a great many charts... in a wide variety of situations", but only the four team charts above are documented on this page.

## Linked / companion articles referenced

- https://hockeyviz.com/txt/fabricxg — the full expected-goals model. Light fetch (headings only) confirms it is "Magnus 3: xG, Shooting, and Goalie-ing" (March 26, 2020, Micah Blake McCurdy), with sections on estimating shot difficulty, odds vs probability, geometric terms, static/dynamic penalties in fitting, and strength/score/rush/rebound and player results. Not distilled here — separate source.

(No other article links appear in the body; navigation links to site tools like /sG, /xG, /ppShotLoc are chrome, not references.)

## Open questions / ambiguities in the source

1. **Smoothing is entirely unspecified.** The article never says how point events become a continuous surface — no kernel family, bandwidth, grid resolution, or regularization is mentioned. This is the largest omission relative to what one needs to reproduce the maps.
2. **Colour-scale calibration is unspecified.** "Doubled" scale for PP/PK is stated, but the base scale (what rate-difference saturates the red/blue endpoints, whether the mapping is linear) is not.
3. **Rate normalization details.** Per-hour rates and a minutes decoration are shown, but whether the surface itself is per-60-normalized (near-certain, inferred) and how the league-average surface is estimated/normalized is not stated.
4. **No mention of venue/scorekeeper location-bias correction,** home/away splits, or score-state adjustment for these maps. Absence of mention is not evidence of absence in the pipeline.
5. **Whether the neutral-zone xG headline uses the full xG or the weighted surface** is ambiguous; the text says "total expected goal rate", which reads as the full-xG sum (inferred).
6. **Coordinate handling** (left/right rink-side pooling, symmetrization across periods) is not discussed, yet the WSH example relies on preserved left/right asymmetry — so shooting-direction normalization without left/right mirroring is implied (inferred).
7. **Player-level shot maps** are not covered here despite the "Team Charts" heading implying a broader family; where player maps are documented is not linked from this page.
8. **xG0's exact form** (how location enters, binning vs continuous) is not given.
