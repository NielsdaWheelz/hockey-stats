# desktop docker hockey disposal

status: complete, 2026-10-21 local date (2026-10-22 utc). the user selected option 3 after the bounded investigation: "run option 3 with the v7 connection check". this separately authorizes the exact desktop objects below; it does not extend 03m's earlier external-data deletion scope or authorize other docker cleanup.

decision: remove the retired predecessor store and august smoke/search stores without an export. permanent loss of any unique legacy rows is accepted. equality with the deleted july dump or colima store was never established. the current native file pipeline has no dependency on these stores; source/config searches and 572 selected current research metadata files found no consuming reference. the resolved retention issue introduced by [pr #41](https://github.com/NielsdaWheelz/hockey-stats/pull/41) is retired here.

## exact scope

all commands used explicit `--context desktop-linux`; container ids were checked against names and mounts before mutation. every listed volume had exactly one container reference, belonging to its corresponding target. only v7 was running. the [execution receipt](receipt.json) retains full ids, reported sizes, the final connection check, shutdown result, removal times and preservation checks.

| container | id prefix | volume | reported size before removal |
|---|---|---|---|
| `hockey-stats-db-1` | `c5d05a901ef4` | `hockey-stats_hockey_pgdata` | 103 gb |
| `hockey-parity-smoke-db-20260801` | `ecce93293159` | same as container | 494.3 mb |
| `hockey-parity-smoke-v5-db-20260801` | `6f055593c6d7` | same as container | 105.2 mb |
| `hockey-parity-smoke-v6-db-20260801` | `81bcf6c7ff39` | same as container | 134.4 mb |
| `hockey-parity-smoke-v7-db-20260801` | `1db57f99578b` | same as container | 130.8 mb |
| `hockey-parity-smoke-v8-db-20260801` | `03119f684ea1` | same as container | 158.5 mb |
| `hockey-parity-smoke-direct228-synthetic-v1-db-20260801` | `ad39e0b8b727` | same as container | 160.3 mb |
| `hockey-parity-smoke-direct228-synthetic-v2-db-20260801` | `6d1499a37544` | same as container | 165.8 mb |
| `hockey-direct228-v6-search-db-20260801` | `f9860c5a67df` | `f48d9fa575882a5cac45aeb0ac782a36209170eeaf23c260966b59084e2f513d` | 461.8 mb |

the august stores total approximately 1.811 gb; there were eight august containers and nine hockey containers overall, correcting the original issue's prose count. docker's sizes are rounded, not an exact host allocation measurement.

## connection check and removal

two read-only `pg_stat_activity` checks found zero other client backends across all databases. the final check ran immediately before shutdown, using `default_transaction_read_only=on`, a ten-second statement timeout and a three-second lock timeout; it excluded only its own backend. no query text or table contents were inspected. normal postgres background processes were not counted as clients. this is a point-in-time client check, not a connection admission fence.

`docker stop --timeout 30` stopped v7 cleanly in 0.263 seconds, with exit code 0 and no oom/error. all nine targets were then verified stopped and their exclusive volume references rechecked. explicit container ids were removed with `docker rm`, without force or the volume flag; each exact volume name was subsequently removed with `docker volume rm`, without force. every command succeeded. all nine ids and volumes were verified absent afterward. no export, image deletion, network deletion, prune, privileged reclamation command, desktop restart or resource-setting change was performed. the `hky-main`, `hky-worker` and `hky-front` sessions were not accessed.

## measured host allocation

the measured file is `/Users/nnandal/Library/Containers/com.docker.docker/Data/vms-data/Docker.raw`. allocation is `stat.st_blocks * 512`; logical size is `stat.st_size`.

| observation, utc | allocated bytes | approximate decimal gb |
|---|---:|---:|
| before, `2026-10-22T02:21:21.987853+00:00` | 293,992,919,040 | 294.0 |
| immediately after, `2026-10-22T02:21:23.652283+00:00` | 293,994,450,944 | 294.0 |
| 38.6 seconds later, `2026-10-22T02:22:02.250160+00:00` | 189,264,207,872 | 189.3 |

the observed net allocation decrease is **104,728,711,168 bytes**, approximately **104.7 gb / 97.5 gib**. automatic reclamation became visible after removal; no manual trim was required. unrelated docker activity continued, so this net host delta is not an exact attribution of every byte to hockey. host available space rose from 102,735,073,280 to 207,342,997,504 bytes over the same observations. the disk's device/inode and 2,199,023,255,552-byte logical size remain unchanged: space was reclaimed without reducing the 2-tib maximum.

## preservation and d2 handoff

all 59 preexisting unrelated container ids, 240 unrelated volume names and 240 image ids remained present after removal. all 18 checked current-project/reference roots retained their identities; all 28 selected source/artifact sentinel hashes matched. all twelve initially dirty/untracked primary files retained their hashes and nanosecond mtimes. active docker context remains `desktop-linux`. these are bounded preservation checks, not a claim to have revalidated every fit or application.

hockey's retention decision and storage cleanup are resolved. dev-server's `docs/macbook-capacity-plan.md` d2 may now reassess the disk budget using the measured allocation. lowering the maximum is still a separate destructive maintenance action: [docker's mac documentation](https://docs.docker.com/desktop/troubleshoot-and-support/faqs/macfaqs/#how-do-i-reduce-the-maximum-size-of-the-file) says it deletes the existing disk image. surviving non-hockey content must be accounted for by that owner before a cap reduction. this approval does not authorize that loss or further pruning. the planned 8-gib memory change remains separate.

the [external audit](../external-corpus-audit.md) and [03m verification](../corpus-03m/verification.md) retain their historical inspection and disposal boundaries unchanged. no scientific verdict, source capture, current-project fit or publication is changed by this cleanup.
