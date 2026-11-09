# spatial finalization bindings and saved-check command review

the saved canonical manifest is `a40ca1c0291579b773db22294f26998f154309b2b65926f00f901331ef0b17d5`; the original incomplete donor remains `f5c467767a45d0b9152a0308e1fc7e407da0d5b465ffdd743baae10918c44521`. their small headers agree except for the new producer and methods catalog; the other catalog descriptors are unchanged. the new methods descriptor is `e41ae390b3b3fc5f314d7336b78728495a148e72de01d2594742588f52848a9a`. completion resources bind that manifest, donor, selection and schema2 admission, recording one 893.23-second strict read; the completion exit is `0`. the original composition exit `1` and its failed graph remain preserved. launch producer is `b053c95`, clean analysis tree `52bcae1c68161d4424cec672837e783eaeead673`.

checker source `var/v1-08-replacement/verify_real_spatial_compose.py` is `4c303d382b25e43563b19ded3a34238648a0b924d94247e1fe00a7b0f57a95a9`. restoring only `COMBINED_SHA=None` reproduces reviewed source `f57a36436ac7197b2a8755371b41c78ad29077f499971cbcbbb947b075507077`. the separately released saved-only invocation is:

```sh
analysis/.venv/bin/python var/v1-08-replacement/verify_real_spatial_compose.py
```

root guards fresh `real/compose-spatial-saved-check-01.json` and its log/exit records under `/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01`, and captures the true exit. this is one saved pass, not a model or source recomputation. its source scope and the earlier held checks are described in [the finalization command review](real-spatial-additive-finalization-command-review.md).

publish command `3f4e199326736bbd4b5326a87b4f33d8d7560381039c707d922235d273bfd6de` restores to reviewed held `cb58aac1a1e053fd610af58b413e01f766275d66ab19b56d34a9b470560a4ab9` when only its combined-manifest pin is withheld. syntax passes. it remains held until saved-result review and separate root release; pinning a manifest is not acceptance.

this review inspected small saved headers and completion metadata, plus the source-pin deltas. it did not run the checker, publication, production reader or numerical work. full saved-result, candidate, runtime, browser and export acceptance remain pending.
