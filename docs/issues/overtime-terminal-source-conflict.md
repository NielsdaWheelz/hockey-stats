# overtime terminal conflicts with established horizon

status: open; source-evidence limitation. reconstruction correctly retains the unavailable overtime horizon.

problem: [2021021103](../../fixtures/captures/2021021103/), philadelphia/new york at `Madison Square Garden`, 2022-04-03, reaches a shootout. both core outcomes report `SO`, establishing a nominal 300-second overtime horizon under the settled contract. api `/plays/295`, event `634`, sort `869`, and original report `/rows/298[PL-299]` instead terminate period 4 at `04:59 / 00:01`. both supplied clock pairs sum correctly. ten original period-4 shift rows end at `05:00`, including goalie rows `/data/106,/406`.

impact: native period 4 has null `end_seconds`, status `unavailable` and issue indices `0,1`: `conflicting_terminal` at both original terminal locators. coverage expects periods `1,2,3,4` and supports only `1,2,3`. known 3,600 regulation seconds and zero unresolved seconds therefore do not establish full-game elapsed exposure. reported event membership and recorded locations remain separate: fifteen timed overtime attempts are outside 5v5, and six shootout attempts remain untimed. timed score `3–3`, final `4–3` and 74 eligible unblocked regulation attempts survive.

evidence: the original complete six-source bundle and unchanged `20212022` references are preserved in fixtures. [the copy manifest](../../fixtures/source-admission-03m.json) binds source/fixture hashes; external `runs/03m-20261010/receipts/older-boundaries.json` records native reconstruction/core equivalence and the exact conflicting rows. the existing `2024020364` report-clock fixture has clocks summing to 1,199 rather than 1,200 seconds and is not this terminal-versus-horizon boundary.

resolution: obtain independently attributed evidence resolving the terminal/horizon discrepancy and review any strict horizon-contract change, or retain explicit unavailability in consumers requiring complete elapsed exposure. do not invent the missing second, snap the terminal to the nominal endpoint, discard supplied terminal evidence or replace the original capture.
