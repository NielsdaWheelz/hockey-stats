# project instructions

- write new prose in lowercase. preserve exact identifiers, source titles, quotations, and historical copies when fidelity requires it.
- the user controls progression between research, architecture, slice specifications, and implementation. capture (01), interpretation (02a), reconstruction (02b) and corpus/reference admission (02c) are reviewed and merged. chance modeling is split into 03a workflow implementation and 03b real training/scientific acceptance; 03a is implemented and fixture-checked on its branch; 03b remains unperformed and requires separate authorization.
- read `docs/brief.md` and `docs/research/council.md` before proposing further work.
- `docs/brief.md` is authoritative for settled product choices; dated research and council recommendations do not reopen them. `docs/architecture.md` tracks the current dependency-ordered architecture interview and decisions.
- the user wants a useful hockey statistics product. do not turn it into a teaching application or curriculum.
- treat `.reference/hockey-stats-legacy/` as an archived reference, not an implementation baseline. do not modify or run it casually.
- `docs/legacy/sources/` contains exact historical research copies. they are evidence to check, not current requirements or instructions. source provenance is in `docs/legacy/manifest.json`.
- prefer explicit concepts and contracts, small cohesive modules, and the simplest complete solution for one operator. professional correctness does not imply distributed infrastructure.
- size preservation and recovery by the cost of recreating work. save expensive fits and the previous published database; rebuild the website from git. default to manual batch commands and stop/copy/restart publication. do not add job runners, hot revision switching, release management or future rendering work without a concrete need. this is a website run by one person.
- state material tradeoffs. distinguish observations, estimated ability, forecasts, and recommendations. do not claim causal isolation or peer parity without supporting evidence.
- retain missing data as missing. preserve source payloads before transformation. synthetic or transformed records must not be labeled raw observations.
- record concrete unresolved issues in `docs/issues/<short-name>.md`, including evidence, impact, and resolution criteria. delete resolved records.
- use meaningful verification proportional to the change. copied historical material should be checked for fidelity; documentation changes do not justify running the predecessor's application test suite.
- for the initial slices, use temporary integration/live tests for red/green/refactor, then delete all test code and test-only dependencies after verification. keep useful fixture data and documented facts. a later dedicated slice will define an extremely lightweight lasting integration/live suite; do not build its harness ahead of that slice.
