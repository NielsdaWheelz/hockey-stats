# qualification ownership and plan consistency

scope: read-only bounded review while the first real fit remains active. no analysis edit, artifact read/rewrite, source pass or numerical job was performed.

## qualification

`player_mechanisms.py::_qualification` has an accidental fallback from `coverage.qualification` to `coverage.players` and then an empty dictionary. it has one caller. neither alternative is a valid current mechanism design: `mechanism_state.py::validate_design` requires both maps, requires their equality, and checks the qualification player axis against the ordered player axis. both source builders assign the same dictionary to both keys. repository search found no distinct mechanism consumer or meaning for the `players` copy.

smallest strict correction: remove the once-used accessor and read `design.coverage['qualification'][player]` at its caller. the existing design contract already establishes both keys and the player membership. valid output is unchanged, and there is one mandatory runtime owner.

retain the two serialized fields and their equality check in this frozen schema1 contract. they are redundant metadata, not two model concepts, but completed fixture artifacts and the active real command bind them in saved design/coverage bytes. deleting a field now would either invalidate those artifacts, rewrite their identity graph or introduce a second format. none is justified or assigned. the explicit cost is a redundant serialized mirror; no migration, fit rerun or backward-compatible path is required for the direct-index correction.

## plan

`docs/plan.md` current-boundary correctly records both v1-10 and v1-19 as separately assigned on 2026-11-14, coordinated on one current exchange4/schema10 foundation, with heavy commands serialized and activation unassigned.

the two stale next-handoff rows are now corrected:

- line130 previously called v1-10 implementation unassigned; it now records assigned/in progress; software and ten fixture heads/two probes are reviewed, while real annuals, references, composition and final acceptance remain ongoing.
- line131 previously called v1-19 the next independent full specification; it now records separately assigned/in progress, retaining the existing finite product boundary and no-new-fit limitation.

the proposed pr-boundary/dependency rows describe responsibilities rather than contradictory assignment states. no broader status rewrite or historical-verdict change is needed.

prepared `.tmp/v1-10/strict-qualification.patch` for root to apply after the active annual finishes. `git apply --check` passes. the patch removes only the once-used accessor and replaces its call with the canonical index; the validated present key returns the identical dictionary entry. active analysis and all artifact bytes remain untouched.

## strict qualification correction

the prepared patch is applied after first-annual completion: the once-used fallback helper is removed, and projection reads the mandatory `design.coverage['qualification'][player]` directly. both serialized schema1 maps and their equality validator remain byte-unchanged in their source owners.

temporary pure controls first demonstrated that both families accepted a missing canonical map through the fallback; both now reject that malformed input. valid canonical projection/support/reference/center outputs match the pre-edit snapshot exactly. all other numerical functions, including recipe construction, remain ast-identical. bounded cli/ownership/mathematics/source checks pass in the [repair receipt](../receipts/cli-ownership-repair.json). no fit, full predecessor/design read or source pass was used, and no further sequencing or plan rewrite was needed.
