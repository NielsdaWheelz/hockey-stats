# project brief

status: research and requirements, 2026-09-29. this records the user's intent and working recommendations, not an approved system design.

## purpose

build a useful hockey statistics website inspired by the explanatory power of hockeyviz and the comparative, decomposable analysis of evolving hockey. understanding will develop through building it; teaching features and a curriculum are not product requirements.

the ambition is trustworthy analysis and excellent presentation. copying the breadth of established sites, matching private models, or exceeding every published method is not an established requirement. those would need separate evidence and scope decisions.

## established constraints

- one primary user/operator, with immediate rollback and live repair available.
- effect on backend and frontend is the user's technology preference. python for numerical and statistical work is a candidate, not a settled boundary.
- preserve the predecessor and recover useful research, source knowledge, data, and pipeline ideas. avoid importing its implementation by default.
- the large downloaded dataset is on a currently detached external drive. its contents, rawness, format, coverage, and integrity have not been inspected in this session.
- ordinary development and tests must work without that drive or live upstream requests. training and corpus-scale validation are separate activities.
- proceed one phase at a time: knowledge base → architecture and systems → reviewable slices/pr specifications → implementation.
- no code changes in this phase. repository administration and documentation are authorized.
- use specialist review to expose disagreements and evidence limits; the reviews are not statements from the researchers whose work we study.

## requirements proposed by the council

1. a number has a defined subject, population, time window, strength state, unit, denominator, and method. filters change those deliberately.
2. observed results, context-adjusted estimates, and forecasts remain distinct, even when shown together.
3. every published result can be traced to source captures, a derivation, and a model version where applicable.
4. tables, charts, and exports use the same selection and agree arithmetically.
5. missing observations, unsupported capabilities, zero values, and uncertain estimates are different states.
6. source corrections can be incorporated without silently leaving stale results or destroying the ability to reproduce an earlier result.
7. statistical and visual detail should serve a concrete hockey question. complexity earns its place through evidence or a clear reduction in confusion.

these are candidates for the architecture specification, not a demand for a generalized lineage platform, universal query grammar, or model registry in the first slice.

## decisions still open

| decision | why it matters | current position |
|---|---|---|
| first recurring user question | determines the smallest useful product and required evidence | game/team performance, player evaluation, and forecasting remain alternatives; no answer assumed |
| initial league, seasons, and game types | determines source coverage and edge cases | nhl is the working scope inferred from the named exemplars; exact window undecided |
| retrospective value versus repeatable ability | determines estimand and use of historical information | preserve both meanings; select one for each model |
| public site and open source timing | affects publication and data redistribution | new repository is private; predecessor remains public and archived |
| open inputs only versus paid research inputs | determines reproducibility and features possible | no paid source or redistribution commitment |
| refresh cadence | determines operational and invalidation burden | batch/postgame is a candidate; live service is not required yet |
| effect version, ui framework, storage, python boundary | determines development and runtime contracts | investigate at architecture stage; no dependencies installed |
| external-drive data admission | determines what can be reused for training and fixtures | inspect before reuse; do not equate a table called raw with an original response |

## phase exit conditions

this reconnaissance provides a preserved archive, selected historical sources, a current product/method survey, evidence-backed salvage findings, and a concise list of open decisions. review those before expanding the knowledge base further.

the next phase should specify one product objective, the important invariants, ownership of source/derived/model/served data, and the operating model. it should compare plausible storage and language boundaries before choosing them.

only then specify the first implementation slice in detail: user-visible outcome, inputs/outputs, acceptance evidence, failure behavior, and rollback. outline later dependencies without pretending research outcomes can be planned exhaustively. a full future backlog now would mostly preserve guesses.
