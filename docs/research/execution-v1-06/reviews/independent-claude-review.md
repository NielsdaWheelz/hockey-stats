# independent adversarial review — v1-06 execution scoring

status: final, 2026-10-23. frozen `41a003b` plus the one reviewed post-freeze display line, and the canonical accepted-01 fixture scores, results and candidate: no blocker found. root recorded global software and canonical fixture green. real acceptance remains blocked on real inputs; nothing here claims a complete real result. read-only on production code and canonical outputs.

temporary reviewer material, deleted by root after global green per this inventory (the reviewer does not delete it): `/Users/nnandal/Documents/code/hockey-stats-v1-06/var/v1-06-independent/` (whole directory, 390 MB: check scripts, `snapshot-41a003b/`, `repro-41a003b/`, `scores-20212022/`, `scores-20242025/`, `scores-20252026/`, `scored-20242025.pickle`, `fresh-selection.json`, `pre-accepted-01-inputs.txt`, `__pycache__/`) and working notes `/tmp/v106-independent-review.md`, `/tmp/v106-valued-composition-review.md`. no reviewer file exists under `/Volumes/Expansion` or in tracked paths. this is computational and source review, not scientific admission.

## executed independent checks

| check | population | result |
|---|---|---|
| scoring recomputation by subtracting actor residual columns from `X@beta`, explicit `w*pi` coalition loops, 24-permutation shapley, bayes posteriors, panel logits | chain-06 20242025: 120 stratified of 1,062 complete events (every block/tip/goalie/unknown/off-ice/missing-coach/g-row/goal/discrepancy kind) | 0 failures; max 8.9e-16 prefixes, 1.4e-16 coalitions, 4.9e-17 shares, 1.1e-16 posteriors; coalition 0/11/15 = prefixes exactly |
| focal projections from panel arrays + saved state | 261 people × 5v5 (801 events, 154,071 origins) and 5v4 (176) | 0 failures; scalars ≤1e-11, maps ≤1e-13; support unions and prior flags exact |
| spec hand cases | synthetic panels | mixture `.5/.41/.41/.41`, on-net `.82`, goal\|unblocked `.82`, conversion `1`; setting `10` not `8`; tip-only contrast `0`; empty panel and absent coefficient explicit |
| event/panel cross-path closure | dev-02, 5 years × 7 public panels | Σ event neutral prefixes = panel neutral masses, worst 3.3e-16 relative |
| assist-label invariance | 20242025, all 49 known labels erased | events, shares, priors, 32 panels identical; only 410 posteriors move |
| goal boundary leakage | 2023–26 fixture designs | 103 boundary goals, all use the pre-goal lineup |
| valued count/cell/time closure | 9 fixture games, 20242025 | 665 eligible attempts; counts and cells equal v1-03; included+excluded = all 5v5 member seconds (324 player-games) |
| score artifact roundtrip + 23 semantic mutations | 20212022, 20242025, 20252026 | writer→strict reader ok; propagation passed; every mutation rejected for its own reason |
| source→exchange | composition-check-01 vs facts-02 + dev-02 | 0 failures; factual rows preserved; paired strata, attempt values, maps, reference-xg mass/seconds closure exact |

final pre-campaign rerun on the frozen sources (2026-10-23 ~01:10): every row above re-executed with 0 failures; fresh 20242025 artifact under the current writer/reader (mandatory `setter_discrepancies`) reads strictly; event→panel closure 1.14e-14 relative; refactored projection 302 ns per (person, origin row). no concrete blocker for the canonical five-year campaign from this review.

frozen-core audit (2026-10-23): production paths byte-identical to `41a003b`; the full battery re-run against `git archive 41a003b`, plus a near-0/1 saturation probe (finite nested masses and representable log-domain levels down to subnormal masses), all pass; a fresh 20242025 artifact records `git_commit 41a003b`. no concrete blocker before the canonical accepted-01 campaign.

## canonical accepted-01 (fixture)

