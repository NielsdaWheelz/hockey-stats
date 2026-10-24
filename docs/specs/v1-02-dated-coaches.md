# v1-02 — dated coaching source

full implementation handoff, 2026-10-22. [the plan](../plan.md) owns assignment; this document assigns no execution. read the [program](experimental-player-analysis.md#a-evidence-and-preparation). this is independent of the running v1-01 preparation and v1-13 publication work.

implementation is complete and independently verified, including all 6,560 real games and 13,120 resolved game-team slots. [execution and acceptance](../research/coaches-v1-02/verification.md) retain exact identities, source limitations and receipts.

## outcome and limits

one supplemental capture command and one offline binder produce a checked, game-dated coach selection for the five admitted regular seasons, `20212022..20252026`: 6,560 games, 13,120 home/away dispositions. subsequent fits explicitly consume this selection without reparsing raw responses or rebuilding base preparation.

the quantity is **the head coach reported by nhl for that game and side, retrieved at the recorded time**. it is not verified bench attendance, tenure, assistants, official career credit, causal coaching quality or information known before puck drop. names, resolved identities, game dates and retrieval times remain separate. source gaps do not erase games or imply a neutral coach.

no fitting, coefficients, design matrices, scratch/official interpretation, automatic roster fallback, tenure database, new acquisition framework, core recapture, publication/schema change, website build or activation. preserve every original capture, native corpus, expensive fit and serving artifact. the six-source corpus remains valid without right-rail.

accepted costs: additional sequential requests/storage, a small reviewed identity table and retrospective source uncertainty. a fresh supplemental directory per request keeps old raw trees untouched but requires explicit source selection. fixture development works detached; full real execution needs the external originals/output location and usable source access. computational/source correctness, acquisition completion and scientific support are separate outcomes.

## source evidence and access boundary

the [2026-09-30 inspection](../research/source-audit.md#additional-source-evidence-without-the-drive) found `/gameInfo/awayTeam/headCoach/default` and its home counterpart in [right-rail](https://api-web.nhle.com/v1/gamecenter/2025020001/right-rail), without a top-level game id. the [official roster report](https://www.nhl.com/scores/htmlreports/20252026/RO020001.HTM) corroborates the two names. these establish a source candidate, not admitted five-season coverage.

on 2026-10-22, three read-only right-rail probes returned 403; the web reader also could not open that endpoint. no raw source files were captured in that specification task. the cause was unestablished. later production-client execution succeeded for all five seasons; [the completed source verification](../research/coaches-v1-02/verification.md#live-source-execution) resolves the access issue without attributing the earlier 403s.

when execution is assigned, freeze five inventory games, one per season, preferring existing fixtures; capture them first with the production command. inspect bodies, identity/context and both names. expand only seasons whose probe supplies a structurally usable, identity-compatible response with at least one nonblank coach name. a failed/empty probe does not prove the whole season inaccessible: mark remaining requests deferred with the access, transport or content reason, not failed or inspected. during expansion, the first 403/429 or two consecutive transport failures stop that season's batch; retain receipts and resume only by an explicit ordinary retry selection. no evasion or automatic retries. isolated missing names remain data rather than a reason to retry every game.

the initial bound is one request per selected game still missing a right-rail capture, including probes, at most 6,560. reuse existing checked captures; choose replacements explicitly and preserve predecessors. a temporary sequential controller may invoke the existing command over the frozen list; retain commands/dispositions and delete the controller after verification. no persistent scheduler or resume engine. if access remains blocked, finish software verification and an honest partial artifact; real admission remains incomplete. serializing unavailable rows cannot complete acquisition.

## owners and commands

| owner | change |
|---|---|
| `app/src/operator/capture.ts` | `captureRightRail` creates a fresh supplemental game directory, then calls existing `captureResponse` once; extend the source type, preserve the default six-request list |
| `app/src/operator/cli.ts`, `capture-report.ts` | admit `--source right-rail`; report its own fresh-directory retry instruction, not landing's core-copy instruction |
| `analysis/src/hockey_stats/captures.py` | a fixed supplemental-source reader using existing receipt/body validation; keep `SOURCES`, core interpretation and provenance sets unchanged |
| new `analysis/src/hockey_stats/coaches.py` | typed selection/identity/artifact records, offline interpretation/binding, coverage, reader and thin module command |
| existing `corpus_inputs.py`, `references.py`, `artifacts.py` | reuse inventory, strict JSON, input identity, exclusive writes and implementation receipts; no new parser or artifact framework |
| source/content owner | reviewed identity table, original supplemental fixtures, checked expected facts and `docs/research/coaches-v1-02/verification.md` |

```text
npm run capture -- --game ID --source right-rail --out NEW_DIRECTORY
python -m hockey_stats.coaches --selection FILE --identities FILE --out NEW_DIRECTORY

bind_coaches(selection_path, identity_path, output) -> coaches_path
read_coaches(coaches_path, expected_purpose) -> validated_coaches
```

the existing pinned app/python environments suffice; no dependency change. the module command is the single offline entry, not an additional alias for `hockey-stats-analysis`. this avoids competing edits to `analysis_cli.py`/`pyproject.toml` while v1-01/13 run. the ordinary capture command remains the network owner; the python binder never requests a URL.

right-rail mode creates exactly `right-rail/capture.json` and, if completely received, `right-rail/body.bin` inside the new root. request `https://api-web.nhle.com/v1/gamecenter/{gameId}/right-rail`. reuse existing timeout, redirects, byte representation, hashes and captured-non-2xx/failed receipts. an occupied output fails before network access. do not copy a core bundle merely to retry this supplement. default capture and `--source landing` retain their current distinct behavior.

## input contracts

all product keys below are required; `?` means nullable, never omitted. reject extra/duplicate keys, flags, games, seasons and nonfinite numbers. selection, identity table, output and reader expectation must have the same purpose. ids retain native eight-/ten-digit season/game strings and positive integer team ids. paths are explicit, resolved relative to their containing input. use a fresh output outside inputs; no discovery of the newest capture or local/external fallback.

```text
selection = {
  schema_version: 1, purpose: real|fixture,
  seasons: [{season, corpus_manifest, sha256, game_ids,
    captures: [{game_id,
      capture: {directory, receipt_sha256}?,
      not_acquired_reason: not_requested|probe_deferred?,
      explanation: string?}]}]
}
```

`real` uses the five ordered manifest identities in the [03n input table](../research/chance-03n/protocol.md#evidence-and-immutable-inputs), with `game_ids:null` and one capture disposition per inventory game. `fixture` allows ordered subsets and explicit nonempty game lists. load the admitted inventory through its existing reader, without opening game envelopes or deriving elapsed exposure. exactly one of `capture` and `not_acquired_reason` is nonnull; an absence requires a nonblank explanation, a selected capture has `explanation:null`. every promised receipt must exist and match its selected hash, requested game, source and URL; missing promised bytes or a malformed receipt is an error. recorded upstream failure is data. select at most one capture per game; never merge two responses or borrow the other side from an older capture.

one maintained identity table maps source strings to stable project-owned coach ids, independent of team and season. ids are explicitly assigned strings such as `coach-mike-sullivan`, not generated at runtime, sorted indexes or nhl player ids. store the checked real table at `analysis/data/coach-identities.json`; fixture identities stay separately labeled. the v1-02 owner maintains it.

```text
identities = {
  schema_version: 1, purpose: real|fixture,
  coaches: [{coach_id, display_name}],
  aliases: [{reported_name,
    applies_to: [{season, game_id, side: home|away}]?,
    coach_id: string?, explanation,
    anchors: [{season, game_id, side, receipt_sha256,
               body_sha256, pointer}]}]
}
```

match the exact preserved source string; do not fuzzy-match, strip accents or silently normalize punctuation. null `applies_to` means all occurrences of that exact string in this selection; a list limits it to those occurrences. at most one alias may match each occurrence, even if two would assign the same id. nonnull ids must resolve to the unique catalogue. `coach_id:null` records a reviewed unresolved identity, with a specific explanation. unmatched names remain `identity_unreviewed`, not automatically invented people.

each alias has a nonempty explanation and at least one selected, verified source anchor containing that exact name. review every distinct name and its team/year distribution; similar names alone do not justify merging identities. multiple spellings for one person need recorded corroboration in the verification record. official reports/announcements may corroborate a manual identity investigation, never populate a missing right-rail name. ambiguous occurrences stay unresolved. a corrected alias changes the table/artifact identity; it cannot rewrite what the source reported. retain verified ids across later updates.

## interpretation and record contract

decode successful bodies with existing strict JSON. upstream extra fields stay raw and are ignored by this narrow parser; our own records are closed. absent/null `gameInfo`, a side, `headCoach` or `default` means coach not reported for the affected side(s). an empty/whitespace-only default string also means not reported. malformed JSON, a non-object root or nonnull non-object `gameInfo` affects both sides; nonnull non-object side/`headCoach`, or nonstring default, makes only that side `coach_malformed`. preserve valid source strings exactly after JSON decoding, including case/spacing. no alternate-language or present-day substitution.

receipt identity plus selected inventory home/away roles binds the observation. check recognized context if supplied: top-level `id`, `gameId`, `season`, `gameType`, `gameDate`, and `gameInfo.{homeTeam,awayTeam}.id`. these are guarded paths, not a claim they exist in the unacquired body. a nonnull invalid or contradictory identifier/date makes both sides `source_identity_conflict`; absent/null corroborators are not a failure or agreement. first successful inspection must pin the report-link paths/types and any additional game/date/team corroborator in the parser and fixture expectations before expansion. validate game-specific nhl html-report links against the selected season/game suffix; conflicting links cannot be ignored. record checked pointers/values and absent fields; never infer teams from coach names or recursively guess identity from unrelated numbers.

```text
game = {season, game_id, game_date, home_team_id, away_team_id,
        source, context_checks, home: assignment, away: assignment}
source = {capture_path: string?, receipt_sha256: hex?, body_sha256: hex?,
          requested_at: utc?, http_status: int?,
          capture_status: not_acquired|captured_2xx|captured_non2xx|incomplete,
          parse_status: unavailable|parsed|malformed|identity_conflict,
          explanation: string?}
context_checks = [{pointer, reported_value: finite_json_value,
                   status: agrees|absent|unavailable|invalid|conflict}]
assignment = {reported_name: string?, coach_id: string?,
              status: resolved|source_unavailable|source_malformed|
                source_identity_conflict|coach_not_reported|coach_malformed|
                identity_unreviewed|identity_unresolved,
              reason: string?, source_pointer, identity_entry: int?}
```

`source_pointer` is the side's fixed `/gameInfo/{side}Team/headCoach/default` locator even when missing. `finite_json_value` permits null, boolean, finite number, string, array and string-keyed object only for retained context evidence, including malformed values; it is not a numerical feature bag. alias indexes are zero-based within the bound table. `resolved` requires a nonblank source name, a checked matching alias and a known id; only it has a nonnull id. every other status has a reason. unknown identity retains a valid source name. retain valid strings as evidence even when a context conflict prevents assignment. source reports and inventory facts never overwrite each other.

unacquired/request-failed/non-2xx sources give `source_unavailable`. malformed JSON/root/`gameInfo` gives `source_malformed`; a malformed side/name gives `coach_malformed` with the opposite assignment preserved and game parse status `parsed`. schema/hash/path/alias contradictions in our own inputs fail the command, rather than being converted to ordinary unknown data. game date/team/type comes from inventory, not retrieval time. output ordering is season, game date, game id; every game retains both assignments irrespective of core source quality or modeled eligibility.

| capture status | required source fields / parse status |
|---|---|
| `not_acquired` | path, hashes, time and http status null; `unavailable`; explicit selection reason |
| `incomplete` | receipt path/hash and request time present; body hash null; http status received or null; `unavailable`; receipt failure reason |
| `captured_non2xx` | receipt path/hash, body hash, request time and non-2xx http status present; `unavailable`; source-status reason |
| `captured_2xx` | receipt path/hash, body hash, request time and 2xx http status present; `parsed`, `malformed` or `identity_conflict` |

`capture_path` names the exact receipt file. hashes are lowercase 64-digit sha256; times reuse receipt UTC format. source explanation is required for unavailable/malformed/conflicting cases, otherwise null. global malformed structure takes precedence over contextual conflict, then side-local missingness/identity resolution. `resolved` has `reason:null` and an alias index; `identity_unresolved` has an alias index/reason but no id; `identity_unreviewed` has a reason and no alias/id; source/name errors have a reason and no alias/id. absent/malformed names have `reported_name:null`; a valid name survives contextual conflict. empty objects with absent fields remain parsed missingness. context-check `absent` has a null reported value; explicit null is `unavailable`, never `agrees` or `conflict`.

## output and downstream composition

copy exact input bytes to `selection.json` and `identities.json`; write `coverage.json`, then `coaches.json` last. no successful artifact after failure; repair the cause and use a fresh directory. no pickle, sqlite, resume state or corpus-sized numerical arrays.

```text
coaches = {
  schema_version: 1, kind: "dated-coaches", purpose,
  interpretation_id: "reported-head-coach-v1", implementation,
  selection: {path: "selection.json", sha256, original_path},
  identities: {path: "identities.json", sha256, original_path},
  coverage: {path: "coverage.json", sha256},
  corpora: [{season, corpus_manifest, sha256}],
  games: [game],
  resources: {wall_seconds, peak_memory_bytes, output_bytes}
}
```

reuse the existing implementation-identity record. resources are finite/nonnegative; output bytes exclude `coaches.json`. member paths are the fixed local names above. `original_path`, corpus paths and source capture paths are resolved absolute paths; copied selections retain their original relative-path base, not the output directory. reader validates copied selections/table/coverage, complete game cardinality against the selection's explicit capture keys, source/alias links and all cross-field rules without opening external corpora, raw captures or URLs. creation validates those original inputs; its stored hashes/locators remain provenance, not scientific evidence by themselves. fixture purpose cannot become real.

later `--coaches FILE` points to `coaches.json`; models bind its exact hash. v1-05/08/10/11 compare purpose, season/corpus identity and selected game/date/home/away keys to base preparation before joining. a fit/score may select its declared year, but cannot substitute another corpus revision, missing game, moved side or newer coach artifact. these consumers own their categorical axes, unknown-coach encoding, support and annual prior logic. no filtering of all games because one side lacks a coach. this artifact adds no unknown person with a fabricated zero effect. coach ids are separate from the publication's skater/goalie `person` catalogue; later method/source provenance binds this feed.

v1-02 does not edit v1-01 facts, v1-13 payloads or old `interpret.py` coach/scratch-unavailable observations. those observations concern their original sources. prepare and publication can progress independently; only numerical consumers need this new evidence.

## content and acceptance

the content owner designs the operator receipt, not a coach dashboard. lead with requested/captured/parsed/resolved counts and the exact limitation; list unresolved rows beneath the summary. no claim of complete historical coaching, verified bench leadership or fitted effects.

`coverage.json` has exact keys `schema_version:1,purpose,seasons,retrieval_range,issues`. each season row has `season,games,slots,capture_counts,parse_counts,assignment_counts,resolved_games,distinct_coaches`; all counts are nonnegative integers, using the enums above with all categories present. `slots=2*games`; capture/parse totals each equal games, assignment totals equal slots. `resolved_games={both,one,neither}` sums to games; `distinct_coaches` counts distinct resolved ids in that season. `retrieval_range={first,last}` gives actual request extrema or two nulls. `issues` has one row per nonresolved slot: `{season,game_id,side,team_id,status,reported_name,reason,capture_path,source_pointer}`. don't add reconstructed minutes or model support. summary tables use games for capture coverage and game-team slots for identity coverage.

the verification record separately reports `software_status`, `acquisition_status:complete|partial|not_run` with specific access/transport/content reasons, resolved-name coverage, identity-review completion, output identities, request count, bytes, time, limitations and reproduction commands. complete acquisition requires an accounted attempted/reused capture for every selected game; successful responses may still have justified visible gaps. admission is `usable_with_documented_gaps` only where actual usable names/identities exist. no source percentage threshold or model-quality gate; unreviewed available names are unfinished work. all-unavailable serialization is not a usable coaching capability.

implementation order and independently reviewed acceptance:

1. **capture:** temporary red→green checks through the real CLI establish exactly one request, exact received bytes/non-2xx preservation, failure receipts and pre-request no-overwrite. verify default six-source/landing behavior and frozen corpus reading unchanged. no live site rebuild.
2. **binding:** small synthetic fixtures cover each disposition, one-sided missingness, exact aliases, same person across teams/seasons, distinct similar names, scoped ambiguity, duplicate alias, wrong receipt/game/URL, corrupt promised bytes, context conflicts and occupied output. independently compute expected records; don't test the parser against its own output. a selected missing receipt is an error, an explicit unacquired row is data.
3. **real source:** after the bounded probe, capture/reuse the admitted inventory as access permits. independently check both sides for each season, one permanent coach-change boundary and one temporary absence case. an [official absence example](https://www.nhl.com/jets/news/head-coach-rick-bowness-to-take-leave-of-absence) motivates checking reported-versus-acting meaning, not silently correcting names. use selected games within the request budget; inaccessible corroboration remains an evidenced limitation. review all distinct aliases and reconcile 6,560 games/13,120 dispositions, requests and reasons. historical completeness cannot be inferred from one source example.
4. **consumer/detached:** read the completed compact artifact without raw roots/network; verify all identity links, fixture-purpose rejection and the later-consumer join invariants with minimal prepared-like records, not a fabricated v1-01 implementation or fit. reread exact input/member hashes and confirm core evidence unchanged. full real source acceptance is separate from detached fixtures.
5. **refactor and close:** remove duplicate derivations at their existing owners, then rerun the affected checks. independent source, systems and content reviewers inspect the final boundaries and receipt. delete temporary tests/controllers/test-only dependencies after verification; retain useful originals, independent expected facts and receipts. no new persistent harness is assigned.

preserve representative right-rail originals under `fixtures/captures/` beside their game evidence with exact receipts and required references; use a separately named capture attempt for a replacement. label the feed supplemental: old six-source complete bundles remain complete. new distinct broken games retain their complete available core bundle as required by [fixture policy](../../fixtures/README.md#fixture-policy-and-local-corpus); synthetic mutations remain separate. record unresolved access/identity/source cases under `docs/issues/` with evidence and closure criteria. implementation may finish with a source blocker, but the handoff must say exactly which real-data work remains.
