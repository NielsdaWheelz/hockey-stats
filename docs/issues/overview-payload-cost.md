# seasonal overview payload cost

problem: the v1-12 real candidate's seasonal overview responses contain inherited families and are 44,480,005, 44,609,885 and 45,286,689 bytes across the three displayed seasons. each request took about five seconds on the acceptance host. this is measured transport/read cost, not a new end-to-end browser latency measurement or an established memory leak.

impact: discovery may load substantially more evidence than its initial table needs. the latest complete candidate has not yet replaced the live schema8 site. measure its actual discovery/profile/comparison journeys before choosing a remedy; do not infer that every large field is unnecessary.

evidence: [v1-12 real acceptance](../research/value-v1-12/verification.md#real-candidate-and-live-acceptance) and its [selector receipt](../research/value-v1-12/receipts/real-candidate.json). reproduce against an isolated compatible schema12 candidate, open a selected-season discovery page and inspect its overview request, then follow profile and comparison navigation. preserve publication/season/selector identity and distinguish response time, parse/render time and subsequent reads.

owner: existing application overview/read and discovery owners, within the bounded v1-20 specification. compare fields consumed by each view with the payload actually fetched. prefer a narrower existing query/projection and lazy detail where supported by that evidence. this records a concrete cost; it assigns no new cache, service, database redesign, performance campaign or rebuild.

the [v1-20 contract](../specs/v1-20-whole-card-closure.md#scalar-overview-and-explicit-evidence-loading) now fixes those summary schemas and explicit peer-detail reads after code inspection found full-family hydration in the overview path. it preserves complete csv evidence; omitted transport bodies cannot become unavailable source evidence. the defect remains open until implementation and measured acceptance.

resolution: retain before/after bytes, request counts and end-to-end timings for the selected journeys, with an explicit practical disposition in the v1-20 contract. verify preserved table/cohort/profile/comparison/history meanings and exact quantities at the changed boundary. a documented decision to retain the measured cost is also a disposition; do not invent a retrospective threshold or call metadata changes free when they require a new candidate build.
