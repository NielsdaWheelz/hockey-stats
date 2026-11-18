# v1-12 value ledger — adversarial specification review (opus)

model: claude opus 5.5 (`claude-opus-5-5`). read-only; this file is the only write. reviewed on-disk `docs/specs/v1-12-value-ledger.md` (md5 `5e1d13ba42db6626d5269c79f648b5c0`) and `docs/specs/experimental-application.md` (md5 `8369a98ebbc3b9a4ecf2c065f490f34f`) on 2026-11-18, against current analysis/app code. memory: inherited orientation only (snapshot `c314e019…`, `[0,3755)` of 8070 admitted); memory tools unavailable; no historical discussion reopened. no artifacts, receipts or real outputs were read. every numerical claim below comes from reading code and contracts, not from execution.

## verdict

the accounting is right. signs, units, multipliers, reciprocal weights, the `.8` placement and the K factorization all match the producers. three problems remain:

- **B1 (blocks):** the draft puts the realized depth group into semantic identity, which silently repartitions cohorts.
- **B2:** `execution_position` has no defined source, which can silently corrupt setter share.
- **B3:** there is no stop condition before a full candidate build that could be wasted.

fix those three and the handoff is implementable. no new user decision is needed now. one becomes needed only if composition produces an unavailable depth reference.

## blockers

### B1 — depth group must not enter semantic identity (content contract; correctness)

**where.** `experimental-application.md`, §value ledger evidence, the paragraph starting "existing overview supplies all 24 ledger selectors". the sentence at issue is "include it in replacement semantic identity so a position-reference change breaks that history line". v1-12 §content and application ¶3 states the break without naming its mechanism. that sentence can stay if it adds "through the shared history-break owner; cohorts unchanged".

**why it is wrong.** `semanticKey` (`app/src/web/analysis-values.ts:1200`) does two jobs. it is history identity (`analysis-history.tsx:79`). it is also the cohort partition key (`analysis-cohorts.ts:142`; members and incompatible peers at `:209–213`). appending the realized F/D group to it causes three problems:

- **all-skater cohorts get narrowed under a false label.** under `peers=all`, a D-reference player's replacement percentile ranks only D-reference skaters, but the label still reads "all skaters" (`analysis-cohorts.ts:132`). everyone else shows up as "incompatible peers excluded" (`analysis-history.tsx:1059`), which falsely claims they are measuring a different quantity.
- **profile-position cohorts become degenerate.** under the default profile-position peers, a skater whose profile says F but whose depth group is D ends up in a tiny cohort labeled "reported forwards".
- **it contradicts the draft's own rules.**
  - league finishing and setting already use position-specific construction (the unit slot, `K_F` vs `K_D`), and they are not partitioned.
  - annual reference variation is not allowed to split histories either.

the replacement quantity has one definition: a player's own league term minus the matching term of their own annual F/D depth reference, under one workload and one depth policy. position-specific replacement levels exist precisely so that values can be compared across positions. an all-skater replacement comparison is the purpose of the construction, not an abuse of it. afaict public usage-rank gar practice uses replacement the same way. the user's suspicion is correct.

**smallest correct change.** replace the sentence with:

> carry the focal annual `depth_position` as datum-level reference evidence, not semantic identity. replacement cohorts keep the existing profile-position default and the all-skater control, labeled that each value subtracts its own F/D depth reference. the shared history-continuity owner breaks a replacement series with reason `depth reference changed (F→D)` when consecutive plotted seasons differ, in raw and percentile scales; league lines are unaffected. cards, standings, history points and csv/png carry the group and the break reason.

the codebase already has this pattern. `historyBreak` (`analysis-history.tsx:64–84`) breaks percentile lines when `peerGroup` changes. it does so through a separate datum-level check (`:82`), not through `semanticKey`.

**add one acceptance row** under "real interface": a labeled synthetic F→D depth change breaks only the replacement line, with its reason. the all-skater replacement cohort pools F and D references and its label says so.

**necessary vs preference:**

