# v1-01 shared-evidence verification

status: detached implementation, readback and independent review passed; real-corpus acceptance is paused pending the external drive. the user assigned the full [specification](../../specs/v1-01-shared-evidence.md), then instructed completion of available work followed by a pause. fixture completion does not clear the five-season, 6,560-game acceptance boundary. [remaining acceptance](../../issues/evidence-v1-01-acceptance.md).

implementation: branch `v1-01-shared-evidence`, worktree `/Users/nnandal/Documents/code/hockey-stats-v1-01`. three non-astra implementers covered source/support, factual context and artifacts; root, peer reviewers and a separate claude session challenged the boundaries. the primary checkout and serving files were not modified by this work.

## delivered contract

`analysis_data` owns `prepare_analysis`, `prepare_game`, `read_prepared`, `read_prepared_game`, `read_prepared_people` and `read_prepared_coverage`. its public readers consume the prepared artifact without opening original sources. source support, context construction and closed record validation remain package internals. existing native, observed and research owners retain their separate supported populations.

`hockey-stats-analysis prepare --selection FILE --out DIR` requires both flags exactly once. selection identities, corpus/capture receipts, member hashes, fixed records, links, units, source availability and count/time support are checked explicitly. output must be new; the manifest is written last. no retry engine, compatibility schema, acquisition, fit, season-rate reducer, database or application change was introduced.

all-strength membership coalescing is shared with the exact old 5v5 projection. event evidence survives missing elapsed membership. the new ordinary-attempt mask owns matched count/time exclusions; consumers add only their own restrictions. chunks partition retained physical segments. event prefixes are source-ordered and pre-event; elapsed prefixes use preceding half-open time and exclude same-clock actions.

