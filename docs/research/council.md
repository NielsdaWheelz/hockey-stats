# council synthesis

date: 2026-09-29. status: initial reconnaissance recommendations. three independent reviewers covered hockey statistics, product design, and systems/data; the primary agent inspected and preserved the predecessor. these are disciplinary perspectives, not imagined quotations from named experts. subsequent user decisions are authoritative in the [project brief](../brief.md); recommendations and open questions below retain their original context.

execution follow-up, 2026-10-08: the assigned [conversion-scale benchmark](chance-03j/decision.md) completed with `inconclusive` and no supported intervention. this preserves the historical recommendations without making avoidance or any other native experiment automatic.

later council review and user-approved direction after merged 03i: [conversion-first research and retained features](model-direction.md), 2026-10-08. the original recommendations below remain dated evidence.

## recommendation

the proposed sequence is sound: preserve the predecessor, build a selective knowledge base, establish the product's questions and statistical meanings, design ownership and contracts, then specify reviewable implementation slices. repository preservation and this first knowledge-base pass are complete. architecture and implementation remain unstarted.

one amendment matters: do not plan every future slice before implementing anything. describe the dependency order, specify the first slice rigorously, and expand later specifications when evidence warrants it. empirical modeling contains questions a plan cannot settle. a detailed speculative backlog would recreate the predecessor's burden before recreating its value.

professional quality here means truthful data, defensible models, coherent interfaces, and recoverable operation. it does not mean reproducing the infrastructure or feature count of an established analytics business. rigor belongs first in meaning and evidence.

## the important philosophical split

the original evolving hockey war objective is retrospective attribution: what value accumulated in a period? magnus uses historical information and aging to estimate persistent player effects. these are different targets. neither is the universally correct interpretation of “player value.” [younggrens' philosophy](https://evolving-hockey.com/blog/wins-above-replacement-history-philosophy-and-objectives-part-1/), [magnus 9](https://hockeyviz.com/txt/magnus9EV)

mccurdy's simulation discussion explicitly values interpretable mechanisms in service of understanding hockey. that is a useful product philosophy, but interpretability does not excuse weak prediction checks or unsupported causal claims. [simulation philosophy](https://hockeyviz.com/txt/magnus8GameSim)

our recommendation is to distinguish **recorded results**, **estimated ability**, and **forecasts**. show them together when useful, while keeping their meanings visible. a sophisticated model cannot resolve a question the product has not actually chosen.

## what the council agrees on

- source evidence precedes model sophistication. unknown handedness cannot become left-handedness to satisfy a decoder.
- metrics need explicit populations, units, exclusions, exposure, baselines, and versions. “xg” names a model-dependent quantity, not a universal measurement.
- preserve components beneath totals. a summary is useful compression when the reader can inspect what it compresses.
- measured events, reconstructed events, imputed actions, and estimated player effects are different kinds of evidence.
- visual design carries analytical meaning: consistent rink frames, comparable axes, understandable denominators, and visible sample size are correctness concerns.
- validation must support the particular claim. fixture tests do not prove a model's calibration; a forecast benchmark does not prove causal attribution.
- offline development should use a bounded, attributed fixture corpus. full training data is a separate input with an explicit identity.

the evidence and limits are detailed in [statistical methods](statistical-methods.md), [product research](product-survey.md), and [systems/data](systems-and-data.md).

## useful disagreements

| question | competing positions | recommended resolution |
|---|---|---|
| what makes a good player metric? | credit realized contribution; estimate repeatable ability | name the estimand for each metric and model; retain both as possible products |
| interpretable regression or flexible prediction? | inspectable mechanisms; predictive interactions | compare against the intended use and honest baselines; neither complexity nor elegance wins by itself |
| maps or tables? | spatial mechanism; fast comparison | share one analytical selection across both views, then choose the first view by the user's question |
| broad public coverage or rich tracked actions? | automated event histories; passing/entry/exit detail | disclose observation limits; do not market reconstructed proxies as tracked actions |
| adopt the old pipeline or rebuild? | valuable edge-case knowledge; known provenance defects and coupling | retain cases and invariants; admit individual mechanisms only after checking their boundaries |
| durable runtime or explicit batch work? | automated recovery; easy operation and repair | choose the smallest mechanism that satisfies actual refresh and recovery requirements; no engine by default |
| stable contracts or research freedom? | reproducible consumers; evolving hypotheses | stabilize evidence identity and result semantics while allowing model implementations to change |

## proposed product direction

borrow hockeyviz's spatial explanation, evolving hockey's decomposition and comparison, money puck's concrete probability questions, all three zones' attention to actions, and reference sites' dependable definitions. these are complementary strengths, not a mandate to reproduce every product. [source-backed comparison](product-survey.md)

the first surface should answer a real recurring question. a game explorer is one good candidate because it offers immediate postgame utility and exposes agreement between events, maps, and totals. a team comparison or narrow player comparison may be better if that is the user's actual need. no first slice is selected in this pass.

the ui should have a clear visual hierarchy and deliberate density: a primary answer, a strong plot or table, then supporting detail. retain precise filters and exports without requiring every visitor to decode an acronym wall. explainability is a quality of the product, not a separate teaching workflow.

## effect and python

the preferred stack is feasible. use effect where it owns application effects, resource lifetimes, boundary schemas, errors, or reactive data. it need not wrap every pure hockey calculation or ui interaction. python is a strong candidate for statistical fitting and analytical computation. sharing artifacts is a candidate boundary; it is not yet a stack decision. [official-source investigation](systems-and-data.md)

the important ownership rule is that a calculation has one authoritative implementation. crossing languages requires an explicit contract for identifiers, units, nulls, populations, versions, and errors. a second language is worthwhile only if its numerical ecosystem pays for that cost.

do not select the database, frontend framework, durable workflow engine, or deployment provider before the required queries, update cadence, and publication behavior are known. effect's v4 release-candidate status also deserves a deliberate decision at implementation time.

## material tradeoffs in this pass

| choice | benefit | cost or limitation |
|---|---|---|
| private new repository | preserves a review boundary for inherited material | public access is delayed; the old archive remains public |
| independent git history and ignored legacy clone | clean new project with accessible archaeology | old code is not reproducible from the new repo alone; the archived remote and manifest identify it |
| copy source dossiers, link other old documents | useful evidence without importing the old specification | some follow-up reading remains in the archive; dossiers themselves remain historical and partly unchecked |
| review public pages and code | attributable evidence without paid access assumptions | no exhaustive subscription-ui audit or access to private production implementations |
| propose a small first analytical surface | earlier real utility and easier reconciliation | richer player models and broader coverage arrive later |
| defer detailed future slices and infrastructure | avoids crystallizing assumptions before evidence | later decisions remain open and require review |

candidate architectural tradeoffs are recorded separately in [systems/data](systems-and-data.md): two languages, batch publication, exact captures, and effect version choice. none has silently become an implementation commitment.

## questions for the architecture review

1. which recurring hockey question should the first useful surface answer: postgame performance, team tendencies, player contribution, or goaltending?
2. is its claim about realized results, repeatable ability, or future outcomes?
3. which seasons, game types, and strength states must it support initially? what source coverage can actually support them?
4. does the site serve already-computed analyses, or must it recompute arbitrary selections interactively? how fresh must results be?
5. must published results be reproducible entirely from open inputs, or may personal research use paid tracking/model data?

do not ask for preferences that can be resolved by engineering judgment. these questions change the purpose or evidence of the system and therefore warrant explicit choices. the [project brief](../brief.md) tracks them without pretending unanswered questions are approved decisions.
