# real descriptive-card activation — 2026-10-26

on 2026-10-31, [v1-06 activation](../execution-v1-06/activation.md) superseded this serving state: schema8 is active and this schema7 publication is the single previous database. the identities, costs and schema7→schema6 rollback procedure below describe the earlier cutover; use the new record for current rollback.

status: **publication active; normal server, live http and actual browser/export verification passed.** source delivery and real source-to-card acceptance already passed through [pr #55](https://github.com/NielsdaWheelz/hockey-stats/pull/55), merged as `816354566b60c8ae423cc73922d9e772a5fc7720`. this release changes serving publication/application state using the existing operator; it adds no production code, fit, acquisition or scientific admission. [integration evidence](verification.md#real-three-season-application-integration--accepted-2026-10-24)

## publication identities

| role | publication | schema | bytes | sha256 |
|---|---|---|---|---|
| active; accepted candidate | `eb4e31ab-a35c-4df6-be34-9bccceb4fe3d` | 7 | 4,635,877,376 | `0526b60cd7f009627de4621717f89e95b1fa4613553bae20be10b466025e9b21` |
| previous; checked old active | `24e41fa7-256c-4f0a-9876-e8d7f8f42056` | 6 | 611,373,056 | `986d727e458600e8a73e57714be9a62dbbda42d209cbd9eb83de8c1ddd5bfc11` |

candidate: `/Volumes/Expansion/hockey-stats/factual/facts-v1-03-20261024-02/candidate/player-analysis.sqlite`. serving directory: `/Users/nnandal/Documents/code/hockey-stats-local/publication`. the ordinary activation operator validates its incoming copy and preserves the old active opaquely as `previous.sqlite`, replacing the older schema-3 previous under the settled single-backup policy.

schema-7 application source is `816354566b60c8ae423cc73922d9e772a5fc7720`; subsequent release documentation does not change its application tree. the schema-6 predecessor requires `cb13d99c406c572abf3f1fa05da34f1bc3ea6726`. its compiled publication check passed before cutover. no port-3000 listener existed before this activation, so this cutover starts the normal server rather than interrupting a running one.

## execution evidence

pinned node dependency installation, typecheck and build passed (`npm-ci.txt`, `typecheck.txt`, `build.txt`). `old-active-check.json` and `database-identities-before.json` bind the checked predecessor and pre-cutover files; `activation-start.json` binds the source, candidate and command. the existing operator completed its full strict incoming validation and rotation with exit code 0; rotation was verified at `2026-10-27T06:18:39Z`. active and previous byte identities match the table above, and `incoming.sqlite` is absent. the normal node-24 server completed its unchanged startup validation and is listening on loopback port 3000. startup readiness took at most 1,259.184 seconds (10-second observation resolution); the operator took 1,145.75 seconds and peaked at 1,003,995,136 bytes rss. `readiness.json` records the running server. `http-live.json` records actual html 200/no-store, built asset 200/immutable, real player api 200 with the expected publication/person identity, and invalid-family 400/no-store. actual browser and saved-export checks also passed, as recorded below. external receipts belong in the [canonical activation evidence](/Volumes/Expansion/hockey-stats/factual/facts-v1-03-20261024-02/acceptance/activation-20261026). `activation-result.json` records the completed rotation. external-file reads briefly returned operating-system permission errors during activation; access was restored and the original operator receipts are readable again, recorded in `access-restored.json`. this did not alter source files or bypass validation. no cold-start validation shortcut or cache is introduced.

concurrent [pr #56](https://github.com/NielsdaWheelz/hockey-stats/pull/56) advanced main to `a279576dbb29a963cd23350b6768e2065297b0e0`; `concurrent-upstream.json` confirms the application source is unchanged from `8163545`. the activation documentation preserves that independent delivery.

## live application and exports

`browser-activation.json` records three actual descriptive cards (carlson, rantanen and crotty), three-season raw histories, season change, the makar/rantanen two-card comparison, discovery filtered to one crotty row and a 375-pixel viewport. each card loaded in approximately 6.5–6.9 seconds. keyboard scrolling moved the narrow card region without widening the document. all checks passed with no recorded browser errors.

`browser-activation.json` records eight native downloads. `saved-output-reconciliation.json` reconciles the three card png/csv pairs: three 1200 × 2324 pngs and 35-column descriptive csvs with 648, 616 and 362 rows. each person has 232 exactly reconciled addressable native leaves and 232 support checks: 696 of each across the three people. array/category/derived paths are explicitly excluded from that bounded reconciliation; the frozen source-to-card acceptance remains the broader source proof. `discovery-csv.json` checks seven field rows for the one selected crotty player.

`live-verification-method.json` records completed visual inspection and readable sparse-field exports, plus corrections to temporary browser-check expectations for spa navigation, explicit unavailable values and long-form csv rows. an initial transient host command/file-access stall was observed; the accepted retry required no application change. the application and accepted live checks used pinned node 24; an initial failed attempt used node 26. no application source changed. the ordinary server is pid `4799`; its operational log remains local at `/Users/nnandal/Documents/code/hockey-stats-local/activation/v1-16-20261026/server.log`. retained evidence belongs in the canonical external receipt directory above, not temporary browser controllers.

## rollback

stop serving before replacing either database. rebuild the schema-6 application from git revision `cb13d99c406c572abf3f1fa05da34f1bc3ea6726`, using its pinned node/lockfile; no archived application build is retained. validate `previous.sqlite` with that code and current `active.sqlite` with schema-7 code. use the [manual cross-version rollback procedure](../../../README.md#manual-cross-version-cutover-and-rollback), substituting schema 6 for the old application and schema 7 for the new application. require an absent `incoming.sqlite`, copy/compare/validate the previous database, rotate exactly once, then restart the matching old build and reload browser tabs. the schema-7 `restore` command cannot read this schema-6 predecessor.

## scope and cleanup

release documentation passed independent review and merged in [pr #57](https://github.com/NielsdaWheelz/hockey-stats/pull/57) as `d8bbd77664cf316c20202250e0660c6a26eda2e8`. primary source synchronization and owned temporary-resource cleanup are complete; `delivery.json` in the canonical activation evidence records the lifecycle and preservation checks. preserve the accepted external candidate, actual card/export evidence, expensive fits, captures, unrelated worktrees and all unrelated primary-checkout documentation drafts. only the previous database slot is deliberately replaced. source gaps, unavailable fields, unfinished modeled components and historical scientific verdicts remain unchanged; this factual-card activation is not complete experimental-product delivery.
