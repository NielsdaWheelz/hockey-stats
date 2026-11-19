**verdict:** i found no blocking defect in the phase-two owners. the converter preserves bytes faithfully. the readers agree on everything that matters. the journeys are wired to one producer's values with no second calculator. what's left is two omissions and some export and parity looseness. the real interface is unverified by anyone, because no real candidate exists yet.

**limits**
- the shared memory server failed to connect and its tools weren't exposed, so there's no prior-history orientation. local memory supplied only project context.
- i read files only. nothing was executed, tested or written, and i read no external data.
- `verification.md` grew a dispositions section (lines 24–35) between my two reads, so the checkout was changing while i read it.
- `verification.md:34` says the shorthanded pass was interrupted and is being redone. so there is no real exchange 6 output, no candidate and no real journey to inspect. everything i say about journeys comes from source, plus the fixture receipts i didn't rerun.

**blocking:** none.

**non-blocking defects and omissions**
1. **the microstat png omits the six ledger rows (medium, inspected).** `microstat-card.tsx:47-125` draws the strip groups and supports but never `model.components`. the status line at `:189` says this is deliberate. the html card (`:191-207`) and the csv (`:28`) do carry the rows. but v1-12 exists to integrate those six rows, and the spec's acceptance names png downloads. either draw them with workload, reference and limits, or record the exclusion as a decision. idk which you intended.
2. **the composed exchange doesn't bind its exchange 5 ancestry (medium-low).** inspected: `convert-exchange6.py:69-72` writes the receipt tying ec5349… to 10daf0… beside the manifest, and nothing references that receipt. `value_composition.py:356,480,572` binds only the converted manifest as `source_results`. `:291-292` (method evidence) and the selection schema don't carry the receipt either. inferred: once the converter is deleted, a detached reader of the candidate can't attest the accepted v1-11 lineage. it has to rely on `receipts/real-conversion.json` in the repo, or compare member digests against the donor by hand. that's recoverable, but it's provenance by testimony. cheap fix: put the conversion receipt in each annual method's `evidence`.
3. **the converter's real path does no schema-6 read-back (low, inspected).** `convert-exchange6.py:66-68` calls `p.read_results` only on the fixture path. so the real receipt's "passed" means "member bytes match the donor digests", not "a valid exchange 6". `value_composition.py:567-570` does validate everything before finalizing, so nothing corrupt can be published. the failure just surfaces later and costs more.
4. **the ledger construction csv's execution-state rows aren't typed (low, inspected).** `ledger-detail.tsx:54-60` leaves the value and reason columns null, puts everything in json, and still labels the unit `goals_per_reference_basket`. the appendix asks for explicit units and unavailable reasons per row type. term rows comply. state rows, team-rank rows (reasons only in json) and weighted-member rows (`depth.reason` in `replacement_reason`) bend the columns.
5. **the two readers break a tie differently (low).** inspected: when every row at a strength is `not_computed`, typescript picks the first row by `player:strength` string order (`ledger-publication.ts:222-225,239-242`), and python picks `min(player)` (`value_evidence.py:398`). with ids `"12"` and `"123"` those disagree. inferred: it only bites with variable-length ids and differing explanations per player. real nhl ids are fixed-width afaict, so fixtures are the only exposure.
6. **the client cross-check is partial (low, inspected).** `client.ts:470-478` checks the summary's `available`, `member_count` and `total_seconds` against the reference. it skips `complete_groups` and `excluded_groups`. the server derives all of them from one validated reference (`ledger-publication.ts:436-442`), so this is incomplete self-consistency, not an exposure.
7. **a cosmetic invented explanation (low, inspected).** `convert-exchange6.py:55` writes `'annual ledger construction not computed'` when a provided ledger family has all-pending rows. `ledger-detail.tsx:128` shows the ledger's own explanation first, and composition replaces the row anyway.

**prior dispositions spot-checked**
- **history identity:** fixed. a withheld state now inherits the cross-year label only when the available years agree (`value_composition.py:506-513`).
- **territory claim:** fixed. the wording comes from the saved diagnostics (`:300-303`, `:323-325`).
- **neutral-rate parity:** fixed. python now checks only supplied donors (`value_evidence.py:396-402`).
- **missing totals:** fixed. typescript checks reason and detail (`player-analysis.ts:2558-2563`).
- **panel nulling:** fixed. a selected score forces a non-null panel in both readers (`ledger-publication.ts:252`, `value_evidence.py:491-493`).
- **empty-panel hard stop:** still in both readers. but upstream composition already marks empty panels unavailable with reason `no_exposure` (`execution_composition.py:228-230`), so the stop is unreachable for valid inputs. inferred; i didn't trace every validator.

**boundaries that hold (inspected)**
- **startup:** strict startup pairs pending families with pending references and rejects provided ledgers that lack one (`analysis-publication.ts:915-975`).
- **detached checks:** the typescript reader checks the full team-by-position matrix, competition ranks and cutoffs, fixed weights, normalized depth means and subtraction, K from enumerated slots, source-pool A, and exact copied inputs and support (`ledger-publication.ts:61-443`).
- **summary path:** the overview summary is the row minus `evidence`, plus coverage that the server computed (`publication.ts:205-231`). sqlite's json functions preserve number text afaict. the client then requires exact scalar equality between summary and detail (`client.ts:469-478`).
- **detail loading:** ledger detail loads only for a single selected ledger metric. analytical term labels, the comparative link and microstat component links all route through it (`client.ts:483-485,969-975,1114-1124`). finishing and setting rows link back separately to the standalone 5v5 skills (`ledger-detail.tsx:154-167`).
- **history:** the F↔D break applies only to replacement lines (`analysis-history.tsx:494-503`), and the shared csv carries `ledger_detail` plus the break reason (`:388,482-483`).
- **pngs:** the analytical and comparative pngs carry workload, reference, coverage and unestimated uncertainty (`analytical-card.tsx:1078-1134`, `comparative-card.tsx:171,703,803`).
- **converter bytes:** every copied member is digest-checked (`analysis_publication.py:2358-2367`). computed donor ledger rows are refused on the real path. pending references match the family explanation that both readers require.
- **storage:** the physical schema for `ledger_reference` and `value_ledger` matches the python ddl.

**unverified:** the real-candidate journeys, payload sizes and startup, and the real donor's ledger-family disposition.
