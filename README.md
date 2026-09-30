# hockey stats

a hockey statistics website grounded in explicit statistical meaning, inspectable evidence, and reproducible analysis.

the implemented slices preserve source responses, interpret one explicitly selected game's captures offline, reconstruct reported event membership, elapsed exposure and recorded coordinates, audit a season inventory against explicit local captures, and exercise the specified chance-model workflow. 03b has completed fresh three-season acquisition, real chronological development/confirmation and scientific comparison/recovery. [the scientific decision](docs/research/chance-03b/decision.md) rejects the declared all-attempt use; 04 is withheld. publication and the website follow separately.

- [project brief](docs/brief.md): settled product direction, initial scope, evidence requirements, and phase boundaries.
- [architecture interview](docs/architecture.md): dependent decisions, recommendations, and remaining evidence.
- [implementation plan](docs/plan.md): small, non-overlapping slices and their dependencies.
- [product roadmap](docs/roadmap.md): proposed v2+ capabilities, separate from the first-build slices.
- [capability inventory](docs/product-inventory.md): skater/goalie components, cards and supporting views; confirmed scope versus candidates.
- [first slice](docs/specs/01-capture.md): faithful source capture and a compact offline corpus.
- [pr2 specification](docs/specs/02-interpretation.md): offline source interpretation; reconstruction has its own command.
- [pr2b specification](docs/specs/02b-reconstruction.md): reported event membership, reconstructed exposure and coordinates.
- [pr2c specification](docs/specs/02c-corpus.md): season inventory, bulk player references and offline corpus accounting.
- [pr03a specification](docs/specs/03a-chance-workflow.md): chance-model workflow and software verification.
- [pr03b specification](docs/specs/03b-training-acceptance.md): fresh three-season corpus, chronological development/confirmation and scientific judgment.
- [pr03c specification](docs/specs/03c-source-revision.md): reviewed and merged; source contracts, expanded fixtures and [full three-season audit](docs/research/chance-03c/decision.md) verified.
- [pr03d specification](docs/specs/03d-chance-revision.md): implemented chance-2 contract; [fixture verification](docs/research/chance-03d/verification.md) establishes software behavior, with review pending.
- [later pr stubs](docs/plan.md#next-slices): 03e–07 retain ownership, dependencies and unresolved decisions; expand each before implementation.
- [pr03c research](docs/research/chance-03c-source-audit.md): overlooked report shot types, measured model coupling and limits of public origin evidence.
- [external-data audit](docs/research/external-corpus-audit.md): inspected legacy database, fidelity findings and fresh-acquisition decision.
- [corpus/reference audit](docs/research/corpus-reference-audit.md): verified season sources, coverage and source limitations.
- [source audit](docs/research/source-audit.md): direct public evidence, omissions corrected and later input dependencies.
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

the command requests play-by-play, boxscore, shift charts, the official game-summary report, the official per-event on-ice report and gamecenter landing sequentially. each source gets `body.bin` and `capture.json`. the body contains the bytes delivered by the http client after content decompression and before text decoding or parsing; its record identifies the request, received headers, byte count and sha-256 digest. capture does not establish game identity, collection completeness or analytical validity.

exit `0` means every requested response returned a complete 2xx body: six for a default game capture, one for landing-only, four for a season capture. exit `1` includes invalid arguments, local failures, incomplete requests, redirects and upstream errors. complete error/redirect bodies are preserved. transport failures still allow later sources to be attempted; filesystem failure stops immediately. there are no automatic retries or redirects. an interrupted body without a complete record is unfinished local work and may be removed manually.

add only landing to an existing game capture:

```sh
npm run capture -- --game 2025020001 --source landing --out /absolute/existing/game-directory
```

the parent must contain a readable version-1 `play-by-play/capture.json` naming this game and source. `--source` accepts only `landing`, once. an existing landing leaf fails before network access. for replacement, explicitly prepare a new game-directory copy without its landing leaf, preserving the original directory and any existing landing evidence. the command neither overwrites nor resumes. new retrieval dates remain distinct from the five earlier responses.

downloads under `var/` are ignored. [the offline corpus](fixtures/README.md) contains three fresh, inspected example games with explicit evidence limits; it is not a training dataset. run `npm run typecheck` from `app/` to check application types. temporary integration/live checks for this slice are deleted after verification, as requested; later changes must recreate them until the lightweight testing slice.

## interpretation

prepare the python package once with uv and the pinned ordinary cpython version, then invoke its installed command directly. the output parent must exist; the output file must be new and outside the capture directory:

```sh
mkdir -p var/interpreted
cd analysis
uv sync --locked
.venv/bin/hockey-stats-interpret --capture ../fixtures/captures/2025020001 --out ../var/interpreted/2025020001.json
```

the command reads six fixed capture records, verifies body lengths and digests, and interprets supported completed regular-season json sources. absent landing remains an explicit source gap. interpretation schema 3 retains source order, missing values, reported results, event locations, shift records, report shooting participants/types and landing scoring rows, with source locators and named reconciliations. the play report supplies attributed event on-ice lists; the game-summary report remains manually inspected reference evidence. no network or external drive is needed.

exit `0` means at least one core source passed game identity, type and state admission, after the document was written. collection gaps and reconciliation mismatches remain explicit in that document. if neither core source is usable but the requested id is known, a diagnostic is saved and exit is `1`. malformed capture contracts, conflicting admitted identities and filesystem failures exit `1` without a successful document; invalid argument syntax exits `2`. `--help` exits `0`.

captures remain unchanged. reported coordinates are not inferred shooting origins. interpretation preserves source facts; reconstruction separately derives elapsed membership and genuine-5v5 exposure. available boxscore groups remain inspectable when a sibling group is unavailable; located issues identify incomplete lists. interpretation records the commit, changes under `analysis/` and python version. dirty or unidentified results are development outputs, not reproducible solely from a commit. remove an interrupted output manually and rerun into a new file. one fully loaded game document favors inspection over bulk storage; sqlite remains the later publication format. json escapes non-ascii text while preserving decoded strings.

temporary end-to-end checks are deleted after verification. the inspected fixture facts remain; changes must recreate checks until slice 07. later slices remain outlines until their inputs and requirements are concrete. the brief supersedes earlier research recommendations where the user has resolved a choice.

## reconstruction

from the prepared python environment, read the captures directly into one offline reconstruction document:

```sh
mkdir -p var/reconstructed
cd analysis
.venv/bin/hockey-stats-reconstruct --capture ../fixtures/captures/2025020001 --out ../var/reconstructed/2025020001.json
```

both options occur exactly once. the output parent must exist; the output file must be new and outside the capture directory. the envelope contains schema version 3, one implementation identity, schema-version-3 interpretation, and reconstruction. chance preparation rejects older versions; regenerate cheap derived corpora from preserved captures. historical artifacts remain usable at their historical git revision.

reported event membership comes from period/clock/kind matching to the official play report. repeated attempt groups require one complete assignment supported by exact team, shooter and known type constraints; missing facts add no constraints. singleton type disagreement leaves membership intact and the type conflicting. reconstruction keeps both original type spellings and their reconciled evidence. landing goals join unique event ids with period, reported clock, team and credited-scorer corroboration. a joined penalty-shot modifier enforces the existing exclusion. own/awarded or unresolved goal modifiers remain in recorded scores and diagnostics, with unavailable analytical physical shooter; they are excluded from chance-2. exact type reconciliation now admits eleven canonical types, including `between-legs` and `cradle`.

elapsed intervals come from coherent shifts, with both goalies required for genuine 5v5. neither source fills gaps in the other. unresolved matches and intervals remain visible. coordinate rotation uses the reported defending side; recorded block locations remain block locations. shooting origins, chance values, player attempt totals, rates and model eligibility are not computed.

exit `0` means an admitted game has at least one supported elapsed interval or timed event, after writing the document. an available diagnostic with no supported classification exits `1`; successful execution does not certify completeness. argument syntax/help and filesystem rules match interpretation. the command summary separates time, attempt, exposure-link and location coverage; detailed located reasons remain in the document. missing collections and unsupported quantities stay null, while supported empty arrays and zero totals remain distinct.

[fixture facts](fixtures/README.md) record source admission, checked boundaries, the penalty-shot goal and shortened overtime example, and the limits of cross-export corroboration. reconstruction requires no network or external drive. future models must choose a coherent event/exposure population and evaluate selective missingness before claiming an ability estimate.

## season references and corpus audit

capture the four fixed season sources into a new directory, with its parent already created:

```sh
mkdir -p var/references
cd app
npm run capture-season -- --season 20252026 --out ../var/references/20252026
```

`--season` and `--out` occur once. season years must be consecutive. `--help` alone exits `0`; invalid invocation exits `1`. the command preserves the season summary, regular-season game inventory, skater bios and goalie bios using the same response-capture implementation as game acquisition. exit `0` requires four complete 2xx responses; content admission happens offline. each source's receipt names its season, exact filtered request, retrieval time, headers, length and digest. failures retain their http/body/transport distinctions; later requests continue after upstream failures, while filesystem errors stop. no retries, alternate sources or automatic downloading are added.

audit the admitted fixture references against the three local game captures:

```sh
mkdir -p var
cd analysis
uv sync --locked
.venv/bin/hockey-stats-corpus --reference ../fixtures/references/20252026 --games ../fixtures/captures --out ../var/corpus-20252026
```

all three options occur exactly once. roots must exist; output must be new, have an existing parent and lie outside both roots. inventory metadata establishes the season; inventory rows establish the population. the audit looks up exactly `<games-root>/<game-id>` for every admitted inventory row, reusing interpretation and reconstruction directly. unrelated directories are ignored. it writes per-game reconstruction envelopes under `games/`, then `corpus.json` last. resolved input paths and relative output links make the selection explicit.

exit `0` means the admitted inventory was accounted for and the report written, even with missing captures, missing bios or reconstruction gaps. unsupported inventory writes a diagnostic report with null populations and exits `1`. per-game local integrity or requested-identity errors remain actionable rows, allow later games to run, and produce exit `1`. unavailable or conflicting upstream game identity keeps its diagnostic but contributes no roster or coverage aggregates. reference integrity and filesystem errors stop immediately. syntax exits `2`; help exits `0`. a directory without its final report is unfinished: remove cheap partial outputs manually and rerun into a new directory.

coverage totals separately retain time, attempts and locations, each with contributing and unavailable game counts. players are ids seen in available admitted rosters, including unused goalies, not participants or a league-wide player population. bio fields join independently: one known value supplies a field; conflicting values leave it null. observations and located issues remain inspectable. no age, historical affiliation, model eligibility or training-ready claim follows from this audit.

to acquire missing games, create the chosen game root, then run an ordinary sequential loop from `app/`. the audit supplies ids; no transcription or batch platform is required:

```sh
../analysis/.venv/bin/python - ../var/corpus-20252026/corpus.json ../var/captures <<'PY'
import json
from pathlib import Path
import subprocess
import sys

report = json.loads(Path(sys.argv[1]).read_bytes())
games = Path(sys.argv[2]).resolve(strict=True)
for game_id in report["missing_game_ids"]:
    subprocess.run(["npm", "run", "capture", "--", "--game", game_id,
                    "--out", str(games / game_id)], check=True)
PY
```

the loop stops on the first failed capture so its receipt can be inspected. rerun an audit into a new output directory after acquisition; a present failed capture is evidence to inspect, not an absent directory eligible for silent overwrite. full-season accounting costs per-game json storage and makes the small local sample visibly incomplete. historical admission and scientific assessment remain separate work.

## chance workflow

`hockey-stats-chance` provides separate offline `fit`, `evaluate` and `score` commands for `chance-2`. [fixture instructions](fixtures/chance/README.md) supply the three-season selections, exact numerical exercise configuration and commands. all eighteen compact games rebuild from their three committed season references without network or external drive.

fitting jointly estimates type/context-dependent origin maps and unblocked probabilities, then conversion given unblocked, with actor-season shrinkage and two factual benchmarks. scoring values recorded opportunity under one target-season joint shooter–goalie reference, holding type and recorded preceding-play/scalar context fixed. unblocked coordinates remain contact/origin proxies; blocks retain observed contact evidence and receive conditional origin distributions. tips are retained without relocation.

evaluation separately reports unblocked conversion, recorded-context all-attempt goal probability, marginal unblocked probability and the joint observed-record likelihood. the latter marginal predictions omit focal location, outcome and posterior; retrospective type and eligibility measurements still prevent a demonstrated pre-release forecast claim. calibration summaries explicitly name the outcome and observed positive count. positive standardized block opportunity is not calibrated against observed blocked zeros.

schema-2 `model.json` is written last after numerical success and alone suffices to score. `fit.json` records numerical completion or failure. schema-2 `score.json` is written last with the matching `attempts.jsonl` digest. assessment requires disjoint games dated strictly after training and never changes the fit or reference. output paths must be new, outside inputs, with existing parents; remove cheap interrupted outputs manually and rerun into new paths. syntax/help exits `2`/`0`; input, numerical and filesystem failures exit `1`; completed artifacts with ordinary evidence gaps exit `0`.

fixture artifacts retain `purpose: fixture_exercise` and `scientific_assessment: not_performed`. complete numerical fits do not establish calibration, physical-origin accuracy, player skill or scientific support. [03d software verification](docs/research/chance-03d/verification.md) records the checks and costs; [03e](docs/specs/03e-training-assessment.md) owns any separately authorized real fitting and assessment. 03b's scientific rejection remains intact. player attribution belongs to 04.

## numerical recovery and historical research

fitting writes schema-2 `checkpoint.json` atomically after completed starts and accepted em updates. optional `--resume /abs/old-fit/checkpoint.json` continues accepted state into a **new** `--out` directory. use identical input bytes, selection, configuration, clean git revision and pinned numerical environment. dirty exploratory fits can complete but cannot resume. preparation, conversion and benchmarks recompute; interrupted inner solves repeat from the preceding accepted state. preserve expensive fits and failed diagnostics; there is no automatic retry or acceptance of unconverged state.

chance-1 envelopes, configs, models and checkpoints are rejected by the active workflow. regenerate cheap reconstruction envelopes from unchanged captures. preserved 03b research artifacts and comparisons require their historical git revision; [the 03b decision](docs/research/chance-03b/decision.md) remains scientific evidence, not an active chance-2 run recipe. the retained `analysis/research/chance_review.py` comparison belongs to a separately specified 03e adaptation before reuse. no historical comparison is silently rerun with changed populations or observation laws.

scoring applies saved contiguous actor-season states. intermediate unobserved seasons retain their fitted penalized states; later seasons carry the latest state forward and label that choice. records before the earliest state remain unavailable with `season_unsupported`. stage-specific actor evidence distinguishes observations in the applied state, observations only in other seasons, and unseen zero prior modes. none implies rookie status. historical scoring is retrospective analysis, not a forecast available at the game's date.

## source review

after regenerating a corpus, run the retained source operator from `analysis/`:

```sh
.venv/bin/python research/source_review.py --selection /absolute/selection.json --out /absolute/new-review-directory
```

the selection uses the existing chance-selection schema and purpose (`fixture_exercise` or `research`). output must be new, outside input directories, with an existing parent. preparation validates the selected envelopes; review rereads those envelopes for source-wide counts. finite schema-1 `review.json` is written last. ordinary source gaps succeed with explicit dispositions; malformed inputs fail. source rows, matched events and eligible attempts retain separate denominators. type reconciliation supplies diagnostics, not a new predictor; the narrow non-goal clock repair retains all source issues.

[the 03c decision](docs/research/chance-03c/decision.md) records the completed three-season before/after audit, detached verification and remaining source limitations. all three seasons are development/comparison evidence after 03b. no refit or revised scientific verdict is implied.
