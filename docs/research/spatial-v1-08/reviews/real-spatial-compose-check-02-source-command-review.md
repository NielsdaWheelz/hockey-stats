# spatial saved-check 02 source and command review

the first saved checker exited `1` after 5.86 seconds without a result json. its net-only context closure check rejected a saved cancellation case; the canonical completed result remains intact. the failed `01` log and exit remain preserved. this was a checker failure, not a new model or publication failure.

checker `c863a97abb0d2763f0a3b09e916fb546aad568a1959a524ef8a28106e5653c20` uses a fresh `02` destination and a localized context closure check at the existing `1e-10*(1+abs(factual)+sum(abs(five terms)))` scale. it checks finite terms, residual, factual, total, tolerance and difference; global `close` and exact saved-scalar comparisons remain unchanged. the author reports only this closure and destination changed from `01`. the canonical strict reader already owns the separate residual-magnitude check.

generated control `7ea6402817aa221110307246955b862c593163f97dc3808385705e3e80a61cff` passed independently for cancellation, ordinary closure, out-of-budget and nonfinite cases. its saved red is `9e995150b43e2e9e4463947d459423e38fd2a65c305a141600aca52252a9d5a5` and green is `903c27430b90c308c413b371eb15f829f56244d44ff0b79977f400c8d4a85be0`.

held command `7c08dbd49b24227a170ab986784e1297643d4b53c767aae336a001b8403bc04c` binds the checker, clean analysis tree `52bcae1c68161d4424cec672837e783eaeead673`, completed manifest `a40ca1c0`, preserved donor `f5c46776`, selection `7ac43cfa` and admission `f07d5a6a`. it guards fresh `02` json/log/exit paths and records the true timed exit; shell syntax passes. root owns release and independent review of its result. no actual checker, model, source reconstruction or numerical pass was run in this review.

## held command correction

before release, root identified that zsh's special `path` variable would alter the child process search path. the corrected held command is `3bb13de09a5f3ca21a903b89b2238615d66af877fb239a3d9ab216acba0ec4a2`. replacing its three `check_target` occurrences with the original `path` in memory reproduces held hash `7c08dbd49b24227a170ab986784e1297643d4b53c767aae336a001b8403bc04c`; no other command bytes changed. the checker remains `c863a97a`, and zsh syntax passes. the old command was not run here. root owns release of the corrected command.
