# skating feasibility evidence

these are the original, unaltered primary responses from the bounded v1-04 run on 2026-10-22 local time (2026-10-23 utc). `primary/` contains exactly three production-client detail attempts for player `8478402`, one per displayed season. each source leaf retains its original `capture.json` and `body.bin`; `origin:primary` describes their source, independently of artifact purpose. no conditional request, retry, redirect, bulk collection or bypass occurred.

all three requests returned http200 json. the literal speed and burst fields are inspectable, but the bodies do not identify the aggregate's player id, season or regular-season/all-situations coverage. maximum-event name/date/game-type witnesses corroborate individual events; they do not prove aggregate scope. the compact result therefore withholds both measurements as `context_unresolved`, retains the individual raw counters without adding them, and leaves population enumeration/acquisition `unestablished`. `adapter_status:not_observed` means no usable primary measurement adapter has been exercised; the received json shape is observed.

`selection-real.json` attributes the three attempts and seven deferred fixed keys. the two adaptive slots remain unused allowances in the [frozen request plan](../../docs/research/skating-v1-04/request-plan.json), without fabricated player identities. position references reuse the original `skater-bios` captures under `fixtures/references/`; these report positions rather than immutable historical truth.

the [verification record](../../docs/research/skating-v1-04/verification.md) owns checked fields, hashes, request accounting, software evidence and the acquisition handoff. [independent source checks](../../docs/research/skating-v1-04/reviews/primary-source-independent.json) retain the literal candidate values and context witnesses. those candidate values are evidence, not admitted season facts. synthetic compact census cases, where retained, establish reader arithmetic and evidence contracts only; they are not nhl payload schemas or a real census.

run the offline command from the repository root with the pinned python environment and this worktree's `analysis/src` on `PYTHONPATH`:

```sh
python -m hockey_stats.skating --selection fixtures/skating-v1-04/selection-real.json --out /absolute/new-directory
```

the command validates original receipts/bodies before binding; `read_skating` subsequently checks the compact artifact and copied selection without reopening those original roots. copying the selection does not change its original relative-path base.
