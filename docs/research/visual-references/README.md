# user-selected visual references

eight images supplied by the user and visually inspected on 2026-10-22. moved from `samples/` and renamed without changing image bytes; 1,482,013 bytes total. original filenames and sha256 values are retained below. filenames identify visible subjects and chart families, not verified source urls or model versions. authorship/branding is visible in the images; original download urls are unknown.

these are design/reference evidence, not our computed results, numerical fixtures or application assets. visible numbers, dates, private-model labels and logos do not become our data or branding. [the visual inventory](../../product-inventory.md#visual-coverage-inventory--2026-10-22) owns scope; [the application contract](../../specs/experimental-application.md#sample-driven-presentation-requirements) owns implementation.

after this review the user clarified v1: complete hockeyviz-style player cards/components and both jfresh skater-card formats, using whatever microstat evidence is available. s01/s02/s07 directly define card compositions; s04/s08 inform their map presentation. standalone s05/s06 scatters and s03's richer reference-band history may follow. embedded card histories remain v1. [release boundary](../../product-inventory.md#v1-card-completion-boundary--2026-10-22)

## inspected examples

| id / image | dimensions | visible target and required distinction |
|---|---|---|
| s01 [pettersson comparative card](jfresh-pettersson-player-card.jpg) | 4096 × 2714 | large headline percentile, aligned component/context tiles, identity/usage, and two embedded history plots. retain this hierarchy and integrated export; our seasonal value is not the image's projected war |
| s02 [glendening microstat card](jfresh-glendening-microstat-card.jpg) | 4096 × 4096 | four grouped sections with twenty labeled percentile cells, readable magnitudes and explicit time/population metadata needed in our version. the image labels projections and tracking provenance; ordinary event data does not establish those tracked actions |
| s03 [bergeron value history](hockeyviz-bergeron-value-history.webp) | 892 × 565 | player trajectory over colored league/role bands, age markers and team strip. the bands contextualize the player; their exact calculation is not provided by the image. do not present them as player uncertainty |
| s04 [henrique on-ice offense map](hockeyviz-henrique-on-ice-offense-map.webp) | 565 × 691 | rink-clipped filled contours, zero-centered density legend, distance axes and an inset with exposure, xg and rate/reference comparison. this is a team's result with the player, not his isolated effect |
| s05 [ottawa player-impact scatter](hockeyviz-ottawa-player-impact-scatter.webp) | 1031 × 1097 | many named players, offensive/defensive axes, zero crosshair and interpreted quadrants. defensive axis is inverted; preserve numeric sign. team is a player-selection filter, not a new team-outcome model |
| s06 [montreal finishing/setting scatter](hockeyviz-montreal-finishing-setting-scatter.webp) | 728 × 745 | named players on two execution axes, a central reference region and declared near-average omission. the image does not define its hide threshold or label-color meaning; our choices must be explicit |
| s07 [robertson isolated-impact card](hockeyviz-robertson-isolated-impact-card.webp) | 519 × 912 | four rink maps, shootiness, paired skill distributions, component-value diagram and total in one sheet. rate differences, relative percentages and common-workload contributions are different units; visual integration cannot merge their meanings |
| s08 [cirelli on-ice defense map](hockeyviz-cirelli-on-ice-defense-map.webp) | 565 × 691 | mirrored defensive rink orientation, contours and the same evidence-inset pattern as s04. blue means fewer attempts, not a changed numerical sign or proof of individual suppression |

s04/s08 visibly label density per 100 square feet and weighted shots per hour. our maps must name their actual mass/density population; copying that label onto raw counts or a different expected-value construction would be incorrect. s05/s06 show percentage/relative axes; our existing per60 and per100 effects need explicit reference conversions before using comparable labels.

## design conclusions

- retain two coherent compositions: a compact comparative tile/history card and a dense analytical map/distribution/component sheet. share quantities/primitives without flattening both into interchangeable dashboard tiles.
- the headline, units, reference, support and selected season must survive export. embed the requested small histories in the comparative card; a separate history page alone does not meet s01.
- retain a later many-player scatter explorer with fixed offense/defense and finishing/setting presets, team/peer filters, labels, inspectable values and profile navigation. label collision handling must not move data points. never silently hide average or low-minute players.
- retain later historical reference bands with explicit annual cohorts/boundaries, age markers and team affiliation. three published seasons remain the initial range. role bands and population quantiles require defined constructions; neither is an uncertainty band.
- implement the contour presentation from authoritative cell mass/area with declared interpolation, boundary behavior, shared scales and scalar closure. keep observed on-ice, modeled isolated and personal-shot maps visibly distinct.
- retain the requested microstat card in the visual target. audit each field's source and definition; display observed, modeled/inferred and genuinely unavailable quantities distinctly. do not replace missing tracking with existing setting/territory coefficients.

tradeoffs: denser cards need deliberate narrow-screen reflow and export sizing; contours smooth visual detail; a full roster scatter needs label/selection behavior; annual bands need reference data; microstats add real source work. color alone must not carry meaning, line-style differences remain useful, and all charts need inspectable numerical values. no new chart framework, model admission requirement, team dashboard, forecasting target or historical acquisition is implied.

## microstat field coverage

the sample supplies the desired field list; it does not establish available inputs. [the official guide](https://hockeystats.com/about/microstat-player-cards) distinguishes manually tracked actions from nhl edge skating measures and describes sampled, season-dependent coverage. it also defines its shots field as unblocked attempts. this is not our existing shots-on-goal field. the following are preparation obligations, not implementation claims; [the input issue](../../issues/microstat-inputs.md) tracks them.

| sample fields | required source/meaning decision |
|---|---|
| goals, shots, primary assists, hits | source event/credit definitions, matched 5v5 exposure, completeness and field-specific cohorts; verify available derivations |
| xgoals | our reference-execution expectation may supply a declared independent quantity; the reference's tracking-enriched construction is not reproduced by renaming it |
| xassists, primary shot assists, in-zone shot assists, rush shot assists, high-danger passes, shots off high-danger passes | actual pass/assister evidence and location/sequence meaning; any inferred counterpart needs its own label, estimand and checked construction |
| in-zone shots, rush shots | a tracked origin/possession label differs from a chronology proxy; specify the available interpretation and its exclusions |
| zone entries, possession entries, zone exits, possession exits, forecheck involvement, defensive-zone puck touches | tracked movement/touches/pressure are absent from the current admitted evidence as complete observations; examine identified sources, retain unavailable states |
| skating speed | inspect public skating measurements, season/player coverage and exposure; the reference's composite is not an arbitrary speed or event-rate percentile |

whole-card parity remains incomplete where evidence is unavailable. supported fields and clearly named experimental counterparts can still form a useful card. the sample does not authorize purchasing tracking, copying a private projection or blocking the rest of the product until every source is available.

## what these images do not settle

no interactive controls were exercised. no supplied image shows our required tables, goalie card, reciprocal wowy, spider, replacement detail or error states. finish the required-card audit for v1; broader reference work follows its release priority. historical bands' thresholds, scatter hide rules, proprietary formulas and color semantics cannot be recovered reliably from pixels alone. preserve those unknowns rather than infer scientific claims from design.

## original file identities

| id | original file under `samples/` | sha256 |
|---|---|---|
| s01 | `HUxvta7WoAAk0m-.jpg` | `2a59299cb39c928968f2615a7829500fdd2113ce43636d752d13c981ed2e5cc5` |
| s02 | `HU_5bnuWoAEHIRH.jpg` | `67e24f361993303d2265c497fcc05296c8fe1843a2f1e22e6ece4f37cbf91fc5` |
| s03 | `bafkreigc46jfqzw4k3tsddaertiibqq7yhzyqawctneqvw7ssoq5vaflru.webp` | `fc675a8fe6a9ea43fcaf83bb01425bae391398d6767d6c7b81cd8b15127add1e` |
| s04 | `bafkreihnsd2g4spckws7vzjn36nk5xzo57earfhnckaik4uek2cb6tpfzm.webp` | `d545c3ddc8c33004e382b5bd1bd1c6c551ca90e8a970a716dff3e0513c241b1a` |
| s05 | `bafkreiblys3hhimhhvxbvcw77tyv6ox5afoxll7iaiwb2ufhmkvt4rsw2u.webp` | `430d3fa179c3516ff1aa5add6e7d216c6c07a12b0db54c2813dd8d15a8f29dda` |
| s06 | `bafkreicsle2uflwxefx4lteixxcwgvx7htxvburqriloenpopgga5mgqg4.webp` | `18232e0a358eedb6aed15d159d82f0ed9b327007c2e5583749ff6257e1fdaa7b` |
| s07 | `bafkreieaax4zmq5s75nqhcgjgvouklosjop6tgtmempxi4bhatpdinhdya.webp` | `18a4744cfe72224707a6138d60381a2640dde70498c416bff6e1406891e9fea0` |
| s08 | `bafkreigp26m3pm7bnhqiiejl5vbbzbhrmg3fu3ci5kdgyo5ad2g3nmtega.webp` | `710c54096ef7e8df64dc364c6b22574d623ddcf715bd947c43d4969c736e7ad9` |
