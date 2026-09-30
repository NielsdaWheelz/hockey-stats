# hockey stats

a hockey statistics website grounded in explicit statistical meaning, inspectable evidence, and reproducible analysis.

the implemented slices preserve source responses and interpret one explicitly selected game's captures offline. modeling, publication and the website follow separately.

- [project brief](docs/brief.md): settled product direction, initial scope, evidence requirements, and phase boundaries.
- [architecture interview](docs/architecture.md): dependent decisions, recommendations, and remaining evidence.
- [implementation plan](docs/plan.md): small, non-overlapping slices and their dependencies.
- [product roadmap](docs/roadmap.md): proposed v2+ capabilities, separate from the first-build slices.
- [capability inventory](docs/product-inventory.md): skater/goalie components, cards and supporting views; confirmed scope versus candidates.
- [first slice](docs/specs/01-capture.md): faithful source capture and a compact offline corpus.
- [pr2 specification](docs/specs/02-interpretation.md): offline source interpretation; on-ice reconstruction follows separately.
- [council synthesis](docs/research/council.md): recommendations, disagreements, and tradeoffs.
- [product survey](docs/research/product-survey.md): useful products, features, philosophies, and user friction.
- [statistical methods](docs/research/statistical-methods.md): what the different models actually estimate.
- [systems and data](docs/research/systems-and-data.md): effect/python candidates, provenance, and offline data requirements.
- [legacy audit](docs/legacy/README.md): archive, salvage inventory, and historical source dossiers.
- [unresolved issues](docs/issues/): concrete findings and what would resolve them.

the predecessor is preserved at [hockey-stats-legacy](https://github.com/NielsdaWheelz/hockey-stats-legacy). its code is available locally under `.reference/hockey-stats-legacy/`; that directory and the git mirror beside it are excluded from this repository. historical research copied here is explicitly marked as historical and has a digest manifest.

the product direction is settled: interpretable, history-informed estimates of 5v5 skater chance creation and suppression, with observed results alongside. begin with a completed regular season; add current-season analysis afterward. processing and fitting run locally with the hdd whenever the user chooses; the website independently serves the last valid publication with its evidence cutoff. effect owns application behavior; python owns numerical work.

the long-term goal is to replicate hockeyviz's player-card and component-analysis capabilities and jfresh's player cards, built piece by piece. [card references](docs/research/player-card-references.md) record the distinction between that destination and the initial target.

## capture

use the node version pinned in `app/.node-version`. install the locked dependencies once, then request one game into a new directory whose parent already exists:

```sh
mkdir -p var/captures
cd app
npm ci
npm run capture -- --game 2025020001 --out ../var/captures/example-01
```

the command requests play-by-play, boxscore, shift charts and the official game-summary report sequentially. each source gets `body.bin` and `capture.json`. the body contains the bytes delivered by the http client after content decompression and before text decoding or parsing; its record identifies the request, received headers, byte count and sha-256 digest. capture does not establish game identity, collection completeness or analytical validity.

exit `0` means all four requests returned complete 2xx bodies. exit `1` includes invalid arguments, local failures, incomplete requests, redirects and upstream errors. complete error/redirect bodies are preserved. transport failures still allow later sources to be attempted; filesystem failure stops immediately. there are no automatic retries or redirects. inspect the records and rerun into a new directory after repairing a failure. an interrupted body without a complete record is unfinished and may be removed manually.

downloads under `var/` are ignored. [the offline corpus](fixtures/README.md) contains two fresh, inspected example games with explicit evidence limits; it is not a training dataset. run `npm run typecheck` from `app/` to check application types. temporary integration/live checks for this slice are deleted after verification, as requested; later changes must recreate them until the lightweight testing slice.

## interpretation

prepare the python package once with uv and the pinned ordinary cpython version, then invoke its installed command directly. the output parent must exist; the output file must be new and outside the capture directory:

```sh
mkdir -p var/interpreted
cd analysis
uv sync --locked
.venv/bin/hockey-stats-interpret --capture ../fixtures/captures/2025020001 --out ../var/interpreted/2025020001.json
```

the command reads four fixed capture records, verifies body lengths and digests, and interprets supported completed regular-season json sources. it retains source order, missing values, reported results, event locations and shift records, with source locators and named reconciliations. the html report remains manually inspected reference evidence. no network or external drive is needed.

exit `0` means at least one core source passed game identity, type and state admission, after the document was written. collection gaps and reconciliation mismatches remain explicit in that document. if neither core source is usable but the requested id is known, a diagnostic is saved and exit is `1`. malformed capture contracts, conflicting admitted identities and filesystem failures exit `1` without a successful document; invalid argument syntax exits `2`. `--help` exits `0`.

captures remain unchanged. reported coordinates are not inferred shooting origins; shift arithmetic is not on-ice membership or genuine-5v5 exposure. available boxscore groups remain inspectable when a sibling group is unavailable; located issues identify incomplete lists. interpretation records the commit, changes under `analysis/` and python version. dirty or unidentified results are development outputs, not reproducible solely from a commit. remove an interrupted output manually and rerun into a new file. one fully loaded game document favors inspection over bulk storage; sqlite remains the later publication format. json escapes non-ascii text while preserving decoded strings.

temporary end-to-end checks are deleted after verification. the inspected fixture facts remain; changes must recreate checks until slice 07. later slices remain outlines until their inputs and requirements are concrete. the brief supersedes earlier research recommendations where the user has resolved a choice.
