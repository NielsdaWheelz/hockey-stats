# pr03c — source evidence for the chance-model revision

status: research/specification authorized; no code, captures or derived artifacts changed. 03b is complete and rejected. [audit and council findings](../research/chance-03c-source-audit.md) · [brief](../brief.md) · [plan](../plan.md)

the landing amendment below addresses [verified additional goal evidence](../research/source-audit.md#additional-source-evidence-without-the-drive). [03d](03d-chance-revision.md) owns the revised estimator and selected features; [03e](03e-training-assessment.md) owns real training/scientific assessment. those are stubs. no separate landing or generic input-audit pr.

## target and scope

recover report attributes, admit landing goal modifiers, remove two causes of unjustified whole-game score exclusion, and measure the revised evidence population. provide usable source evidence for 03d without claiming it fixes calibration or origins.

one source revision, with five non-overlapping responsibilities below. no predictor, likelihood, kernel, numerical penalty or acceptance-threshold changes; no refits, publication, attribution model, fallback feed, legacy reader, tracking importer or annotation tool. explicit landing penalty-shot evidence enforces the existing population exclusion. 03b artifacts and rejection remain historical evidence. the drive is detached; its original captures are required before completing full-corpus verification.

## 0. effect capture owns the additional response

add `landing` to the fixed game sources, requesting `https://api-web.nhle.com/v1/gamecenter/{gameId}/landing`. default capture still requires a new output directory and now attempts six sources sequentially. reuse `captureResponse`, the current receipt version, body representation, timeout and no-redirect/no-retry behavior; preserve the complete response before interpretation.

one additional mode in the existing cli:

```sh
npm run capture -- --game 2025020001 --source landing --out /absolute/existing/game-directory
```

accept only the single value `landing`; reject unknown/repeated options before network access. require the parent game directory and a readable version-1 `play-by-play/capture.json` with matching `gameId` and `source`. this is accidental-path protection, not a second scientific receipt validator. exclusively create only the missing `landing/` leaf; an existing leaf fails before requesting. no overwrites, missing-source discovery, automatic resume or generalized source selector.

update capture reporting for six default requests or one selected request, leaving season capture at four. remove the hardcoded five-response assumption; derive success from the operation's nonempty requested response set. failure guidance must preserve any existing landing leaf: use an explicitly prepared new game-directory copy for a replacement capture, preserving the original. retain ordinary manual cleanup guidance for unfinished local work. no force option.

for the existing corpus, add landing once per game using this mode; an explicit sequential operator loop suffices. cost: 3,936 additional requests, not reacquisition of the existing five bodies. every new receipt keeps its actual retrieval date. inputs are a mixed-retrieval evidence set, not a simultaneous snapshot. full-corpus acquisition waits for the drive and implementation authorization.

## 1. interpretation owns source facts

reuse `play_report.extract_report`, `interpret_game`, the existing game/team roster lookup and located issues. preserve the api `Event.shot_type`, report description and captured bodies unchanged.

add nullable fields to `ReportRow`: `shooting_team_id: int`, `shooter_sweater_number: int`, `shooter_id: int`, `shot_type: string`. these are report-derived observations, not api replacements. retain exact parsed type spelling; normalization belongs to reconciliation. resolve the leading shooter's jersey through the unique game/team roster, never through the candidate on-ice list or fuzzy name matching. unknown supplied teams and unresolved supplied jerseys retain an integrity issue and null id; their issue still withholds membership. nulling an invalid supplied identity must not turn it into ordinary missing evidence.

parse only attributed attempt-description forms: leading team/`#jersey` for `GOAL`, `MISS`, `BLOCK`, and leading team/`ONGOAL - #jersey` for `SHOT`; goal-count suffixes and assists are not shooter identities. identify type only in the explicit comma-delimited type position. do not mistake blocker, assistant, zone or miss-reason text for the shooter/type. teammate-blocked wording has the same shooting-team meaning. preserve unknown tokens and expose them in the audit; no generic natural-language parser or guessed team alias.

source vocabulary initially corroborated by fixtures: `Wrist`, `Snap`, `Slap`, `Backhand`, `Tip-In`, `Deflected`, `Wrap-around`, `Poke`, `Bat`. audit additional spellings before adding explicit mappings. unknown source text is not silently converted to a known type or ordinary non-penalty play.

admit the exact api pair `537` / `failed-shot-attempt` as a known **non-goal** kind for complete timed-goal accounting. retain its native kind; wrong code/key pairs and unknown kinds remain unresolved. do not recode it as `missed-shot`, infer a universal penalty-shot flag, or add it to the four modeled attempt kinds. existing report penalty-shot evidence and shootout distinctions remain authoritative for their own records. this repairs score completeness, not the modeled attempt population.

### landing goal observations

extend python's fixed source catalogue/url admission. reuse completed regular-season validation, then compare landing's game id, season, type, date and home/away team ids with the established core identity; landing cannot replace it. missing/non-2xx/malformed or conflicting landing payloads make this source unavailable with a reason; receipt/digest violations remain input-contract errors. never route landing through result accounting: it lacks `gameOutcome` and its scoring summary is not a complete shootout event feed.

add `landing_goals: list[LandingGoal] | null` to interpretation. flatten `/summary/scoring/{period_index}/goals/{goal_index}`; retain that exact `source_path`. each row has nullable `event_id`, `period_number`, `period_type`, `time_in_period`, `elapsed_seconds`, `team_id`, `credited_scorer_id`, `goal_modifier`. period facts come from the enclosing `periodDescriptor`; scorer from `playerId`; team from strict boolean `isHome` and admitted game teams. a supplied `teamAbbrev.default` must agree; invalid supplied context remains an issue, not ordinary missing evidence. keep exact modifier text.

malformed scoring collections are unavailable; valid collections retain deficient rows and located issues. reuse clock/type/identity helpers. shootouts keep a valid reported clock but have no elapsed exposure. preserve duplicate ids and unsupported strings for diagnosis; do not discard inconvenient rows to create a unique join. missing/null modifier differs from a malformed value. no default type, modifier or physical shooter.

## 2. reconstruction owns joins and reconciled attributes

retain period/elapsed-clock/kind grouping and unique source identities. for repeated **attempt** groups:

1. require equal nonzero api/report group sizes and valid, unique identities. invalid rows cannot be discarded to manufacture a match.
2. build candidate edges from exact known shooting-team/shooter evidence and normalized known type. missing fields add no invented constraint; contradictory known values remove the edge. a supplied jersey must agree with its unique roster identity before being used as identity evidence.
3. accept only one complete one-to-one assignment for the whole group. stop searching after a second solution. use existing statuses: invalid identities → `unavailable`, unequal sizes → `ambiguous`, zero complete assignments → `unmatched`, multiple assignments → `ambiguous`. retain unresolved membership and a located reason in every unsuccessful case. do not recover a convenient subset of an unresolved group.
4. apply existing participant, goalie, membership, situation, penalty-shot and team checks after matching. one report row cannot serve two events. no row-order, coordinate-nearness, inferred timing or consensus-membership tie-break.

keep non-attempt matching unchanged. retain ordinary singleton matching; newly parsed participant contradictions withhold membership. a singleton type disagreement leaves event identity intact but type unresolved. repeated groups use type to disambiguate only when both values are supported, so a disagreement can prevent that group's join. this conservative difference is explicit; greater recovery is not the objective.

each reconstructed attempt adds `shot_type_evidence`:

```text
{
  api_value: string|null, report_value: string|null,
  value: string|null,
  status: agreement|api_only|report_only|missing|conflict|unsupported|unmatched
}
```

`api_value` and `report_value` preserve source spelling. canonical `value` uses explicit mappings to `wrist/snap/slap/backhand/tip-in/deflected/wrap-around/poke/bat`. precedence: unmatched report identity → `unmatched` and null, retaining any api observation; then any present unsupported token → `unsupported` and null; then compare supported observations. agreement supplies the common value, differing values yield `conflict` and null, exactly one supplies its value with its named basis, and null/null is `missing`. do not infer type from outcome, coordinates, player identity or a default category. existing event/report source indices locate the evidence; conflicts/unsupported forms add located issues.

type absence/conflict alone does not invalidate otherwise established 5v5 membership. later models own type eligibility. `chance_data.prepare` forwards this evidence and uses its canonical value for the existing `shot_type` diagnostic field; it does not add a predictor. retain api originals in interpreted events. inspect existing `tip_deflection_recorded_proxy` diagnostics using the reconciled type; this still does not relocate tips.

### landing-to-event join

join only api goals by `eventId`, checking uniqueness across **all api events** and all landing rows. require known agreeing period number/type, valid reported clock, team and credited scorer. compare shootout clocks without requiring elapsed seconds. do not match by clock/order when ids fail, and do not require coordinates, assists, strength or cumulative scores to agree. consult located interpretation issue codes for the row and enclosing period: malformed modifier/clock stays unavailable; contradictory team abbreviation stays conflict. never infer validity from nullable values alone or inspect error-message prose.

each reconstructed api goal carries `goal_modifier_evidence`; other events carry null:

```text
{ source_path: string|null, reported_value: string|null,
  status: reported|missing|unavailable|unmatched|conflict|unsupported }
```

precedence: unavailable source, unusable/duplicate id or missing/invalid corroboration → `unavailable`; valid unique api id with no landing counterpart → `unmatched`; a unique counterpart with contradictory context → `conflict`. retain a uniquely located counterpart's path/text even when unusable. only after a successful join: absent/null modifier → `missing`; exact `none`, `own-goal`, `awarded`, `penalty-shot` → `reported`; other strings → `unsupported`, preserving text. malformed non-string modifiers are `unavailable` with a located issue. duplicated candidates remain in interpreted rows; evidence has no arbitrarily selected path/value. unmatched/invalid landing rows remain in the audit.

extend reconstruction's existing positive report-penalty-shot rule with a joined `reported` modifier `penalty-shot` before classification/coverage: it must not emit `five_on_five` for that event. retain supported member lists, unrelated membership issues and unchanged elapsed exposure; do not manufacture resolved membership to classify an exclusion. preparation validates/forwards the evidence and enforces the same existing outside-5v5 exclusion. `none` cannot negate a report exclusion, repair membership, or certify an ordinary physical attempt. shootouts remain outside regardless of modifier. own-goal/awarded/unknown evidence remains diagnostic in 03c; 03d owns physical-attempt/actor treatment. modifiers never predict their own outcomes; timed goals still contribute to score accounting.

## 3. chance preparation owns pre-event score

amend `_scores` at its existing boundary: a strictly classified non-goal with unsupported elapsed time need not invalidate independent goal accounting. its clock stays null and its source issue stays visible.

still require unique source ordering, known nondecreasing periods, valid regulation/overtime versus shootout classification, both matching `timed_goals` checks and coherent goal ownership. every timed goal needs a supported clock; compare chronological order among all records with supported clocks. unknown potentially scoring events, contradictory known chronology or unsupported goal clocks withhold score support. read score before applying each goal. an attempt missing its own timing remains unavailable through reconstruction. no invented clock or blanket waiver for source errors.

keep `2023020078`'s conflicting frame unresolved. keep foreign-team, inconsistent/overlapping shift and unsupported-period evidence unresolved. these changes neither infer defending sides nor manufacture player exposure.

## 4. research owns the admission audit

reuse `hockey-stats-corpus` to regenerate cheap derived records into new directories from unchanged captures. reuse the exact three 03b comparison selections: 1,312 games in each earlier season, and the 1,309 previously selected 2025–26 games. these are now development/comparison populations, not fresh confirmation. account separately for the complete 1,312-game 2025–26 inventory.

one retained operator: `.venv/bin/python research/source_review.py --selection /abs/selection.json --out /abs/newdir`, run from `analysis/`. consume the current selection/corpus/envelope contracts and `chance_data.prepare`; do not duplicate parsers, matching, score reconstruction or eligibility. preparation does not return every report/landing row: reread its already validated game envelopes identified in `prepared["inputs"]` for source-wide counts, and use prepared attempts for analytical populations. no new loader framework, network or model input. purpose remains `fixture_exercise` or `research` from the selection.

write finite `review.json` last, schema 1, containing executing implementation identity, actual input hashes, selection/purpose, existing coverage, counts by season/event kind/match status/type-evidence status, landing availability/modifier/evidence status, same-clock group sizes/outcomes, score-unavailable reasons, unknown tokens, and source locators for contradictions/recoveries. distinguish source rows, matched events and eligible attempts; do not use them as interchangeable denominators. show explicit penalty-shot exclusions and unmatched shootout events separately. reuse existing exclusive writing/failure behavior; ordinary gaps remain explicit, malformed inputs fail.

write `docs/research/chance-03c/decision.md`: before/after coverage on identical game selections; recovered/excluded cases and reasons; api/report type agreement and missingness by outcome/season; modifier coverage and cross-retrieval conflicts; remaining source limitations; next-model implications. use retained 03b coverage as the baseline without running an old reader or relabeling old fits. report absent landing inputs as gaps rather than an implicit modifier `none`. every selected game needs a recorded landing request disposition, including failed requests; successful full coverage is not promised. explain every population change; unexplained changes prevent completion. no claimed improvement in model performance without a new study.

carry forward the [field-to-feature audit](../research/model-input-audit.md): distinguish captured-but-uninterpreted facts from deliberately omitted predictors. retain attributed report-distance/own-goal examples for the next coordinate/actor decision; do not add their parsers or silently exclude events in this slice. each relevant public-method input needs an explicit include/assess/omit decision in the NEXT model specification, including any additional source admission. this prevents another api-only availability assumption without expanding 03c into every listed feature.

## contracts, files and cutover

| owner/files | responsibility |
|---|---|
| `app/src/operator/capture.ts`, `cli.ts`, `capture-report.ts` | sixth game source, bounded landing-only mode, truthful success/failure reporting; reuse existing capture primitives |
| `analysis/src/hockey_stats/captures.py`, `interpret.py` | source receipt/url admission, landing observations, exact kind semantics, report attributes and shared roster identity; interpretation schema **3** |
| `analysis/src/hockey_stats/reconstruct.py` | unique attempt-group matching, type reconciliation and landing goal join; reuse membership/frame/exposure rules |
| `analysis/src/hockey_stats/cli.py`, `corpus.py` | both reconstruction-envelope writers emit schema **2** with embedded interpretation 3; corpus report remains schema 1 |
| `analysis/src/hockey_stats/chance_data.py` | require envelope 2/interpretation 3, forward/validate type and modifier evidence, existing penalty-shot exclusion, narrow score guard |
| `analysis/research/source_review.py` | source/population summaries only; no estimator or second reconstruction |
| `fixtures/captures/`, `fixtures/references/`, `fixtures/README.md`, `README.md` | bounded affected captures and their season references, hand-checked facts and commands; no new harness or dependencies |
| `docs/research/chance-03c/decision.md`, `docs/issues/` | report, resolved source issues and explicit remaining scientific work |

hard cut the current reader to the new envelope/interpretation versions and regenerate derived inputs. do not migrate old artifacts or add version dispatch. model mathematics and saved model format do not change. historical artifacts remain readable through their historical git revision. centralize the type mapping at its owner; remove duplicated attempt-team parsing where structured report evidence replaces it. keep the html extractor structural and reuse the existing roster resolver.

## verification and content

temporary end-to-end checks: first demonstrate current failures, then run the installed interpretation → reconstruction → corpus → preparation → review path after each responsible repair. refactor, repeat the relevant checks, then delete all test code/test-only dependencies. retain raw fixtures, hand-checked facts and the scientific source-review operator.

- copy original captures for `2023020001`, one confirmed failed-penalty game such as `2023020955`, and `2024020102` into the local fixture set when the drive is available. also copy the existing four-source reference bundles for `20232024` and `20242025`; corpus admission cannot use the local 2025–26 inventory for those games. verify receipt/body identity; source extracts in the local review mirror are not substitute captures. no need to copy the season corpus locally.
- capture landing for the three existing fixtures using the new mode. verify all original files unchanged, a sixth-source default capture, refusal before network on bad arguments/receipt identity/existing leaf, and existing error-body/interruption behavior. check status reporting for default, landing-only and season commands.
- admit bounded native captures for `2025020282`, `2025020307` and `2025020184`: copy their five original sources from the drive, then add new landing receipts. verify the attributed own-goal/awarded joins from the source audit. local review extracts support research but do not substitute for complete originals. freshly recaptured examples may exercise software offline only when explicitly distinguished from frozen-source verification.
- verify all nineteen scoring-summary joins in the existing fixtures, including the penalty-shot and shootout-winner cases. omitted shootout goals stay unmatched. exercise missing/null/unknown/malformed modifiers, conflicting context, duplicate ids and unavailable landing; unrelated game facts remain usable. a confirmed landing penalty shot is absent from reconstructed 5v5 counts and prepared eligibility even when report wording lacks that marker; `none` never reverses a report exclusion. own/awarded observations pass through without invented physical actors or new exclusion rules.
- recover api indices `212/213/214/215` against `PL-216/217/218/219` for `2023020001`; retain true ambiguity, unequal groups, conflicting facts and duplicate ids. check singleton joins, teammate blocks, goals with assists, unsupported grammar and unique roster resolution.
- reproduce all 111 report-only block types and the 249 previously matched unblocked agreements in the existing fixtures; report any newly recovered joins separately. exercise missing, unknown and conflicting tokens; never fill a type or use it as a modeled outcome flag.
- exact failed-attempt semantics restore ordinary goal accounting; wrong pair/unknown-event cases still fail. the unsupported takeaway clock in `2024020102` remains null while independently supported pre-event scores recover; invalid goal timing/ordering still fails.
- reconcile coverage changes on the original full selections. raw bytes and elapsed-exposure results remain unchanged; frame/shift defects remain explicit. ensure old envelope versions fail visibly and fresh derived inputs work without fitting.

analytical owners define populations and counting rules; the content designer makes their denominators, labels and locators explicit. lead with one compact before/after table and attributable cases. “report-derived”, “reconciled”, “unknown” and “conflicting” describe evidence, not measured physical truth. no new dashboard or plots are required.

## final state and next boundary

03c is complete when the new source contract works end to end, all selected games have an explained disposition, and type/modifier/source coverage is documented for 03d. source issues close only on their recorded evidence criteria; own/awarded physical-attempt semantics, conversion, origin accuracy/value stability and unsupported probability claims remain open. 04 remains withheld for the rejected candidate.

03d and 03e retain the subsequent model/assessment decisions, including coherent type/origin conditioning and the already exposed seasons. 03b's thresholds and verdict are not rewritten.

tradeoffs: one more source-focused review boundary delays the model revision but prevents fitting against omitted or selectively excluded facts. landing adds one request per game and possible cross-retrieval disagreement. conservative matching retains some recoverable-looking cases; unsupported tokens remain explicit until audited. regenerating cheap derived data costs time/disk, while preserving expensive fits and original observations. public origin evidence remains limited; no replay subscription, tracking dependency or manual annotation campaign is assumed.
