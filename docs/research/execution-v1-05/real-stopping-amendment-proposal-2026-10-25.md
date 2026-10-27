# pending real v1-05 stopping amendment

status: unapproved proposal. explicit user approval is required before any production change or fresh campaign. the diagnostic preview is complete; all 99 protected paths and source-clean checks pass. no policy is adopted.

all twenty real baseline heads complete, but final `u/q` fail the unchanged `1e-5` probability-stability bound. propose tightening only native `ftol`, uniformly across `u/q/r` and every `g` em inner solve, using the existing `L-BFGS-B` primitive and raw coordinates.

| contract | current baseline / continuation | proposed baseline / continuation |
|---|---|---|
| native `ftol` | `1e-14 / 1e-15` | `1e-15 / 1e-16` |
| native `gtol` | `1e-6 / 1e-7` | unchanged |
| em objective / responsibility tolerances | `1e-8, 1e-6 / 1e-9, 1e-7` | unchanged |
| em update cap | `100 / 100` | unchanged |
| native `maxiter`; default `maxfun`, `maxls` | `10000`; `15000`, `20` | unchanged |
| allowed em objective increase | `1e-10*(1+abs(previous_objective))` | unchanged |
| process memory; maximum probability change | `64 GiB`; `<=1e-5` | unchanged |

objective, populations, entry-or-carry priors, zero/prior-mean starts and minimum-completed-objective selection remain unchanged. synchronize `DEFINITION["solver"]["ftol"]`, `_solve_start`, `continue_head` comparison metadata and the strict reader's expected continuation tolerance. no restarts, scaling, new solver or framework.

evidence: [diagnostic preview](real-stopping-preview.json), sha256 `2a4acc3fd248c112755143b66566f5fcbcbfb4e70bec53f694bbdcaff67f2a53`. the diagnostic exactly replays the original failures, then continues saved `1e-15` coefficients at `1e-16` on the same objective, old 2024 priors and full frozen selector:

| head | original failed change | incremental preview change | iterations / evaluations |
|---|---:|---:|---:|
| `u` | `1.2808432675537329e-5` | `3.889186265260136e-7` | `12 / 43` |
| `q` | `1.4692029087437497e-5` | `2.2608070832097482e-6` | `179 / 201` |

both preview solves terminate on `ftol`, not raw `gtol`: gradients remain `0.0019150` / `0.0051998`, above `1e-7`. near objective `70000`, one float64 ulp is `1.45519e-11`; `1e-16*70000` is below that. this supports bounded empirical probability stability, not a convergence certificate or global guarantee. independent review checks arrays, source controls and all 97/107 prior-only formulas. [operator preservation](real-stopping-preview-preservation.json) confirms all 99 protected paths unchanged. measured preview wall is `6909.79s`, peak resident memory `17231806464` bytes, zero swaps; preparation consumes `6746.0912s`.

qualification after approval: assign a new literal recipe hash with a strict cutover; first complete a fresh five-year fixture chain, stopping on any failure. only after qualification, run a fresh real chain from `20212022`, sequentially, with independent annual/resource/preservation checks and four passed final probes on the full selector. earlier changed coefficients feed later point priors: the old-prior preview cannot qualify the replacement chain. no old-recipe predecessors, probe promotion or recipe mixing. new-chain `zero`/`prior_mean` starts use new-chain prior history. retain existing expensive fits as historical evidence.

cost: five new annual fits, plausibly 12–15 hours, an estimate only. observed later-year commands took roughly 2h23–2h45; cached first-year cost is unknown and stricter solves may take longer or fail. full handoff remains incomplete; scientific admission is not asserted and cleanup awaits final verification.
