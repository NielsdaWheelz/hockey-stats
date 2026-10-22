# synthetic dated-coach evidence

all files in this directory are constructed fixtures, including the nhl-shaped bodies, urls and capture receipts. none is an original upstream response. `selection.json` has `purpose: "fixture"`; `identities.json` is separate from the empty real catalogue under `analysis/data/`.

49 games and 98 game-team slots span two synthetic seasons, with four explicitly assigned identities. `expected.json` records independently chosen assignment statuses. the examples cover exact case/spacing/accents, one-sided missingness, malformed structures, source identity conflicts, explicit unacquired/failed/non-2xx dispositions, scoped ambiguity, the same identity across teams/seasons, and distinct jon/john identities. report examples exercise candidate guarded paths; they do not establish the actual feed schema.

the two corpus manifests contain inventory/ledger records only. their relative references and the selection's explicit capture keys allow the production binder to run without game envelopes, the hdd or network. original six-source game bundles remain under `../captures/`; these synthetic files are supplemental contract examples.

from the repository root, with the pinned python environment available:

```sh
PYTHONPATH=analysis/src analysis/.venv/bin/python -m hockey_stats.coaches \
  --selection fixtures/coaches/selection.json \
  --identities fixtures/coaches/identities.json \
  --out /tmp/coaches-fixture-new
```

choose a fresh output outside this fixture directory. the successful example reports 47 requested games, 45 captured 2xx responses, one captured non-2xx response, one incomplete request, 27 parsed games, 13 identity conflicts and 36 resolved slots. five bodies are globally malformed; two games were explicitly unacquired. totals describe these synthetic cases only. inspect unresolved rows and exact input/member hashes in the output.

[verification](../../docs/research/coaches-v1-02/verification.md) retains the red/green, independent review and preserved-core receipts. temporary drivers were removed after verification; the production binder and detached reader are the reproduction interfaces. full real-source acceptance remains pending.
