# pr03c — source evidence and scientific revision

researched 2026-09-30. no implementation, recapture or fitting. three reviewers covered statistics, source contracts and public evidence/content. [03b's rejection](chance-03b/decision.md) remains unchanged. the next implementable boundary is [source revision](../specs/03c-source-revision.md); a new chance model needs a subsequent specification.

implementation follow-up: [03c's completed decision](chance-03c/decision.md) supersedes the implementation gaps below. the original research counts remain attributed to their earlier reader; no fit or scientific verdict was rewritten.

## evidence we overlooked

the subsequent [field-to-feature audit](model-input-audit.md) broadens this finding: the rejected candidate also omits documented context features, while several useful captured fields remain unstructured. it separates source mistakes, explicit simplifications and later product scope. 03c remains a source revision; the next model must justify its information set explicitly.

the api omits `shotType` for all 111 blocked attempts in the three local fixtures. the already captured nhl play reports explicitly describe a type for every one. treating api missingness as absence from public evidence was an incomplete source audit.

| fixture | report block types | matched unblocked api/report agreement | report body sha256 |
|---|---:|---:|---|
| `2025020001` | 37/37 | 82/82 | `2911d9f2cc567284aad4dc161e04f0fa9cb9153ad1088fb8b492d56aa2061837` |
| `2025020006` | 40/40 | 83/83 | `37e8a9c8d8f32428890a9be0ee32abeaa847a5579615e212c61e90084e56a310` |
| `2025021094` | 34/34 | 84/84 | `eb0bf73de066f115e69f1d259829106a61c1b2bc16ecfe4e753cb2c0305e68a9` |

these are source-audit counts, not a true-5v5 training population. agreement uses only events matched by the current reconstruction; it cannot establish agreement in excluded groups or earlier seasons. report block types total 66 wrist, 28 snap, ten slap, three backhand, two tip-in, one deflected and one poke.

example: `2025020001`, `PL-6` names marchand, the opposing blocker and `Wrist`. teammate-blocked rows also carry explicit types. `play_report.extract_report` already preserves the description; interpretation does not extract its shooter/type. reproduce by reading `fixtures/captures/<id>/play-report/body.bin`, selecting `BLOCK` rows, and comparing comma-delimited type tokens with api fields on uniquely matched events. no response bytes were changed.

the [same-clock issue](../issues/same-clock-event-matching.md) records another omission: two shooters distinguish `PL-216/217` in `2023020001`, while wrist/poke distinguish `PL-218/219`. the pre-03c reader rejected repeated period/clock/kind groups before consulting these facts. exact source constraints can recover some events; they do not justify row-order matching or filling genuinely missing facts.

## what the rejected fits explain

the local review mirror contains the saved models even while the drive is detached. read-only comparison of anchor against `short_kernel` found the sole configuration change `kernel_distance_ft: 20 → 10`:

| saved comparison | development | confirmation |
|---|---:|---:|
| exactly equal conversion coefficients | all 1,659 | all 1,825 |
| joint reference records/counts/weights | identical | identical |
| changed block-avoidance coefficients | 1,570 | 1,717 |
| maximum absolute coefficient change | 3.064329 | 3.766404 |

grids/layouts are identical; origin distributions differ. the reported unblocked-value changes therefore arise through refitted block avoidance, not conversion, reference weighting or changed grid/recorded coordinates. the kernel's geometric assumption did change. blocked values additionally depend on changed origin posteriors. a conversion calibration adjustment alone cannot repair this coupling.

model hashes, under `/Users/nnandal/Documents/code/hockey-stats-03b-review/03b-20260930/fits/`:

- `development-recipe-anchor/model.json`: `e19cd99d08604bef734be30c9c0c6f9295da089d3da824c4373ba597bb69b222`.
- `development-recipe-short_kernel/model.json`: `0e0129ed1ae9ee172ad4c65a923886f5dc1f23a31943c2ef8244bc8184bd0568`.
- `confirmation-anchor/model.json`: `737020776fd18ec0b76cdef721ff31e14d45c482c39cb04336230b514077fd69`.
- `confirmation-short_kernel/model.json`: `e49ba0e0008403d4d71f2752687a7bf53aaf8cd4ac2bc82656dc24d4c4947805`.

## public independent-origin evidence

the user has no full-game replay access. do not plan a subscription or manual annotation campaign as a prerequisite.

the official [big data cup 2026 definitions](https://github.com/bigdatacup/Big-Data-Cup-2026) describe shot coordinates as releases, including blocked attempts. a bounded in-memory inspection of [one official event file](https://github.com/bigdatacup/Big-Data-Cup-2026/releases/download/Data/2025-10-11.Team.A.%40.Team.D.Events.csv) found 1,878 rows and 26 blocks, 23 with five skaters per side. all 26 supply release coordinates; all secondary coordinates are empty. league identity is unverified; no paired block-contact field or reliable nhl game mapping was established. externally reported releases can inform that sample's release distribution; they cannot validate our conditional origin reconstruction without corresponding block evidence. the [provider agreement](https://github.com/bigdatacup/Big-Data-Cup-2026/blob/main/legal.md) contains use restrictions; no redistribution permission is assumed.

[pitassi et al.](https://cs.uwaterloo.ca/~brecht/papers/isace-2025-traffic.pdf), figure 3 and its text, identify a guenther release subsequently blocked by donato in utah–chicago on 2024-10-08. the text supplies a potentially useful public example, not a representative downloadable validation corpus. no release coordinate was extracted or independently verified here. the paper also describes inferred/corrected release timing and unmatched attempts; tracking-derived records are not automatically physical ground truth.

feasibility result: external releases and a published nhl case exist; an independently paired nhl release/block sample remains unestablished. no tracking importer, computer-vision system or annotation ui is justified by this finding. a bounded later investigation may inspect one additional cup game and match the published case; it must identify what new fact that work could establish first.

## implications for the next scientific specification

[hockeyviz's published xg8](https://hockeyviz.com/txt/xg8) distinguishes shot-type geometry, discusses problematic tip coordinates and specifies a heuristic blocked-origin imputer. this supports inspecting those source attributes; it does not validate our forward kernel. its [2026–27 preview](https://hockeyviz.com/txt/preview2627) announces rewritten models with explanations forthcoming, not a replacement recipe available to copy here.

the council agrees that 03b's consequential probability-bin calibration failure is direct evidence against that candidate. shot-type discrepancies expose useful omitted heterogeneity, but do not alone prove miscalibration conditional on the model's smaller information set. adding one type coefficient is a hypothesis, not an established cure. type-specific conversion multiplied by type-pooled block avoidance is generally not a coherent type-conditional goal probability; the origin distribution also needs its conditioning specified.

we also overconstrained the earlier scientific gate. zero-excess bounds require sufficiently precise evidence of nonpositive excess loss, with no allowance for practically negligible degradation. a useful retrospective valuation does not logically require that result on every marginal probability diagnostic. arbitrary kernel stress is not a confidence region, and cellwise/max-event instability is not identical to instability of an eventual regional/player conclusion. these are reasons to justify the NEXT protocol from its claims, not to relabel 03b as accepted. [proper-scoring-rule foundations](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf)

measured physical-origin accuracy requires independent observations. explicitly model-conditional spatial estimates need defensible assumptions, adequate factual-probability diagnostics where calibration applies, and consequential sensitivity. standardized opportunity is not calibrated against factual goals. estimates must not claim that unobserved origins were measured accurately. independent evidence remains valuable without becoming an undeclared league-wide tracking project. current chance-1 remains unsupported.

all three seasons have informed development. changed reconstruction, fresh downloads or different folds do not create untouched confirmation. a revised specification must distinguish historical development diagnostics from separately justified confirmation and explain any changed criteria before judging its new results. [selection-bias research](https://www.jmlr.org/papers/v11/cawley10a.html)

## boundary and remaining evidence

03c owns report attributes, uniquely supported same-clock joins, exact failed-attempt non-goal semantics, scoring-relevant chronology and a source/population audit. conversion/origin model design follows those outputs. unresolved frame and shift conflicts remain unavailable; correction requires additional source evidence.

the external drive is detached. local fixtures and the verified review mirror support this specification; the mirror's source extracts are not complete captures for integration verification. implementation must obtain the original affected captures and full admitted corpus when available. no additional user preference is needed for this boundary.
