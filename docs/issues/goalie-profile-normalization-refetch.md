# repeated goalie profile requests after discovery

the first real discovery → profile browser journey recorded 26 api responses for 13 distinct selected requests. this violates the bounded loading contract and doubles the selected profile work. the journey reported no page or api error; numerical publication reconciliation passed separately.

reproduce on source `4b17ac7`, publication `21630954-ad5f-4763-9abc-4e9ba859e615`: open goalie discovery for20252026, search karel vejmelka and follow his profile link. inspect the api request inventory through the completed profile navigation. the failed receipt and cost are preserved under `/Volumes/Expansion/hockey-stats/runs/application-v1-19-20261114-01/real/exports/attempt-01/`.

the suspected cause is profile url normalization removing the redundant kind selector and revalidating the same loaded selection. independent request-identity and navigation review must establish the cause before repair.

resolved when the responsible url/navigation owner avoids the redundant fetch, actual discovery → profile requests are unique, and final real navigation/download acceptance passes against the same candidate. no cache, second publication or database rewrite is needed.