| check | result |
|---|---|
| code identity | HEAD and every score/results producer record `41a003b`, not dirty; production paths diff 0 lines |
| pinned inputs | five chain-06 state manifests, coaches and root-r6 hash-equal to the pre-campaign record |
| score selection and artifacts | closed ordered five-year selection with manifest digests; strict reads; previous-state chain intact; 20252026 propagation passed (≤4.3e-7 probability, ≤9.0e-7 per100/map, 0 danger crossings) |
| independent reproduction | reviewer rerun of the writer from `git archive 41a003b` with the same inputs: all 73 members of all five years byte-identical |
| event→panel closure | Σ event neutral prefixes = panel neutral masses, 2.2e-16 over 5 years × 7 public panels |
| numerical recomputation | scoring and projections independently recomputed on 20212022, 20242025 and 20252026: 0 failures |
| canonical results | factual preservation, attempt values, all paired strata, saved-projection equality, maps, reference-xg mass/seconds closure exact (16.820396 / 29.576646 / 15.220757 goals; 157,290 / 208,080 / 114,880 skater-seconds); composition receipts digest-bound; recorded-assist evidence only on credited goals (28/49/44, discrepancies 0/1/1) |
| canonical candidate | `player-analysis.sqlite` sha256 `d553ffb22362d392f374d052d92f8c31dce00c6f9bd85d7605a1cba6fec1c1b4`, read with `mode=ro&immutable=1`: user_version 8, delete journal, integrity and foreign keys ok, schema 8; every stored execution summary, breakdown, map, setter, share, attempt supplement and reference-xg value equals the canonical results for 2023–26; stored strata close; the read created no files |

the personal-row/coverage predicate residue is withdrawn: retained 5v5 intervals already require native roster positions (skaters C/L/R/D/F, goalies G), and the valued shooter must be a member of such an interval, so every personal shooter is either a covered skater or a skipped goalie.

post-freeze change reviewed: `app/src/web/execution-evidence.tsx` line 18 (one line, after `41a003b`) only formats a displayed `unavailable_reason` with spaces instead of underscores. the helper feeds four table cells (`execution-evidence.tsx:92-96`); the evidence csv, raw keyed json, api payloads and numerical code are untouched. the schema requires a reason whenever the value is null (`player-analysis.ts:188`), so the optional chain never prints `undefined`. approved as a display-only copy change. the separate final app copy review, browser checks and screenshots belong to the app owner and root; this review did not reproduce them.

## findings disposition
- verified repairs: sqlite user_version 8; sentinel share recipients; exact coalition entries; valued count/cell closure; goalie share identity versus unreported source goalie; fixture goalie setter team; propagation receipt rows; failed-propagation evidence; participation reason counts; stratum order; recorded-assist evidence only for the credited assister.
- accepted limitation (root decision): setter `Support.events` is the exact likelihood union including mean-coupled rows, never an observed-pass count; the prespecified setter sparsity selector is potentially near-tie-driven (fixture: four distinct union values across 245 setters). candidate/mean/union counts are shown together.
- later verified: a goalie physical shooter keeps team interval value but no personal skater row (`personal_shooter_not_skater`); real 2021-22 has 8 such attempts with both goalies in net. composition binds the scored type to the prepared model shot type.
- composition repairs verified at the source boundary: all 1,062 complete paired 20242025 events pass the positive outcome/actor/team/type/state binding and every type flip fails; recorded-assist evidence marks exactly one candidate on each of 49 credited goals plus one outside-universe discrepancy (50 credited scored goals); one participation aggregator, whose included + excluded seconds partition all exact-strength member time for 7,882 skater × strength keys over five fixture years; unvalued attempts are counted once and listed with keys in a method-bound receipt.
- closed residues: the effect reader now repeats the named-setter attacking-team check; the personal/coverage predicate difference is unreachable on valid artifacts (see above).
- acknowledged prerequisites and costs, not software blockers: real acceptance stays blocked until the real v1-01 preparation, real v1-05 states and real v1-03 facts exist and pass their own acceptance; real-panel projection cost is still to be measured (fixture 302 ns per person-origin row, ≈ 2–3 h per real season); the prespecified setter sparsity selector may be tie-driven; the prepared-kind projection fallback is unexercised on fixtures. earlier development compositions (`composition-check-01`, dev-01..04) are superseded by accepted-01.
