# spatial history audit confuses source identity with annual selection

the temporary independent annual checker compares complete `prepared` and `coaches` binding dictionaries across years. their source `purpose/path/sha256` identities are shared, while prepared `members` and coach `selected_game_ids` are annual selections and must differ. source `ed289155` line 192 therefore refuses valid year-to-year manifests before numeric evidence is read.

impact: the first actual year-two independent history check exited 1; age/history/reference/projection verification remains incomplete. this is a checker defect, not evidence of a production defect. [preserved run and exact evidence](../research/spatial-v1-08/reviews/real-spatial-history-20222023-01-saved-review.md)

the completed annual is `bdc5c2d4`; canonical readback and saved metadata pass. the refused check read only two manifests: preparation differs only in 1,313 annual members per season, and coaches only in 1,312 selected game ids per season. the numerical derivations and every numerical check remain unreached. preserve the failed external invocation and its exact old checker identity.

resolution: distinguish shared source identity from each manifest's bound annual selection, add a tiny synthetic annual-selection regression and refusal controls, obtain independent source review, and complete a separately released fresh saved check. preserve the failed run; no automatic retry or changed numerical criterion is authorized.
