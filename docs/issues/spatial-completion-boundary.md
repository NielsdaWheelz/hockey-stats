# completed spatial heads need a projection boundary

problem: `fit_spatial` preserves three completed head json/npz pairs, then owns projection and canonical writing in the same entrypoint. the user interrupted real `20222023` during `_actual_adjustments`; all three fits survive, but the unsaved design and annual manifest do not. the fitter refuses the occupied directory, and no public completion path exists.

impact: finishing year two requires reconstructing its inputs and projecting its retained fits. repeating the optimizer would waste completed expensive work. the partial annual remains ineligible as predecessor.

evidence: interruption receipt `0bc1f5cb`, reconnection preflight `e9515116`, original analysis `2866624d`. all six component files and twelve run records rehash exactly; head statuses are complete. accepted predecessor `3b7b5133`, score `296ae017`, preparation and coaches remain pinned.

resolution: share the ordinary annual constructor/project/write/read path with explicit completion; use a strict head reader bound to the accepted predecessor, exact original component bytes and one same-arithmetic objective/gradient consistency check per head. rebuild once, use fresh sibling `20222023-complete-01`, make zero new solves/probes, and distinguish retained fitting provenance/cost from new work. missing original design bytes remain an explicit limitation. no cache search, checkpoint engine, fallback or numerical change.

proof: temporary tiny end-to-end controls and independent source/command review, then one real reconstruction with all three exact anchors, canonical readback, saved-run provenance and independent raw-history/projection acceptance. any mismatch stops before projection and leaves the donors untouched. no successor is released until the completed annual passes.
