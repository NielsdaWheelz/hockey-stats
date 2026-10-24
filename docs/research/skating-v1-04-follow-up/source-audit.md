# skating follow-up inspection — 2026-10-22

read-only specification research, subsequently deferred by the user. no production capture receipts, retained response hashes, accepted measurements, census or implementation were produced. the completed [v1-04 protocol and verdict](../skating-v1-04/verification.md) remain unchanged. [the plan](../../plan.md#current-boundary) owns assignment; [the source issue](../../issues/microstat-inputs.md) owns the open delivery gap.

## relevance and decision

the [jfresh microstat guide](https://hockeystats.com/about/microstat-player-cards) explicitly uses nhl edge for its skating-speed composite, combining top speed and 20+ mph burst frequency. its other tracking fields come from a different observation source. our selected quantities remain two separately named raw measurements, not a reproduction of that composite.

the inspected [xg8](https://hockeyviz.com/txt/xg8) and [magnus9 ev](https://hockeyviz.com/txt/magnus9EV) descriptions do not name edge skating aggregates as inputs. the [2026–27 preview](https://hockeyviz.com/txt/preview2627) announces newer methods whose full descriptions are not supplied there; this inspection cannot establish all current private implementation choices. edge is not a dependency of our specified execution or attribution recipes.

the user chose **defer edge entirely**, accepting that the two selected skating fields remain unfinished. preserve existing source code/evidence and these findings. no new adapter, acquisition/census campaign, skating ranks, publication contract or full follow-up implementation handoff is assigned. other microstat work proceeds with explicit missing values. this is a priority decision, not proof that the source is inaccessible or scientifically useless.

## stronger source evidence found

ordinary native requests inspected the official player page and its client assets. the detail component binds `entityId`, `selectedSeason` and `selectedGameType` to `/edge/skater-detail/{entityId}/{selectedSeason}/{selectedGameType}`; `/now` is used only when selection is absent. its overview maximum-speed display consumes that response; the deeper skating-speed tab fetches the separate detail endpoint. rendering of the overview's direct 20+ counter was not checked. the strength selector applies to skating distance, not skating speed.

the overview exposes `/player/id` and `/player/position`, a direct `/skatingSpeed/speedMax/imperial` and a direct `/skatingSpeed/burstsOver20/value`. the latter avoids reconstructing a total from detail bins. `seasonsWithEdgeStats` lists available selections; it does not alone identify the selected aggregate. event dates and a matching player name are corroboration, not substitutes for the selector/request contract.

| requested regular season; player `8478402` | maximum mph | direct 20+ count | earlier preserved detail counters | reported games/goals/assists |
|---|---:|---:|---|---|
| `20232024` | 24.191 | 456 | 390 + 66 | 76 / 32 / 100 |
| `20242025` | 23.969 | 442 | 359 + 83 | 67 / 26 / 74 |
| `20252026` | 24.6119 | 681 | 530 + 151 | 82 / 48 / 90 |

root independently checked the old detail bodies and local `fixtures/references/{season}/skater-bios` receipts/bodies: the listed speeds, detail-counter sums and reported games/goals/assists reconcile. this corroborates source interpretation; it does not promote these unpreserved overview reads into admitted product values.

the [official glossary](https://www.nhl.com/nhl-edge/glossary) calls maximum speed sustained but does not establish the smoothing duration or sampling algorithm. it describes burst onset above 18 mph, termination below 16 mph and classification by the episode maximum. exact computational boundary inclusion/rounding, zero/null sentinel rules, tracking completeness and the aggregate's own update time remain unproved. retrieval time would not establish the latter. all six inspected values were positive.

the selected-season landing component calls `/edge/skater-landing/{season}/{type}`. the inspected `20252026/2` response supplies `leaders`, not a complete population. the observed player search has a query and limit of 20, without a demonstrated seasonal enumeration contract. no complete edge census was found.

the three admitted skater-bios bodies contain 924, 920 and 940 unique player ids respectively, with positive reported games and matching source totals: **2,784 candidate player-seasons**, not an edge census. if resumed, those could bound later acquisition without claiming a complete skating reference population. exact collection cost and acceptance remain unspecified; no bulk work follows from this count.

## inspection accounting and locators

the source reviewer made 13 native gets across ten urls, all http200, totaling 7,523,840 response bytes. the main asset was fetched four times while inspecting different symbols. these are read-only inspection counts, not production receipts or execution under the old twelve-request protocol. three preceding web-reader opens returned a player-page shell, glossary timeout and inaccessible listing. root separately checked public methodology pages through the web reader. no source payload files were written.

| native locator | requests | bytes per response |
|---|---:|---:|
| `https://www.nhl.com/nhl-edge/skaters/connor-mcdavid-8478402/20252026/2` | 1 | 106937 |
| `https://wsr.nhle.com/static/js/main.bundle.js?rel=4.3.1-55da735f` | 4 | 1815034 |
| `https://wsr.nhle.com/static/js/EdgeSkaterDetail.6d282b873f72b1390e4e.bundle.js` | 1 | 11780 |
| `https://api-web.nhle.com/v1/edge/skater-detail/8478402/20232024/2` | 1 | 4840 |
| `https://api-web.nhle.com/v1/edge/skater-detail/8478402/20242025/2` | 1 | 4839 |
| `https://api-web.nhle.com/v1/edge/skater-detail/8478402/20252026/2` | 1 | 4827 |
| `https://www.nhl.com/nhl-edge/glossary` | 1 | 84177 |
| `https://wsr.nhle.com/static/js/EdgeSkaterLanding.ea101ed08890226a603a.bundle.js` | 1 | 5843 |
| `https://api-web.nhle.com/v1/edge/skater-landing/20252026/2` | 1 | 6101 |
| `https://wsr.nhle.com/static/js/6033.08bff691db8b491b04a3.bundle.js` | 1 | 34360 |

## resumption notes, not an implementation assignment

if resumed, prefer the direct overview measurements and capture the official context/definition evidence before deciding whether a sample is usable. do not repeat the old circular requirement that corroborating evidence waits for an already-admitted measurement. a verified selector/request contract can establish context without redundant season/type fields in every body; a url alone cannot.

reuse `captureSkating`, `captureResponse`, `read_skating_capture` and `skating.py`. the current binder deliberately rejects primary available measurements and requires the old optional probes to stay deferred. an evidence-backed adapter amendment must remove those campaign-specific restrictions at their owner; manually editing a result is insufficient. no amendment is made now.

raw-value admission, candidate acquisition, source enumeration and percentile transport remain separate. a leaderboard, a union of leaders or a bios candidate list cannot silently certify the old source-census definition. preserve this distinction and the existing `census_unverified` behavior until separately specified and checked.
