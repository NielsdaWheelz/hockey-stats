# v1-20 specification — adversarial opus review, initial pass

reviewer: claude code, model `claude-opus-5-5` (opus 5.5), 2026-11-20. read-only. [handoff under review](../../specs/v1-20-whole-card-closure.md).

## scope

the reviewed specification is the working-tree draft of `docs/specs/v1-20-whole-card-closure.md`, re-read after root's mid-review amendments: physical scans now belong to admission (line 125), backend output now compiles into an empty `dist/node` (line 136), and the draft defines receipt handling during schema 8 rollback (line 153). line numbers below refer to that re-read.

i checked the draft against these sources:

- `app/src/server/{publication,analysis-publication,observed-publication,ledger-publication,main}.ts`
- `app/src/operator/publication-cli.ts`
- `app/src/shared/player-analysis.ts`
- `app/src/web/{comparative-card.tsx,analysis-values.ts,analysis-discovery.ts,analysis-history.tsx,peer-distributions.tsx,client.ts,routes/league.tsx}`
- `analysis/src/hockey_stats/{mechanism_composition,analysis_publication,execution_composition,value_composition,value_evidence,territory,territory_state,territory_evidence}.py`
- pins in `docs/research/value-v1-12/receipts/real-candidate.json` and `docs/research/execution-v1-06/activation.md`

## limitations

- **no runtime checks.** this is documentation, code and receipt inspection. nothing was built, tested, hashed or acquired. no sqlite file was opened. software and data acceptance are not claimed.
- **external drive not mounted.** `/Volumes/Expansion` was absent, so the donor root and candidate path were not checked on disk. pins were compared only against the retained receipts.
- **rehearsal commit not checked.** dev-server's `160bd0b8…` is outside this repository.
- **compiler determinism assumed.** typescript 7.0.2 is assumed to emit identical files from identical inputs. this was not verified.
- **startup memory orientation inherited.** shared memory orientation came from the parent's frozen snapshot `c314e019…` covering [0,3755), with a backlog up to 8070. no further memory reads were made.
- **local state was observed, not changed.** the observations below about the primary checkout and listener used `ls`, `ps` and `lsof` only.

## confirmed

- **pins match.** the candidate sha `d73cb8ba…`, its 32,039,075,840 bytes, publication `35ce39e0…`, results sha `6d05679d…` and selection sha `5b6e3f0b…` all match `real-candidate.json`. so do the costs: build 18,011 s native, first http 3,361 s, peak memory 3.33/3.02 gb, first overview 44,480,005 bytes. the schema 8 pin `9a5b4061…`/`dbac3ffb…` (11,310,997,504 bytes), schema 7 pin `eb4e31ab…`/`0526b60c…` and source `0e0f5694…` match `activation.md:9-14`.
- **the receipt design is at the right layer.** exact database bytes plus identical compiled validator code mean that every invariant established at admission still holds for the strict selected readers. skipping the census is therefore sound, not a weakening.
- **serving indexes can be rebuilt cheaply.**
  - people come from the `person` table (`analysis-publication.ts:510-525`).
  - grids are two `analysis_grid` rows (`:770-776`).
  - ledger coverage is a pure function of the annual reference's `positions`/`groups` (`ledger-publication.ts:437-445`).
  - the observed readers close only over `sql` and local schemas (`observed-publication.ts:175-240`).
- **ledger records are insulated from the territory text.** ledger dependencies copy only method/reference/support ids and support projections (`value_evidence.py:21-56`). changing territory prose cannot perturb ledger rows.
- **resolved by the amended draft.** startup no longer runs `validatePhysical`'s `integrity_check`/`foreign_key_check` (`analysis-publication.ts:188-200`; draft line 125). stale outputs are excluded from the isolated build (line 136).

## findings

severity scale: **blocker** means the contract as written produces a wrong or misleading result. **required** means a small specification change is needed before handoff. **nit** means an optional refinement.

### f1 — blocker: discovery-table csv is an unlisted consumer of overview evidence

