# pr05 — publication

status: **stub; not ready for implementation.** expand when 04 defines the analytical outputs. labeled fixture outputs can support development before scientific acceptance; they cannot support a real analytical release. [plan](../plan.md) · [architecture](../architecture.md)

## purpose and contract

turn declared analytical outputs into one self-contained sqlite publication and coherent read responses for 06. inputs include supported player-season effects, spatial outputs, observed game/season summaries, reconstructed exposure, coverage and uncertainty definitions. outputs are a checked candidate database, read queries and an explicit local publication/restore procedure. browsing must work without python or the external drive.

python owns export, analytical eligibility, reference conditions, units and reconciliation. effect owns application reads and file publication. proposed module homes are `analysis/src/hockey_stats/` for export, and server/read, operator and shared boundary modules within `app/src/`; exact files follow the full specification. do not duplicate hockey calculations in sql or typescript.

## settled behavior and exclusions

serve the active database read-only for the server's lifetime. return related data together for each view. after checking a candidate, explicitly stop the server, copy the completed file into place, restart and reload. preserve one previous valid database; an incomplete copy must leave intact files available for manual repair. restore compatible code through git and lockfiles when necessary. retain no old website builds.

no automatic activation, historical-publication browser, hot switching, job runner or generalized storage layer. publication retention does not authorize deleting source history or expensive fits. accepted costs are manual operation and brief browsing interruption.

## full specification and completion

define the schema, reader compatibility, complete view responses and concrete candidate checks. carry identities, evidence cutoffs, supported populations, missing-value reasons and analytical status. publication preserves the eligibility and reference definitions supplied by 03–04. percentile cohorts belong to later comparison features, not an invented publication default.

content design owns operator wording; analytical owners supply its scientific meaning. distinguish “database checks passed,” “fixture publication” and “scientifically supported results.” completion requires detached reads, reconciliation, incompatible-reader rejection and demonstrated manual activation/restore with bounded fixtures. structural validity alone never establishes scientific support.
