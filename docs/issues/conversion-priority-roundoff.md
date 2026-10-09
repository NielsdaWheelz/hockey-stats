# conversion priority can classify identity roundoff as harm

status: open. owner: numerical comparison and statistical decision design. observed in completed 03j, commit `3373f19`; the real study remains `inconclusive`. this is distinct from the supported-refit solver convergence limitation.

evidence: [03j verification](/Users/nnandal/Documents/code/hockey-stats-03j/docs/research/chance-03j/verification.md), section numerical limitation and tradeoffs, records an identity fixture with nominal paired log-loss difference about `3.85e-18` nats and positive interval lower endpoints. the literal frozen zero-threshold rule therefore returns `conflicting_or_adverse`; verification identifies this as fixture roundoff, not empirical harm. retained verification evidence is under `/Users/nnandal/Documents/code/hockey-stats-03j-runs/verification/`.

impact: future reuse can turn numerical representation differences into a directional research recommendation. all real 03j refits converged and its three intervals cross zero by much larger amounts; this issue supplies no reason to reinterpret that result, refit automatically or relax historical admission criteria.

resolution: independently establish paired identity/near-identity arithmetic and a justified numerical-resolution contract, then specify any changed comparison/decision rule prospectively before another study. meaningful effect thresholds and numerical error bounds are different concepts; no post-result epsilon, silent clipping or repaired historical verdict. identity and nearby controlled examples must not report empirical harm/benefit solely from rounding, while independently resolved differences retain their direction. preserve the reproducer and old protocol/results.
