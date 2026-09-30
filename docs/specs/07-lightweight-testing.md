# pr07 — lightweight lasting verification

status: **stub; not ready for implementation.** specify after a useful capture-to-publication/read path exists, before the first product is complete. until then, retain the agreed temporary integration/live verification approach and useful fixture evidence. [plan](../plan.md) · [brief](../brief.md)

## purpose and ownership

retain a small, repeatable set of checks for consequential software behavior. inputs are the implemented commands/read boundaries, a bounded offline fixture corpus and independently checked facts. outputs are a few lasting integration checks, explicitly invoked live checks, and concise instructions for running them. scientific calibration, origin validity and player-attribution assessment remain separate research responsibilities.

keep checks within their application or analysis project, reusing ordinary entry points. fixture evidence belongs under `fixtures/`; shared analytical diagnostics remain production research code. select the minimum runner and exact files later. no testing service, orchestration framework, exhaustive matrix or continuous fitting.

[03c](03c-source-revision.md#offline-evidence-amendment) already owns expanded raw fixtures and the larger local corpus; every subsequent slice preserves distinct new failures under the [fixture policy](../../fixtures/README.md#fixture-policy-and-local-corpus). 07 consumes that evidence rather than postponing its collection. default checks use a small declared selection from committed fixtures; broad local-corpus checks are explicitly invoked. raw storage size does not determine routine test workload. do not require the larger corpus, network or drive for the default checks, or introduce a corpus download/synchronization harness.

## scope and full specification

choose cases for important contracts and observed regressions: source bytes/provenance, missing or conflicting evidence, analytical handoffs, coherent database reads and manual publication recovery. verify a meaningful browser path through 06. manually check cheap presentation details; full historical training does not belong in software tests.

offline checks must run without the drive or network. live checks must identify their upstream dependence and separate source unavailability from a demonstrated application defect. fixtures cannot silently replace required real inputs.

content design owns check/report wording and fixture annotations. record whether each case is captured, transformed or synthetic; name its provenance, independently checked expected facts and limits. generated snapshots are not independent truth. exact event/exposure populations must accompany expectations that depend on them.

completion means another invocation can reproduce the chosen checks, failures identify the broken contract, and the suite stays practical to run. passing it establishes software behavior, never scientific acceptance or whole-corpus coverage.