1. **necessary:** do not partition cohorts by the realized group.
2. **necessary:** show the group on every replacement display and export.
3. **necessary in some form:** make an F↔D change visible in history.
4. **preference:** whether (3) is a broken line or a connected point with an annotation. i recommend the break, because it reuses the existing renderer and adds no new mechanism.
5. **scope, not needed:** a "same depth group" peer option.
6. **optional, for consistency:** the same owner could also mark `execution_position` changes on finishing, setting and league lines.

### B2 — `execution_position` has no defined source (arithmetic integrity)

**where.** `experimental-application.md`, `value_ledger.evidence.execution_position`; v1-12 §exact accounting ¶4 ("reuse v1-10's focal probability `p_i` and its fitted annual position").

**why.** two different position sources exist, and they can disagree:

- shootiness uses the prepared annual `position_group` (`mechanism_design.py:119–120,334–335`). this is what selects the unit slot (`player_mechanisms.py:317–326`).
- execution uses the game-dated `reported_position` (`execution_design.py:204–206`).

p's slot and K must use the same position. an implementer who takes the field name literally will compute K for the wrong position, and setter share will be wrong without any error.

**fix.**

- define `execution_position` as the `position_group` carried by all seven bound shootiness rows, and require it to be identical across them.
- that one field selects the unit slot, p and K.
- readers check it against each shootiness input row.
- execution's own role stays in execution support.
- renaming the field (e.g. `unit_position`) is optional.

### B3 — no stop between real composition and the candidate build (sequencing; conditional user decision)

**where.** v1-12 §owners and interfaces, the work-order paragraph.

**why.** under the user's all-member rule, a single positive-weight depth member missing any one term withholds the whole F or D reference for that season. an unknown shootiness position is enough, because it removes finishing and setting. nothing checks this outcome before the build. the predecessor build took 17,017 s (about 4.7 h) to publish and about 50 min to start strictly. the user chose the policy without seeing what it produces.

**fix.** after the real `summarize --family ledger`, report for each season × position:

- availability;
- member count and seconds;
- positive-weight members that lack terms, by term and reason;
- excluded-group coverage.

if any of the six references is unavailable, stop and go back to the user before building. this is not a new study: composition already computes all of it. only that outcome would require a material user decision.

## non-blocking corrections

### N1 — make K checkable without external reads

**the math.** under the shootiness softmax with fixed unit counts:

- the published `neutral_probability` values are the all-neutral slot probabilities `q_F,s` and `q_D,s` (`player_mechanisms.py:323–326`);
- `n_F*q_F + n_D*q_D = 1`;
- for each remaining slot, `r_j = q_j/(1-q_focal)` exactly.

so K is a closed form of the published `q` values, the unit counts and the 2/3/1 setter weights.

**the change.**

- store `q` per state in `state_references`.
- require it to equal every provided shootiness row.
- let both readers recompute K by direct-slot enumeration, compared with `close`.
- the same closed form gives the 20252026 shootiness-probe K directly from the saved probe projections (`probability`, `neutral_probability`), with no re-centering and no design reads.

this is not the forbidden `(1-p_i)/(1-p0_i)`: only neutral `q` values enter. `1-q` should stay well away from zero in every declared unit (afaict; assert a floor). at present K is the one annual constant that readers have to take on trust.

### N2 — drop the extra closure allowance for ledger sums

`close` already allows `1e-9` absolute error (`analysis_publication.py:249–250`, `player-analysis.ts:2572–2575`). the extra `64*2^-52*sum(abs(terms))` allowance only exceeds that once `sum(abs(terms))` passes about 7×10⁴ goals, which never happens at ledger scale. use one comparator in both readers. keep the term-scaled allowance where territory already needs it.

### N3 — resolve the annual group from a single consistent label

v1-12 §depth ¶2 makes a player's annual group unknown whenever any positive-time observation lacks time. that holds even when every observation carries the same resolved F/D label, so the missing time cannot change the answer. the unknown status then has two costs:

- it cascades to both groups on every team the player represented (¶3);
- it withholds the player's own replacement value.

