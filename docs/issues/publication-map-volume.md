# real publication map volume

problem: schema7 deliberately stores complete native/display map payloads. detached v1-13 verifies a compact fixture, not full three-season storage/startup/response cost. the independent reviewer estimates gigabytes of map json at full player/selector coverage; that estimate is not a measured failure.

impact: real serializers may produce an unnecessarily costly publication or startup validation pass. the reader streams rows, but must decode and validate every supplied map. selected responses also retain their full declared payload; no speculative cache, pagination or service has been added.

evidence: [v1-13 verification](../research/publication-v1-13/verification.md) records fixture bytes, build/check/startup memory and response sizes. the 20.3 mb candidate exercises complete selector rows with mostly explicit pending payloads, so its cost must not be extrapolated as full-size acceptance.

resolution: with the first real map producer integration, measure a representative complete season's map bytes, build/check/startup time, peak memory and selected/overview responses. repair measured excess at the serializer/query owner while preserving exact fixed contracts and bounded row processing. no fit or acquisition is required merely to size serialized existing output. this is not an additional scientific gate or a new benchmark framework.
