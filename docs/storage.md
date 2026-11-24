# local storage

retained locations at the 2026-11-23 delivery.

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

the local and origin branches named `implement/v1-09-special-teams` retain the original special-teams source at `77d9627`. pr #63 landed the same tree in a squash commit. the retained branch preserves the intermediate producer revisions that the delivery evidence cites. [pr #63](https://github.com/NielsdaWheelz/hockey-stats/pull/63) · [retention record](research/storage-consolidation-20261118/verification.md)

## historical input locators

`analysis/src/hockey_stats/input_locations.py` owns filesystem resolution for native input readers. the ordinary local file `~/Documents/hockey-stats/locations.json` contains exactly `schema_version:1` and `roots:[{"from":"/old/absolute/root","to":"/retained/absolute/root"}]`. sources are unique normalized absolute prefixes; the longest component prefix applies once. targets cannot fall under another mapped source. missing mapped inputs fail their existing reader contract; there is no search or fallback to the old location. a process reads one configuration snapshot; restart it after editing the table. installations without relocated evidence need no table.

artifact bytes, declared provenance strings and digest checks stay unchanged. input locations are resolved at i/o and explicit locator comparisons. relative source references retain their declared parent; contained artifact members use their actual directory. detached readers still do not reopen original source ancestors. output paths are explicit permanent paths and are never redirected by this table.

historical shell commands and absolute file links still quote their original paths. shells and file browsers do not consult the table. obtain the current location with:

```sh
analysis/.venv/bin/python -m hockey_stats.input_locations /original/absolute/path
```

this prints an existing location; it does not certify content without its recorded digest. current operation uses canonical paths. historical source versions remain available through git, and frozen protocols/verdicts remain unchanged.

## serving

the macbook service at `127.0.0.1:3000` serves schema 12 publication `bdebf3d9-2f44-4e2e-9c20-94e5cf5c2c32`, 32,039,075,840 bytes, sha256 `956a26e7b21f77c47d2ada72961a7e1c2e53abb85ef35cc91bbe0acc2e57eeb3`. the local database and receipt are `~/Documents/hockey-stats/local/player-analysis/active.sqlite` and `active.sqlite.validation.json`. the checked runtime is installed in the primary `app/` from source `39949ff5c1957a9412471a7f5b1adacfbd2cb473` and app tree `31e01947c6413e4482a04fe2647d0bed87017b57`. use the named source when rebuilding. [delivery verification](research/application-v1-20/verification.md).

`previous.sqlite` is the sole rollback database, schema 8 publication `9a5b4061-f909-4c1b-b624-5729e5acb6bf`, 11,310,997,504 bytes, sha256 `dbac3ffb061a31502b3455203db5e0b48488c3ff45dbc32b370c9cbc22576bb5`. it has no receipt and requires source `0e0f5694721bb2f25b64c6dff905209a5feea93f`, its pinned dependencies and the historical full startup. [rollback instructions](operations.md#rollback).

follow the [operator instructions](operations.md) for admission, stage, exact-path preview, switching and restart. the external donor and accepted candidate are retained on expansion. named real evidence lives at `~/Documents/hockey-stats/local/application-v1-20-20261122` and earlier fixture/rehearsal evidence at `~/Documents/hockey-stats/local/application-v1-20-20261120`. [the plan](plan.md#current-boundary) owns assignment and status.

[consolidation verification](research/storage-consolidation-20261118/verification.md) records the earlier schema 8 storage move and restart.
