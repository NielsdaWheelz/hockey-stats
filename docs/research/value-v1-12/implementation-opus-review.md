ten-term arithmetic, the depth algorithm, the 4v5 reuse and the narrow territory reader all hold up. nothing found blocks source or arithmetic work. what's left is mostly reader parity, identity stability and a few hard stops.

limits first. no commands could run (bash is disabled here), so nothing was executed or tested. the shared memory server rejected its credential, so there was no prior-history orientation. files changed while i read. line numbers are as of my read.

**fixed during review (keep the regressions)**
- `value_composition.py` imported `reference_digest` from `territory_evidence`, which doesn't define it. that was an ImportError at load. it now calls `publication.reference_digest` (lines 258, 452).
- `ledger-publication.ts` checked team-group order by comparing `"team:position"` strings. that rejects real data, because team `"1:F"` sorts after `"10:D"`. it now compares team then position (131–137). `.tmp/ledger-detached-validation.ts:161-164` is the regression.

**defects still present**
1. **history-splitting identity, medium.** `value_composition.py:~476-483` builds the ledger method's identity (`design_sha256`/`reference_id`) from whichever upstream rows are *provided* in each year. a year where some table/strength has no provided rows gets a different identity. the web history key (`analysis-values.ts:1201-1207`) then breaks every ledger history at that year as "quantity definition changed". the spec says availability and hashes must not split histories. cheap check before the build: compare the three annual ledger methods' `reference_id`. better fix: derive meaning from family/recipe declarations, not row presence.
2. **hard-coded territory claim, medium.** `value_composition.py:300` always states "final-year hazard sensitivity exceeded its budget". it should come from the bound reference's saved diagnostics, or the ledger's own `territory_*` statuses. fixtures currently print an unchecked claim.
3. **empty panel aborts the year, low-medium.** at `player_value.py:201`, an available finishing/setting value with a zero-opportunity panel stops composition instead of withholding the term. the TS check at `ledger-publication.ts:369-370` matches. either prove upstream can't supply a skill on an empty panel, or withhold with a reason.
4. **new shorthanded states inherit a 4v5 blind spot, low-medium.** at `player_mechanisms.py:784-787`, an attempt whose choice strength differs from its short segment's strength is skipped. the segment is not excluded, so the attempt is lost but its time is kept. 4v5 must stay as accepted. for 3v5/3v4, penalty-expiry boundaries make this plausible: exclude the segment, or count these cases in the real reduction and document them.
5. **saved shorthanded reductions are barely checked, low-medium.** `validate_shorthanded_reference` (`player_mechanisms.py:557-653`) accepts any internally consistent receipt with the right prepared/score bindings. it never checks retained keys or masses against the score stream, and the receipt carries no implementation identity. so a receipt from an older buggy helper would pass as "checked exact reuse".
6. **readers disagree on shared attempt rates, low.** python checks every player's spatial row against the annual rate (`value_evidence.py:403-407`). TS checks only provided rows (`ledger-publication.ts:227-241`). mixed row availability passes one and fails the other.
7. **TS checks totals less strictly, low.** for an unavailable total, TS checks only that the value is null (`player-analysis.ts:2557-2560`). python also requires the missing term's exact reason (`value_evidence.py:342-351`). the spec requires reasons to match across summary, detail and export.
8. **panel metadata can be nulled, low.** `value_composition.py:102` takes the panel from the first provided execution row. if a state has none, the panel is null even though the score manifest has it. both validators assume the same (`value_evidence.py:446-447`, `ledger-publication.ts:243`). this conflicts with "no nulling known metadata".
9. **final-year diagnostics assume full rows, low.** `value_composition.py:180-195` assumes every skater has a provided penalty/shootiness row and a probe row. the territory path skips missing rows instead. `mechanism_composition.py:81-85` guarantees full rows on the real path, so only fixtures are at risk.
10. **partial schedules can rank as complete, low for real data.** `read_reported_usage` (`analysis_data.py:1290-1298`) and the summarizer count only selected games. if a selection is a subset of the inventory, a group can be "complete" over a partial schedule, and `inventory_games` is mislabeled. confirm the real `selection.json` has `game_ids: null` for all three years. otherwise mark such groups incomplete, as `execution_design.py:841` does.
11. **source-reducer edges, low.**
    - `descriptive.py:1649` stops the whole reduction on a mismatched boxscore team instead of excluding the group. the interpreter always sets that team, so this can't happen today.
    - a single unidentified boxscore row with zero time is skipped as a scratch (`descriptive.py:1677`, `:1707`). the spec says an unidentified potential skater excludes both groups.

**verified correct**
- the ten terms: signs and units are right. the 5v5/pp/pk multipliers apply once. penalties taken is not negated. defense, pk and ice lost are negated once.
- `.8` appears once. K is enumerated from the saved logits in both readers, with no `1-p0` division, including the rounded-one case.
- the shooter-role check uses the shootiness rows' role, and neutral p is checked against the full unit.
- zero-weight states give exact zero. finishing and setting availability stay separate. totals require all ten terms.
- depth: ranks follow the competition rule, cutoff ties stay regular, and each player gets one fixed annual weight, normalized before multiplying. an unknown depth group gives not_applicable. a missing member vector withholds the whole position reference. the python validator regenerates ranks, means and subtraction.
- the 4v5 path matches the pre-change `reduce_minor_reference` in the main checkout: same date-order accrual, same sum vs fsum, same dispositions. zero-event time is kept, and the score stream is grouped by game and fully consumed.
- the narrow territory reader digest-checks its files, loads only `values` and does not reproject.
- the selection is closed, and the ledger evidence query rejects strength/population/type selectors.
- the web layer renders producer values only. the F↔D history break applies to replacement lines only.

**not reviewed**
- `physical-schema.ts`, `client.ts`, the comparative/analytical/microstat cards, png/csv exports beyond `ledger-detail.tsx`, and the exchange-5 converter (`.scratch/v1-12/convert-exchange6.py`).
