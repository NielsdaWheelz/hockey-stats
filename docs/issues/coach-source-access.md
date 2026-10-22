# coach source access

recorded 2026-10-22. owner: [v1-02 dated coaching source](../specs/v1-02-dated-coaches.md#source-evidence-and-access-boundary).

## problem and evidence

the selected right-rail feed has not been admitted locally. during specification, three read-only requests through urllib for `2021020001`, `2023020093` and `2025020001` returned http 403; the web reader also could not open right-rail. no response was saved as an admitted capture. the cause is unknown; this is not proof that every client/game is denied or that historical data do not exist.

the [prior inspection](../research/source-audit.md#additional-source-evidence-without-the-drive) recorded structured coach names for `2025020001`. its [official roster report](https://www.nhl.com/scores/htmlreports/20252026/RO020001.HTM) is accessible and corroborates those names; that does not establish right-rail access or authorize an html fallback.

## impact and resolution

fixture/software work can proceed; five-season real admission cannot be promised from prior inspection. once execution is assigned, use the existing capture client for the specified five-season probe, retaining original receipts/bodies. expand only verified usable source access; don't issue thousands of repeated denied requests. ordinary retries use a new directory, never overwrite evidence or bypass restrictions.

resolved when demonstrated usable source access and the required acquisition/binding have a checked coverage receipt, or an explicitly revised source contract replaces this feed. if blocked, keep exact attempt evidence, unrequested scope and the cause's uncertainty visible. unknown rows alone do not resolve this issue. no fitting, serving change or new acquisition has been performed by this specification task.

## assigned detached implementation — 2026-10-22

the user assigned v1-02 implementation, then confirmed detached work until the hdd is connected. the external root `/Volumes/Expansion/hockey-stats` is absent. [software verification](../research/coaches-v1-02/verification.md) proceeds independently; no new live probe has been attempted. real acquisition and identity review remain unstarted, rather than inferred unavailable from the earlier 403s.

the first successful production probe must pin actual report-link paths/types and other supplied identity corroborators before expansion. preserve representative originals under `fixtures/captures/` and reconcile every selected game's capture disposition. five-season, permanent-change and temporary-absence checks remain pending. an empty real identity table or successful synthetic binder run does not resolve this issue.
