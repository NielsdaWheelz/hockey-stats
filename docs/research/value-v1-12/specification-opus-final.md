# v1-12 value ledger: second review of amendments (opus)

- **Model:** claude opus 5.5 (`claude-opus-5-5`).
- **Scope:** a delta-only review. This file is the only write.
- **Versions reviewed:** `docs/specs/v1-12-value-ledger.md` (md5 `008e591ee58603d5b41e228d32813d73`) and `docs/specs/experimental-application.md` (md5 `5a42cd052fe9a5fc7e31d1cddfcc4a58`).
- **Code checks:** I made two targeted feasibility checks against code, and nothing else:
  - published shootiness evidence carries `position_group` (`mechanism_composition.py:107`; it is validated at `analysis_publication.py:1556`).
  - the final-year shootiness probe saves its own centered reference (`player_mechanisms.py`, `fit_mechanism`: `probe=dict(…,reference=probe_projected[2],…)`).
- **Memory:** inherited orientation only; memory tools are unavailable.

## Verdict

**No blockers remain.** B1 and B2 are fixed correctly. B3 is settled by the owner's explicit decision. N1, N3, N4, N5 and N6 are acceptable as amended, and the amended N1 is better than what I proposed. There are three small clarifications below. None blocks implementation.

## Disposition of each amendment

- **B1: fixed.**
  - The depth group is now datum-level reference evidence, and the cohort `semanticKey` is unchanged.
  - Profile-position defaults stay in place, and all-skater standings stay available. Both are labeled "each player minus own F/D depth reference".
  - A separate history break, `depth reference changed (F→D)` or its reciprocal, applies only to replacement lines. It applies in both the raw and percentile scales, and it is exported.
  - `ValueLedgerSummary` carries `depth_position_group`, so the history owner can apply the break without loading the full evidence. Unknown↔known transitions already break as "value unavailable".
- **B2: fixed.**
  - `unit_position` is bound to `evidence.position_group`, must agree across the provided shootiness rows, and alone selects the slot, p and K.
  - The execution role stays in execution support.
  - The binding is feasible because the field is already published and validated.
- **B3: settled by decision, not a blocker.**
  - The pre-build report of availability, members and seconds, excluded groups and missing positive-weight terms keeps the consequence visible.
  - The user had already accepted source-driven withholding. Another approval gate would re-ask a decision that has been made. I withdraw that part of B3.
- **N1: accepted, and stronger than my version.**
  - Saving max-subtracted centered neutral slot logits gives stable, detached enumeration for K and for neutral-p checks. It involves no division by `1-p0`.
  - It covers the probe too, because the probe's centered reference is saved.
- **N2: retained by the user. The principle is fine, but the bound is incomplete.** See C1.
- **N3: fixed.**
  - A single consistently resolved F/D label determines the annual group despite missing time.
  - The affected team-group is still excluded.
  - Rows with an unresolved label, and mixed-role players with incomplete time, remain unknown.
  - This removes the cross-team cascade without any risk of misclassification.
- **N4: fixed.** `close` applies to shared scalars. Categorical axes and bindings must match exactly.
- **N5: accepted.** The conditional wording is more accurate than mine. The direction of the shrinkage bias depends on the priors (entry versus carry) and on the true depth level, so asserting "understated" overclaimed.
- **N6: fixed.**
  - One server projection produces `ValueLedgerSummary`. Full copied evidence comes only from the selected `family=ledger` endpoint.
  - Summary, detail and export must match exactly, and payloads are measured before the build.

## Remaining clarifications (non-blocking)

**C1: the term-scaled allowance is only n-independent under compensated summation.**

The user's standard is "a numerical bound, not plausibility". Measured against that standard:

- With naive recursive summation, the worst-case error grows like `(n-1)·2^-53·Σ|x_i|`.
- `64·2^-52·Σ|terms|` therefore covers only about 129 terms.
- Depth means can have several hundred weighted members, so this bound does not hold for them.

The smallest correct fix:

- Both readers recompute every checked ledger sum with compensated or exact summation: `math.fsum` in Python, and a Neumaier or Shewchuk loop in TypeScript.
- Apply the declared allowance uniformly to all ledger sum checks: terms, states, totals, weighted means and subtraction. "Where needed" invites drift between the Python and TypeScript readers.
- Integer seconds sums are already exact and do not need this.

**C2: classify a missing member row.**

The no-gate policy depends on telling source-driven withholding apart from broken construction. Add one rule:

- A positive-weight member of a complete group whose published skater-season row is missing is a construction or join defect, so composition stops.
  - This holds because unresolved identities already exclude the group through the `identity_conflict` reason.
- Missing upstream estimates that carry their own reasons are accepted withholding.

**C3: name the source of the probe's logits.**

"Its own K" should state that the probe's neutral slot logits come from the role offsets in the centered reference saved in `probe.json`. They do not come from the baseline offsets, and no re-centering or design read is needed.

## Decisions

- **User decisions:** none outstanding.
- **Routine:** C1, C2 and C3.
- **Remaining blockers:** none.
