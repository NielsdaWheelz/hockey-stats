# event membership at shift boundaries

status: open; pr2b implementation verification. identified 2026-09-29. the user confirmed adding the official event on-ice report; no reconstruction implementation exists yet.

problem: reported shift clocks support duration arithmetic but do not uniquely determine event membership at a shared substitution second. using the incoming lineup for every event misattributes goals. withholding every boundary event creates selective missingness.

evidence: a read-only audit used both [local fixtures](../../fixtures/README.md) and the official play-by-play reports for [2025020001](https://www.nhl.com/scores/htmlreports/20252026/PL020001.HTM) and [2025020006](https://www.nhl.com/scores/htmlreports/20252026/PL020006.HTM). these reports are not yet admitted fixture captures. their agreement with other nhl exports is corroboration, not an independent observation of the game.

- all 11 timed goals occur at recorded lineup boundaries. their reported on-ice lists match outgoing lineups; incoming lineups omit a named scorer or goalie in eight cases.
- all 128 faceoffs match incoming lineups.
- ten non-goal attempts occur at lineup boundaries: eight reported lineups match incoming membership, two outgoing. a universal shot-boundary rule fails too.
- the two counterexamples are calgary/edmonton `/plays/108`, event `568`, period 2 `01:51`, report row `PL-112` (calgary #52 weegar, not incoming #24 bean); and `/plays/195`, event `776`, period 2 `17:14`, report row `PL-199` (#7 bahl, not incoming #24 bean). named actors and the reported situation code fit both candidate lineups, so those checks cannot resolve these events.
- withholding every attempt whose outgoing and incoming lineups differ retains 221 of 242 timed attempts but removes every timed goal. that population cannot silently become the chance model's training data.

reference identities: research requests around `2026-09-30T00:56:00Z` returned http 200. `PL020001.HTM`: 1,404,394 bytes, sha-256 `2911d9f2cc567284aad4dc161e04f0fa9cb9153ad1088fb8b492d56aa2061837`; `PL020006.HTM`: 1,378,106 bytes, sha-256 `37e8a9c8d8f32428890a9be0ee32abeaa847a5579615e212c61e90084e56a310`. scratch responses are research evidence, not production capture records; fixture admission must preserve its own request metadata.

reproduction: interpret type-517 intervals and compare membership immediately before and after each timed event clock. map report jerseys through `(teamId, sweaterNumber)` in the captured `rosterSpots`; compare exact player sets. distinguish report row numbers from api `eventId` and `sortOrder`. in these examples, period, elapsed time and event kind uniquely match all timed attempts and faceoffs across reports; this does not establish universal join uniqueness.

confirmed direction: capture and interpret the official per-event on-ice report, using it for reported event membership and shifts for elapsed exposure. match events explicitly; retain unmatched, ambiguous and conflicting evidence. do not substitute an inferred shift lineup when event evidence is unavailable. cost: one additional fixed capture source, an html parser and explicit cross-source matching. no general feed-reconciliation framework. the [broader source audit](../research/source-audit.md) assigns other useful evidence to its next consumer.

resolution: implement the [pr2b contract](../specs/02b-reconstruction.md) and demonstrate offline reconstruction against admitted reports, both counterexamples, goals, faceoffs and a synthetic ambiguous match. preserve source bytes, separate reported event membership from reconstructed intervals, and report duration, event and location coverage separately. no claim of population-wide reconstruction accuracy follows from fixtures. delete this issue after implementation verifies the contract and the lasting source facts are recorded with the fixtures.
