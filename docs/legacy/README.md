# legacy archive and salvage audit

audited 2026-09-29. this original source/doc inspection is not a runtime certification. the subsequent [external-data audit](../research/external-corpus-audit.md) records the separately authorized database inspection and fresh-acquisition decision.

## preservation and repository migration

the former public `NielsdaWheelz/hockey-stats` repository was renamed to [hockey-stats-legacy](https://github.com/NielsdaWheelz/hockey-stats-legacy) and archived. its github repository id remains `1278466215`; its main commit is `1d45312ed4a2d797150e377c87ecdba231b5ebfc`. its closed [pull request 1](https://github.com/NielsdaWheelz/hockey-stats-legacy/pull/1) remains available. no source files or history were changed in the predecessor.

a git mirror was created and passed `git fsck --full` before the rename. it includes the main branch and the pull-request head `fdfd193c0763a1921a1efe749e0185685697e31f`. local locations, excluded from the new repository:

- `.reference/hockey-stats-legacy.git/`: bare git mirror.
- `.reference/hockey-stats-legacy/`: working clone for inspection, with its origin pointing to the renamed archive.

the new [hockey-stats](https://github.com/NielsdaWheelz/hockey-stats) repository is private, has a separate history and repository id `1396540409`, and begins with documentation only. private-by-default trades immediate public access for time to review inherited material before publication. the old archive remains public.

reusing the old name means it must no longer be used as an address for legacy history. references in the new research use the renamed archive and pinned commits. other old clones, if any, need their remotes repointed before use. a git mirror preserves git objects and refs, not a separate export of github issues, settings, or attachments; those remain with the archived github repository.

rollback is available without deleting history: the legacy repository can be unarchived; restoring its former name would first require moving the new repository to another name. no rollback was performed.

## what was found

the archived checkout contains 119 markdown documents under `docs/`, totaling 45,153 lines, and 57 migration files. these measurements indicate scope, not quality. its own documents distinguish intended design from implementation and record substantial unfinished scientific work. old claims of completion or blockers have not all been revalidated against this head.

the valuable material includes a detailed nhl source catalogue, domain edge cases, statistical semantics, 17 primary-source research dossiers, and an existing small offline fixture corpus. much of the implementation and planning machinery is coupled to the predecessor's broader commitments. importing all of it would silently import those commitments too.

## salvage decisions

all source links below are pinned to the archived head. “retain” means retain evidence, not accept every statement as current truth.

| material | evidence | treatment and reason |
|---|---|---|
| 17 hockeyviz/evolving hockey source dossiers | [source directory](https://github.com/NielsdaWheelz/hockey-stats-legacy/tree/1d45312ed4a2d797150e377c87ecdba231b5ebfc/docs/research/frontier-xg/sources) | copied byte-for-byte into `sources/`; historical research worth preserving with dates and attribution |
| peer evidence crosswalk | [crosswalk](https://github.com/NielsdaWheelz/hockey-stats-legacy/blob/1d45312ed4a2d797150e377c87ecdba231b5ebfc/docs/research/frontier-xg/evidence-crosswalk.md) | retain a pointer; its claim inventory is useful archaeology, but its parity obligations are not new requirements |
| endpoint catalogue and observed quirks | [data sources](https://github.com/NielsdaWheelz/hockey-stats-legacy/blob/1d45312ed4a2d797150e377c87ecdba231b5ebfc/docs/design/data-sources.md) | use as investigation checklist; claims of availability and source authority need current captures |
| metric definitions and conceptual explanations | [metrics](https://github.com/NielsdaWheelz/hockey-stats-legacy/blob/1d45312ed4a2d797150e377c87ecdba231b5ebfc/docs/design/metrics.md), [glossary](https://github.com/NielsdaWheelz/hockey-stats-legacy/blob/1d45312ed4a2d797150e377c87ecdba231b5ebfc/docs/design/glossary.md), [concepts](https://github.com/NielsdaWheelz/hockey-stats-legacy/blob/1d45312ed4a2d797150e377c87ecdba231b5ebfc/docs/design/walkthrough/modeling-concepts.md) | selectively consult when specifying a metric; do not inherit implementation-specific terms as hockey concepts |
| ingestion/reconstruction knowledge | [actual ingestion](https://github.com/NielsdaWheelz/hockey-stats-legacy/blob/1d45312ed4a2d797150e377c87ecdba231b5ebfc/docs/services/ts-app/ingestion.md), [reconstruction source](https://github.com/NielsdaWheelz/hockey-stats-legacy/tree/1d45312ed4a2d797150e377c87ecdba231b5ebfc/packages/core/src/ingestion/reconstruction) | retain boundary cases and compare mechanisms against raw inputs; no wholesale code import |
| raw capture and offline reprocessing | [capture](https://github.com/NielsdaWheelz/hockey-stats-legacy/blob/1d45312ed4a2d797150e377c87ecdba231b5ebfc/packages/core/src/ingestion/per-game-ingest/raw-snapshot-capture.ts), [reprocess](https://github.com/NielsdaWheelz/hockey-stats-legacy/blob/1d45312ed4a2d797150e377c87ecdba231b5ebfc/packages/core/src/ingestion/per-game-ingest/per-game-reprocess.ts) | keep the intended invariant; actual upstream transformations violate it for several feed families |
| offline fixture corpus | [fixture guide](https://github.com/NielsdaWheelz/hockey-stats-legacy/blob/1d45312ed4a2d797150e377c87ecdba231b5ebfc/packages/core/fixtures/README.md) | already available in the local clone; retain as candidates and case catalogue, not a trusted new fixture contract |
| schema, durable engine, services, frontend, rule subtree, campaign protocols | [design index](https://github.com/NielsdaWheelz/hockey-stats-legacy/blob/1d45312ed4a2d797150e377c87ecdba231b5ebfc/docs/design/index.md), [status](https://github.com/NielsdaWheelz/hockey-stats-legacy/blob/1d45312ed4a2d797150e377c87ecdba231b5ebfc/docs/services/_status.md) | leave in archive; rebuild requirements before choosing mechanisms |
| scientific issues and implementation backlog | [remaining work](https://github.com/NielsdaWheelz/hockey-stats-legacy/blob/1d45312ed4a2d797150e377c87ecdba231b5ebfc/docs/implementation/remaining-work.md) | consult as a list of known traps; old issue status is not independently verified or a new backlog |
| downloaded data and trained artifacts | [external database audit](../research/external-corpus-audit.md) | projected inputs and missing reports exclude wholesale admission; fresh captures selected; old fits/backup preservation still to inventory before any cleanup |

## copied research provenance

[manifest.json](manifest.json) records each source path, original commit, byte count, and sha-256. all 17 copies match their source files exactly. the copied files retain their historical capitalization, quotations, conclusions, and internal claim ids. none are normative instructions for this project.

their original parent [research readme](https://github.com/NielsdaWheelz/hockey-stats-legacy/blob/1d45312ed4a2d797150e377c87ecdba231b5ebfc/docs/research/frontier-xg/README.md) dates review passes to july 2026 and describes them as paraphrased dossiers rather than article mirrors. our new reviews recheck selected important claims; they do not revalidate every claim in these dossiers.

| topic | retained files |
|---|---|
| shot probability and player outcome layers | [xg 7](sources/hockeyviz-xg7.md), [xg 8](sources/hockeyviz-xg8.md), [location fabric](sources/hockeyviz-fabricxg.md), [eh xg](sources/evolving-hockey-xg.md) |
| spatial effects and valuation | [magnus 9 even strength](sources/hockeyviz-magnus9ev.md), [magnus 9 special teams](sources/hockeyviz-magnus9st.md), [isolation](sources/hockeyviz-isolate.md), [eh war](sources/evolving-hockey-war.md) |
| context and mechanisms | [aging](sources/hockeyviz-age22.md), [blueline traversals](sources/hockeyviz-bluelinetraversals.md), [penalties](sources/hockeyviz-magnus8p.md), [score sequence](sources/hockeyviz-scoreseq.md), [shifts 1](sources/hockeyviz-shifts1.md), [shifts 2](sources/hockeyviz-shifts2.md), [shootiness](sources/hockeyviz-shootiness.md) |
| simulation and display | [game simulation](sources/hockeyviz-magnus8gamesim.md), [shot maps](sources/hockeyviz-shotmap.md) |

## concrete findings

two confirmed problems constrain salvage: [raw provenance and invented handedness](../research/external-corpus-audit.md), and fixture fidelity, resolved for the new system through [fresh fixture admission](../../fixtures/README.md). the [external audit](../research/external-corpus-audit.md) confirms stored-data defects; [remaining inventory](../issues/external-data-inventory.md) concerns preservation before any separately authorized cleanup.

the old corpus contains 11 curated games, one labeled live and ten synthetic, plus a separate failure-injection game. all 79 manifest hashes verify. several files from the live-labeled game are nevertheless transformed. the play-by-play and shifts appear to use an untouched capture path in the inspected code; this is evidence of a candidate, not independent proof of capture history.

the original source/doc inspection installed no dependencies, started no old application processes and copied no application code. the later external audit started only the old vm/database with explicit authorization, queried read-only and stopped both afterward. no training jobs ran or source data changed; historical model results remain unverified.
