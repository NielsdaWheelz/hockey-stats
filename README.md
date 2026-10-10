# hockey stats

a hockey statistics website grounded in explicit statistical meaning, inspectable evidence, and reproducible analysis.

the implemented slices preserve source responses, interpret one explicitly selected game's captures offline, reconstruct reported event membership, elapsed exposure and recorded coordinates, audit a season inventory against explicit local captures, prepare retained local feature facts and explicit stage designs, and fit, assess and score chance-2 models. 03b completed fresh three-season acquisition, real chronological development/confirmation and scientific comparison/recovery; [its scientific decision](docs/research/chance-03b/decision.md) rejects the declared all-attempt use. 03e completed all three development recipes and their common-cohort evaluation, scoring and comparison under its unchanged [protocol](docs/research/chance-03e/protocol.md); [its decision](docs/research/chance-03e/decision.md) is `withheld` because all three fail declared all-attempt calibration. no primary survived, so dependent transfer, kernel variants and final fits were not run. no handoff is issued; 04 and publication remain unauthorized, and the website is unstarted.

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
- [pr03d specification](docs/specs/03d-chance-revision.md): implemented chance-2 contract; [fixture verification](docs/research/chance-03d/verification.md) establishes software behavior.
- [pr03e specification](docs/specs/03e-training-assessment.md): completed bounded retrospective assessment, `withheld`; [protocol](docs/research/chance-03e/protocol.md), [verification](docs/research/chance-03e/verification.md) and [decision](docs/research/chance-03e/decision.md).
- [pr03f specification](docs/specs/03f-model-development.md): completed saved diagnosis and twelve-cell component screen; [decision](docs/research/chance-03f/decision.md), [verification](docs/research/chance-03f/verification.md) and [protocol](docs/research/chance-03f/protocol.md). context interactions recommended for further component research; history ablation worsens losses. no joint fitting or admission.
- [pr03g specification](docs/specs/03g-chance-assessment.md): reviewed and merged; completed saved-fit integration and spatial diagnosis. [decision](docs/research/chance-03g/decision.md): `assess_integrated`, without fitting or admission.
- [pr03h specification](docs/specs/03h-chance-revision.md): reviewed and merged in `d828085`; [decision](docs/research/chance-03h/decision.md) is `withheld` after two required own-bin failures. [verification](docs/research/chance-03h/verification.md) records one saved-stream pass, independent reviews and deleted temporary tests; no fitting or handoff.
- [pr03i specification](docs/specs/03i-chance-revision.md): reviewed and merged in `d3d1b92`; completed saved localization/composition diagnosis. [decision](docs/research/chance-03i/decision.md) preserves its avoidance proposal; candidate `withheld`. [verification](docs/research/chance-03i/verification.md) records independent reviews and temporary-test deletion closure; no fitting or admission.
- [pr03j specification](docs/specs/03j-chance-experiment.md): implemented and executed: [decision](docs/research/chance-03j/decision.md) `inconclusive`, with no supported intervention; [verification](docs/research/chance-03j/verification.md) records all 6,000 refits and independent checks. no admission or follow-on fit.
- [pr03k specification](docs/specs/03k-feature-repertoire.md): retained local facts, chronological history and explicit stage selection; [field/design ledger](docs/research/features-03k/ledger.md) and [software verification](docs/research/features-03k/verification.md). [policy/inventory](docs/model-features.md) records available families and their limits; no new scientific fit or admission.
- [later pr stubs](docs/plan.md#next-slices): 04–07 retain downstream responsibilities. expand each before implementation.
- [pr03c research](docs/research/chance-03c-source-audit.md): overlooked report shot types, measured model coupling and limits of public origin evidence.
- [external-data audit](docs/research/external-corpus-audit.md): inspected legacy database, fidelity findings and fresh-acquisition decision.
- [corpus/reference audit](docs/research/corpus-reference-audit.md): verified season sources, coverage and source limitations.
- [source audit](docs/research/source-audit.md): direct public evidence, omissions corrected and later input dependencies.
- [council synthesis](docs/research/council.md): recommendations, disagreements, and tradeoffs.
- [model direction after 03i](docs/research/model-direction.md): approved sequence, council disagreement, measurement/uncertainty obligations and retained research challengers.
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

downloads under `var/` are ignored. [the offline corpus](fixtures/README.md) contains twenty-one complete game bundles and their season references, with explicit evidence limits; it is not a training dataset. run `npm run typecheck` from `app/` to check application types. temporary integration/live checks for this slice are deleted after verification, as requested; later changes must recreate them until the lightweight testing slice.

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

temporary end-to-end checks are deleted after verification. the inspected fixture facts remain; changes must recreate checks until slice 07. later slices remain outlines until their inputs and requirements are concrete. the brief supersedes earlier research recommendations where the user has resolved a choice.

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

## source review

after regenerating a corpus, run the retained source operator from `analysis/`:

```sh
.venv/bin/python research/source_review.py --selection /absolute/selection.json --out /absolute/new-review-directory
```

the selection uses the existing chance-selection schema and purpose (`fixture_exercise` or `research`). output must be new, outside input directories, with an existing parent. preparation validates the selected envelopes; review rereads those envelopes for source-wide counts. finite schema-1 `review.json` is written last. ordinary source gaps succeed with explicit dispositions; malformed inputs fail. source rows, matched events and eligible attempts retain separate denominators. type reconciliation supplies diagnostics, not a new predictor; the narrow non-goal clock repair retains all source issues.

[the 03c decision](docs/research/chance-03c/decision.md) records the completed three-season before/after audit, detached verification and remaining source limitations. all three seasons are development/comparison evidence after 03b. no refit or revised scientific verdict is implied.
