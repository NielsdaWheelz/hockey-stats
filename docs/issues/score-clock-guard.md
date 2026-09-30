# contradictory non-goal clock removes whole-game score support

status: open; reconstruction/preparation contract follow-up from 03b.

problem: the fresh `2024020102` capture has an overtime `TAKEAWAY` at api source index 360 whose elapsed and remaining clocks both report `00:00`. the reviewed clock interpretation correctly leaves elapsed time unknown. preparation conservatively requires supported clocks for every timed event before establishing pre-event score, so this non-goal row removes score support for all attempts in the game.

impact: 140 recognized attempts remain explicit: 88 unavailable and 52 outside 5v5, with no eligible attempts. ordinary timed goals reconcile to 3–3; the final 3–4 includes the shootout. neither that reconciliation nor the event's non-goal description authorizes bypassing the current completeness guard during 03b.

evidence: native guards, raw receipts, report/API rows and counts are retained in `/Volumes/Expansion/hockey-stats/chance/03b-20260930/inputs/development-assessment-whole-game-source-checks.json`, sha256 `f070cd4f4fd35191d966da9c7c316773faeec9d3382b5b7364fbb37420e22ad4`. the complete 2024–25 source review found this clock case and two distinct failed-penalty-shot taxonomy cases.

resolution: review score reconstruction's required evidence at its responsible boundary. establish when a strictly identified non-goal row with unsupported time can leave independent timed-goal accounting valid, while retaining contradictory/unknown potentially scoring rows and correct ordering. verify on this attributed capture and contradictory cases, regenerate changed populations, and repeat the scientific assessment with separately justified confirmation. do not invent a clock, alter the raw payload or waive completeness in a research script.
