# v1-20 specification — adversarial opus review, targeted second pass

reviewer: claude code, model `claude-opus-5-5` (opus 5.5), 2026-11-20. read-only. [handoff](../../specs/v1-20-whole-card-closure.md) · [initial findings](specification-opus-initial.md) · [root dispositions](specification-review.md).

## scope

this pass checks only whether the current handoff resolves initial findings f1–f9. it compares the amended clauses (lines cited below) with the code already read in the first pass. it is not a new full review.

## limitations

- **no runtime checks.** nothing was built, tested, hashed or served, no database was opened and no external artifact was read. the drive was not mounted.
- **new source reads were small and targeted:**
  - `territory.py:36-41, 112-127, 454-485`, `territory_state.py:405-416` and `artifacts.py:45-53`, to check that the f5 literal parse can work.
  - one parse of `app/src/server/physical-schema.ts`, to check the f6 primary-key premise.
- **real data not checked.** the real donor territory strings were not inspected.
- **no acceptance claimed.** this pass establishes no software, data, delivery or scientific acceptance.

## verification of dispositions

| finding | handoff clauses | verdict |
|---|---|---|
| f1 discovery csv | line 109 | **resolved.** discovery-table csv joins peer expansion and distribution csv under one fixed mapping and the same publication/projection verification. it keeps table, peer and column order, filters and outsiders. it explicitly forbids empty evidence columns caused by transport omission, and measures the extra family reads separately. this matches `analysis-discovery.ts:403-406` and the `base.family="overview"` metrics (`analysis-values.ts:271-279`). |
| f2 delivery runtime | lines 158, 160, 162, 178 | **resolved, with one small clarification (n1).** a ready schema 8 runtime from `0e0f569…` is kept at a named path outside rehearsal scratch, smoke-started and retained through the switch. dependency/cache availability is established before stop, and the in-memory process is not taken as proof of restartability. commands run from the frozen isolated build. primary assets change only after stop. a rebuild uses the accepted revision with an empty backend output. an installed-identity mismatch triggers rollback, never re-admission during the outage. "build before" is now a precondition, not an implicit rebuild. |
| f3 validator timing | line 147 | **resolved.** validator, node and lockfile identity are captured at process entry and recomputed before the receipt is written. a change is rejected. no concurrent writer or build is stated as an operator precondition. |
| f4 client deep equality | line 107 | **resolved.** `checkOverview` and `scalarRows` are named and compare against the exact projection. datum equality keeps identity, the original estimate/fact, status, reasons, support, qualifications, workload, methods, reference and semantic keys. the existing pending-envelope reason normalization (`client.ts:735-738`) is preserved. independent checks compare original full fields, not the projection with itself. |
| f5 territory correction | lines 117, 119, 123 | **resolved; nonblocking residual (n2).** <br>• exact old slots `limitations[5]` and `assessment.findings[0].summary` are proven, along with the prefix/suffix and the baseline statuses against the bound head manifests. <br>• the diagnostic literal is parsed with `ast.literal_eval` and compared with the sha-bound `reference.json`, never executed. <br>• `read_territory_reference`/full state are banned. <br>• the limits come from the bound recipe's `diagnostic_limits` (`territory.py:41`, inside a digested recipe body); the goals limit covers map-l1, and no third constant set is added. <br>• ledger evidence is declared a composition-time snapshot, with no new containment check. <br>• an already-corrected input is accepted only through its original correction receipt. |
| f6 preservation proofs | line 127 | **resolved.** results→results descriptor/byte equality is separated from one measured heavy candidate→candidate ordered comparison with typed row hashes. exceptions are field-level: `publication_id`, `generated_at`, named producer implementation/environment fields, and the three owned `analysis_method` rows. results go to `candidate-preservation.json`. premise checked: all 41 fixed tables in `physical-schema.ts` declare a primary key, so primary-key order is defined. |
| f7 receipt fields | lines 140-149 | **resolved.** `checks` is removed. the file digest covers compiled server/shared files only; node and lockfile are compared separately, with named errors. startup compares the four named metadata fields. |
| f8 projection details | lines 101, 105, 133 | **resolved.** the recorded-penalty omissions are explicit. each present person in a provided family needs exactly one row; missing or duplicate rows fail. coverage applies only to provided ledger references, over the declared seasons, so fixtures may have fewer years. |
| f9 restore | line 158 | **resolved by choice.** `restore` is exactly the shared stage-previous→activate path, with its temporary-copy cost stated. there is no second rotation implementation. rejecting the rename swap trades space and i/o for a single failure path. that is acceptable, since staging runs before the interruption. |

## remaining nonblocking notes

**n1 — lockfile locator after install (lines 145, 162).**
- *problem.* startup compares the `package-lock.json` digest separately. line 162 installs "the exact checked compiled application and its matching locked dependencies" into the serving location without merging primary git. if the serving location's lockfile file stays at the primary head's bytes and those differ from the accepted revision's, startup refuses and activation falls back to rollback.
- *why it is safe.* the failure is safe: no wrong code is served.
- *cost if left.* it would turn into a failed activation that one sentence prevents.
- *fix.* name the lockfile the runtime hashes (the installed application's `package-lock.json` next to `dist/`). include it in the installed set. make "recompute installed identity before serving" cover all three fields: files, node and lockfile.

**n2 — check the real donor text early (lines 119, 172-175).**
- *afaict the parse will work.* the raw diagnostics hold only python `float`, `None` and `str`:
  - the maxima pass through `float()` (`territory.py:482-483`).
  - the shift means and tail fractions come from `fsum` (`territory.py:121-127`).
  - so `str(...)` should parse with `literal_eval`.
- *if it fails.* a numpy scalar repr anywhere would make the strict parse reject. that is a safe failure, but it would block the metadata deliverable only at real execution.
- *fix.* run the cheap old-text proof over the three real `territory-v1-11-*` donor methods first, before other real work. fixtures cannot establish this.

## disposition

**clear.** no blockers or required fixes remain. f1–f9 are resolved in the current handoff. n1 and n2 are optional one-line refinements that root may fold in. this review does not establish implementation, data, delivery or scientific acceptance.
