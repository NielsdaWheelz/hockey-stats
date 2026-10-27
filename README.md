# hockey stats

a hockey statistics website grounded in explicit statistical meaning, inspectable evidence, and reproducible analysis.

the project preserves source evidence and implements offline hockey reconstruction, feature preparation, chance-model research and a private observed-results website. the [implementation plan](docs/plan.md) owns current status, assignments and next steps; scientific completion and software completion are distinct.

- [project brief](docs/brief.md): settled player question, scope and user choices.
- [architecture](docs/architecture.md): responsibilities, contracts and one-operator operation.
- [implementation plan](docs/plan.md): current direction, lean next specs and completed-study index.
- [model direction](docs/research/model-direction.md): scientific rationale, alternatives and limits.
- [roadmap](docs/roadmap.md) and [capability inventory](docs/product-inventory.md): full player-analysis destination.
- [feature repertoire](docs/model-features.md): retained facts/encoders, scientific use and source dependencies.
- [council](docs/research/council.md), [source audit](docs/research/source-audit.md), [input audit](docs/research/model-input-audit.md), [product survey](docs/research/product-survey.md) and [statistical methods](docs/research/statistical-methods.md): attributable research.
- [fixtures](fixtures/README.md), [lasting-check scope](docs/specs/07-lightweight-testing.md) and [unresolved issues](docs/issues/): software evidence and remaining limitations.