**fix:** "if all positive- or unknown-time observations resolve to one F/D group, that is the annual group despite missing time; missing time still makes the affected team-group incomplete." this is exact and leaves the user's group-exclusion decision untouched.

### N4 — name the comparator for "agree across players"

state that the check uses `close`. the st projector writes one shared neutral array into every player row (`spatial_rates.py`, `_project_special_teams`), so exact equality probably holds. but v1-10's own reducer compared repeated neutral rates with `isclose(…, 1e-10)` (`player_mechanisms.py:557`).

### N5 — state one interpretive limit in ledger detail

the depth reference averages shrunken estimates. members with little information sit nearer their priors, and entrants sit nearer neutral zero. as a result:

- the depth mean sits closer to league average than the depth population really does;
- replacement gaps are understated;
- F and D benchmarks can be shrunk by different amounts, which also qualifies cross-position replacement comparisons.

this needs a label only, not a model change.

### N6 — clarify where per-row evidence loads

`value_ledger.evidence` copies, per row:

- nine spatial supports, including role coefficient support;
- seven execution supports;
- seven shootiness supports.

say that overview rows carry the 24 estimates and their reasons, and that this evidence loads with the selected `family=ledger` detail. otherwise, measure its size before the build.

### de minimis — no change needed

both the spatial A and the 4v5 source-pooled A count attempts taken by goalie shooters (`spatial_design.py:177–179`, `player_mechanisms.py:618`). p, however, sums to one over skaters only. so `H·A·Σp` over-allocates by the goalie-attempt share. this is the canonical formula and the effect is negligible.

## verified against code

- **5v5 / pp / pk xg terms.**
  - `*_xg_per60` is focal minus neutral (`spatial_composition.py:321–323,464`).
  - pp uses physical advantaged-time weights, and pk mirrors them exactly (`spatial_rates.py:884,914,918`).
  - negating defense and pk once is correct.
- **penalties.**
  - the taken value is already signed −1 (`mechanism_composition.py:97–99`).
  - rates are per directed hour of supported 5v5, so ×`1000/60` is the right basket.
- **territory.** the per-basket scalars already include `1000/60` (`territory.py:143`).
- **execution.**
  - all seven strengths are published (`analysis_publication.py:19`).
  - `setup_weight = .8·opportunities`, and S is per assisted opportunity (`execution_composition.py:225`; `analysis_publication.py:1195,1265`). so `.8` enters exactly once, through setter share.
  - setter weights are 2/3/1 (`execution_design.py:106–107,544–548`).
- **K algebra.** the softmax obeys IIA, so the other slots' probabilities are exactly `(1-p_i)·r_j`. K depends only on state × position, which gives fourteen constants.
- **4v5 A.** `sh_support` saves `attempts` and `included_seconds` (`player_mechanisms.py:655`).
- **depth source.**
  - the interpreted boxscore list becomes nonnull as soon as any one array parses (`interpret.py:605–633`). so the spec's "nonnull is insufficient" rule is necessary.
  - the observed `game` table holds the full 1,312-game inventory (`observed.py:750–780`), so the team × F/D matrix cross-check is feasible.
- **old reader assertion.**
  - both readers assert that every component shares one reference/support policy (`analysis_publication.py:2771–2776`; `app/src/server/analysis-publication.ts:1615–1634`).
  - family labels differ by design (`spatial-league-centered-virtual-v1`, `reference-execution-zero`, `shooter-common-unit-v1`, …).
  - so the assertion must be removed, as the spec says.
- **null-total rejection.** the current validator accepts a null total when all components are present (`analysis_publication.py:1730–1739`). the new rejection requirement is needed, and it is in the spec.

## decisions

- **user decisions now:** none. the league headline, depth reference alongside it, the 1000/100/100 workload and complete groups all stand.
- **conditional:** only B3's outcome (an unavailable reference) would require one.
- **routine:**
  - B2's definition;
  - N1–N6;
  - score-stream ordering;
  - choice of comparator.
- **preference within B1:** broken line vs annotated marker. recommend the break.

## remaining blockers

B1, B2 and B3. all three are text changes to the two specs. none needs fitting, source reads or a new study.