**problem.**
- `composeDiscoveryRows` reads every metric whose `family` is `"overview"` from the overview response (`analysis-discovery.ts:403-406`).
- that covers all of `base` (`analysis-values.ts:271-279`): penalties, territory, 5v5 execution and shootiness, and the ten comparative tiles in the overview preset (`analysis-discovery.ts:109-118`).
- `discoveryCsvRows` (`analysis-discovery.ts:~560`, called from `routes/league.tsx:400`) emits `analysisCsvRow`. that row includes `reference_panel`, `coefficient_support`, `paired_evidence`, `mechanism_detail`, `territory_detail` and `goalie_detail` (`analysis-history.tsx:318-391`).
- line 107 lazy-loads only for peer expansion and the distribution csv. it says "full distribution/card/detail csv columns retain their existing meanings" and omits the discovery csv.

**failure.** after the hard cut, a discovery export of the overview or penalties preset writes empty evidence columns. that is exactly "loading detail looks like absent scientific evidence", which line 42 forbids.

**fix.** add the discovery csv to the lazy consumers. use the same fixed route mapping and the same publication/projection verification before joining. measure its cost, since the overview preset can need four full families. the alternative is to declare an explicit `not_loaded` column contract, but that changes an existing export's meaning.

### f2 — blocker for a7: delivery runtime and command placement are unspecified

**observed (read-only).**
- pid 91302 serves `app/dist/node/server/main.js`, compiled on 30 oct from schema 8 code, against `…/local/publication/active.sqlite`.
- the primary checkout's source is the schema 12 head, and `app/node_modules` is empty. the live process has its modules in memory, but schema 8 cannot be restarted from the primary checkout as it stands.

**holes.**
- (a) **rollback runtime.** step 7 (line 165) says "restore exact schema 8 bytes with its matching code" and assumes that runtime exists. the rehearsal (line 164) builds one at an alternate port but does not require it to be retained. fix: before stopping port 3000, require a ready rollback runtime with an exact path, retained through activation. that is either the rehearsed `0e0f569` checkout with `npm ci` and a build, or a reinstalled primary. it must be smoke-started at an alternate port. note that `npm ci` may need registry or cache access.
- (b) **where `stage`/`activate` run.** the old primary build lacks these commands. line 149's "build before either runs" would rebuild primary `dist` under the running server. that replaces the `dist/client` assets it serves, so the "old site remains usable" claim fails. fix:
  - run `stage`/`activate` from the frozen isolated build.
  - make "build before" an operator precondition, not an implicit build inside the npm script.
  - rebuild primary only after stop, with `npm ci` into an empty `dist/node`. line 136 currently scopes emptiness to the isolated checkout, but a non-empty primary `dist/node` would carry a different file set, so startup would reject the receipt.
  - state that a startup digest mismatch takes the rollback path.

### f3 — required: the validator digest must bind the code that actually ran

**problem.** line 138 brackets the 56-minute check with before/after database hashes but says nothing about the validator. if the digest is computed at issuance, a rebuild in the same checkout during the run yields a receipt naming code that did not run.

**fix.** compute the validator digest, node version and lockfile digest at process start. recompute them before the exclusive write and reject on change. this costs milliseconds.

### f4 — required: the overview-vs-detail runtime checks deep-compare full bodies

**problem.** two client checks deep-compare full detail against the overview, including evidence:
- `checkOverview` (`client.ts:336-383`) compares overview members to detail families.
- `scalarRows` (`client.ts:719-744`) compares the whole `AnalysisDatum`, including the evidence fields, with `equal(selected, peer)`.

**failure.** with summary members, both throw for every profile and comparison.

**fix.** line 105's "shared with equivalence checks" implies the fix but does not say it. name both call sites. each must compare `project(full)` with the summary, and datum equality must cover scalar, support, reference and semantic fields with evidence load state excluded. this is low risk, because the first fixture run would catch it, but the join semantics belong in the contract.

### f5 — required: territory correction preconditions and inputs