the closed segment schema represents exact state through the four membership cardinalities; source status remains in `game.ledger`, `game.inputs` and linked `native_intervals`, while matched-rate disposition remains in `ordinary_attempt_support`. retained `identity_observations` remains conditional under the [03k contract](../features-03k/ledger.md#exact-shared-fields-and-history-windows); the validator checks both its required presence on unresolved joins and equality to the retained original arrays.

## selected evidence and resources

[fixture selection](selection-fixture.json), [fixture manifest](fixture-manifest.json), [coverage](coverage.json), [source freeze](source-freeze.json) and [independent facts](independent-facts.json) identify the final artifact. its local path is `/Users/nnandal/Documents/code/hockey-stats-v1-01/var/v1-01-root/root-r6`. source captures are the existing committed originals. no new broken-game download or replacement fixture was needed.

| season | inventory | selected / all six sources parsed | original events | attempt facts | resolved physical seconds | included seconds | excluded seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
| `20212022` | 1,312 | 7 | 2,192 | 824 | 25,619 | 25,399 | 220 |
| `20222023` | 1,312 | 5 | 1,497 | 596 | 18,595 | 14,984 | 3,611 |
| `20232024` | 1,312 | 6 | 1,948 | 715 | 21,887 | 21,887 | 0 |
| `20242025` | 1,312 | 9 | 3,044 | 1,092 | 29,275 | 27,966 | 1,309 |
| `20252026` | 1,312 | 9 | 2,978 | 1,101 | 25,663 | 14,597 | 11,066 |
| total | 6,560 | 36 | 11,659 | 4,328 | 121,039 | 104,833 | 16,206 |

these are selected-fixture facts, not full-season coverage. parsed source availability does not establish complete records, matched elapsed support or model applicability. coverage separately records 11,949 unresolved known seconds and one game with unknown horizon; an unknown duration is not zero missing time. exact-state physical time, directed team time, actual skater/goalie slot time, source kinds/outcomes, report-only records and every completeness denominator remain in the coverage receipt.

final preparation measured 152.38 seconds wall time, 1,038,254,080 peak resident bytes and 1,939,136,248 output bytes excluding the manifest. python was `3.14.8`; source content hash is `b2ac65f8e6dd7c1faec2bade6a4dc446646c322ca17a0e5182d3d80d5a92379f`; policy hash is `28624b42c78254a0000c97205b73a5ff5ff59fbc237264c77d4cd4e339178795`. the manifest records the input-contract snapshot commit and a dirty working tree; content hashes identify the verified implementation precisely. fixture costs do not establish real runtime, peak memory or drive capacity.

## checks and adversarial repairs

| boundary | evidence |
|---|---|
| input and artifact | temporary cli-to-public-reader test was red before implementation, then green through refactors. strict command/selection, malformed member, refreshed-hash semantic corruption, missing/incomplete output and occupied-output cases are in [checks](checks.json). original-source reads and socket connections were denied during detached reader checks |
| source and support | all 37 existing capture fixtures preserve native reconstruction, old 5v5 segments and old conflict predicates exactly; [source fixtures](source-fixtures.json), [peer review](source-review.json). all 36 selected games retain every original event exactly by source index and every native interval/report row; partitions and independent score/unit arithmetic are checked in the final facts receipt |
| context and labels | synthetic actual 3/4/5/6-member arithmetic and partial sums, source-ordered same-clock/goalie prefixes, no skipped successor, stop cutoffs 0/2/3 seconds, reattempt cutoffs 0/5/6 seconds, unresolved kinds, first-action censoring, closing goals, valid terminals versus bare eof and direct missing-history locators passed. [future invariance](future-invariance.json) records byte-identical earlier predictor facts after later trusted-input mutations; raw admission is a separate checked boundary |
| dated identity | [seven actual multi-team people](people-facts.json) match original dated teams/sweaters, latest supported roster names, positions and named bio observations; february-1 age references and unknown effective times/height units are explicit. conditional conflicting-join evidence and malformed date/age/sweater links are checked |
| preserved consumers | [full canonical before/after results](preserved-consumers.json) match exactly through existing observed reducers on all three displayed 1,312-game seasons: hockey facts, support, personal/spatial/deployment quantities and reasons. [36 research/core fixture projections](research-projections.json) also match exactly after the final repair; no historical fit or application rebuild was required |
| downstream readiness | [actual reader exercise](downstream-readers.json) selects ordinary execution event facts, all-strength descriptive states and matched elapsed chunks in `2025020001` and `2025021094`, with original sources/network denied. it neither fits nor establishes a downstream recipe's eligibility |
| real handoff | pending: all 6,560 selected games, all partitions, complete coverage reconciliation, real original-source spot checks and real resource measurements require the absent drive |

independent review repaired outcome-dependent episode availability at the focal row; uncertain participation fabricated across source gaps; incomplete physical-action label semantics; goalie workload taint from known empty nets/own goals; unresolved support mislabeled ambiguity; unassigned interior attempts left in included runs; abbreviated season identities; missing raw block coordinates; and strict source/member consistency gaps. [final independent review](independent-review.md) separates computational findings from operating costs and scientific claims.

representative checked cases:

- `2022020822`: the incoming-lineup goal at `/plays/93`, period 2 clock 116, retains pre-score 0–1; assigned following elapsed play has score 1–1.
- `2024021235`: 292 events and 110 attempts survive absent shift membership; zero resolved segments and 110 `membership_unavailable` reasons. event evidence supplies no denominator.
- `2024020186`: union exclusion is 49 seconds for this new all-strength mask: the old 46-second 5v5 conflict plus a distinct 3-second 6v5 run. the old 02d predicate and exclusions are unchanged; there is no second subtraction of its baseline 132 seconds.
- `2025021094`: the penalty shot at `/plays/164` is outside ordinary matched support; the final ordinary goal at `/plays/304` is retained in actual overtime `[40,41)`, with no invented full overtime.
- `2025020565`: distinct overlapping own rows for `8482684` cannot establish a known physical union. [original locators and expected behavior](../../../fixtures/README.md#v1-01-individual-participation-overlap-check--2026-10-22) retain all rows; 27 clean spans supply 1,564 known seconds, with complete time/start/age/rest withheld. known 5v5 time intersects clean participation and never exceeds known total time. exact duplicates and endpoint adjacency remain valid controls.

## costs, consumer limits and pause

the closed direct-fact json schema repeats located evidence and missing reasons. the measured fixture output extrapolates to hundreds of gb for five seasons; richer real histories may cost more. [storage issue](../../issues/prepared-evidence-size.md) retains the required real measurement and storage-contract decision. an interned representation was not silently substituted for the specified schema.

conservative run exclusions and conflicting individual-component omissions lose usable time rather than invent exact participation. elapsed workload is intentionally piecewise constant. missing history and optional normalized height remain missing. two game-at-a-time passes retain compact prior-game summaries rather than every event in memory. these choices preserve the selected meanings at the cost of support, disk, source rereads and downstream decoding time.

consumer contracts must keep `feature_facts.outcome` and `immediate_outcomes` out of predictors and select named predictor groups explicitly. the reused `prior_shorthanded_side` means the prior side with fewer skaters, including extra-attacker states; it does not prove penalty expiry. verified source order can place review goals after a same-clock stoppage; [episode source-order issue](../../issues/episode-source-order.md) requires an explicit execution-consumer decision about outcome-dependent availability. no causal, calibration, ability or scientific admission claim follows from this implementation.

v1-13 is independent in `/Users/nnandal/Documents/code/hockey-stats-v1-13`, branch `implement/v1-13-typed-publication`. this branch's `analysis_cli.main(argv=None) -> int` exposes only `prepare`: required `command` subparser, no flag abbreviation, existing `cli.Once`, `prepare_analysis(selection, out)`, absolute manifest path on success/0, contract/io/value errors on stderr/1 and argparse errors/2. v1-13 owns `publish`, the combined dispatch/entrypoint and observed-publication cli removal; delivery root reconciles shared edits. neither detached fixture set depends on execution of the other.

temporary tests/controllers and test-only snapshots are deleted after final green; [deletion receipt](test-deletion.json) retains their identities and outcomes. original fixtures, compact checked facts and the final local fixture artifact remain. no persistent harness or dependency was added.

the ready [real selection](selection-real.json) fixes all five 03n paths/hashes. after the drive is available and this work resumes, run from the worktree with a new external output directory:

```sh
uv run --project analysis hockey-stats-analysis prepare \
  --selection docs/research/evidence-v1-01/selection-real.json \
  --out /Volumes/Expansion/hockey-stats/prepared/evidence-v1-01
```

then complete the [remaining acceptance](../../issues/evidence-v1-01-acceptance.md), including every public game/people/coverage read, original-source reconciliation and actual downstream exercise. the command is preparation, not the whole acceptance procedure. the [plan](../../plan.md#current-boundary) owns the requested pause and resumption.
