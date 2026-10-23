# application temporary cleanup record

status: completed after the root declared the global software and canonical fixture checks green. the root owns removal of `var/v1-06/`; this application cleanup did not touch it or any external source, fit, score, candidate or publication.

- deleted `app/v1-06-check.ts` after its focused checks passed. the compact [schema receipt](application-schema-green.txt) remains.
- deleted the superseded browser folders `application-artifacts/canonical-wide/`, `canonical-narrow/` and `canonical-native/`. retained the final `canonical-final-wide/`, `canonical-final-narrow/` and `canonical-final-native/` screenshot and export artifacts.
- deleted `/tmp/v106-focused-browser.mjs`, `v106-focused-zoom.mjs`, `v106-key-zoom.mjs`, `v106-check-zoom.mjs`, `v106-zero-shot.mjs`, `v106-live-browser.mjs`, `v106-sandbox-browser.mjs`, `v106-source-api-check.py`, `v106-detached.sb` and `v106-source-detached.sb`.
- deleted `/tmp/v106-wrong-block-goalie.sqlite`, `v106-defending-setter.sqlite`, `v106-nongoal-assist.sqlite` and the temporary `/tmp/v106-zoom-extension/`.
- deleted chrome profiles `/tmp/v106-cdp-profile/`, `v106-native-zoom-profile-2/`, `v106-native-zoom-profile-3/`, `v106-visible-zoom-profile/`, `v106-native-zoom-final/` and `v106-unzoomed-canonical/`. the earlier `/tmp/v106-native-zoom-profile/` belongs to the synthetic review and was not removed here.
- stopped only application review servers `41926`, `41928`, `41929` and chrome debug sessions `9227`, `9228` after verifying their process commands. `lsof` then showed no review listeners on those ports; an unrelated ssh listener on `9228` remained untouched.
- retained the canonical 837,971,968-byte external candidate with its unchanged sha256 `d553ffb22362d392f374d052d92f8c31dce00c6f9bd85d7605a1cba6fec1c1b4`; no wal/shm files were present after the final check.
