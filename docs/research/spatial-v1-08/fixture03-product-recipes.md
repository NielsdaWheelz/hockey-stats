# fixture03 product recipes

status: root accepted the actual five-state fixture03 chain, three final probes and composition. the consumed selection is sha256 `134c452211cdc966d3b54c702b8f3d0b2372a2da9e553a3f0773f8037b7e32a5`; accepted results are `2d2974937637e7c32dbebd6c9c43bfab05a39299f2823e116008e8d319b90b0e`. the single released publication has now exited zero with producer verification passed; independent publication review and application/api/browser acceptance remain separate. no server or activation has been launched. [completion](receipts/fixture03-publication-completion.json) · [acceptance ledger](verification.md). the original [preparation receipt](receipts/fixture03-product-recipes.json) remains historical; the recorded commands are not instructions to repeat occupied outputs.

source bindings:

- accepted execution fixture exchange: `/Volumes/Expansion/hockey-stats/runs/execution-v1-06-20261026-01/fixture/current-02/results/manifest.json`, sha256 `499acc1f9363d136d7e148d12af045fcf17b7f27b018b2e11612447ccb992d8d`.
- original observed selection: `/Volumes/Expansion/hockey-stats/runs/execution-v1-06-20261026-01/fixture/observed-selection.json`, sha256 `24cda3b5a287569c01694718a504a45824ce8cb4d9ec08b81fd9643bd3871a37`. its three corpus digests exactly match the accepted exchange's observed bindings; its absolute original corpus paths remain unchanged.
- common preparation sha256: `603ee00dfe069c99eb5fda3bda9f5d60ea9969fa3820a1df3b5bfcf16cefb7df`; coach artifact sha256: `d876634925f7abaabc5e1300efd3a7837511a74628dd98943ffc682b69d7602c`.
- exact five execution targets: `fixture/current-02/scores-selection.json` under the execution campaign above, sha256 `58f7820080e6dc283af7ba6b9731122c24803523407e6a23857029b327a8f44d`.
- accepted fixture03 states, consumed in this order: `20212022` → `a0fc5f45458bc48d5e03ab582d7cc4669d69a38d702997514a7dddd1093944dd`; `20222023` → `04bae620926b2ce11733b63e64d942b87caec7c4f778411195a581f679b771da`; `20232024` → `d6b4661c7f6a94d7b86f1666197d770e20c45114e1aa5d17eebe63b87b6046af`; `20242025` → `e6980f33e35ff4cf68679a2b504f5251bf06a176ac0309c4fb8ee9713cf47244`; `20252026` → `93bf863b93421b82d15868b5fc94bfde355fddd164dfc5ddb81d97c3a3014f46`. the helper now pins every identity; the already-consumed selection was never rewritten. [reconciliation](receipts/fixture03-selection-reconciliation.json).

from `/Users/nnandal/Documents/code/hockey-stats-v1-08`, the exclusive selection helper enumerates the five fixed paths `/Volumes/Expansion/hockey-stats/runs/spatial-v1-08-20261031-01/fixture03/<season>/manifest.json` and writes the existing strict selection shape. run it only after root accepts the complete chain:

```sh
analysis/.venv/bin/python var/v1-08-product/fixture03/prepare-selection.py
```

the exact composition command is:

```sh
PYTHONPATH=/Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/src \
analysis/.venv/bin/python -m hockey_stats.analysis_cli summarize \
  --family spatial \
  --results /Volumes/Expansion/hockey-stats/runs/execution-v1-06-20261026-01/fixture/current-02/results \
  --states /Volumes/Expansion/hockey-stats/runs/spatial-v1-08-20261031-01/fixture03/states-selection.json \
  --out /Volumes/Expansion/hockey-stats/runs/spatial-v1-08-20261031-01/fixture03/results
```