- **(a) prove the old text before replacing it.** the summary occurs twice: `limitations[5]` and `assessment.findings[0].summary` (`mechanism_composition.py:342-353`). mirror `_REFERENCE_XG_OLD` (`execution_composition.py:116`). require both donor strings, per year, to equal the current composition rebuilt from the sha-bound diagnostics before replacement. otherwise drifted text could be silently overwritten. the receipt's "exact changed JSON paths" records where, not what was proven.
- **(b) read the diagnostics without reconstruction.** the diagnostics live in the bound `reference.json` (method input role `derivation`, `mechanism_composition.py:333-335`). read that document strictly by its bound sha. do not call `read_territory_reference`: it recomputes variants from state (`territory_state.py:595-597`), which is numerical reconstruction outside metadata-only scope.
- **(c) give the sensitivity limits one owner.** "exceeded hazard sensitivity" needs limits that are not stored in the diagnostics. `compare_territory_variants` keeps status and maxima only, and its limits are literals at `territory.py:482`, duplicated as `diagnostic_limits` at `territory.py:41`. the formatter must use one existing owner, either the bound design's `diagnostic_limits` or a constant shared with the comparison, not a third copy.
- **(d) record that the ledger's evidence copy is a snapshot.** the xg pattern appends the receipt to `method.evidence` and `findings[0].evidence` (`execution_composition.py:51-53`). the ledger method copied territory's evidence at composition time (`value_composition.py:293-295, 324-327`), and line 115 keeps it byte-identical, so it will lack the new receipt. afaict no validator requires the ledger's evidence to contain all of the upstream evidence (`ledger-publication.ts:431-436`). the contract therefore holds, but the spec should state that the copy is a composition-time snapshot and that no check may require containment.

### f6 — required: "compare every inherited record to the donor" needs an artifact and a method

**problem.** line 117 is ambiguous about what is compared.
- successor results against donor results is cheap: member descriptors and bytes, already in the correction receipt.
- the new 32 gb candidate against the pinned 32 gb candidate is a heavy full read of both files.

**fix.**
- name the method, for example a per-table ordered row comparison or digest.
- name the exclusions: the `publication` row's identity, provenance and timestamp fields, and the three `territory-v1-11-*` rows in `analysis_method`.
- schedule it as a heavy macbook command with measured time.

otherwise it will be skipped or improvised.

### f7 — nit: receipt field ambiguities

- **(a) where the runtime and lockfile go.** line 136 folds the node version and lockfile digest "with" the file digest, yet the receipt carries them as separate fields. keep `validator.sha256` over files only and compare the three fields separately. that supports line 44's goal of an operator who can tell code, runtime and lockfile mismatches apart.
- **(b) the `checks` object.** it can only ever read `passed`. its four keys also do not match the code's stages: cross-record, repeated-fact and ledger checks all run inside `validateAnalysis` (`analysis-publication.ts:777-779, 915-975`). either drop it or map each key to a named function.
- **(c) "catalog identities".** line 140 compares "metadata/catalog identities" against the receipt, but the receipt carries no catalog identity. name the compared fields instead: `publication_id`, `schema_version`, `purpose`, `available_seasons`.
- **(d) the concurrent-writer rule.** "no writable concurrent owner" (line 138) cannot be checked with ordinary stat calls. state it as an operator precondition, evidenced by the before/after identity.

### f8 — nit: overview projection clarifications

- **(a) penalties.** replace "unused recorded subrecords" (line 101) with the exact omission: `recorded_drawn`, `recorded_taken`, `recorded_served` and `evidence`. overview consumers use only the four estimates, support and `method_id` (`analysis-values.ts:452-470`). `recorded_*` is used only in selected detail (`analytical-details.tsx:822-830`).
- **(b) row cardinality.** today, a present person without exactly one row fails the read (`publication.ts` `readSummary`, `rows.length !== 1`). the seasonal keyed join must keep that: a missing or duplicate row for a provided family is a read failure, never absence.
- **(c) ledger coverage years.** the full validator sets coverage only for provided ledger references (`analysis-publication.ts:915-975`). serving should mirror that rather than assume "three annual reference envelopes" (line 123). fixtures may publish fewer seasons.

### f9 — nit: unnecessary work in `restore`

**problem.** `restore` (line 149) copies 32 gb from `previous` to `incoming`. rotation then overwrites `previous` anyway (current code: `publication-cli.ts`, rename `active`→`previous`).

**fix.** verify the previous pair's receipt in place, then swap by renaming. that reaches the same end state with no copy and no extra space. alternatively, define `restore` as `stage --candidate DIR/previous.sqlite` followed by `activate`, with no separate code path.

**note.** until a second schema 12 activation, `previous` is schema 8 with no receipt, so `restore` can only be proven on fixtures.

## disposition

**changes required.** fix f1 and f2 before handoff. f3–f6 are small required amendments. f7–f9 are optional refinements. root should resolve these and request a targeted second pass. this review does not establish software, data or delivery acceptance.
