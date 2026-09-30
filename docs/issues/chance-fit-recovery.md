# chance fit recovery

status: open; measured prerequisite for further 03b fitting.

problem: a fit retains no numerical progress until both starts finish. the first full 2023–24 fit took 26.7 minutes; its two starts required 480/419 em iterations. replacing interrupted larger-window work can cost substantially more than the bounded capacity trial.

impact: a process interruption discards expensive accepted numerical work. raising the iteration ceiling from 500 to 2,000 makes an explicit recovery boundary prudent before further fits.

evidence: `/Volumes/Expansion/hockey-stats/chance/03b-20260930/inputs/development-anchor-costs.json` records the uncontended run. its completed model sha256 is `d3b5c8f7e549fe01f2df8221646aaa938db43495ccb4511d7b42eb742a1d0802`.

resolution: save accepted em state and completed starts in one replaceable checkpoint. resume only through an explicit input into a new output directory, binding exact prepared inputs, selection, configuration and executing implementation. preserve iteration budget, diagnostics and winner selection; restart an interrupted inner optimizer. temporary installed-command checks must establish equivalence with uninterrupted fitting, visible identity/state failures, preserved failed starts and exclusive outputs. no automatic retries or job framework.
