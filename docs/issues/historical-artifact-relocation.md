# historical artifact relocation

the approved 2026-10-20 migration moved eight historical research roots to `/Volumes/Expansion/hockey-stats/archive/local-research-20261020` and replaced their local paths with symlinks. the verified 03b offline duplicate now links to its existing external original. artifact bytes remain unchanged; file access requires the drive.

some historical validators resolve paths before comparing them with frozen selections. symlinks preserve access but change those resolved paths. both 03l completed-component checks (`development-baseline` and `season_transfer-sequence`) and the development-training selection-reference check passed before relocation and now raise `consumed selection differs from cohort selection`. both detached corpus readers still pass with 1,312 games each.

reproduce through `hockey_stats.chance_components.selection_reference` using the unchanged cohort at `/Users/nnandal/Documents/code/hockey-stats-runs/chance-03l-20261009/cohorts/development-training/cohort.json`. [reader receipts](/Users/nnandal/Documents/code/hockey-stats-local/storage-migration-20261020/readers-after.json) record the bounded checks; the same receipt directory retains per-file hashes, inventories and migration results.

the user explicitly accepted this limitation. an affected replay requires restoring its original local layout or a separately reviewed reader fix. resolution requires the affected native checks to pass while preserving artifact hashes and historical verdicts. no reader code or frozen evidence was changed for this migration.
