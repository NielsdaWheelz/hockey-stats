# same-clock event matching

status: open; identified during fresh 2023–24 development-source review for 03b.

problem: reconstruction rejects every nonunique period/clock/kind group before examining participant or shot-type evidence. this implements its current conservative matching contract, but some rejected groups contain enough attributed source information to resolve the events. high overall capture coverage does not make this selective exclusion random.

evidence: `/Volumes/Expansion/hockey-stats/chance/03b-20260930/inputs/development-training-coverage.json` records 606 unavailable attempts among 1,154 eligible-or-unavailable attempts in two-attempt same-clock groups (52.51%), versus 422 among 124,477 singleton attempts (0.339%). 604 paired exclusions carry `ambiguous_event_match`. these denominators include unresolved membership; they are not certified true-5v5 populations.

the first two rejected groups in game `2023020001` are inspectable without fitted maps:

- period 3, `00:36`: api source indices `212` and `213` identify shooters `8475158` and `8476887`. the unchanged api roster maps them to nashville jerseys `90` and `9`; raw report rows `PL-216` and `PL-217` name those different shooters.
- period 3, `00:37`: api indices `214` and `215` identify the same shooter, but their recorded shot types are `wrist` and `poke`. raw report rows `PL-218` and `PL-219` distinguish the same types.

all four report rows contain identical five-skater/one-goalie lists for each side and ordinary-shot descriptions. their exclusions therefore reflect a coarse linking contract, not absent membership evidence. these examples do not establish that every same-clock group is recoverable.

impact: attempts close in time are disproportionately excluded. source geometry and event type suggest rebound/sequence selection can matter, but no causal or measured performance effect has been established. player event/exposure compatibility and all-attempt scientific scope need an explicit judgment; calibration on retained attempts cannot certify the excluded population.

resolution: at the reconstruction/report boundary, admit exact source participant/type constraints and accept only a uniquely supported one-to-one match. retain missing values, contradictory evidence and genuinely nonunique groups. do not infer identity from an arbitrary row position. a consensus-membership alternative must separately identify its candidate-row evidence and keep exact event identity unresolved. review the changed admission contract, verify representative recoverable and irreducible groups with temporary live checks, regenerate affected cheap corpora, and reassess development selection before freezing a newly justified confirmation. the current 2025–26 confirmation cohort is consumed by 03b; retuning and rerunning it does not provide fresh confirmation. existing fits must retain their original evidence identities.

2024–25 full-season source review also found 522 unavailable among 914 two-attempt eligible-or-unavailable rows (57.11%), versus 279 among 124,722 single-attempt rows (0.224%). the exact native source/preparation record is `inputs/development-assessment-coverage.json` under `/Volumes/Expansion/hockey-stats/chance/03b-20260930/`. these source-only ratios are descriptive selection evidence, not measured causal or predictive bias. [the scientific decision](../research/chance-03b/decision.md) preserves the limits of claims on retained attempts.
