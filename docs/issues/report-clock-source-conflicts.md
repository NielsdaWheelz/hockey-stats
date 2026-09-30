# inconsistent report clocks

status: open; source-evidence limitation. the interpreter correctly retains null elapsed time.

problem: three period-2 `SPC` report rows supply clocks summing to 1199 seconds rather than 1200: `2024020364`, `PL-197`, `19:04 / 0:55`; `2024020491`, `PL-252`, `19:01 / 0:58`; `2024021002`, `PL-192`, `19:17 / 0:42`.

impact: those rows cannot establish an elapsed clock or support a clock-based join. source descriptions, both supplied clocks and located `inconsistent_event_clock` issues remain visible. independent api goal accounting and elapsed exposure remain supported; no invented second or timing correction is needed for 03c.

evidence: the complete representative bundle is preserved in [fixtures](../../fixtures/captures/2024020364/). [the source review](../research/chance-03c/decision.md) records all three locators; native interpretation leaves `/rows/196[PL-197]/elapsed_seconds` null. verified historical body hashes establish source equivalence, without requiring earlier receipts.

resolution: obtain independently attributed clock evidence or retain explicit unavailability in any consumer that needs these report rows. preserve the original clocks; do not infer whether elapsed or remaining time is wrong. this limitation does not block the correctly bounded 03c contract.
