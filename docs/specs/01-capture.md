# 01 — faithful capture and a compact offline corpus

status: specification for review; no application code or admitted fixtures yet. scope: one capture command and two small example games. [plan](../plan.md), [architecture](../architecture.md), [legacy defects](../issues/legacy-raw-provenance.md).

## target and boundary

given an explicit nhl game id and a new output directory, preserve each requested response body exactly as delivered by the http client, with enough metadata to identify it. later analysis can read these files offline. a captured response is evidence, not a validated game or reconstructed hockey fact.

include four fixed sources: play-by-play, boxscore, shift charts and the official game-summary report used to check a few facts. no discovery, season downloads, roster enrichment, report parser, reconstruction, fitting, sqlite, frontend or permanent test harness. no legacy code or data imports. fresh captures replace the old fixture baseline.

## command and source api

from the repository root, create the download parent once: `mkdir -p var/captures`. from `app/`, run `npm run capture -- --game 2025020001 --out ../var/captures/example-01`.

`--game` is a ten-digit string; upstream responses determine whether it exists. `--out` must be new and its parent must exist. reject invalid arguments or an existing destination before network access. one game per invocation; repeat the command for another game or retrieval. the operator names directories; no capture-id generator, catalog or deduplication service.

| source key | get request |
|---|---|
| `play-by-play` | `https://api-web.nhle.com/v1/gamecenter/{gameId}/play-by-play` |
| `boxscore` | `https://api-web.nhle.com/v1/gamecenter/{gameId}/boxscore` |
| `shifts` | `https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId%3D{gameId}&limit=-1` |
| `game-summary` | `https://www.nhl.com/scores/htmlreports/{season}/GS{gameSuffix}.HTM` |

for these nhl ids, `{season}` concatenates the first four digits and the following year; `{gameSuffix}` is the last six digits. `2025020001` gives `20252026/GS020001.HTM`. fixed urls only; no arbitrary-url cli, alternate feeds or endpoint fallback.

request sequentially with a descriptive user-agent. use a 30-second timeout covering request and body read; persistence is outside that timeout. do not follow redirects or retry automatically. retain redirect/error bodies and `location` where supplied. complete all four requests after transport or upstream failures; filesystem failure stops immediately. manual rerunning uses a new destination.

exit `0` only if all four bodies were captured completely with 2xx statuses. exit `1` for invalid invocation, local failure, an incomplete request or any other http status. a 2xx capture can still contain malformed json: this command does not parse hockey payloads.

## files and record schema

each output directory contains `<source>/body.bin` and `<source>/capture.json`. the relative record path identifies the retrieval within that directory. a later download uses another directory even if its bytes match. no additional batch manifest is needed for four fixed sources.

`capture.json` is an application-owned record; its formatting need not match any upstream document:

| field | contract |
|---|---|
| `schemaVersion` | literal `1` |
| `gameId`, `source` | requested id and one of the four keys above |
| `request` | `{ method: "GET", url: string, requestedAt: utc-iso-string }` |
| `httpStatus` | integer when headers arrived; otherwise `null` |
| `responseHeaders` | received lowercase keys from `content-type`, `content-encoding`, `content-length`, `date`, `etag`, `last-modified`, `location`; absent headers omitted |
| `state` | `"captured"` or `"failed"` |
| `body` | when captured: `{ path: "body.bin", representation: "http-client-body", bytes: nonnegative-integer, sha256: lowercase-hex64 }`; otherwise `null` |
| `failure` | when failed: `{ kind: "transport" | "body-read" | "timeout", message: string }`; otherwise `null` |

retain status and selected headers if they arrived before a body-read failure or timeout. otherwise use `httpStatus: null` and `responseHeaders: {}`.

`http-client-body` means after the client's content decompression, before text decoding, parsing, projection or reserialization. source `content-length`/`content-encoding` describe the response and may differ from the stored representation. empty complete bodies are valid captures; failed reads are not empty successful responses. the digest and length describe exactly the saved bytes.

buffer one response in memory, write its body, then write its record. a body without a complete valid record after interruption is unfinished; ignore it and remove it manually if desired. do not retain partial downloads or add resume/fsync machinery for these cheap requests. a failed request gets metadata with `body: null`; a local write failure may prevent recording metadata and must be reported directly. earlier completed captures remain usable.

use effect's existing http client, filesystem and error primitives. `FetchHttpClient.layer` with `response.arrayBuffer` preserves the chosen boundary; do not apply `filterStatusOk` before persistence. use node's argument parsing and sha-256 primitives. no custom http abstraction, stream processor, plugin registry or task runner.

## offline content and evidence

retain two game directories containing eight fresh response captures under `fixtures/captures/` and a short `fixtures/README.md`. production downloads go under ignored `var/` or an explicit external path. these fixtures are examples for development, not a training corpus or a promised complete edge-case suite.

| game | facts to check and record | useful boundary |
|---|---|---|
| `2025020001` — chicago/florida, 2025-10-07 | final 2–3; shots 19–37; 361 play records; shift response `data.length = total = 856`, including 851 type-517 and five type-505 records | regulation, blocks, same-time events, empty net; shift feed contains non-shift records |
| `2025020006` — calgary/edmonton, 2025-10-08 | final 4–3 after shootout; timed-play goals 3–3; shots 22–35; 374 play records; shift response `data.length = total = 826` | overtime and shootout are not regulation goal/shot counts |