`/bin/sh var/v1-08-product/fixture03/summarize.sh` wraps that command with `/usr/bin/time -l`, exclusive log and exit records. the existing writer performs strict result reading before finalization; do not add a redundant full exchange scan. the temporary full composition checker is retained for root to select if independent saved-row acceptance needs it.

after root accepts composition, the exact publication command is:

```sh
PYTHONPATH=/Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/src \
analysis/.venv/bin/python -m hockey_stats.analysis_cli publish \
  --observed /Volumes/Expansion/hockey-stats/runs/execution-v1-06-20261026-01/fixture/observed-selection.json \
  --results /Volumes/Expansion/hockey-stats/runs/spatial-v1-08-20261031-01/fixture03/results \
  --out /Volumes/Expansion/hockey-stats/runs/spatial-v1-08-20261031-01/fixture03/candidate
```

`/bin/sh var/v1-08-product/fixture03/publish.sh` records ordinary time/resource/log/exit evidence. publication already performs integrity, foreign-key, conservation and independent readback checks. neither command activates a database or changes an accepted predecessor.

root owns the actual application verification. the final prepared profile is sha256 `42c21d266fd7ab0d7b83893fa4d84c17b765eddd1005fabcb919c946352f84d6`; [fresh controls](receipts/fixture03-detached-controls-final.json) bind unchanged before/after profile digests, 27 paired actual input denials and built-asset access. [candidate access](receipts/fixture03-candidate-access.json) adds the finished database positive control. neither establishes runtime acceptance. after the checkpoint wording patch, run pinned node `24.21.0` typecheck and build once, then confirm port `3398` is unused. `/bin/sh var/v1-08-product/fixture03/server.sh` starts the built application against only the new candidate under the prepared sandbox profile. the profile denies original preparation/coaches, execution inputs, all five spatial states, composed exchange, analytical source, source fixtures and research documents. it permits the candidate and built application. before launch, paired one-byte control reads must succeed outside the profile and fail under it for existing concrete denied inputs; syntax acceptance alone does not prove detachment.

the equivalent server command is:

```sh
/usr/bin/sandbox-exec -f var/v1-08-product/fixture03/detached.sb \
/Users/nnandal/.local/share/mise/installs/node/24.21.0/bin/node \
app/dist/node/server/main.js \
  --publication /Volumes/Expansion/hockey-stats/runs/spatial-v1-08-20261031-01/fixture03/candidate/player-analysis.sqlite \
  --port 3398
```

the server startup includes the existing strict detached reader. retain its actual process identity, startup time, memory and selected request costs; wait for actual readiness without a fixture timeout or automatic relaunch. use the preserved live target checker with an all-three-year actor pair:

```sh
PATH=/Users/nnandal/.local/share/mise/installs/node/24.21.0/bin:$PATH \
app/node_modules/.bin/tsx var/v1-08-product/live-check.ts \
  http://127.0.0.1:3398 8475726 8476462
```

this checks actual three-year player scalars, exact selected quartet/csv receipts and one/two-player complete/effect map api closure. toffoli/hamilton are an existing three-year forward/defense fixture pair. root separately inspects discovery sorting/filtering, same-position and mixed-position comparisons, low-minute/entrant/traded/prior-only/gap cases, actual browser downloads, ordinary/narrow/native-200% layouts and a detached browser. no api or synthetic-interface check substitutes for that evidence. stop only the recorded owned server process after the selected checks; preserve candidate, logs and temporary checks until full acceptance.

checkpoint content correction, applied in `3f9f90c`:

> spatial support reason counts are games with a located excluded segment, counted once per reason code; codes can overlap within a game.

the method limitations and existing `spatialSupportMeaning` now carry this sentence through selected detail, csv and scalar png. a missing roster projection has an empty reason-count list; its unavailable explanation and unquantified gap retain the missing-evidence meaning. no schema or wire field changed. focused red→green checks pass all thirteen affected 5v5 rows against the strict schema, method wording and selector/csv preservation; pinned typecheck passes. no full synthetic exchange rebuild was run.
