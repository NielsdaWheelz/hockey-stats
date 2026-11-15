# v1-10 implementation and acceptance

status: in progress. the user assigned the complete specification on 2026-11-14. branch `implement/v1-10-penalties-shootiness`; isolated worktree `/Users/nnandal/.codex-work2/worktrees/296c/hockey-stats`. the primary checkout and its ten supplied draft documents remain preserved. source/design, numerical/state and publication/application owners work in parallel; root owns cli integration, independent reviews and serial real execution.

verification follows temporary integration/live red → green → refactor → green, with campaign tests deleted after acceptance. fixtures and checked scientific/source evidence remain. software, real integration, numerical diagnostics and scientific support are separate verdicts. no activation is assigned.

accepted modeling tradeoffs remain those in the specification: conservative ordinary-minor scope, richer penalty context, pooled shooter skill across seven states, fixed position weights/units and priors, age-neutral raw point-history borrowing, approximate isolated-minor valuation, and unknown optimizer accuracy. final diagnostics do not retroactively establish earlier numerical accuracy.

current environment reuses existing pinned python and application dependencies through worktree-local symlinks. python commands set this worktree’s `analysis/src` on `PYTHONPATH`; no primary source/build/database is modified.
