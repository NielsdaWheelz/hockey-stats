# spatial composition still pins the original execution inputs

problem: `spatial_composition.py` still binds the original v1-06 exchange (`cab50e44`) and five original score manifests. the approved start repair replaces those inputs. real spatial composition would therefore refuse the newly fitted chain.

impact: this blocks the final real spatial summary, not fitting or scoring. the accepted first state `3b7b5133` consumed replacement score `37263bfc`; the active execution composition also consumes the accepted replacement selection `58837631`. their numerical construction does not use these spatial-composition admission constants.

evidence: `ACCEPTED_RESULTS`, `ACCEPTED_RESULTS_SHA256` and `ACCEPTED_VALUED` in `analysis/src/hockey_stats/spatial_composition.py`. its final target is still original score `580f85fb`, while accepted replacement score `40e23b35` binds assembled state `59e3432d`. fixture composition bypasses the real admission guard, so fixture acceptance does not close this cutover.

resolution: after the active execution composition and saved-output check pass, pin that exact accepted exchange path/hash and the five accepted replacement score hashes. replace only these seven literals. preserve strict descendant/family/catalog, annual-history, recipe/basis and final-probe checks; keep no original-input branch or fallback. the compositor already releases each large design into its small projection snapshot, so no memory abstraction or lifetime change is needed.

verification: focused real-guard integration checks must admit the replacement base/targets and a compatible descendant, refuse original inputs or altered provided families, and preserve the fixture path. source review must prove all functions and numerical fitter files unchanged. update the year-two command/helper's analysis-tree identity and review it before launch. the final real summary must pass on all five accepted states and all three passed final probes. preserve historical inputs and receipts; no refit or rescore is required for this admission-only change.

current blocker: analysis, the active execution-composition command and its saved-output checker stay frozen through their exits. the replacement exchange hash is unavailable until that output is complete and accepted. preparation is held outside `analysis/`; no production placeholder is introduced.
