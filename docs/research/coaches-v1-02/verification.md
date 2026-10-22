# dated coaching verification

2026-10-22. [specification](../../specs/v1-02-dated-coaches.md) · [assignment](../../plan.md#current-boundary).

## status and meaning

software_status: pass_detached. acquisition_status: not_run. real admission: incomplete. real resolved-name coverage: not measured. real identity review: not started. all required real-source acceptance remains open.

the hdd was absent at execution start. the user explicitly requested detached development until it is connected. no live right-rail request, five-season selection or real coaching artifact has been produced in this work. the empty real identity catalogue assigns nobody; synthetic identities are separate fixture evidence.

the quantity remains the head coach reported by nhl for a game and side, retrieved at the recorded time. it does not establish bench attendance, career credit, causal influence or information available before puck drop. software verification cannot establish historical coverage or scientific support.

## scope and preservation

implementation uses `/Users/nnandal/Documents/code/hockey-stats-v1-02`, branch `implement/v1-02-dated-coaches`, based on `ee9d389`. the primary checkout's unrelated edits and the v1-01/13 worktrees are outside this change. the original full specification and source-access issue were copied from the primary checkout without editing that checkout.

before verification, `/tmp/hockey-v1-02-protected.json` recorded hashes and mtimes for 483 existing core fixture/reference files and the active publication. all remained unchanged at closeout; [the cleanup/preservation receipt](closeout.json) records the result. no application build, serving restart, publication/schema edit, fitting or core recapture is assigned here.

## verification receipts

| boundary | evidence | result |
|---|---|---|
| capture cli | [red](capture-red.json), [green](capture-green.json) | real `npm run capture` with a controlled fetch transport: one request, exact binary bytes/hash, manual redirects, 302/403 bodies, transport/body-read failures, no request into occupied output, default six-source and landing semantics |
| preserved core | [original/current comparison](frozen-source-reads.json), [receipt reread](core-receipts.json) | all 37 original fixture interpretations equal; all five 1,312-game fixture-derived inventories load; all 222 core receipts read under the final validator |
| binder | [red/green](binder-red-green.json), [red log](binder-red.log), [green log](binder-green.log) | four integration groups pass after tests first failed on the absent module |
| independent acceptance | [red](independent-red.json), [green](independent-green.json) | 15 groups pass; 49 synthetic games, 98 slots, two seasons and four identities |
| independent source/systems review | [additional checks](source-review.json) | eight targeted checks pass against the final source hash |
| retained fixture run | [exact output identity/resources](fixture-output.json), [inputs and expected facts](../../../fixtures/coaches/README.md) | production module command and detached reader pass from retained relative-path fixtures |

final `coaches.py` sha256: `33a9aff733323d11bd2fd5898f3b30bde5bb02f1fdf799d5f5b6830926275808`. python `3.14.8`; capture cli/typecheck use pinned node `24.21.0`. `tsc -p app/tsconfig.json` passes; no site build is needed for this operator-only change.

the independent checks cover every assignment disposition, global-malformed/context/side precedence, exact/scoped aliases and collisions, stable ids across seasons/teams, distinct similar names, source integrity, closed/resealed records, parent/child context consistency, inventory-only binding, occupied output, duplicate/unknown flags and detached reads with external files/network forbidden. minimal prepared-like records exercise later-consumer purpose/corpus/game/date/side joins; no v1-01 implementation or numerical fit is fabricated.

review repaired invalid receipt http-status acceptance, a malformed-url exception, bool/float aliases and coverage counts, contradictory retained report evidence, and the initially absent operator summary. the shared receipt reader owns status bounds; `strict_json` owns finite json; the binder owns interpretation/identity/coverage; the detached reader validates without mutating records. the operator summary reduces stored coverage rather than recalculating game facts.

the retained fixture output is `/Users/nnandal/Documents/code/hockey-stats-local/coaches-v1-02/fixture-20261022/coaches.json`: 47 requested games, 46 complete captures (45 2xx/one non-2xx), one incomplete request, two unacquired games, 27 parsed games, 13 context conflicts, five malformed bodies and 36/98 resolved slots. this is deliberately adverse synthetic coverage, not a real coach estimate. total output is 208,716 bytes; the artifact's member-byte receipt excludes `coaches.json` as specified. [the receipt](fixture-output.json) records exact hashes, wall time and peak memory. its implementation identity truthfully records the base commit with dirty source; final source hashes establish which implementation was exercised.

temporary tests/controllers and the task dependency symlink are removed after final green; retained receipts describe historical `/tmp/` execution paths, not lasting commands. no test-only dependency was added. cheap fixture output remains separate from source fixtures; no expensive output was created locally.

reproduce from the repository root, using an available pinned environment and a fresh output:

```sh
PYTHONPATH=analysis/src analysis/.venv/bin/python -m hockey_stats.coaches \
  --selection fixtures/coaches/selection.json \
  --identities fixtures/coaches/identities.json \
  --out /tmp/coaches-fixture-new
```

the public reader is `read_coaches(path, "fixture")`; `"real"` rejects fixture artifacts. the existing capture command accepts `--source right-rail --out NEW_DIRECTORY`; retries preserve the predecessor and use another explicit directory.

## real execution still required

1. connect the hdd and verify the five ordered manifest hashes in the [03n input table](../chance-03n/protocol.md#evidence-and-immutable-inputs). freeze one inventory game per season, preferring existing fixtures.
2. run those five probes with the production capture command into fresh external directories. preserve every original receipt/body. inspect both names, all supplied context and the actual report-link paths/types; pin those paths and expected facts before expansion.
3. expand only usable seasons within the 6,560-request initial bound. stop each season on its first 403/429 or two consecutive transport failures; defer unattempted games with explicit reasons. replacement attempts require explicit selection and new directories.
4. review all available exact names and team/year distributions, retaining source anchors and explicit ambiguity. independently check each season, one permanent change and one temporary-absence case; corroboration cannot fill missing feed names.
5. bind and independently reconcile 6,560 games and 13,120 side dispositions, requests, hashes, coverage, retrieval range, bytes and resources. verify the final artifact detached. record partial acquisition honestly if access fails; all-unavailable rows cannot establish a usable coaching feed.

[the source-access issue](../../issues/coach-source-access.md) tracks these unresolved source obligations. there is no fallback feed, automatic retry controller or runtime admission switch.

## accepted costs

one fresh supplemental directory per request preserves previous evidence and requires explicit capture selection. exact aliases require manual review and remain independent of teams/seasons. valid source names can support manually reviewed aliases even when that source has conflicting game context; the conflicted game itself never resolves either assignment. the compact reader validates stored relationships without reopening original inputs; later numerical consumers must additionally compare game/date/side and corpus identities with their own preparation. candidate report-link parsing has fixture proof only until a successful original pins the actual feed structure. a failed bind can leave a partial fresh directory, but never a successful `coaches.json`; repair the cause and select a new output.
