# real downstream preparation

historical, superseded by [the replacement product recipes](replacement-product-recipes.md). the old commands, paths and preparation receipt below are preserved evidence, not current launch instructions; accepted real input pins change only after the replacement artifacts are accepted.

status: unexecuted recipes only. the first real annual is running; every real state digest remains pending acceptance. no state, source-game or array was opened for this preparation, no selection was written, and no downstream command was launched. [bounded metadata receipt](receipts/real-downstream-recipes-preparation.json) binds the actual three small accepted metadata files. the existing [inputs](inputs.json) own prepared, coach and execution target pins; their large files were not reopened.

fixed inputs:

| input | absolute locator | sha256 |
|---|---|---|
| accepted execution exchange | `/Volumes/Expansion/hockey-stats/runs/execution-v1-06-20261026-01/real/results/manifest.json` | `cab50e44334924284e11b84f744b1bdaac8b337f00f53334892c91ac5683d3d5` |
| original observed selection | `/Volumes/Expansion/hockey-stats/runs/execution-v1-06-20261026-01/real/observed-selection.json` | `5b6e3f0b8ae736260070549677a59bbf648ebab9a916729333eeb577611331e9` |
| execution score selection | `/Volumes/Expansion/hockey-stats/runs/execution-v1-06-20261026-01/real/current-04/scores-selection.json` | `2f8fcb59d80cbd59c18b11d3d0c9dade850559754c1b19af907ea0effa094ec1` |
| preparation, reused pin | `/Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02/manifest.json` | `63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c` |
| coaches, reused pin | `/Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json` | `102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0` |

the accepted exchange's three corpus bindings match the original observed selection exactly. the five score paths/digests match `inputs.json`; no target was rescored or rediscovered.

all planned states are fixed paths under `/Volumes/Expansion/hockey-stats/runs/spatial-v1-08-20261031-01/real/`: `20212022/manifest.json`, `20222023/manifest.json`, `20232024/manifest.json`, `20242025/manifest.json`, `20252026/manifest.json`. **every accepted digest is pending**, including the running first year. `var/v1-08-product/real/prepare-selection.py` contains five explicit `None` placeholders and refuses before any state read or selection write until root supplies all five accepted hashes. then its ordinary exclusive write produces `real/states-selection.json` in the existing strict shape. root still separately releases selection, composition and publication after the required head/probe acceptance; software completion is not scientific admission.

from `/Users/nnandal/Documents/code/hockey-stats-v1-08`, the prepared commands are:

```sh
PYTHONPATH=/Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/src \
/Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/.venv/bin/python \
  -m hockey_stats.analysis_cli summarize --family spatial \
  --results /Volumes/Expansion/hockey-stats/runs/execution-v1-06-20261026-01/real/results \
  --states /Volumes/Expansion/hockey-stats/runs/spatial-v1-08-20261031-01/real/states-selection.json \
  --out /Volumes/Expansion/hockey-stats/runs/spatial-v1-08-20261031-01/real/results
```

```sh
PYTHONPATH=/Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/src \
/Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/.venv/bin/python \
  -m hockey_stats.analysis_cli publish \
  --observed /Volumes/Expansion/hockey-stats/runs/execution-v1-06-20261026-01/real/observed-selection.json \
  --results /Volumes/Expansion/hockey-stats/runs/spatial-v1-08-20261031-01/real/results \
  --out /Volumes/Expansion/hockey-stats/runs/spatial-v1-08-20261031-01/real/candidate
```

`var/v1-08-product/real/summarize.sh` and `publish.sh` wrap these exact commands with ordinary `/usr/bin/time -l`, exclusive logs and exit files, rejecting occupied destinations. they remain separate unexecuted scripts, not a pipeline or scheduler. the real candidate is distinct from both accepted v1-06 candidates and the active/previous publications. no activation command is included.

`var/v1-08-product/real/server.sh` likewise remains unexecuted. it selects only `/Volumes/Expansion/hockey-stats/runs/spatial-v1-08-20261031-01/real/candidate/player-analysis.sqlite`, pinned node `24.21.0`, built `app/dist/node/server/main.js` and isolated port `3399`. its prepared `real/detached.sb` keeps the source/coach/execution/local-alias denials, denies the whole fixture03 tree, the five real annuals, real results/selection and candidate sidecars, and permits the intended real database and built assets. profile runtime controls, candidate identity, actual build hashes and port availability must be bound at the eventual root release; no sandbox or server check was run now. scripts received syntax-only review, without running their commands.

## remaining product evidence

the original one/two-player api receipts remain narrower historical evidence. root authorized a focused extension of the existing temporary `live-check.ts`; [the expanded actual pair receipt](receipts/fixture03-api-two-player-expanded-green.json) now checks both players across all three years, their exact quartets/support, 48 returned map rows and native/display/density integrals. twelve common scales are independently reconstructed over both players and both 5v5 roles, as the wire contract requires. an in-memory corruption of the second returned player's integrated value is rejected. only the actual two-player target was rerun; no new harness or production change was introduced.

concrete remaining gaps are the actual browser journeys and downloads: spatial discovery filtering/sorting, all eight selected views, same-position/mixed-position comparison, history gaps and actual scalar png/csv; normal/narrow/native-200% layout and detached browser evidence remain pending while cua is unavailable. api row generation does not prove a downloaded csv/png or rendered content. the regular target pair exercises captured prior-only zero-time magnitudes; a separate api pair now exercises two absent fixture years, and the actual discovery-consumer check verifies all eight values/filter/sort behavior. neither proves an entrant or traded-player browser journey. no final-year fixture skater has two teams, so the traded case needs real data when available or an explicitly labeled fixture for interface behavior. root's existing-operator disposable rollback passes; its receipts preserve both exact hashes without any serving mutation. no extra test campaign is proposed; select the remaining cases in the eventual bounded browser/real acceptance pass.
