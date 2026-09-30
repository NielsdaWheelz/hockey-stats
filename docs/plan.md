# implementation plan

the [brief](brief.md) fixes the product; [architecture](architecture.md) fixes settled system boundaries. this page owns sequencing. detailed decisions live in the linked slice specs and research, not a second specification here. [roadmap](roadmap.md) and [capability inventory](product-inventory.md) retain the later player-analysis destination.

completed: [01 capture](specs/01-capture.md), [02a interpretation](specs/02-interpretation.md), [02b reconstruction](specs/02b-reconstruction.md), [02c corpus](specs/02c-corpus.md), [03a chance workflow](specs/03a-chance-workflow.md) and [03b training/assessment](specs/03b-training-acceptance.md). 03b is merged in `9132131`; its [scientific decision](research/chance-03b/decision.md) rejects the declared all-attempt use. completion does not imply scientific support.

## next slices

the user reports 03c implementation is underway in a separate session; the offline-evidence amendment belongs to that work. all later documents are **stubs**, recording purpose, ownership and outstanding decisions; they are not ready for implementation. the user controls progression. this documentation update does not authorize new fitting or later slices.

| slice | responsibility | dependency / completion boundary |
|---|---|---|
| [03c source revision](specs/03c-source-revision.md) | landing modifiers, report attributes, supported joins, score repairs, expanded raw fixtures/local corpus and source/population audit | implementation underway; full verification needs original captures, on the drive or verified local copies |
| [03d chance revision](specs/03d-chance-revision.md) | selected features and one coherent revised estimator using the existing workflow | specify from 03c evidence; fixture success establishes software behavior |
| [03e training/assessment](specs/03e-training-assessment.md) | real development, fits and a written scientific judgment | admitted corpus, local storage and reviewed protocol; success is not guaranteed |
| [04 player attribution](specs/04-player-attribution.md) | history-informed 5v5 creation/suppression, spatial effects, uncertainty and observed evidence | scientifically supported chance values and compatible exposure |
| [05 publication](specs/05-publication.md) | python sqlite export, effect read contract, explicit activation and one rollback database | agreed analytical/view contract; labeled fixture outputs can precede scientific acceptance |
| [06 website](specs/06-website.md) | league table/search, profiles/maps, comparisons and complete-season/game evidence | 05; real analytical release needs supported 03–04 outputs |
| [07 lightweight testing](specs/07-lightweight-testing.md) | tiny lasting integration/live suite using maintained fixtures | stable end-to-end path, before first-product completion; fixture collection already belongs to 03c and subsequent slices |

05–06 can develop against explicitly labeled fixture publications once their shared contract is specified. serving and development remain independent of the hdd; numerical processing remains local. later components get their own specs when selected from the roadmap, not speculative numbered prs now.

## current discussion versus implementation

here: maintain the bounded [input audit](research/model-input-audit.md), source contracts and ownership while 03c runs. 03c owns concrete source repairs, expanded offline evidence and full-corpus coverage; 03d owns selected model features; 03e owns real training and assessment. no separate research, landing-only, fixture or generic field-parser pr is needed. 03c completion needs the original captures and full selections; a verified local copy can replace drive access. record missing originals and incomplete copying explicitly.

additional inputs belong to the first model/component that requires them. coach admission defaults to 04 but can move into 03d if that candidate needs it. optional tracking and later goalie/penalty/territorial inputs remain with their own components. [source evidence](research/source-audit.md) records candidates and limits.

## shared rules and first-product completion

- reuse existing primitives; hard-cut superseded derived contracts without legacy readers or silent fallbacks. preserve source bytes, expensive fits and 03b's historical verdict.
- initial slices use temporary integration/live red/green/refactor checks, then delete test code and test-only dependencies. retain useful fixtures/facts. 07 defines the later lasting suite; scientific assessment tools remain analytical work.
- each full spec names contracts, module owners, verification, content rules and material tradeoffs. no generic importer, model platform, scheduler or release manager follows from this plan.
- publish explicitly: one completed sqlite database, one previous valid database, manual stop/copy/restart. rebuild website code from git.

the first product explains supported 5v5 player contribution with coherent maps/scalars, uncertainty, observed game evidence and visible gaps. it serves without python or the drive. software verification and scientific support must both justify a real analytical release.