these are observations from the 2026-09-29 source survey, not forever-fixed upstream values. check the actual admitted captures and explain later source changes rather than altering payloads to match this table. admission also checks body identity: play-by-play/boxscore id, season/type/date/teams, each shift record's game id, and the report's date/teams/game number. the request id alone proves none of those. check the reports manually; no report parser belongs here. the eight inspected responses totaled about 0.99 mb.

the content designer's rule: every annotation states purpose, exact source/field or report locator, what was checked, and its limit. distinguish a directly inspected source field from corroboration by another nhl export; neither is independent measurement of the game. no generated snapshot is its own correctness oracle. real fixtures have no modifications; any intentionally altered bytes used during verification are labeled synthetic and kept separate.

the first report's “5v5” total includes an empty-net interval and cannot establish our later genuine-5v5 exposure. roster membership does not establish participation or handedness. preserve blocked-event ownership, event ids, original order, `sortOrder`, unknown fields and missing values unchanged. `limit=-1` returned all shift records in this survey; `limit=5` returned five while advertising `total=856`. verify collection completeness when admitting fixtures; capture success alone does not establish it. no paginator is included.

## command content

per source: `captured shifts for game 2025020001: http 200, <n> bytes`. for an http error, add `source error response; body preserved`; for 3xx, `redirect response; body preserved`. for an incomplete read: `capture incomplete for shifts, game 2025020001: <cause>; no complete body saved`.

after attempting all four sources, print disjoint counts: `<n> captured 2xx responses; <n> captured non-2xx responses; <n> incomplete requests`, then the output directory. on local failure, name the affected path and useful action; omit the normal summary and do not count unattempted requests as upstream failures. no payload dumps, default stack traces, dashboard or claims that a game is valid merely because capture succeeded.

## implementation boundaries

| files | responsibility |
|---|---|
| `app/package.json`, `app/package-lock.json`, `app/tsconfig.json`, `app/.node-version` | one node/effect project; capture script using `tsx`, typescript and compatible effect/platform/node packages |
| `app/src/operator/capture.ts` | fixed source requests, persistence and schema; `captureGame({ gameId, outDirectory })` returns an effect producing four capture records after requests finish; filesystem failure fails it immediately |
| `app/src/operator/cli.ts` | arguments, invocation, content above and exit status |
| `fixtures/captures/`, `fixtures/README.md` | the two admitted captures and manually checked annotations |
| `.gitignore`, root `README.md` | exclude downloads/build output and document the command |

`captureGame` uses the existing effect http/filesystem services; cli wiring supplies their node/fetch implementations. tests can provide a client mapping requests to a real local http server, without production test flags or a new application interface. keep the schema with its only implementation; split further only for actual complexity. no python or browser scaffolding in this slice.

## acceptance and red/green/refactor

1. temporary integration checks exercise the command's capture path through real http and filesystem operations: unchanged whitespace/unknown fields/missing fields, decoded gzip bytes, complete 404 or malformed bodies, truncated reads and refusal to overwrite an existing directory. assert saved bytes, digests, records and exit/result accounting. do not mirror internal helper calls.
2. establish the meaningful failing checks, implement, pass, refactor and rerun. one explicit live pass captures both listed games and checks body identity, manually inspected source facts, corroborated report values and shift totals. unavailable live sources leave that acceptance item incomplete; never substitute legacy or synthetic data and call it passed.
3. verify offline reading of the admitted files without network or the hdd. no reconstruction claims. run ordinary type/build checks appropriate to these files.
4. delete all temporary test code, servers, test-only dependencies and test scripts after verification. retain the real fixture corpus, annotations and production validations. summarize results in the implementation change description. the later testing slice owns any lasting suite or broader fixture set.

tradeoffs: four sequential requests and operator-named folders keep operation simple; no automatic retry or resume. buffering is appropriate for these observed small payloads; measure before expanding to bulk acquisition. preserving the report adds one small response per game in return for inspectable corroboration. deleted checks must be recreated until the later testing slice. unfinished files can need manual cleanup.

## source review

read-only probes on 2026-09-29 succeeded using a descriptive user-agent and `Accept-Encoding: identity`; some other clients returned 403 or failed to open these urls. no access guarantee is inferred. actual implementation must verify its own client, including decompression.

primary examples: [play-by-play](https://api-web.nhle.com/v1/gamecenter/2025020001/play-by-play), [boxscore](https://api-web.nhle.com/v1/gamecenter/2025020001/boxscore), [shifts](https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId%3D2025020001&limit=-1), [regulation report](https://www.nhl.com/scores/htmlreports/20252026/GS020001.HTM), [shootout report](https://www.nhl.com/scores/htmlreports/20252026/GS020006.HTM). published [effect platform source](https://registry.npmjs.org/@effect/platform/-/platform-0.97.2.tgz) confirms fetch and array-buffer delegation; [fetch's content-decoding rules](https://fetch.spec.whatwg.org/#http-network-fetch) explain the byte boundary. no dependencies, captures or test code were added during specification.