the predecessor is preserved at [hockey-stats-legacy](https://github.com/NielsdaWheelz/hockey-stats-legacy). its code is available locally under `.reference/hockey-stats-legacy/`; that directory and the git mirror beside it are excluded from this repository. historical research copied here is explicitly marked as historical and has a digest manifest.

the product direction is settled: interpretable, history-informed estimates of 5v5 skater chance creation and suppression, with observed results alongside. begin with a completed regular season; add current-season analysis afterward. processing and fitting run locally with the hdd whenever the user chooses; the website independently serves the last valid publication with its evidence cutoff. effect owns application behavior; python owns numerical work.

the long-term goal is to replicate hockeyviz's player-card and component-analysis capabilities and jfresh's player cards, built piece by piece. [card references](docs/research/player-card-references.md) record the distinction between that destination and the initial target.

## private observed results

the localhost-only website shows included recorded 5v5 results: personal shots on goal, goals and primary assists alongside team attempts while on ice. each population has its own matched time, rates and coverage. search/sort the league table, filter by reported position, listed season team and minimum included minutes, then open a compact observed profile, inspect peer distributions and game evidence, or compare two players. spatial views add matched recorded unblocked attempts for/against, shown against the included league average or as absolute rates. these are unadjusted observations; no fitted ability or xg enters this publication. comparative cards place the five recorded rates among explicitly selected peers; higher percentile always means a higher recorded rate, including opponent attempts. [observed-results contract](docs/specs/05a-observed-website.md) · [05a verification](docs/research/observed-05a/verification.md) · [comparison contract](docs/specs/05b-observed-comparison.md) · [05b verification](docs/research/observed-05b/verification.md) · [explorer contract](docs/specs/05c-player-explorer.md) · [05c verification](docs/research/observed-05c/verification.md) · [descriptive-card contract](docs/specs/05d-descriptive-cards.md) · [05d verification](docs/research/observed-05d/verification.md) · [spatial contract](docs/specs/05e-spatial-views.md) · [05e verification](docs/research/observed-05e/verification.md) · [comparative-card contract](docs/specs/05f-comparative-observed-cards.md) · [05f verification](docs/research/observed-05f/verification.md)

05g adds 2023–24 through 2025–26, with a shared season selector and three-row player history. [history contract](docs/specs/05g-observed-history.md) · [verification](docs/research/observed-05g/verification.md). the earlier schema-6 activation is recorded in [historical activation evidence](docs/research/observed-05h/verification.md#explicit-activation). the active schema-7 publication and current rollback identities are tracked in [v1-16 activation](docs/research/application-v1-16/activation.md).

02d's [accepted source/exposure assessment](docs/research/source-02d/verification.md) removes 132 physical seconds across three contradictory runs, with unchanged included counts. eighteen recovery requests supply no matched support; all 57 gaps remain. the pinned schema-5 candidate and bounded frozen-ledger audit remain attributable evidence. schema 6 inherits the settled observed policy.

05h adds selected-season teammate/opponent tables from every retained on-ice interval, including zero-event time. shared minutes and overlapping shares use the selected player's included 5v5 time; peer filters do not change deployment. each table starts with ten rows and expands locally to all counterparts. a player may occur in both after a trade. these are recorded relationships, without quality or chemistry claims. schema 6 preserves the checked 02d population and all prior facts. [deployment contract](docs/specs/05h-observed-deployment.md) · [verification](docs/research/observed-05h/verification.md). the active schema-7 publication has its own [activation record](docs/research/application-v1-16/activation.md).

use node `24.21.0`, pinned in `app/.node-version`. stop the running server before rebuilding its assets or replacing its publication. on this mac, explicitly put the installed node executable first so npm's children use the same runtime:

```sh
export PATH="$HOME/.local/share/mise/installs/node/24.21.0/bin:$PATH"
cd app
node --version
npm ci --include=dev
npm run typecheck
npm run build
npm run serve -- --publication /absolute/schema-7-candidate/player-analysis.sqlite --port 3067
```

to review another revision, build a separate checkout with the pinned node path above and serve it on a separate port:

```sh
cd /absolute/review-checkout/app
npm ci --include=dev
npm run typecheck
npm run build
npm run serve -- --publication /absolute/schema-7-candidate/player-analysis.sqlite --port 3067
```

open `http://127.0.0.1:3067/`. this revision reads schema 7 only. the active schema-7 publication is tracked in [the current activation record](docs/research/application-v1-16/activation.md). use a separately built checkout and unused port to inspect another candidate. only its sqlite file is needed for browsing. rebuild compatible applications from git; no archived build is needed.

the server validates one existing read-only database before listening and needs the built `dist/client/` assets. source roots, python, the external drive and external network are unnecessary for browsing. stop it with ctrl-c before replacing the publication. no lan host option is provided.

discovery filters intersect and start with every published player, including low-minute names. choose a reported forward/defense group or a listed season team; type a nonnegative whole-minute minimum, then press enter or apply. the team filter matches season membership and keeps whole-season values, including other teams. `clear filters` preserves sorting. invalid minute drafts leave displayed results unchanged.

the season selector changes the league list, seasonal identities, peers, maps and game evidence together. it preserves committed discovery/reference/detail/map settings and comparison ids. a team filter absent from another season remains visible with zero matches. searches and pickers use the selected season only. omitted direct links resolve to the newest published season and record it in the url without a second request; explicit invalid or unpublished seasons show recovery links. browser loading hides the previous year's facts until the response arrives.

profiles place a linked, newest-first history table between the selected-season card and its detail. each row retains that year's name, teams/reported position, five raw rates, separate personal/on-ice minutes and coverage, and any global unassigned-game gap. missing records stay explicit; a present record with unavailable support retains its reasons. history has no percentiles, pooled totals or trajectory claim. raw annual differences can reflect league environment, missingness or deployment. `no published player record` establishes neither zero production nor whether the player played.

use `compare players` above the league table, or `compare this player` on a profile. each comparison slot has a name search and explicit result buttons; typing does not change the selected player. choose two distinct skaters to see their existing counts, rates, matched minutes and coverage side by side. `clear first player` and `clear second player` repair either selection. a direct `/compare?season=20242025&a=<first-player-id>&b=<second-player-id>` link preserves season and slot order on reload. an absent selection keeps its id and profile/history link; the pair card, distributions and maps wait for both seasonal records.

each column describes that player's own included evidence; the players need not share games, teammates, opponents or gaps. attempts for are the player's team's attempts while on ice, not personal shots. the summary table supplies no adjusted comparisons or ability estimates. spatial maps show descriptive rate differences from that season's physical league reference. profile links open listed-game evidence with `back to comparison`; `back to players` restores the recorded originating league destination, including its season, filters and sort. return context lives only in browser history: a copied or new-tab profile link returns to the selected season's unfiltered league. site home also uses the selected season.

profiles and complete comparisons show five rows: personal shots on goal, goals and primary assists, then on-ice attempts for and against. each pairs a raw rate per 60 included minutes with an observed-rate percentile. the percentile counts lower rates plus half of exact ties, using unrounded published rates. higher always means more of the recorded rate; against is not reversed into a defense rating.

the default reference uses the selected player's reported forward/defense group and at least 300 included 5v5 minutes. personal and on-ice cohorts apply that cutoff to their own time and retain eligible partial records. mixed-position pairs use separately named groups; all-skater mode shares one group per family. membership uses exact seconds, even when displayed minutes round alike. below-floor players keep their raw values and highlights without a percentile; unavailable rates have no mark. empty and singleton references are explicit.

`detail metric` chooses one raw-rate rug and expandable numeric peer table; all five overview rows stay visible. both comparison selections share the detail's increasing raw-unit axis. reference group, minute minimum and metric edits use the loaded response without another request. `reset peers` restores position/300 while preserving the metric, map mode and selected players.

the league also sorts personal shots on goal/60, goals/60, primary assists/60 and personal included minutes. discovery minimums and game counts continue to use on-ice time; peer membership uses each metric family’s included time. profiles and comparisons show personal counts and rates; game rows expose their contributions and coverage. shots on goal include scored and saved shots; goals are already included. primary assists are first credited assists, not all assists or measured passing. goal strength selects credit even after an assister changes off. personal support can be smaller than on-ice support; its common denominator excludes a whole segment when credit is unresolved. neither population is an official complete total.

profiles and comparisons show where recorded unblocked attempts occurred during independently matched spatial time. the default difference from the included league average and `map=absolute` use the same fixed display smoothing: five-foot bins; gaussian standard deviation ten feet. both for/against maps use the shooting team’s frame, attacking toward the top; right is positive y. every available panel shares one scale, which changes with selection. red means more attempts, not better performance. the included league reference shows its own selective coverage and two team-directions per physical minute; peer controls do not alter it.

spatial minutes can differ from on-ice and personal minutes: a missing coordinate, unresolved frame or outside-rink event removes its whole assigned segment’s counts and time for both teams. zero-event time remains. positive-time zero attempts give zero absolute density; no time gives no rate map. expandable tables retain integer recorded counts, raw bin rates and displayed densities/differences for every cell. game rows reconcile spatial counts/time with the season. smoothing is descriptive pooling, not statistical precision or isolated ability; maps stay in the browser.

from a loaded, present profile, `download player png` saves one compact 1200-pixel-wide image with all five counts/rates/percentiles, both support and reference summaries, seasonal identity, source/coverage context and publication time/id. the image and filename name the selected season. facts and settings are captured synchronously at the click; navigation during export does not change that snapshot. it uses browser rendering without a request or reaggregation. long names grow the image; full reasons, raw-rate detail, maps and history remain on the page. failed export permits retry.

the peer minute cutoff is a viewing rule, not evidence of reliability. each eligible player contributes one mark, including partial records; shared play makes these related observations. discovery filters do not change peers. `/players/<id>?peers=all&peerMin=0&metric=goals60` and `/compare?a=<id>&b=<id>&peers=all&peerMin=0&metric=against60` retain reference and detail settings on reload. `metric` accepts `sog60`, `goals60`, `primaryAssists60`, `for60` or `against60`, defaulting to `sog60`. invalid, empty or repeated metric keys normalize by history replacement while preserving unrelated keys. profile/comparison/peer links carry committed settings; return links restore the recorded destination context and retain existing map-mode behavior. plots describe observed results, not uncertainty or ability.

development’s api uses port 3000, so stop its existing server before that development workflow; separate built-candidate review leaves it running. development uses two terminals, each in `app/` with the pinned node executable first:

```sh
npm run dev:api -- --publication /absolute/schema-7-candidate/player-analysis.sqlite
```

```sh
npm run dev:web
```

open `http://127.0.0.1:5173/`; `/api` proxies to `http://127.0.0.1:3000`. development api mode omits asset serving. both listeners bind only to loopback. browser and server have separate type checks; the build rejects browser imports of node/sqlite or server/operator implementations.

to build a new candidate, prepare the locked python environment from the repository root and choose a new output directory whose parent exists:

```sh
cd analysis
uv sync --locked
.venv/bin/hockey-stats-analysis publish --observed /absolute/observed-selection.json --results /absolute/completed-results --out /absolute/new-candidate
```

the observed selection has exactly `schema_version:1`, `purpose:"real"|"fixture"` and an ascending `corpora` list of `{season,path,sha256}`. corpus paths are absolute existing files with distinct resolved identities; digests bind their exact bytes. real selections require all three declared seasons and both pinned 2024–25/2025–26 corpus identities. 2023–24 uses the freshly prepared, frozen corpus recorded in verification; preparation uses the existing native command and local originals specified in the history contract. fixtures select one to three explicitly marked fixture corpora and cannot become real. no implicit discovery, acquisition or subset selector exists.

02d's offline recovery review and assessment use fresh output directories. from the repository root, after preparing the locked python and application environments:

```sh
analysis/.venv/bin/python analysis/research/source_exposure.py recovery \
  --corpus /absolute/original-20242025/corpus.json \
  --captures /absolute/three-probe-captures --out /absolute/new-recovery-review
analysis/.venv/bin/python analysis/research/source_exposure.py assess \
  --original-selection /absolute/original-selection.json \
  --selected-selection /absolute/selected-selection.json \
  --baseline /absolute/schema-4-baseline/observed.sqlite \
  --candidate /absolute/schema-5-candidate/observed.sqlite \
  --recovery /absolute/new-recovery-review/recovery.json \
  --attribution-result /Users/nnandal/Documents/code/hockey-stats/docs/research/attribution-04b/result.json \
  --out /absolute/new-assessment
```

recovery performs no acquisition; its capture directory must already contain the exact three probes. conditional expansion uses `--probe-receipt` and all 57 complete bundles only after useful matched support is verified. assessment reuses the pinned application peer calculator, so `app/node_modules` and the pinned node executable must be available. assessment exits `0` when complete, `1` when required research evidence remains pending, and `2` on an input error. [02d verification](docs/research/source-02d/verification.md) binds the real selection, failed recovery, checked candidate and complete acceptance evidence.

`publish` requires both the observed selection and an explicitly selected result bundle. [v1-13](docs/specs/v1-13-typed-publication.md) defines the fixed manifest, catalogs, family tables and missing states; producers call `write_results` to serialize them. an observed-only candidate supplies explicit pending-family dispositions. fixtures remain fixtures, including captured-game examples. no fit, discovery, acquisition or real-model activation is implied.

argument errors exit 2, help exits 0, and contract/i/o failures exit 1. the builder aggregates and independently reads back observed facts, streams strict family members, validates source/method/support identities and cross-record closure, then writes receipts before renaming `player-analysis.sqlite.incomplete` to `player-analysis.sqlite`. existing output is refused. only a completed database is needed for serving; reads never open preparation, fit or receipt paths.

the typed api has five endpoints:

- `/api/league?season=20242025&kind=skater&family=observed&strength=5v5` returns the selected cohort. only league/profile default to the newest season.
- `/api/players/<id>?season=20242025` returns identity, scalar families, observed games/deployment and three-year history, without a league payload.
- `/api/maps?season=20242025&players=<id>[,<id>]&family=observed&strength=5v5&view=effect` returns selected maps and the shared display scale.
- `/api/players/<id>/evidence?season=20242025&family=personal_shots&strength=5v5&outcome=all_unblocked` returns finalized evidence, including unlocated attempts.
- `/api/players/<id>/context?season=20242025&mode=on_off&population=recorded_all_attempts` returns matched dressed-game groups; `with_without` additionally requires one/two teammates.

[v1-13's selector matrix](docs/specs/v1-13-typed-publication.md#reader-and-api-contract) fixes analytical families and compatible selectors. invalid/duplicate/unknown selectors return typed 400; unknown season/person returns 404. a known person absent this season returns 200 with null selected identity and an explicit API `absent` state. unfinished work returns `not_computed`, not zero; ordinary read failures return 500 with retry copy. every response carries publication/season identity and resolving source/method/support catalogs. the old `spatial=` query is removed.

for an explicitly assigned activation, check the candidate, stop serving, then copy/rotate explicitly:

```sh
npm run publication -- check --candidate /absolute/schema-7-candidate/player-analysis.sqlite
npm run publication -- activate --candidate /absolute/schema-7-candidate/player-analysis.sqlite --directory /absolute/publication
npm run serve -- --publication /absolute/publication/active.sqlite
```

activation validates an exclusive incoming copy and reports its digest. it preserves an existing active file as opaque predecessor bytes and reports that byte identity; an incompatible predecessor is checked using its matching git build. exactly one `previous.sqlite` remains. for schema-7 restore, stop serving, run the following, restart and reload:

```sh
npm run publication -- restore --directory /absolute/publication
```

a cross-schema previous file requires the manual procedure below. the current source reads schema **7** only; it retains the authoritative observed reducers and their population/display versions. building/checking a candidate does not activate it, admit a model or complete real player cards. current pages still present the supported observed journeys; direct goalie profiles show identity/history and the explicit unfinished-presentation message.

### manual cross-version cutover and rollback

the historical schema-3 → schema-6 activation is complete. its schema-6 publication `24e41fa7-256c-4f0a-9876-e8d7f8f42056` uses application code `cb13d99`; its then-previous schema-3 publication `84a9da75-2cdf-44e7-a463-21e79a02929e` requires code `d3dee76`. recreate it with `git worktree add --detach <old-checkout> d3dee76`; install its pinned lockfile and rebuild. the old schema-2 backup was replaced by that validated schema-3 active. the separate checked schema-5 baseline still uses `523a4d4`.

the forward example below describes the completed schema-3 → schema-6 procedure. the completed schema-7 activation uses the new operator above, which preserves its predecessor opaquely; [its record](docs/research/application-v1-16/activation.md) owns current identities and rollback instructions. cross-schema rollback always uses manual copies and each database's matching build. build and preflight compatible code on a separate port first, then set paths and stop serving. the subshell aborts on any failed check; an existing incoming file is an error. `cmp` requires exact copy equality before rotation. the completed activation staged and validated the incoming copy before stopping, reducing the interruption.

```sh
(
set -eu
old_app=/absolute/schema-3-checkout/app
new_app=/absolute/schema-6-checkout/app
publication_directory=/absolute/publication
candidate=/absolute/candidate/observed.sqlite
(cd "$old_app" && npm run publication -- check --candidate "$publication_directory/active.sqlite")
(cd "$new_app" && npm run publication -- check --candidate "$candidate")
test ! -e "$publication_directory/incoming.sqlite"
cp "$candidate" "$publication_directory/incoming.sqlite"
cmp -s "$candidate" "$publication_directory/incoming.sqlite"
(cd "$new_app" && npm run publication -- check --candidate "$publication_directory/incoming.sqlite")
mv "$publication_directory/active.sqlite" "$publication_directory/previous.sqlite"
mv "$publication_directory/incoming.sqlite" "$publication_directory/active.sqlite"
(cd "$new_app" && npm run serve -- --publication "$publication_directory/active.sqlite")
)
```

this replaces the previous backup with the validated old active. if interrupted, retain intact files and repair their names manually; do not rerun blind. rollback also stops serving and validates **both** current active and previous with their compatible code before overwriting either backup. use the same filled paths:

```sh
(
set -eu
old_app=/absolute/schema-3-checkout/app
new_app=/absolute/schema-6-checkout/app
publication_directory=/absolute/publication
(cd "$new_app" && npm run publication -- check --candidate "$publication_directory/active.sqlite")
(cd "$old_app" && npm run publication -- check --candidate "$publication_directory/previous.sqlite")
test ! -e "$publication_directory/incoming.sqlite"
cp "$publication_directory/previous.sqlite" "$publication_directory/incoming.sqlite"
cmp -s "$publication_directory/previous.sqlite" "$publication_directory/incoming.sqlite"
(cd "$old_app" && npm run publication -- check --candidate "$publication_directory/incoming.sqlite")
mv "$publication_directory/active.sqlite" "$publication_directory/previous.sqlite"
mv "$publication_directory/incoming.sqlite" "$publication_directory/active.sqlite"
(cd "$old_app" && npm run serve -- --publication "$publication_directory/active.sqlite")
)
```

rebuild the old checkout from git and its pinned lockfile before serving when needed; reload the browser after either restart. same-version activation/restore continue to use the existing commands above. there is no migration or historical-schema reader.

if replacement is interrupted, inspect the intact `active.sqlite`, `previous.sqlite` and `incoming.sqlite` with their matching build's `publication check`, repair the names manually, then restart. an existing incoming file stops another copy. use compatible code from git when needed. there is no hot switching, release manager or automatic cleanup.

matched counts and time lose the same uncertain segments. valid zero-event time survives; missing counts remain missing, while supported zero counts remain zero. incomplete player associations limit every season summary and are listed in coverage details. included minutes are not official full ice time; `covered` means no known relevant gap in source-supported listed evidence. conservative exclusions, source selection and manual publication interruptions are accepted costs. source/model verdicts are unchanged by website completion.

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

downloads under `var/` are ignored. [the offline corpus](fixtures/README.md) contains thirty-six complete game bundles across five seasons, one interrupted bundle and their season references, with explicit evidence limits; it is not a training dataset. run `npm run typecheck` from `app/` to check application types. this slice's temporary integration/live checks were deleted after verification. new work follows the prospective [lasting-check policy](docs/specs/07-lightweight-testing.md).

## interpretation

prepare the python package once with uv and the pinned ordinary cpython version, then invoke its installed command directly. the output parent must exist; the output file must be new and outside the capture directory:

```sh
mkdir -p var/interpreted
cd analysis
uv sync --locked
.venv/bin/hockey-stats-interpret --capture ../fixtures/captures/2025020001 --out ../var/interpreted/2025020001.json
```

the command reads six fixed capture records, verifies body lengths and digests, and interprets supported completed regular-season json sources. absent landing remains an explicit source gap. interpretation schema 4 retains source order, missing values, reported results, event locations, shift records, report shooting participants/types, event credits, boxscore fields and landing scoring rows, with located field problems and named reconciliations. the play report supplies attributed event on-ice lists; the game-summary report also supplies located recording observations. original spellings, formatted strings and evidence gaps remain visible. no network or external drive is needed.

exit `0` means at least one core source passed game identity, type and state admission, after the document was written. collection gaps and reconciliation mismatches remain explicit in that document. if neither core source is usable but the requested id is known, a diagnostic is saved and exit is `1`. malformed capture contracts, conflicting admitted identities and filesystem failures exit `1` without a successful document; invalid argument syntax exits `2`. `--help` exits `0`.

captures remain unchanged. reported coordinates are not inferred shooting origins. interpretation preserves source facts; reconstruction separately derives elapsed membership and genuine-5v5 exposure. available boxscore groups remain inspectable when a sibling group is unavailable; located issues identify incomplete lists. interpretation records the commit, changes under `analysis/` and python version. dirty or unidentified results are development outputs, not reproducible solely from a commit. remove an interrupted output manually and rerun into a new file. one fully loaded game document favors inspection over bulk storage; sqlite remains the later publication format. json escapes non-ascii text while preserving decoded strings.

the initial temporary end-to-end checks were deleted; inspected fixture facts remain. new work follows [07's prospective policy](docs/specs/07-lightweight-testing.md): retain explicitly selected stable checks, discard campaign machinery. full specifications precede implementation, and the brief supersedes older research recommendations.

## reconstruction

from the prepared python environment, read the captures directly into one offline reconstruction document:

```sh
mkdir -p var/reconstructed
cd analysis
.venv/bin/hockey-stats-reconstruct --capture ../fixtures/captures/2025020001 --out ../var/reconstructed/2025020001.json
```

both options occur exactly once. the output parent must exist; the output file must be new and outside the capture directory. the envelope contains schema version 4, one implementation identity, schema-version-4 interpretation, and reconstruction. chance preparation rejects older versions; regenerate cheap derived corpora from preserved captures. historical artifacts remain usable at their historical git revision.

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

audit the admitted fixture references against the local game captures:

```sh
mkdir -p var
cd analysis
uv sync --locked
.venv/bin/hockey-stats-corpus --reference ../fixtures/references/20252026 --games ../fixtures/captures --out ../var/corpus-20252026
```

all three options occur exactly once. roots must exist; output must be new, have an existing parent and lie outside both roots. inventory metadata establishes the season; inventory rows establish the population. the audit looks up exactly `<games-root>/<game-id>` for every admitted inventory row, reusing interpretation and reconstruction directly. unrelated directories are ignored. it writes per-game reconstruction envelopes under `games/`, then `corpus.json` last. resolved input paths and relative output links make the selection explicit. interpreted references and corpus reports use schema 2; raw capture receipts and inventory-row contracts are unchanged.

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

## retained local features

`hockey-stats-features` inspects prepared facts and requested numerical designs without fitting:

```sh
cd analysis
.venv/bin/hockey-stats-features --selection /absolute/run/inputs/selection.json --config /absolute/run/inputs/config.json --out /absolute/run/reports/features
```

selection schema 2 is exactly `{schema_version,purpose,corpora,history_corpora}`. `corpora` names target `{path,game_ids}` entries; `history_corpora` names explicitly admitted corpus paths. paths resolve against the selection file. nonempty history inventories must contain every target. empty history is legal and leaves history requirements unavailable. history supplies strictly earlier-date evidence; it never adds target rows or changes baseline eligibility, reasons or coverage. same-date games do not acquire an order from their ids.

config schema 3 requires `stage_families` for all five stages (`origin,u,r,unblocked,all_attempt`) and `trait_assumptions`. arrays use the canonical order in the [design ledger](docs/research/features-03k/ledger.md). the unchanged baseline selects `[game_additive,recent_additive]` in every stage. select other retained families explicitly; there is no implicit feature set, automatic interaction expansion or all-features campaign. `recent_interactions` requires `recent_additive` and cannot enter origin. `recent_detail` is an alternative to the old recent basis. candidate `recent_geometry` and `off_wing` enter only `u,r,unblocked`; off-wing also requires `reported_hand_stable_trait`.

shared game and player-game facts carry local, pregame and history evidence once per key. source locators name the exact field they support, independent of map or locator order. null fields retain exact unavailable/conflict/not-applicable problems and source locators; complete totals and supported partial sums are distinct. current body, affiliation and hand reports retain retrieval dating. outcomes and postgame totals remain evidence or strictly lagged history, never focal predictors.

the three arguments occur once and cannot be abbreviated. output must be new, outside inputs, with an existing parent. valid source gaps succeed with visible field/design denominators; invalid contracts fail. syntax compiles even when no selected row is eligible. `features.json` schema 1 records exact designs, preparation/config/input identities, representative values/locators, coverage and measured resources. `completion.json` is written last and binds the report and execution; it is the success marker. interruption requires a cheap rerun into a new path. no model or scientific assessment is produced.

fit/score encoding raises a keyed error when a selected requirement is unavailable. omission retains the extractor; there is no silent row drop, generic null-to-zero rule or missingness predictor. candidate geometry is evaluated at explicit grid origins; recorded block contact enters only the measurement/posterior law. standardized opportunity freezes the original attempt's selected circumstances and hand, then swaps residual shooter/goalie coefficients. reference probabilities use exact bounded batches without a context cache; this costs repeated computation while keeping circumstance identity explicit.

03k verifies local software and source evidence. it does not acquire external data, establish physical origins, run a real fitting campaign or reopen scientific withholding. dated research remains bound to its recorded git revision; future study permissions are separate.

## chance workflow

`hockey-stats-chance` provides separate offline `fit`, `evaluate` and `score` commands for `chance-2`. [fixture instructions](fixtures/chance/README.md) supply the three-season selections, exact numerical exercise configuration and commands. the eighteen-game chance exercise rebuilds from its three committed season references without network or external drive; the [source case index](fixtures/README.md#compact-case-index) retains three additional boundary examples.

fitting jointly estimates type/context-dependent origin maps and unblocked probabilities, then conversion given unblocked, with actor-season shrinkage and two factual benchmarks. scoring values recorded opportunity under one target-season joint shooter–goalie reference, holding the original selected game, preceding, deployment, workload, history and hand circumstances fixed. unblocked coordinates remain contact/origin proxies; blocks retain observed contact evidence and receive conditional origin distributions. tips are retained without relocation.

evaluation separately reports unblocked conversion, recorded-context all-attempt goal probability, marginal unblocked probability and the joint observed-record likelihood. the latter marginal predictions omit focal location, outcome and posterior; retrospective type and eligibility measurements still prevent a demonstrated pre-release forecast claim. calibration summaries explicitly name the outcome and observed positive count. positive standardized block opportunity is not calibrated against observed blocked zeros.

schema-4 evaluations retain twenty fixed probability bins globally and per game, and record exact preparation and stage-design identities. global subgroup summaries and additive `per_game[].groups` share category/value descriptors, including stage-specific actor support; every selected game retains every subgroup, including zero-count groups. per-game subgroup metrics contain only `outcome`, `count`, `observed_positive_count`, `predicted_probability_sum`, `log_loss_sum` and `brier_score_sum`, with no subgroup bins. period and minute-band residuals are omission diagnostics. `tip_distance` and `tip_below_goal_line` assess only eligible unblocked original `tip-in`/`deflected` conversion, using recorded coordinates before quantization. they partition that subset, not all attempts; their predictions still use native quantization.

configurations, `fit.json`, `model.json`, checkpoints, score rows and `score.json` use schema 3; native joint evaluations use schema 4 and components use schema 3. models/components/checkpoints bind exact preparation and stage designs, including columns, fixed transforms and penalties. `model.json` is written last after numerical success; scoring also requires an explicit selection whose facts are prepared under the current contract. `fit.json` records numerical completion or failure. `score.json` is written last with the matching `attempts.jsonl` digest. assessment requires disjoint games dated strictly after training and never changes the fit or reference. output paths must be new, outside input directories, with existing parents; evaluation writes a json file, while fit and score create directories. remove cheap interrupted outputs manually and rerun into new paths. syntax/help exits `2`/`0`; input, numerical and filesystem failures exit `1`; completed artifacts with ordinary evidence gaps exit `0`.

fixture artifacts retain `purpose: fixture_exercise` and `scientific_assessment: not_performed`. complete numerical fits do not establish calibration, physical-origin accuracy, player skill or scientific support. [03d software verification](docs/research/chance-03d/verification.md) records the historical checks and costs. [03e's completed assessment](docs/research/chance-03e/decision.md) withholds the revised chance family; all three seasons were previously examined, so its chronological assessment is retrospective evidence, not untouched confirmation. 03b's scientific rejection remains intact. player attribution belongs to 04, which remains unauthorized.

## numerical recovery and historical research

fitting writes schema-3 `checkpoint.json` atomically after completed starts and accepted em updates. optional `--resume /abs/old-fit/checkpoint.json` continues accepted state into a **new** `--out` directory. use identical input bytes, selection, configuration, clean git revision and pinned numerical environment. dirty exploratory fits can complete but cannot resume. preparation, conversion and benchmarks recompute; interrupted inner solves repeat from the preceding accepted state. preserve expensive fits and failed diagnostics; there is no automatic retry or acceptance of unconverged state.

the active workflow rejects old affected envelopes, references, corpora, selections, configs, models, components, checkpoints and prediction streams. regenerate cheap derivatives from unchanged captures. preserve expensive historical fits and execute dated protocols at their recorded git revisions; no coefficient adaptation or dual reader is supplied. the mathematical family remains `chance-2`; schema changes add feature preparation and explicit designs, not scientific admission.

scoring applies saved contiguous actor-season states. intermediate unobserved seasons retain their fitted penalized states; later seasons carry the latest state forward and label that choice. records before the earliest state remain unavailable with `season_unsupported`. stage-specific actor evidence distinguishes observations in the applied state, observations only in other seasons, and unseen zero prior modes. none implies rookie status. historical scoring is retrospective analysis, not a forecast available at the game's date.

## chance research review

compose research manually in an external run directory with sibling `inputs/`, `corpora/`, `fits/`, `assessments/`, `scores/` and `reviews/`. put selections, configurations, protocol copies and evidence manifests in `inputs/`; using the common parent for selections would make every sibling an input-directory output. run expensive fits sequentially, preserve their checkpoints and completed models, and regenerate cheap derivatives under one identified clean implementation.

`evidence.json` schema 2 names absolute paths. this pilot example uses one assessment and one score; the frozen development protocol supplies the actual benchmark labels for later cohorts:

```json
{
  "schema_version": 2,
  "purpose": "research",
  "protocol": "/absolute/run/inputs/protocol.md",
  "assessments": [
    {"label": "anchor", "path": "/absolute/run/assessments/anchor.json"}
  ],
  "benchmarks": {
    "unblocked_conversion": "anchor",
    "all_attempt_recorded_context": "anchor"
  },
  "scores": [
    {"label": "anchor", "path": "/absolute/run/scores/anchor/score.json"}
  ],
  "reference_score": "anchor",
  "resampling": {"draws": 2000, "seed": 3032026}
}
```

from `analysis/`, run:

```sh
uv run python research/chance_review.py --evidence /absolute/run/inputs/evidence.json --out /absolute/run/reviews/pilot
```

the output must be new, outside all input directories, with an existing parent. assessments require schema-4 research evaluations and linked schema-3 research models with matching preparation/design identities; fixture artifacts fail. `benchmarks` is required exactly when assessments are nonempty, and each label must identify a supplied assessment. candidate log loss and brier compare with that selected model's saved benchmark sums for every member. marginal unblocked has no benchmark. omit `scores` and `reference_score` together for an assessment-only pilot; score-only evidence uses an empty assessment list and omits `benchmarks`.

one score references itself and supplies coverage, tip-ledger and absolute spatial-mass summaries. pairwise sensitivity is empty with reason `no compatible alternative supplied`; comparison-only figures are omitted with the same reason. additional score members require identical sources, selected event order/statuses, grid, training population, reference season and joint reference counts/weights. mismatches fail rather than become paired evidence.

the reviewer resamples pooled sums over counts using 2,000 paired whole-game draws, plus seven- and fourteen-calendar-day dependence blocks, with `PCG64` seed `3032026`. selected zero-contribution games remain present. any zero-denominator draw makes its interval null with the undefined count and reason; there is no redraw. captions state the quantity, selected population, reference and conditioning; pointwise intervals exclude fitting, selection and origin-law uncertainty. tip distance measures proxy dependence, not validated physical origin. opportunity sensitivity compares model-implied surfaces and cannot establish player robustness.

finite schema-2 `comparison.json` is written last after figures succeed. it binds the protocol, evidence and linked artifacts and records executing and fitted-model implementation identities separately. malformed, old, nonfinite or incompatible inputs fail visibly. native artifacts retain `scientific_assessment: not_performed`; [the written decision](docs/research/chance-03e/decision.md) owns the scientific verdict and any conditional 04 obligations. scoring final training games adds no held-out probability evidence.

## chance-component development

current component commands use the same explicit config and prepared facts as native numerics. from `analysis/`:

```sh
.venv/bin/python research/chance_development.py fit-component --selection /absolute/run/inputs/training.json --cohort /absolute/run/cohorts/training/cohort.json --config /absolute/run/inputs/r-interactions.json --quantity unblocked_conversion --protocol /absolute/run/inputs/protocol.md --out /absolute/run/reports/component
.venv/bin/python research/chance_development.py evaluate-component --selection /absolute/run/inputs/later-games.json --cohort /absolute/run/cohorts/assessment/cohort.json --component /absolute/run/reports/component/component.json --arm baseline --protocol /absolute/run/inputs/protocol.md --out /absolute/run/reports/component-evaluation
```

`r-interactions.json` is config schema 3 with `[game_additive,recent_additive,recent_interactions]` selected for `r`. the other quantity is `all_attempt_recorded_context`, which uses its own named stage selection. the old `--features` flag is removed. conversion uses candidate/assigned-cell geometry; the direct all-attempt component omits focal geometry and observed block status as predictors. standalone fits share native numerical primitives and perform no em or opportunity scoring. native model readers reject component artifacts.

component, standalone fit/evaluation/completion and prediction-stream schemas are 3. explicit cohort schema 1 binds source keys, dispositions, preparation and consumed bytes. construct it through `chance_cohort.component_cohort` and the existing finite-json writer; empty required families declare `all_source_eligible`, while `['sequence']` declares the conversion study's matched population. fitting validates original coverage before filtering and counts actors on included rows. source exclusion, quantity applicability, study inclusion and prediction disposition remain separate. outputs are new directories outside inputs, with existing parents. numerical failure retains diagnostics without a substitute component or successful completion. assessment must be strictly later than training with disjoint ids. completion is written last; it means software completion, never scientific approval. changed old schemas fail; historical commands require their recorded revision.

the native composition api requires explicit `all_source_eligible` membership as well as matching numeric settings, training evidence, actor support, preparation and core contracts. selected-family components cannot replace its conversion stage, even when their exclusions happen to be zero. the dated 03f twelve-cell screen and later saved-study commands retain their fixed research authority, including the original single-config binding. execute those historical studies at their recorded git revisions. a new mixed-recipe study needs a separately specified protocol/config binding; 03k supplies no new campaign or manifest.

[03f's protocol](docs/research/chance-03f/protocol.md), [verification](docs/research/chance-03f/verification.md) and [decision](docs/research/chance-03f/decision.md) remain historical evidence. component gains do not establish physical origins, standardized opportunity stability or player attribution.

## defending-sequence conversion study

[03l](docs/specs/03l-conversion-sequence.md) compares four fresh native conversion fits on explicit sequence-complete cohorts. the assigned study is complete: [verification](docs/research/chance-03l/verification.md) records four converged fits and reconciled software/research evidence; [decision](docs/research/chance-03l/decision.md) is `mixed_direction,no_supported_next_fit,not_admitted`. saved research artifacts run at frozen revision `ccbaa85`.

its manual commands require located paths and exclusive output directories:

```sh
.venv/bin/python research/chance_sequence.py cohort --selection /absolute/run/inputs/development-training.json --protocol /absolute/run/protocol/protocol.md --output /absolute/run/cohorts/development-training
.venv/bin/python research/chance_sequence.py fit --selection /absolute/run/inputs/development-training.json --cohort /absolute/run/cohorts/development-training/cohort.json --config /absolute/run/inputs/baseline.json --protocol /absolute/run/protocol/protocol.md --output /absolute/run/fits/development-baseline
.venv/bin/python research/chance_sequence.py evaluate --selection /absolute/run/inputs/development-assessment.json --cohort /absolute/run/cohorts/development-assessment/cohort.json --component /absolute/run/fits/development-baseline/component.json --arm baseline --protocol /absolute/run/protocol/protocol.md --output /absolute/run/evaluations/development-baseline
.venv/bin/python research/chance_sequence.py report --inputs /absolute/run/inputs/report.json --protocol /absolute/run/protocol/protocol.md --output /absolute/run/reports/sequence
```

prepare training/assessment cohorts for both declared windows, then run development baseline/sequence and season-transfer baseline/sequence in that order, one preparation/fit process at a time. both arms train on identical source keys. the common-trained baseline also predicts omitted eligible unblocked rows; main metrics use included rows only. the fixed report manifest binds successful fit/evaluation completions, or located failure evidence and explicit stop reasons. numerical/source/resource failure stops remaining expensive work. a negative or uncertain scientific result completes the bounded study. [the protocol](docs/research/chance-03l/protocol.md) fixes exact settings, populations, intervals conditional on fitted models and developmental decision gates; it grants no admission, 04 handoff or publication.

## observable conversion decomposition

[03o](docs/specs/03o-outcome-decomposition.md) compares the product of two native recorded-outcome layers with two immutable short-history direct controls. `unblocked_on_net` trains on all eligible unblocked attempts; `on_net_conversion` trains on recorded on-net attempts. both predict every eligible unblocked assessment attempt, including misses. stage diagnostics use their own training-target populations; the goal comparison uses the complete common unblocked population.

from `analysis/`, use `research/chance_decomposition.py` with its five explicit commands: `cohort`, `reuse`, `fit`, `evaluate` and `report`. `--help` lists their required paths. cohorts have no protocol dependency; freeze target audits, control-reuse inputs, config and clean code in the protocol before reuse and fitting. `fit --reuse` names the reuse completion; report fit and assessment references name their actual completion files. outputs are exclusive directories outside inputs. research controls are pinned to original 03n evidence and never refitted automatically. bounded original-fixture controls use separate fixture protocols and need no external drive.

the [completed study](docs/research/chance-03o/verification.md) has two exactly reused controls, four converged stage fits and independently reconciled complete assessments. [the decision](docs/research/chance-03o/decision.md) is `decomposed_direction,no_supported_representation,null,not_admitted`: every primary interval crosses zero. the report verifies saved source labels, predictions and objectives, then compares direct and decomposed goal losses with paired game and calendar intervals conditional on the six models. stage losses are descriptive. successful computation and any representation nomination grant no model admission, integration, 04 handoff or publication. future opportunity standardization must average the two-layer product over the same joint actor reference; multiplying separately averaged layers is generally wrong.

## mirror pooling within the decomposition

[03p](docs/specs/03p-chance-structure.md) ties reflected spatial coefficients separately within each q/g type map, while refitting the unchanged remaining terms. both arms already contain q/g. four fresh mirrored fits are compared with the four immutable 03o components under a prospective 99% predictive-gain retention policy relative to a training-rate constant. 3,936 independent spatial coefficients become 2,088 per stage; expanded native prediction arrays remain unchanged.

from `analysis/`, `research/chance_mirror.py` exposes `reuse`, `fit`, `evaluate`, `numerics` and `report`; `--help` lists the required explicit paths. fit and assessment inputs name completion files. the two matrix manifests require explicit completed/failed/not-run cells. use new exclusive output directories. original research paths/hashes are pinned; separate bounded fixture exercises need neither the external drive nor a fabricated historical result. [the protocol](docs/research/chance-03p/protocol.md) fixes exact inputs and policies; [verification](docs/research/chance-03p/verification.md) records the manual commands and evidence.

eight fixed capped continuations produce diagnostic states, preserving all original fits. paired game/calendar intervals condition on fitted models and the training reference; numerical movement is reported separately. fewer coefficients, convergence and a developmental nomination do not admit a model or establish player accuracy.

the [completed decision](docs/research/chance-03p/decision.md) is `within_budget,nominate_mirror,mirror_y,not_admitted`: both windows meet the selected cost policy and pass bounded numerical sensitivity. calibration limitations and every historical verdict remain explicit.

## source review

after regenerating a corpus, run the retained source operator from `analysis/`:

```sh
.venv/bin/python research/source_review.py --selection /absolute/selection.json --out /absolute/new-review-directory
```

the selection uses the existing chance-selection schema and purpose (`fixture_exercise` or `research`). output must be new, outside input directories, with an existing parent. preparation validates the selected envelopes; review rereads those envelopes for source-wide counts. finite schema-1 `review.json` is written last. ordinary source gaps succeed with explicit dispositions; malformed inputs fail. source rows, matched events and eligible attempts retain separate denominators. type reconciliation supplies diagnostics, not a new predictor; the narrow non-goal clock repair retains all source issues.

[the 03c decision](docs/research/chance-03c/decision.md) records the completed three-season before/after audit, detached verification and remaining source limitations. all three seasons are development/comparison evidence after 03b. no refit or revised scientific verdict is implied.


## historical corpus admission

03m uses the existing native capture/corpus commands and an offline admission audit. bulk inputs live under `/Volumes/Expansion/hockey-stats`; existing studies keep their absolute local input paths. the ordinary detached working set selects 2024–25/2025–26 from the fixed local raw root. preflight the mounted apfs uuid `EBBBAAB0-DA80-40ED-B9B9-E8C0CCEB56A0` before each external batch; an absent or mismatched drive stops work.

from `analysis/`:

```sh
.venv/bin/python research/corpus_admission.py --selection /absolute/run/inputs/selection.json --out /absolute/run/audit
```

both flags are required exactly once. outputs are exclusive and outside the selection parent, corpus and raw input roots. schema-2 selections declare explicit corpus paths/game ids and `history_corpora=[]`. `research` requires exactly all official inventory games in all five seasons, 2021–22 through 2025–26; bounded selections use `fixture_exercise` and make no five-season claim. no source discovery, fixture fallback or network request occurs in the audit.

raw receipts/bodies are read through native validators and bound against stored provenance. references are rederived; identity-gap diagnostics are separately rederived without core preparation. one game at a time passes shared core preparation/source review and the existing 65-column `r` circumstance encoder. source status, conversion applicability and encoding availability have separate reconciled counts; absent populations remain null and available empty populations remain zero. eligible blocks stay source-eligible but conversion-inapplicable.

schema-1 `admission-audit.json` is written last after reduction checks. `complete` means the declared population was accounted for, including honest upstream gaps; `scientific_assessment` is always `not_performed`. contract/i/o failures exit 1 without a complete artifact; syntax exits 2 and help exits 0. located encoding failures retain `failure-diagnostics.json`. no fitting, history campaign or scientific admission follows. [verification](docs/research/corpus-03m/verification.md) binds the execution evidence and explicit storage/capture paths.
