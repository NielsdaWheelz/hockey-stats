# operating the private site

the macbook serves the last admitted local publication on [localhost](http://127.0.0.1:3000/). the application opens a standalone sqlite file read-only. expansion is needed for the retained bulk inputs, fits and external candidates. local browsing and a restart of the admitted pair use the installed build, pinned node and local files. [file locations, identities and source revisions](storage.md#serving).

## start the installed build

start the installed server from the repository root when port 3000 is free.

```sh
export PATH="$HOME/.local/share/mise/installs/node/24.21.0/bin:$PATH"
cd app
node --version
npm run serve -- --publication "$HOME/Documents/hockey-stats/local/player-analysis/active.sqlite" --port 3000
```

use node `v24.21.0` and the existing `app/dist`, dependencies, lockfile, database and adjacent receipt. verify the publication id in a skater and goalie response, for example `/api/players/8477073?season=20232024` and `/api/players/8478872?season=20252026`.

## build or preview a candidate

1. in a separate checkout of the selected source, put the pinned node on `PATH`. run `npm ci --include=dev`, `npm run typecheck` and `npm run build` in `app/`. its compiled backend runs both admission and serving. keep the existing listener's build intact.
2. for a new candidate, run the following from the isolated checkout. select an existing observed selection and the completed analytical results directory. use a fresh output directory with an existing parent.

```sh
cd analysis
uv sync --locked
.venv/bin/hockey-stats-analysis publish \
  --observed /absolute/observed-selection.json --results /absolute/completed-results \
  --out /absolute/new-candidate
```

the real observed selection names three distinct corpus manifests in ascending order for 2023–24 through 2025–26. each has a path and expected sha256. the results manifest must bind the same purpose, seasons and corpus digests. the delivered selection and final result exchange are identified in the [candidate build record](research/application-v1-20/verification.md#drive-backed-candidate-and-preservation). a rebuild from those inputs produces a new publication id and generation time. exact restart or rollback uses the retained database and its matching runtime. capture, preparation or fitting require their own inputs. [selection reader](../analysis/src/hockey_stats/publication.py) · [analytical commands](../analysis/src/hockey_stats/analysis_cli.py).

3. from the isolated `app/`, run full admission for a new or changed database, validator, node version or lockfile. use a finalized standalone database without a sqlite journal, wal or shm companion. keep writers and rebuilds stopped during the check. the check reads the whole database and writes `<file>.validation.json` on success.

```sh
npm run publication -- check --candidate /absolute/new-candidate/player-analysis.sqlite && \
npm run serve -- --publication /absolute/new-candidate/player-analysis.sqlite --port 3067
```

an existing compatible receipt permits direct preview or restart. startup compares the compiled server/shared hash, node and lockfile, hashes the database and opens its indexes. the v1 full check took 59 minutes on expansion. local receipt-backed preview started in about 15 seconds. the admission and startup timings used different storage. [admission and preview evidence](research/application-v1-20/verification.md#admission-and-detached-preview).

## switch the listener

the successful v1 procedure exercised the final active pathname while the old directory served. two earlier in-place promotions reached a hash-time metadata refusal after stop. use the following sequence when planning a cross-version switch. allow space for the stage, verified predecessor copy and the existing serving directory until cutover is checked.

1. prepare a matching rollback build from the stored source and lockfile. smoke-start it against the exact predecessor at an alternate port. create a new, empty destination directory on local storage. in that directory, copy the verified predecessor to `active.sqlite`, with its sidecar when it has one, and compare the copy to its known digest. the running directory and original files stay available.
2. stop the earlier preview. using the checked new build, promote within that **unserved** directory. `stage` copies and verifies an exclusive incoming pair. `activate` rotates the cloned predecessor to `previous.sqlite` and renames the incoming database and receipt to active.

```sh
npm run publication -- stage --candidate /absolute/new-candidate/player-analysis.sqlite --directory /absolute/unserved-final-directory && \
npm run publication -- activate --directory /absolute/unserved-final-directory && \
npm run serve -- --publication /absolute/unserved-final-directory/active.sqlite --port 3067
```

3. check the expected id, api and assets at that exact path. the delivered v1 switch passed two ordinary starts there after an initial preview refusal. leave the pair at that path through the switch. if metadata changes during hashing, inspect the underlying error, companions and writer activity, and compare the database and receipt with their recorded identities. keep the old service available while resolving a failed preview. recover the accepted bytes after an unexpected digest mismatch. an intentional change to the database or validator requires fresh full admission. [recorded failure](issues/macos-publication-file-identity.md).
4. stop preview and port 3000, install the matching checked application, manifests and dependencies, then start against the exact previewed pathname on port 3000. compare publication id, representative skater/goalie responses and the actual frontend assets to the preview. reload existing browser tabs. record the serving location and retain the single verified previous publication after successful handoff. the final switch took 15.363 seconds in v1. [activation and live checks](research/application-v1-20/verification.md#final-activation-and-live-verification).

## rollback

while the old directory and matching runtime are intact, a failed switch can return to that verified pair on port 3000. after cleanup, the rollback resides in the `previous` slot. schema 8 requires its recorded build and a database without a receipt.

stop serving before moving slots. preserve the schema 12 active database **with its receipt** under unused temporary names, move the verified schema 8 previous file to active, then put the displaced schema 12 pair in the previous slot. install the schema 8 runtime, start it against the restored active file, check its id and a known profile, and reload. if moves were interrupted, reconcile each filename with its known hash before starting. two recorded recoveries restored schema 8 and the expected profile, with about 523 seconds of historical startup each. [rollback sources and identities](storage.md#serving) · [actual rollbacks](research/application-v1-20/verification.md#first-switch-and-actual-rollback).

for a previous database and receipt compatible with the current schema 12 validator, the stopped-service `npm run publication -- restore --directory /absolute/publication` path stages a checked copy of the previous pair and rotates it. keep room for that extra pair. this case was exercised with fixtures. [fixture verification](research/application-v1-20/verification.md) · [operator implementation](../app/src/operator/publication-cli.ts).

## source and research commands

| task | command or reference |
|---|---|
| capture one game bundle or one season reference bundle to a fresh path | from `app/`, `npm run capture -- --game 2025020001 --out /absolute/new-game` or `npm run capture-season -- --season 20252026 --out /absolute/new-season`. the season command captures the reference bundle, including inventory and bios. each game needs a separate capture. [game capture](specs/01-capture.md) · [season references](specs/02c-corpus.md) |
| reconstruct a checked local game | from the prepared `analysis/`, `.venv/bin/hockey-stats-reconstruct --capture ../fixtures/captures/2025020001 --out /absolute/new-game.json`. create the output parent first. [fixture facts](../fixtures/README.md) |
| prepare or fit | [five-season preparation](research/evidence-v1-01/verification.md) · [producer contracts](specs/experimental-player-analysis.md) · [frozen chance exercises](../fixtures/chance/README.md) |
| historical command examples | from any checkout, `git show 9d1b9fa:README.md` preserves the original capture, corpus, feature, chance, assessment and recovery commands alongside their stated versions |
