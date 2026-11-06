# real export adaptation: source-only strategy

no candidate, artifact, api, download or browser read was performed. adapt the existing temporary `var/v1-08-product/replacement/actual-csv-download-check.py` after root supplies the accepted publication/database identity and actual download paths. do not replace the existing formatter checks with a new export harness or infer real counts from the fixture.

## first bounded candidate read

open the exact accepted sqlite path with `mode=ro&immutable=1`; retain its accepted digest rather than rehashing the whole file, and compare size/mtime before and after. check the single publication identity/schema/purpose row and the three season corpus identities. read only the three displayed seasons' `person`, `skater_spatial` 5v5 scalar payloads, referenced `analysis_method` payloads and the bounded `player_season` observed metadata needed for the visible-table minutes/filter expectation. no maps, full strict-reader repeat, source-game scan or numerical pass is needed for export expectations.

this existing scalar join supplies names, positions, teams, all sixteen estimates and aggregate support:

```sql
select s.season, s.player_id, s.method_id, s.availability, s.payload_json,
       p.display_name, p.reported_position, p.teams_json
from skater_spatial s join person p using(season, player_id)
where s.season in ('20232024', '20242025', '20252026')
  and s.strength='5v5' and p.kind='skater'
order by s.season, s.player_id;
```

bind regular discovery ids present in all three years; one regular primary serves the api script's three-year assertion. select a same-position second and mixed-position second, with low-minute/traded/absent-year journeys assigned where actual records permit. entrant status still needs the separately accepted bound head-support records, because publication absence alone cannot prove entry. record whether unavailable, zero-time prior-only and absent-year cases actually exist rather than forcing a fixture narrative onto real data.

## actual downloaded histories and distribution

retain the existing exact quartet, original estimate/null reason/uncertainty, support, person, corpus, reference, limitations and evidence checks. remove only fixture-specific ids, counts, values, defense-only assumptions and forced prior-only/absent outcomes. each selected history contains the three declared years in order; an absent year has no selected person/value/support/quartet/uncertainty and retains the existing explicit absence reasons. a present nullable estimate remains `unavailable`, distinct from an absent person. numeric csv cells retain their exact signed native values; compare an empty csv field with null, never `float('')` or zero.

for a convenient actual download, use the same selected scalar in a regular player's history and a same-position comparison distribution. `spatial.5v5.defense_xg_per60` reuses the existing checker's field and quartet mapping directly; its label means more against when positive. peer cutoff `0` exercises positive-exposure low-minute members, while the default `300` behavior remains covered by real discovery/api/native checks. choose an additional real absent/prior-only history only if such a case exists; otherwise keep its labeled fixture evidence.

compute cohort membership independently from candidate estimates: finite selected value, recognized requested position group (or all skaters), positive spatial support seconds, requested cutoff and matching semantic identity. construct that identity from the published quantity/recipe/reference/support-policy contract, not the method id or warning wording. mixed-position defaults yield separate forward/defense groups. the distribution file is each group's members in name/id order plus selected outsiders, with each selected outsider appended once. its row count is not automatically cohort size. independently compute midpoint percentiles as `100 * (less + equal / 2) / n`; zero/unknown exposure and values outside cutoff retain the magnitude but withhold the percentile and supply their exact reason.

source owners: `analysis-cohorts.ts:qualificationReason/buildAnalysisCohort/standing`, `peer-distributions.tsx:distributionRows`, `analysis-history.tsx:analysisCsvRow`, and `export.ts:csvText`. text formula prefixes can carry a leading apostrophe; numeric negative values do not. json fields remain exact after csv decoding.

## actual visible-table csv

`discoveryCsvRows` emits one record per visible player per column: **nine records/player**, minutes first plus all eight spatial metrics. check `table=spatial`, `strength=5v5`, contiguous row/column order and exact column ids against the actual selected filters/sort. check the eight metric rows with the same candidate-bound estimate/support/method expectations. the minutes metadata row uses `player_season.included_seconds` as native seconds and `included_seconds / 60` as display minutes, with the existing observed metrics support; it is not a spatial estimate; preserve its metadata evidence rather than requiring spatial quartet/method fields there. observed minutes own display filters, while spatial seconds own metric qualification. filtering does not shrink peer cohorts.

root should preserve the settled filter/sort/url and actual downloaded filename alongside the fresh bytes. the table filename is `spatial-5v5-<season>-<publication_id>.csv`; history/distribution filenames already encode selected ids, metric and year(s). actual filename collisions may acquire a browser suffix, so supplied downloaded paths—not guessed names—own the file read.

## warning, pixels and scope

compare each spatial csv row's complete `method_limitations`/`method_evidence` to its candidate method. the accepted admission warning and its evidence must occur only in `spatial-v1-08-20252026`; earlier spatial methods retain their own limitations. validate the exact warning from the accepted candidate/admission rather than matching only a few words. history csv must preserve all annual method records and the final-year warning.

root must inspect a fresh history png containing all three years and the final warning, including its ending, on the actual final build. png status/season/strength/direction/reference/support/absent uncertainty remain required. the renderer measures/wraps all limitation text and grows the image; source inspection is not proof that the downloaded bitmap fits the real text. full receipt lists and the quartet table are detail/csv obligations, not extra png requirements.

record downloaded file bytes/hash/mtime, accepted candidate identity, actual source/dist binding and observed export/render cost with narrow scopes. the existing native fixture evidence supplies the pattern, never the real verdict. no build, model pass, broad test, scientific admission or activation follows this preparation.
