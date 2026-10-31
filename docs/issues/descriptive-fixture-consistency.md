# descriptive fixture consistency

## problem and impact

the frozen v1-13 descriptive summaries and interval examples are independently valid schema examples, not a coherent full-card oracle. v1-16 must not claim source-to-card accounting from them unchanged. no real-output defect is established, and historical foundation acceptance remains unchanged.

## evidence — 2026-10-22

under `fixtures/publication-v1-13/results/`, select player `9000001` in `20232024-descriptive-skater_descriptive.jsonl` (line 73). both on/off attempt summaries have `for_count=3,against_count=2,seconds=600`; both goal summaries repeat those values.

`20232024-evidence-dressed_game.jsonl` places that player in game `2023020001`, team 18. `20232024-evidence-interval_player.jsonl` places them in `fixture:0,1,2`, not `fixture:3`. independent sums of `20232024-evidence-interval_fact.jsonl` give:

| population | on for/against/seconds | off for/against/seconds |
|---|---|---|
| attempts | 5 / 3 / 60 | 4 / 2 / 40 |
| goals | 1 / 1 / 60 | 1 / 0 / 40 |

reproduce by selecting the player's dressed game-team keys, partitioning those interval facts by actual membership and population, then summing `for_mass`, `against_mass` and `end_seconds-start_seconds`. retain zero-event intervals.

## resolution

[v1-16](../specs/v1-16-descriptive-card-context.md#verification-and-handoff) owns a small attributed coherent derived fixture, or reuse of v1-03's independently checked factual fixture. record exact parent files, changes and checked card expectations; preserve the old examples and their receipts. compare all exercised descriptive populations/support with the new expected facts, then verify api/card/history/png/csv transport. no production algorithm change or historical source campaign is authorized. delete this issue when the replacement evidence is recorded.
