# hockey stats

a hockey statistics website grounded in explicit statistical meaning, inspectable evidence, and reproducible analysis.

the first implemented slice preserves source responses for one explicitly selected game. modeling, publication and the website follow separately.

- [project brief](docs/brief.md): settled product direction, initial scope, evidence requirements, and phase boundaries.
- [architecture interview](docs/architecture.md): dependent decisions, recommendations, and remaining evidence.
- [implementation plan](docs/plan.md): small, non-overlapping slices and their dependencies.
- [first slice](docs/specs/01-capture.md): faithful source capture and a compact offline corpus.
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

later slices remain outlines until their inputs and requirements are concrete. the brief supersedes earlier research recommendations where the user has resolved a choice.
