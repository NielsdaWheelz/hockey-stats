# real app build source review

clear for the separately released task-checkout typecheck and fresh build. held command `afa5e7b8bd75bc9214b2f582759611aaa1db76b28bc703cfab6dad73c0be0635` became `1a0ffa6a16a07de07fa650992d95dcce25121ab0a23076b4078fdae60eae26fc` by changing only the root release literal; restoring the held literal in memory reproduces the held hash. shell syntax passes. [preparation](real-product-final-build-preparation.md) retains the held-command history.

an initial source review found that building over existing `app/dist` could retain obsolete output. the revised command removes only `/Users/nnandal/Documents/code/hockey-stats-v1-08/app/dist` after successful typecheck and before build. it uses node `24.21.0`, checks clean app tree `e01418f448cbfaae517685d7927a90cd37343660`, guards fresh external records, captures both exits and costs, and binds the ordered source/dist file lists and server entrypoint. source identity is checked against `0861036972ccacc7bb8cb6393b0e3cb697293d44c873f36bee0a0e5bd4223511`; dist identity is measured from the new build.

root reports no listeners on ports 3398 or 3399. no build, database, server, api, browser, activation or primary serving-file action occurred in this review. root owns launch; successful build alone cannot establish candidate or runtime acceptance.
