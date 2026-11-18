# local storage

current layout after the 2026-11-18 consolidation:

| responsibility | location |
|---|---|
| source, fixtures, locked environments and the compatible serving build | `~/Documents/code/hockey-stats` |
| future active task worktrees | `~/Documents/code/.worktrees/hockey-stats/<task>` |
| bounded local corpora, evidence and publication | `~/Documents/hockey-stats/local` |
| retained local raw captures | `~/Documents/hockey-stats/raw` |
| frozen task evidence and source remnants | `~/Documents/hockey-stats/archive` |
| operator inventories and migration receipts | `~/Documents/hockey-stats/maintenance` |
| full inputs, expensive fits and bulk research | `/Volumes/Expansion/hockey-stats` |

retain the existing two recent local seasons, the fixed third-season exception and useful fixtures. this move adds no local full mirror. source evidence and expensive numerical work remain preserved; superseded cheap publications/builds are disposable after checking their consumers. keep the active publication and one previous database. historical candidates needed by a retained assessment are inputs, with that dependency recorded explicitly.

new retained outputs use these permanent roots directly. a worktree contains source and disposable scratch; its removal must not remove the only copy of an input, result, receipt or fitted state. source revisions belong in git; protect necessary refs before deleting a checkout. no cleanup daemon or storage service is required.

## historical input locators

`analysis/src/hockey_stats/input_locations.py` owns filesystem resolution for native input readers. the ordinary local file `~/Documents/hockey-stats/locations.json` contains exactly `schema_version:1` and `roots:[{"from":"/old/absolute/root","to":"/retained/absolute/root"}]`. sources are unique normalized absolute prefixes; the longest component prefix applies once. targets cannot fall under another mapped source. missing mapped inputs fail their existing reader contract; there is no search or fallback to the old location. a process reads one configuration snapshot; restart it after editing the table. installations without relocated evidence need no table.

artifact bytes, declared provenance strings and digest checks stay unchanged. input locations are resolved at i/o and explicit locator comparisons. relative source references retain their declared parent; contained artifact members use their actual directory. detached readers still do not reopen original source ancestors. output paths are explicit permanent paths and are never redirected by this table.

historical shell commands and absolute file links still quote their original paths. shells and file browsers do not consult the table. obtain the current location with:

```sh
analysis/.venv/bin/python -m hockey_stats.input_locations /original/absolute/path
```

this prints an existing location; it does not certify content without its recorded digest. current operation uses canonical paths. historical source versions remain available through git, and frozen protocols/verdicts remain unchanged.

## serving

the active schema-8 publication is `~/Documents/hockey-stats/local/publication/active.sqlite`; its schema-7 predecessor is `previous.sqlite`. the 2026-11-18 restart uses the same compiled app and the same database bytes. current source reads schema11, so rebuilding the primary app would replace the older compatible serving build. use a separate checkout for candidate review. the accepted schema11 territory candidate remains inactive on the external drive; cleanup does not rotate publications or admit a model.

[consolidation verification](research/storage-consolidation-20261118/verification.md) records preservation, native reader checks, the deliberate restart and its measured interruption. [the plan](plan.md) owns subsequent assignments; activation remains separate.
