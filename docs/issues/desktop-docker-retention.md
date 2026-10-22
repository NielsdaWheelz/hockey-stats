# desktop docker retention

status: outstanding user decision. no deletion scope exists; `AGENTS.md` protects desktop docker and forbids inferring deletion permission.

problem: docker desktop still holds a predecessor hockey postgres store and nine postgres containers from august parity/search work. the current pipeline has no container dependency, but nothing records whether these are retained deliberately.

impact: `hockey-stats_hockey_pgdata` occupies about 103 gb of docker desktop's disk image, about 246 gb used in all. the macbook capacity plan (dev-server `docs/macbook-capacity-plan.md`, decision d2) leaves docker's disk image limit unchanged until this is decided, because shrinking the image can destroy its contents. `hockey-parity-smoke-v7-db-20260801` has `restart=unless-stopped`, so every docker desktop start brings a postgres 16.13 server back up; at inspection it had been up 30 hours, since docker's 2026-10-20 restart.

evidence (2026-10-21, read-only `docker ps -a`, `docker inspect`, `docker system df -v`):
- volume `hockey-stats_hockey_pgdata`, about 103 gb, created `2026-07-12T21:36:30Z`, compose project `hockey-stats`. its container `hockey-stats-db-1` (postgres 16.13, working directory `/Users/nnandal/Documents/code/hockey-stats`, created `2026-07-21`, restart `no`) exited 0 about two months ago.
- containers created 2026-08-01: `hockey-parity-smoke-db-20260801`, `hockey-parity-smoke-v5-db-20260801`, `-v6-`, `-v7-`, `-v8-`, `hockey-parity-smoke-direct228-synthetic-v1-db-20260801`, `-v2-`, and `hockey-direct228-v6-search-db-20260801`. all exited 255 two months ago except v7. volume `hockey-parity-smoke-db-20260801` is about 494 mb.
- the [external audit](../research/external-corpus-audit.md) inspected a different store: the colima `hockey` profile on `/Volumes/Expansion`, deleted in 03m. the docker desktop volume's july 12 creation date matches `/Volumes/Expansion/backups/hockey_20260712.dump`; whether they hold the same generation is unverified.

decision required: keep the store in place; export it to `/Volumes/Expansion` and then remove it; or remove it under an explicit deletion scope. the parity/search containers and their volumes need the same decision. clearing v7's restart policy is a smaller independent step that stops it from returning on each docker start.

resolution: the user records a decision and it is carried out. no hockey container is left set to restart; the volume is either removed, with any export verified first, or its retention is recorded here as intentional. the dev-server plan can then set d2's disk limit.
