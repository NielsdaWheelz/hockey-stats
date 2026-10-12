# implausible elapsed lineup counts

problem: captured shifts can put seven players from one team on the ice without duplicate-player or interval-identity defects. this prevents supported elapsed membership; it does not by itself invalidate separately reported event membership or timed score.

evidence: original complete [2022020009 bundle](../../fixtures/captures/2022020009/) and [20222023 references](../../fixtures/references/20222023/), captured during 03m. period 2 `[18:24,19:14)` has six distinct seattle skaters at shifts `/data/51,/296,/400,/446,/468,/709` plus goalie `/data/195`. anaheim has five skaters `/data/92,/135,/597,/688,/754` plus goalie `/data/226`. independently inspected original rows support thirteen active records. reconstruction retains 50 unresolved seconds with null interval membership; it must not choose a skater to remove.

impact: player exposure is incomplete for this interval. current event-level conversion preparation remains separately accountable: this game has 69 eligible unblocked attempts and supported timed-score accounting. no model or physical membership is admitted by that result.

reproduction: run the native reconstruction command on the fixture; inspect `implausible_elapsed_lineup`, period 2 intervals and original `shifts/body.bin` rows at the locators above.

resolved when: separately attributable evidence establishes a coherent elapsed lineup over the affected interval, and native reconstruction reconciles it without inventing membership. keep this original reproducer; a corrected download is a new capture. no source-backed local correction is currently available.
