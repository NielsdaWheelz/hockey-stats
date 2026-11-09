# goalie prior method bindings

problem: goalie method inputs name only the current source year and immediate predecessor year, while fitted support correctly retains older raw last-supported seasons. the method already lists the full fitting history; its prepared/coaching season axes omit that history.

impact: the strict public contract rejects otherwise completed final-year fixture scores. no candidate or completion manifest was produced. estimates, source evidence, states and the two saved probes remain preserved.

evidence: `/Volumes/Expansion/hockey-stats/runs/goalies-v1-07-20261108-01/fixture-scores-final-01/20252026/`; `/tmp/goalie-final-fixture-score-01.log`. clean producer `76e2d96c` exited 1 after 80.22 seconds: `support prior seasons are not bound to method inputs and fit seasons`. goalie `8475683` carries stopping support from `20212022`, but method input seasons contain only `20242025` and `20252026`.

resolution: bind the global prepared/coaching artifacts to their actual selected history through the current year, preserving exact current-year state/panel and immediate predecessor axes. retain the validator. a fresh final-year score and its detached public contracts must pass before this issue is resolved; no new fit or optimizer probe is required.
