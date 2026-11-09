# first real goalie annual — held command

status: **HELD**. command preparation only; no real fit, source replay, candidate command or output directory has been started here. root releases execution after fixture acceptance and the sibling v1-17 heavy command has exited. [the spec](../../specs/v1-07-goalie-continuation.md) owns the numerical boundary.

run root: `/Volumes/Expansion/hockey-stats/runs/goalies-v1-07-20261108-01`. fit `20212022`, with no predecessor and no final-year probe. retain the original completed baseline. the v1-17 compatible composition parent is selected later; it is not a fit input.

## pins and environment

all paths below are relative to `/Volumes/Expansion/hockey-stats`. these expected digests come from the assigned spec and accepted execution receipts; this command preparation did not repeat their source/member validation.

| role | path | sha256 |
|---|---|---|
| preparation | `prepared/evidence-v1-01-02/manifest.json` | `63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c` |
| coaches | `runs/coaches-v1-02-20261022-01/coaches-01/coaches.json` | `102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0` |
| five-year base selection | `runs/execution-spatial-replacement-20261031-01/real/scores-selection.json` | `588376316a8b4d5311a1677bb3f1419f3754854f25dd2a28e09e3e8c000f9450` |
| original combined composition input | `runs/execution-spatial-replacement-20261031-01/real/results/manifest.json` | `a40ca1c0291579b773db22294f26998f154309b2b65926f00f901331ef0b17d5` |
| selected first annual base scores | `runs/execution-spatial-replacement-20261031-01/real/scores/20212022/manifest.json` | `37263bfc650a06f09adc2c64588c19d3b61cd1e9cdb65dc2ba71a8f88ed5ca8d` |

local environment inspected at `2026-11-09T04:52:11Z`: analysis tree `a727a28b49624f41c70ed26fa0dc6abe6a430bc3`, clean analysis subtree, python `3.14.8`/arm64, numpy `2.5.3`, scipy `1.18.1`. lockfile sha256 `bae38095f3dea6bdb860501eca311b1c33390c7a1e8b7aae76966572f118acdd`; goalie recipe sha256 `cd57b284183962a5795f0c1b2c15065881be3531a4de46b70a20e163907a97c6`.

numpy reports `accelerate` for blas/lapack, backend version unknown. `OPENBLAS_NUM_THREADS`, `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `VECLIB_MAXIMUM_THREADS`, `NUMEXPR_NUM_THREADS` and `BLIS_NUM_THREADS` were unset. retain the existing environment and record those values at launch. thread count remains backend-managed and unmeasured; no dependency synchronization, backend change or thread tuning belongs to this command.

## release-time preflight

record the actual launch commit and unchanged analysis tree; `git status --porcelain --untracked-files=all -- analysis` must be empty. confirm the prepared entry point, lockfile/runtime and expected pins above. inspect only the small selection/annual manifests and required file hashes; the ordinary fit command owns the one full selected-year source/base-score validation. confirm the first selection entry has season `20212022` and the exact annual path/digest above.

confirm no other heavy command is running, the external mount exists, and both the annual destination and log are absent. create only the existing run's `real/states` and `real/logs` parents after release. leave the annual destination to the command. retain one-heavy-command execution within the existing 64 gb envelope; actual first-year cost is measured, not projected from fixtures.

## direct command after root release

```sh
cd /Users/nnandal/Documents/code/hockey-stats-v1-07
/usr/bin/time -l analysis/.venv/bin/hockey-stats-analysis fit \
  --family goalie \
  --prepared /Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02 \
  --coaches /Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json \
  --valued /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/scores/20212022/manifest.json \
  --season 20212022 \
  --out /Volumes/Expansion/hockey-stats/runs/goalies-v1-07-20261108-01/real/states/20212022 \
  > /Volumes/Expansion/hockey-stats/runs/goalies-v1-07-20261108-01/real/logs/fit-20212022-01.log 2>&1
```

baseline controls are `maxiter=10000`, `ftol=1e-15`, `gtol=1e-6`, `maxfun=15000`; zero/current-prior starts deduplicate when equal. no automatic retry follows any exit.

## preflight receipt template and adjudication

replace pending values only after root releases the exact command. the receipt belongs outside the annual artifact, for example `docs/research/goalies-v1-07/receipts/real-first-fit-preflight.json`.

```json
{
  "kind": "goalie-first-real-fit-preflight",
  "status": "HELD",
  "recorded_at_utc": null,
  "launch_commit": null,
  "analysis_tree": "a727a28b49624f41c70ed26fa0dc6abe6a430bc3",
  "analysis_clean": null,
  "lockfile_sha256": "bae38095f3dea6bdb860501eca311b1c33390c7a1e8b7aae76966572f118acdd",
  "recipe_sha256": "cd57b284183962a5795f0c1b2c15065881be3531a4de46b70a20e163907a97c6",
  "input_pin_checks": "pending; five exact roles in the table above",
  "runtime_backend_thread_record": "pending launch-time confirmation of the values above",
  "external_mount_and_fresh_paths": "pending",
  "sibling_heavy_commands_exited": false,
  "season": "20212022",
  "previous": null,
  "expected_final_probe_solves": {"h": 0, "d": 0},
  "output": "/Volumes/Expansion/hockey-stats/runs/goalies-v1-07-20261108-01/real/states/20212022",
  "log": "/Volumes/Expansion/hockey-stats/runs/goalies-v1-07-20261108-01/real/logs/fit-20212022-01.log",
  "native_exit_code": null,
  "activation": false
}
```

record native exit, `/usr/bin/time -l` wall/peak memory, manifest identity, source/target exclusions and separate h/d dispositions. the producer performs canonical saved-state validation. a small saved metadata/history review then checks exact bindings, controls, raw ledgers and absent first-year probes; avoid another source replay or full input scan.

exit `0` requires both baseline heads completed. exit `1` may still leave a valid annual container with an unavailable head and its incoming ledger preserved. inspect that container and failure reasons; preserve completed independent work and all diagnostic records. absence of a completion manifest is incomplete output. neither a nonzero exit nor unknown optimizer accuracy authorizes a rerun, endpoint promotion or base campaign. root adjudicates before releasing another heavy command. fitting establishes no scientific admission or activation.
