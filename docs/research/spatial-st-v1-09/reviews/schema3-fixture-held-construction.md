# held schema3 fixture construction

status: prepared and syntax-checked; NOT_RUN. all bulk fixture reads, writes and publication remain held for a separately assigned resource window. the current first-annual reservation does not authorize this command. no output directory has been created. the frozen first-real producer is untouched.

the temporary command is `.tmp/application-st-schema3-held.sh`; its controller is `.tmp/application-st-schema3-held.py`. exact command/controller digests, metadata checks and selected parents are recorded in [preparation02](../receipts/fixture-schema3-held-02.json), copied verbatim from `/Users/nnandal/Documents/code/hockey-stats-local/v1-09-verification/fixture-schema3-preparation-02.json`; preparation01 remains preserved. root and an independent reviewer inspect the command before execution. any changed input pin or analysis tree requires a deliberate new review and binding.

the shell exclusively acquires `fixture-schema3-01-command.log` before the command, captures native time and controller stdout/stderr, records `controller_exit` and writes `fixture-schema3-01-command.exit` outside the fresh output directory. it returns the actual status; evidence-write failure fails the wrapper. argv, environment and input pins are unchanged. the successor shell sha256 is `a849ff0ca801b75dc5186aa467beedd3234eb1c52deed4a5fc6099b0369f786b`.

## selected fixture parts

| input | pinned sha256 |
|---|---|
| current v1-18 canonical manifest | `38c35b8c40b4e4e592d48710cd47c7b624467f56ac0168c949c7dccbc9901c02` |
| canonical support-correction receipt | `6743983f4e57243b71995c9f97f9e83aa3e54281445efee13cddff2db1dee49d` |
| saved st public-part manifest | `7511d91b96e74baacf849b6cc37ac5992b2a89c3340fe276bd8917862563cea1` |
| canonical st alias selection | `35600061f73327383c5af0ee0feb050506de437f90c7cfa52de9bf7057a767c2` |
| existing six-capture observed selection | `d53cc2255c1beba187e76f9b83e1a3838f27ad7116c301c3132be14487d11210` |

the authoritative current canonical root is `/Users/nnandal/Documents/code/hockey-stats-v1-18/fixtures/publication-v1-13/results`; its parent contains `analytical-v1-18-support-correction.json`. the historical public st parts remain under `fixture-e2e-01/results-ledger-pending`. its spatial members total 739,799,844 bytes, established by file metadata only. those mixed map files have not been scanned during preparation.

bounded comparison of the original ev scalar/adjustment fixture rows against the current canonical files finds no ev scalar change and three newly provided ev adjustment rows for the demonstration player. the supplied support-correction receipt declares three map-support changes, including the ev attempt map and the finishing/ice-won maps, with numerical values unchanged. no counts or exposure are inferred from those declarations. current canonical ev evidence is consumed verbatim; it did not exist in the historical exchange. the old mixed-map ev differences are checked and recorded only while consuming the stream in the assigned window.

## construction contract

the controller calls the existing `write_results(selection, catalogs, family_rows, output)` to create schema3, then the ordinary `build_publication` to create the inactive schema9 candidate. it does not call an old exchange reader, exchange converter, fitter, full state reader, rate evaluator, array loader or spatial recompositor.

each saved scalar/map/adjustment member is consumed once. the old st rows retain their public numerical bodies. the corresponding ev rows are replaced by exact current canonical rows; later canonical pending ev seasons remain explicitly pending. the shared `spatial_evidence_rows` owner supplies eight st selectors from the canonical aliases and interleaves them with current canonical ev evidence. `_AnnualProjection` receives seven fields with an unused empty native-array dictionary. `read_saved_spatial_evidence` owns saved-evidence validation, and `_special_teams_method` owns regenerated method metadata against those aliases and their saved references. saved diagnostic flags are copied into the method-status summary; no probability or sensitivity comparison is recomputed.

the canonical people/sources/supports and nonspatial fixture bodies are authoritative. this also carries their explicit map-support correction. current canonical methods win identifier collisions; the saved synthetic execution aliases are retained. declared prepared-method bindings are rebound to the existing honest synthetic preparation, and method input hashes are updated. this metadata attribution is recorded before writing. ledger families remain pending, preserving the accepted decision against substituting the old fictional totals.

input hashes are checked while streams are consumed, not by a preliminary 742 mb pass. the current writer still performs its required output validation, and the publication owner still performs its normal checks. receipts retain the exact consumed-member hashes, bounded ev differences, construction identity and publication costs. the original st states, public exchange and schema8 candidate remain unchanged historical evidence.

## cost and remaining proof

the former composition took 167.12 seconds and the saved-only schema8 publication took 375.745 seconds. those are historical costs, not forecasts for the new evidence-bearing construction. this command reads the selected public fixture parts, writes the complete current exchange and builds one fresh candidate. it performs zero fits, probes, numerical evaluations or array loads. publication and strict validation still incur real cpu and storage costs.

only python syntax, prohibited-call inventory, shell syntax and small metadata/pin checks have passed. the controller itself, schema3 writer, schema9 publication, final web consumers, api/browser/downloads, layouts and isolated rollback are NOT_RUN for this fixture. v1-18 owns the final six-file web merge; this preparation changes no web source.
