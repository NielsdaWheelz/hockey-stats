# cli predecessor and design ownership review

scope: static, read-only review during the active first real annual. no analysis edit, source/artifact scan or numerical command was performed.

## predecessor

`analysis_cli.py:131` calls the default full `read_mechanism_state` and retains that object while preparing and fitting the next season. full reading hashes/decodes the previous design and its arrays, checks large-array domains and reproduces projections. a full read can also reproduce a saved probe comparison; normal preceding years1–4 have no probes. these are source-independent artifact reads, not source capture reads or ordinary old objective evaluations.

`fit_mechanism` consumes only the preceding manifest, completed status, raw ledger and path. its own path-based dispatch already requests `narrow=True`. the state writer binds the previous manifest through that path; it does not need the old design or arrays.

smallest correction: add `narrow=True` to the cli's existing reader call. the public narrow reader verifies the consumed member hashes/bytes, finite typed raw ledger, actor/chronology/prior/support/reference contracts, completed native baseline and any saved diagnostic record. the fitter then checks exact consecutive family/recipe and stable prepared/coach lineage. the previous coefficient archive is not consumed: its agreement with the authoritative raw ledger is established by completed-state full validation and the saved audit, not repeated for every consumer. no new read mode or weakened carry contract is needed.

this avoids retaining the old dense design during the next preparation, compression and solve. it does not explain the first annual's observed38.1gb peak: the first annual has no predecessor. no exact future byte or runtime saving is claimed here.

## current raw design

`analysis_cli.py:137–140` retains its local raw `design` during the entire fit call. `fit_mechanism` rebinds its own parameter to a compressed dataclass copy. penalty compression uses indexed csr/dense copies and newly summed response arrays; source metadata and source locator records are shared where appropriate. replacing the callee's local cannot release the cli's reference to the raw arrays. both designs therefore remain live through optimization and artifact validation even after compression has returned.

without mutating the caller's input, changing the public prepare/fit contracts, or adding ownership containers/cleanup machinery, the simplest correction is to pass the preparation expression directly to `fit_mechanism`. the caller then has no named raw-design reference after argument evaluation; ordinary function-local rebinding releases it once compression finishes.

one bookkeeping field needs an explicit choice: the cli currently inserts `input_read_wall_seconds` into `design.resources`. recommend reporting that cli-only measurement in the command log before the inline prepare/fit call. the source's existing `preparation_seconds`, the fitter's resource record and native whole-command measurements remain saved. this relocates one diagnostic measurement rather than silently dropping it, and avoids a once-used preparer wrapper, mutation of caller-owned design fields or a changed numerical interface. existing saved resource records remain valid and untouched.

transient raw-plus-compressed overlap while compression constructs its result still exists. compression's temporary grouping keys and the current state's full validation also have their own costs. these two bounded changes remove proven unnecessary retention; they do not establish a new peak-memory forecast or justify a broader performance/lifecycle project. likelihoods, grouping, priors, coefficients and projections are unchanged.

## implementation and bounded verification

after the first real annual completed, the reviewed cli edits were applied without a fit or large read. predecessor dispatch now requests `narrow=True`; the preparation expression is passed directly into `fit_mechanism`. `input_read_wall_seconds` is written to ordinary stderr, while the source's `preparation_seconds` and numerical cost records retain their owners. no additional lifetime wrapper or cleanup machinery was introduced.

six family-specific ownership controls first failed, then passed: both families request the narrow reader; a weak reference proves that the cli releases the raw argument after callee rebinding; and source resource metadata remains unchanged while the read-cost log survives. the weak-reference control uses tiny synthetic objects and no numerical execution. it verifies ownership, not a peak-memory saving. existing cli eight-case, pure eleven-case mathematics and three pure source-method checks also pass. the [receipt](../receipts/cli-ownership-repair.json) binds the bounded evidence and exact scope. no real annual, source corpus or historical artifact was rerun or rewritten; the reserved v1-19 heavy window remained unused by this work.
