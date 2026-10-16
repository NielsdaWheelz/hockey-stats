# attribution numerical evidence

`scipy-lower-cholesky.npz` is a synthetic matrix fixture, not a hockey capture or a fitted state. it preserves the exact 64-dimensional prior named in the original 04a [defect review](/Volumes/Expansion/hockey-stats/runs/attribution-04a-20261014/reviews/numerical-defect-review.json), `/decisive_evidence/small_reproducer`: `.004*eye(64)+.0001*ones((64,64))`.

`scipy-lower-cholesky.json` binds the file hash, checked facts and independent closed-form lower factor. the prior's eigenvalues are `.004` (63 directions) and `.0104` (the all-ones direction). a correct factor has a zero upper triangle and reconstructs the prior to maximum absolute error `<=1e-15`. the saved expected factor comes from the compound-symmetry closed form, independently of either factorization routine.

reproduce by loading the arrays with `numpy.load(...,allow_pickle=False)`, then comparing `scipy.linalg.cholesky(prior,lower=True,check_finite=False)` and `numpy.linalg.cholesky(prior)` against `expected_lower` and `prior`. the pinned scipy `1.18.1` build returned 112 nonzero upper entries in the reviewed execution. those values contaminate a dense `L@L.T`; their exact values may vary. this is the public cholesky defect that invalidated 04a's first execution, distinct from `cho_factor`'s documented unspecified opposite triangle.

04b uses the numpy primitive and checks the original prior-space posterior equations. this fixture retains the input and checked expectation after temporary integration tests are deleted; it is not a permanent test harness. the original scientific verdicts and external diagnosis remain unchanged.
