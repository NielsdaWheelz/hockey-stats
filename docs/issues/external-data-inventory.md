# external data inventory

status: drive inspected during pr03b specification; remaining inventory is limited to preservation before any archive deletion. the user chose a fresh three-season training corpus. the [completed admission audit](../research/external-corpus-audit.md) removes the detached-drive blocker; old-data reuse is not a prerequisite for pr03b.

## problem and impact

the old hockey database, backups and campaign outputs have been located and sampled. model metadata references saved artifacts, but their files and the contents of older vm/rescue images have not all been inventoried. deleting those paths now could discard expensive fits or unique historical observations. this remaining preservation question does not justify importing old projections into the new pipeline.

## evidence

the [read-only audit](../research/external-corpus-audit.md) found a 67-gb database, 20,769 game ids, 172,666 snapshots, projected boxscores/rosters and no saved per-event on-ice reports. the user authorized vm startup and read-only sql, then chose fresh captures. full archived source remains at `.reference/hockey-stats-legacy/`.

## resolution evidence

before any requested deletion, identify the exact hockey-only paths, locate/check saved fit artifacts and decide what to retain, including unique source snapshots. distinguish sparse image logical sizes from allocated space. record the retention/deletion decision; this issue can then be closed without pretending the archive has become valid training input. no deletion is currently authorized.

fresh [03b](../specs/03b-training-acceptance.md) capture/admission uses existing 01–02c contracts. missing drive/input remains an explicit unavailable input; no automatic fallback to fixtures or the old database.
