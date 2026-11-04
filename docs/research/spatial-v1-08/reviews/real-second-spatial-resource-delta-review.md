# independent second spatial resource-reporting delta review

verdict: clear. this changes reporting only; the year-two package remains held without an accepted first-year spatial manifest pin. [preceding held-package review](real-second-spatial-held-command-review.md)

| artifact | sha256 |
| --- | --- |
| current `accept_real_spatial_20222023.py` | `d0c4552972131f00405c283ea36dab0614264144036d6a7b68b9c7a824d42b9b` |
| unchanged year-two command | `763dcef14c6ac1867783445ea8e36b9c305fbaf966af7013db771bc143f1910f` |
| `real-20222023-spatial-preparation-held-02.json` | `5767b13bc69d4fcd62759550f49182f69b0f6b8d2e5cc46d2b546b69d4cdc383` |
| `spatial-second-resource-check.py` | `0f42f90102ee138e144a3bbaa56dfd64d6d0370afb80496b7ee2801af9d80e04` |

these files are under `var/v1-08-replacement/`. removing only the two new memory-regex lines and restoring the former timing field reproduces prior helper hash `18e1ecb1` exactly. the history inspection, unavailable predecessor guard, input bindings, exit handling and exclusive receipt destination are untouched.

the receipt now uses the first-year schema: `whole_command={timing,maximum_resident_bytes,peak_memory_footprint_bytes}`. it selects the last `/usr/bin/time` timing, resident-memory and footprint samples independently, converts them to their ordinary numeric types, and records null for missing fields. these capture whole-process peaks, including the final canonical read, rather than treating the producer's earlier measurement as the whole command. no resource threshold, numerical gate or eligibility change was introduced.

the new red/green evidence is bound by held-02. the independent scratch-only control passes both cases: multiple positive samples select the last values, and absent metrics produce three nulls. saved-state inspection is stubbed. unchanged history/command controls were not repeated. held-02, all cited control files and historical held receipt `340fb272` reproduce their recorded identities; live first-year command `35cc8c55` and helper `05dd2400` remain exact.

no actual real/fixture artifact, source pass, analytical array, reader, evaluator, fit or native call was performed. no commit was made. accepted first-year evidence/resources, matching concrete predecessor pins and root's later release remain required before year-two execution.
