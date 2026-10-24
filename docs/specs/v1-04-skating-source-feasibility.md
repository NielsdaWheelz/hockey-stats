# v1-04 — skating-source feasibility

full handoff under [the factual contract](experimental-card-facts.md#tracking-and-skating-admission-boundary) and [microstat crosswalk](../product-inventory.md#microstat-skater--s02-and-documented-fd-variants). [the plan](../plan.md#proposed-pr-boundaries-and-dependencies) owns assignment. the user chose **feasibility plus a costed acquisition handoff**, not conditional bulk collection. this document assigns no execution.

## outcome and limits

determine whether ordinary primary-source access can supply the two agreed skating measures for `20232024`, `20242025`, `20252026`, and whether a complete reference population can be obtained. deliver attributed probe receipts, independently checked sample observations where possible, a finite source/census contract and a concrete acquisition estimate. a supported blocked result completes this feasibility investigation; it does not complete historical admission.

the two outputs are `skating_max_speed_mph` (source maximum sustained speed, mph) and `skating_bursts_over20_count` (source 20+ mph burst count). no private skating composite, per60 conversion, reconstructed 5v5 denominator, model fit or source percentile substitution. retain the source's regular-season/all-situations meaning and retrieval time. these are retrospective measurements, not pregame covariates or estimated ability.

no bulk player loop, new provider, paid tracking, proxy/browser bypass, automatic fallback parser, retry engine, generic importer, publication/schema/browser change, dependency, site build or activation. existing observations and expensive evidence remain intact. small probes and local reference copies work without the hdd; later historical collection keeps its own explicit storage/assignment contract.

accepted costs: this may end with useful software and an evidenced access blocker but no raw skating values. a successful sample still leaves collection/integration work. the benefit is a source contract based on exercised evidence, with no guessed payload schema or premature ranking claim.

## evidence and bounded execution

[current inspection](../research/skating-v1-04/source-audit.md) found three historical detail requests denied with 403. public documentation supplies definitions; it does not supply an exercised historical payload or census. the implementation must repeat the bounded check through the actual capture owner. use only the fixed primary locators below; definitions and actual returned fields remain separate evidence.

| source kind | fixed locator / identity |
|---|---|
| `detail` | `https://api-web.nhle.com/v1/edge/skater-skating-speed-detail/{playerId}/{seasonId}/2`; player, season, game type2 |
| `listing` | `https://www.nhl.com/nhl-edge/skaters/{seasonId}/2/skating-speed/all`; season, game type2; the `all` suffix does not prove a census |
| `glossary` | `https://www.nhl.com/nhl-edge/glossary`; no invented player/season |

at most **twelve attempted requests for the entire assigned run**, including failures; no implicit retries or redirects. freeze the three initial keys, seven fixed conditional keys and two adaptive slots before network work. bind an adaptive slot's player/season and reason before requesting it, citing the listing evidence that selected it. record planned-but-skipped keys with reasons and unused adaptive allowance as a count, not fabricated player requests.

1. initial probes: player `8478402`, one detail request per displayed season. run these three distinct seasonal checks even if one receives 403; a 429 or two consecutive transport failures stop the initial batch and leave remaining slots deferred.
2. a season permits optional inspection only after its initial response actually contains usable, identity-compatible measurement evidence. HTTP200, an html shell or parseable unrelated json does not suffice.
3. conditional allowance: one defenseman detail (`8480800`) and one listing per viable season; one glossary request overall; up to two additional detail requests chosen from actual listing evidence to examine low/zero bursts, traded/duplicate identity or another unresolved field boundary. total allowance including initial probes is twelve. absent a useful contrasting candidate, leave the slot unused.
4. any optional 403/429 or two consecutive transport failures stop **all remaining optional** requests. malformed/content-incompatible results stop expansion of that season. ordinary failures retain their distinct receipts; unused slots are deferred, not failed or inspected. no alternate host, query guessing or general enumeration follows.

an accessible response may contain a full finite table within this bound; inspect what was actually received. do not continue its pagination or fetch every participant here. record demonstrated next-page/qualification rules and the remaining count as the later acquisition handoff. a top-ten list without a known full universe remains `unestablished`, not a partially completed census with an invented denominator.

## owners and interfaces

| owner | change |
|---|---|
| new `app/src/operator/skating-capture.ts`, `skating-cli.ts` | fixed source/argument validation and one explicit supplemental request; new `capture-skating` script in `app/package.json` |
| existing `operator/capture.ts` | add only explicit skating identity variants; reuse `captureResponse` for bytes, hashes, selected headers, timeout, manual redirects and receipts |
| existing `analysis/src/hockey_stats/captures.py` | fixed skating receipt reader; narrowly extract common receipt/body validation if needed, without copying it or changing core completeness |
| new `analysis/src/hockey_stats/skating.py` | offline selection binding, inspected source adapter if available, sample/census artifact, strict reader and thin module command |
| existing `references.py`, `artifacts.py` | reuse the bios field meaning, strict json, exclusive writes and implementation attribution |
| source/content owners | checked source contract, small original fixtures and `docs/research/skating-v1-04/verification.md` |

```text
npm run capture-skating -- --source detail --season SEASON --player PLAYER --out NEW_DIRECTORY
npm run capture-skating -- --source listing --season SEASON --out NEW_DIRECTORY
npm run capture-skating -- --source glossary --out NEW_DIRECTORY
python -m hockey_stats.skating --selection FILE --out NEW_DIRECTORY

captureSkating(selection, outDirectory) -> CaptureRecord
bind_skating(selection_path, output) -> skating_path
read_skating(path, expected_purpose) -> validated_artifact
```

reuse pinned environments. reject duplicate/unknown/irrelevant flags before any request; the three real seasons are fixed. player ids are positive digit strings; game type is fixed2. each invocation creates a fresh root and one source leaf (`edge-skating-detail`, `edge-skating-listing` or `edge-skating-glossary`) containing existing `capture.json`/`body.bin` receipt semantics. glossary identity contains only `source`; detail adds `seasonId`, `playerId`, `gameTypeId:2`, listing `seasonId`, `gameTypeId:2`. no arbitrary-url option. occupied output fails before networking.

coordinate the small `CaptureIdentity`/common-reader changes with v1-02; retain its concurrent right-rail variant. do not edit its game cli/report, v1-01's analysis command registration or existing six/four-source `SOURCES`/`REFERENCE_SOURCES`. default capture completeness and all old receipts remain unchanged. the new module command is the only offline entry; no alias/runner or daemon.

## source interpretation

before implementing a successful adapter, inspect actual captured bodies and pin their literal paths/types, units, null/sentinel rules, context fields and aggregation level in the verification record. implement one explicit reader for the observed source shape; evidence pointers document it, not drive a configurable parser. upstream extra fields stay raw and may be ignored; missing required semantic context cannot be invented. html and json are different formats: `strict_json` is not an html parser. a login/denial/shell is not a dataset.

validate body/report context against requested player, season and regular season. a url alone is insufficient; dated maximum-event evidence corroborates a year but does not prove the aggregate covers its entire season. retain every context witness and any source-as-of timestamp. identity/type/year conflicts withhold affected values. never accept current-year numbers under an archival path.

use the source's maximum-speed definition and available mph precision. a reported zero needs established non-sentinel meaning; negative/nonfinite values are invalid. burst counts must be nonnegative integers. use an explicit source 20+ total, or add two counters **only after actual schema/definition evidence establishes disjoint 20–22 and 22+ categories**; retain both original counters/locators and record that addition. never add a total to its subset, infer a count from a maximum, or infer zero from missing fields. if only other units/categories exist, report the contract gap rather than quietly repurpose the field.

one missing measurement does not remove the other. overlapping rows with identical identities/values may share one normalized observation while retaining all witnesses; conflicting responses remain unresolved until an explicit supported selection. no averaging, summing traded-team maxima or stitching different snapshots. a single source row must establish season aggregate versus team fragment before it becomes a player-season fact.

when no usable primary shape is observed, implement/verify the capture, receipt and unavailable-result path only. `adapter_status=not_observed`; do not fabricate NHL field names or advertise synthetic parser checks as source-schema acceptance. a later source change may require its own adapter amendment. this is an explicit empirical limit, not an unexplained placeholder.

## selection and compact artifact

all product objects are closed, with required keys; `?` below means nullable. reject duplicate keys/ids, nonfinite numbers, contradictory selections and purpose mismatch. `real` uses the three displayed seasons; `fixture` may use named subsets. paths resolve relative to the containing selection; copied selection keeps its original base. `capture.directory` contains the named source leaf; position-reference `directory` is the season root containing `skater-bios/`. every selected receipt/body hash and identity must validate before interpretation. missing promised bytes are a contract error; an explicit failed/unrequested attempt is data.

```text
selection = {
  schema_version:1, purpose:real|fixture, seasons,
  requests:[{request_id,kind,season?,player_id?,
    capture:{directory,receipt_sha256,origin:primary|synthetic}?,deferred_reason?}],
  position_references:[{season,directory,receipt_sha256,body_sha256}]
}

skating = {
  schema_version:1, purpose, implementation,
  selection:{original_path,sha256,copied_path:"selection.json"},
  adapter_status:not_observed|primary_shape_exercised,
  captures:[{request_id,kind,season?,player_id?,url,requested_at?,
    http_status?,state:captured|failed|deferred,receipt_path?,receipt_sha256?,body_sha256?,
    origin:primary|synthetic|null,
    failure:{kind:transport|body-read|timeout,message}?,deferred_reason?}],
  source_contracts:[{kind,format:json|html|null,identity_rules:[string],
    measurement_rules:[string],enumeration_rules:[string],shape_evidence:[witness],
    definition_evidence:[{url,title}],limitations:[string]}],
  observations:[{season,player_id,reported_position?,position_group:f|d|null,
    position_evidence:[witness],context_evidence:[witness],source_as_of?,
    skating_max_speed_mph:measurement,
    skating_bursts_over20_count:measurement}],
  census:[{season,enumeration:unestablished|partial|checked_complete,
    inclusion_rule?,reported_total?,universe_ids?,observed_listed_ids,
    enumeration_evidence:[witness],
    measurements:[{measurement_id,acquisition:unestablished|partial|checked_complete,
      eligible:{f:[],d:[]},
      exclusions:[{player_id,position_group:f|d|null,reason}],
      unresolved:[{player_id,position_group:f|d|null,reason}]}]}]
}

measurement = {value?,status,reason?,
  evidence:[witness],transformation:direct|sum_disjoint|null}
witness = {
  source:{kind:request,request_id}|{kind:position_reference,season},
  locator:{kind:json_pointer|html_label,value:string},raw_value:json_value
}
status = available|source_null|missing_field|not_requested|http_unavailable|
         transport_failed|schema_unresolved|context_unresolved|invalid_value|conflict
```

`kind` is `detail|listing|glossary`; ids are strings, seasons eight-digit strings, counts nonnegative integers, timestamps ISO8601, hashes lowercase sha256. `json_value` preserves the finite source value; it is not another extensible product object. definition titles/urls and rules are documentary strings, not executable mappings. `source_contracts` has exactly the three source kinds; an unobserved structure has null format, empty unverified rules and an explicit limitation. each witness resolves a selected receipt or position reference and a concrete json pointer/visible table label. documentary citations cannot replace measurement witnesses.

available real-purpose values require primary witnesses, validated context and finite valid values; fixture values may instead cite explicitly synthetic witnesses. unavailable values are null with nonblank reasons. create a row for every requested detail identity, even when unavailable; additional listing observations need verified context/fields. deferred detail ids retain `not_requested`; no fake player row for glossary/listing failures. failures retain the exact receipt failure; deferred rows carry a reason and null receipt/status/body/timestamp; captured rows have null failure/deferred reason even for non2xx. body-read failures may retain a status. timeout/body-read/transport failures become `transport_failed` measurements with the precise cause retained. positions normalize `C/L/R/F` to `f`, `D` to `d`; unknown/conflicting reports yield null, never an inferred forward.

select at most one attempt for a `(kind,season,player)` key; preserve predecessors outside this selection. the three initial real keys and all capture/deferred slots reconcile against the request plan and cap. timestamps/status/body hashes reflect actual receipt states, not binding time. write `selection.json` and `skating.json` exclusively. the compact reader validates copied selection, purpose, unique keys, values, evidence links and census partitions without reopening network/raw roots; creation validates original bytes. selected captures declare original-primary versus synthetic origin in the attributed selection/fixture record; real artifacts reject synthetic inputs, and deferred rows have null origin. `primary_shape_exercised` requires an available value from an attributed original primary capture, including an original preserved as a fixture; neither HTTP200 nor a synthetic body establishes it. artifact purpose and source origin remain distinct.

use the existing small `fixtures/references/{season}/skater-bios` captures through `read_reference_capture(directory, "skater-bios")` and the existing `playerId`/`positionCode` interpretation; do not load all four reference sources or recapture a season. preserve exact receipt/body identity. these are captured reports, not proof of immutable historical position; any source-position discrepancy remains visible. later integration must reconcile against its annual `Person`, not silently overwrite either report.

## census and downstream contract

the universe is the complete **declared source-listed regular-season population**, including any documented source qualification rule. it is not all observed 5v5 skaters, current rosters, the top leaders, the sampled ids or the subset already in the website. preserve source-listed players outside today's publication catalogue.

enumeration and measurement acquisition have separate statuses. `universe_ids=null` until a finite complete membership list and its terminal/page/total evidence are established. preserve an observed subset separately. enumeration `partial` means the source establishes a finite population/paging rule but its membership is not fully enumerated; `checked_complete` requires the full unique set and boundary evidence. acquisition can be `checked_complete` for a measurement only after enumeration is complete and every universe id has an eligible or justified exclusion disposition, with no unresolved acquisition. a readable response alone establishes neither. if only top-N evidence exists, keep `unestablished` and do not assert full-population exclusions or completeness.

within each year and measurement, source-listed ids partition into eligible F, eligible D, explicit exclusions and unresolved acquisition/identity. null source measurements and unknown/conflicting positions are explicit exclusions; failed/unrequested fetches are unresolved, not exclusions chosen to improve coverage. nullable `position_group` keeps unknown positions outside both groups. the four unique sets are disjoint and exhaust the universe when known; otherwise they describe only the inspected subset and cannot assert a source denominator. every eligible id resolves to an available same-season observation for that measurement and its evidenced position group; source-null exclusions resolve to source-null evidence. partition arithmetic cannot certify invented membership. valid detail observations outside the declared source population remain raw-only with that reference exclusion stated. invalid/context-conflicting measurements remain unresolved, never legitimate null exclusions. counts derive from unique sets; `reported_total` is a nullable source assertion with a witness, not proof of completeness. preserve documented source qualification, but add no 300/50-minute or reconstructed-time cutoff.

the receipt reports universe/listed/acquired/available/excluded/unresolved counts per year/measurement/group, with unknown denominators null. raw samples may be usable while census remains incomplete. this slice emits **no percentile**, including when a complete table fits inside the probe budget. source ranks remain evidence only.

v1-17 consumes these exact observations through the fixed `microstats.py` owner; it does not reparse sources. existing schema7 `FactValue` can carry mph with null numerator/denominator and count with `value=numerator`, null denominator, both denominator kind `none`. unknown elapsed/events/eligible-weight coverage remains null; burst count is not `Support.events`. no prior seasons, modeled uncertainty or invented exposure. both measures share one card slot with separate labels/values and missingness.

schema7's `Source` does **not** encode census completeness. v1-17 owns the explicit publication/cohort extension binding measurement, season, source definition/receipts, census membership and position. it must preserve the complete declared peer universe or withhold ranks, never silently recompute over a publication subset. current `census_unverified` behavior stays unchanged here. useful values do not require a complete cohort; scientific accuracy is not being certified.

## acceptance and acquisition handoff

the content designer owns operator output/source labels, not a premature skating dashboard. lead with what was inspected, what worked and what remains unknown. show captured versus usable samples and population status separately; never call blocked capture zero speed or full admission. source measurements need year, units, all-situations scope, retrieval/source coverage and precise missing reasons.

1. **red→green capture:** temporary integration checks through the real command prove exact returned bytes/receipt/hash, denied bodies, transport/body failure, fixed url/identity, irrelevant flags, occupied output before request and unchanged core/right-rail capture behavior. use controlled transport fixtures only as transport fixtures, not invented NHL success payloads.
2. **binding/adapter:** strict-json/receipt corruption, missing promised bytes, purpose/id/year/type mismatch and duplicate selection checks. if a primary shape is observed, preserve one original and independently check literal field/value witnesses; test null versus zero, malformed/negative/count precision, direct versus demonstrated disjoint counters, duplicate/traded rows and one unavailable measure. label altered cases synthetic. without a source shape, report that branch unverified instead of constructing fictional schema fixtures.
3. **census:** independent small fixtures cover top-N without denominator, incomplete pages, whole-source enumeration, duplicate ids, measurement-specific nulls, unresolved acquisition, unknown positions and source-only players. fixture exercise validates artifact arithmetic, not access or a real source census.
4. **real bounded run:** obey the twelve-request protocol; reconcile all planned/captured/deferred outcomes and source evidence. actual reads use the production client, not search-engine values. record `software_checks`, `access_result` and `adapter_status` separately, raw-value feasibility for all six season×measurement cells, and enumeration/acquisition feasibility per season/measurement. a blocked conclusion requires actual attempted receipts; software checks alone cannot establish source access failure. one exercised measurement cannot establish the other five cells.
5. **refactor/review:** independent source, systems and content review; rerun only affected receipt/adapter boundaries and pinned relevant checks. remove duplicate parsing/validation at its owner, not unrelated research code. delete temporary tests/controllers/test-only dependencies after final green. retain small attributed originals and checked facts under `fixtures/skating-v1-04/`, plus verification identities, request/byte/time counts, commands and limitations. no full app build or live listener/database change is needed for an operator-only change.

the final verification record contains the **acquisition handoff**, not an executed campaign: demonstrated locators/parameters and field schema; source universe/qualification/pagination evidence; per-season candidate ids and exclusions; outstanding identities/positions; request count or an explicitly unknown bound; measured sample bytes/latency and an honest extrapolation with assumptions; proposed raw/output locations; required missing schema/source work; and the exact v1-17 integration obligations. if access is blocked, say which evidence must change before collection can be estimated. do not invent an execution estimate or new retry technology.

update [the existing microstat issue](../issues/microstat-inputs.md) and plan with the actual result. acquisition remains a separately assigned follow-up after its scope/cost is concrete; no automatic new campaign or implementation assignment follows. real microstat/card closure remains with the source/factual producers and v1-17. inaccessible skating must not delay unrelated fields.
