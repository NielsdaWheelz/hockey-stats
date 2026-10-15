# 04a attribution feasibility protocol

date: 2026-10-14. the user assigned the complete [04a specification](../../specs/04a-attribution-feasibility.md), with separate worktree implementation, independent review at each boundary and temporary verification deleted after closure. this is research only. no acquisition, chance fitting, model admission, publication or player-card handoff is authorized by this protocol.

the corrected execution root is `/Volumes/Expansion/hockey-stats/runs/attribution-04a-20261014-02`. the original root without `-02` remains preserved and explicitly invalidated: a scipy triangular-factor defect corrupted prior matrix products. [verification](verification.md) records the discovery, minimal numerical repair and repeated checks. no scientific choice changed. `inputs/spec-snapshot.md` preserves the assigned specification exactly, sha256 `6a8484a1a937a50ce997edd4a78589fb80679e277ab5f8819963ec5f0720d404`. `inputs/selection.json`, sha256 `67cb59a415943f9ce24c62544c9a6e45adab6e6a872b8eba73709affdb7d72d5`, selects the five corrected 03m corpora in chronological order.

`inputs/protocol.json` was frozen before corrected preparation, fitting or simulation, sha256 `bd5c921dbfa7fedb6957c972707434ec3aadfa85e522bca0c49e8481563237de`. it binds clean implementation `d80d7321bc8e114361ce2dab712cf5a429c52584`, python `3.14.8`, numpy `2.5.3`, scipy `1.18.1`, and lockfile sha256 `bae38095f3dea6bdb860501eca311b1c33390c7a1e8b7aae76966572f118acdd`. manual commands set `OPENBLAS_NUM_THREADS=2` and `VECLIB_MAXIMUM_THREADS=2`. subsequent documentation records results; the frozen statistical rules remain unchanged. numpy supplies all four cholesky factorizations; the previous scipy factor path has been removed. the original protocol was `2a0a5d68aedbf007ed48867d4c1ba0551eeef11d700017d4a4db5abd5f828d5d` at `e50072d`. corrected execution repeats the ten annual fits and 600 replicates after numerical invalidation, with no alternative estimator or additional scientific selection; both physical executions remain accounted for.

## evidence and populations

the 2021–22 through 2025–26 manifests, original 03m selection and final admission audit retain the exact paths and digests recorded in [03n's protocol](../chance-03n/protocol.md). all five manifest hashes, the selection and audit hashes have been checked. the 6,560 inventory games establish the intended inventory, not complete exposure.

`all_attempts` uses recorded goals, shots on goal, misses and blocks. `unblocked_spatial` uses the first three on coordinate-complete admitted exposure. native score chronology, reported membership, elapsed intervals and source corroboration determine admission. counts and time share each population's masks in both attacking directions. positive zero-event segments remain. unknown membership and horizons remain unknown; a partial game can retain independently supported time. missing spatial coordinates remove affected spatial counts and time without erasing usable scalar evidence.

the source ledger preserves each event's assignment, exclusions and collateral losses. separate annual row ledgers bind native segment keys, lineups, context strata, seconds and sparse counts. source input hashes, grid, design and protocol determine population identity. player ids remain stable across trades. the greatest shared-exposure pair and the greatest combined-exposure pair with no shared exposure are selected from final-season scalar exposure before any fitting, with sorted-id ties.

## annual estimator

two separate five-year chains use relative recorded rates with weights `seconds/3600 * r`, where `r` is that population's annual league team rate per 60. each row has five offense and five defense indicators. flat observed context strata are attacking home/away, period `1|2|3|overtime` and pre-event score difference clipped to `-3..3`.

the scalar response covariance is one. the spatial covariance is the diagonal first-season half-count cell-share matrix, frozen thereafter. the native 656-cell grid is neither pooled nor smoothed. full player covariance is retained; no player-cell kronecker matrix is allocated.

first-year variance `a` and subsequent innovation variances `q` are selected by each population's matched scalar restricted gaussian likelihood. each search evaluates exponents `-8,-7.5,…,0`, then refines the best interior point's neighboring bracket once with `xatol=1e-4,maxiter=40`. all finite evaluations compete; ties favor smaller variance. endpoint winners or failed/nonfinite refinement remain `scale_unresolved`, including inherited limitations. no expanded search is permitted.

subsequent priors carry the entire previous centered mean and covariance, add current innovation to old states and append independent zero-mean entrants with variance `a`. absent players remain. current exposure centering transforms both complete covariance and means, with the corresponding five-player offset added to every context mean. earlier states never consume later evidence.

cholesky solves use the specified sufficient-statistic equations. equation residuals must be at most `1e-8` under the specification's scaled infinity norm. nonfinite or invalid algebra stops the dependent chain. signed effects and negative complete fitted rates remain visible; neither is clipped. the real budget is ten annual fits.

## recovery and sensitivity

the fixed simulator uses three cases, 200 replicates each, five seasons and both chains. its schedule and lineups use `PCG64(40400)`; response streams use `PCG64(40401+case_index)`. mixed and count-stress cases share their fixed design. the prescribed teams, durations, balanced schedule, truths, entrant/returner changes and paired players remain unchanged. all generating means have been checked positive without clipping or redraws. every replicate/year reselects its own scale.

truth is transformed to each realized annual rate and exposure centering before comparison. generating scalar coefficients are exact integer ticks of `1/40`; spatial coefficients are ticks of `1/400`. the centered truth functional forms its numerator using those ticks and integer exposure seconds before the final division, preserving exact zero contrasts. this changes no generating means or response draws. recovery summaries use a replicate as the independent unit for each named contrast and year. bias, rmse, interval widths, pointwise coverage with wilson intervals, false claims, and paired sum/difference recovery are descriptive evidence. poor recovery or undercoverage can complete the study; broken algebra cannot.

location unit stresses move model mass five nominal feet toward or away from `(89,0)`, using nearest valid native centers and native-order ties. the same transport acts on coefficient maps, prior response means/covariance and league count density. player covariance and chance valuation surfaces stay fixed. singular transported response covariance is retained exactly. probability stresses shift each valuation surface by `±.10` log odds. these are separate unit stresses, with no crossed campaign or truth-error interpretation.

## provisional valuation and claims

only final-season maps receive the exact saved 03n direct and 03o decomposition transfer weights named in the specification. all three completion hashes have been checked. native component validation and predictor encoding retain the original annual-state carry-forward. validation checks the existing hash-bound historical audit and coverage; it does not reconstruct or newly audit training sources. no 03p substitution, refit or fallback is permitted.

the common joint reference is equally weighted final-season unblocked events admitted to the spatial population and native core projection, with actors present in all three models. misses remain eligible for reference prediction. identical predictor tuples are collapsed by frequency only after retaining source keys and exclusions. direct and product surfaces average `p` and `q*g` over the same tuples; the product of independently averaged stages is not used. observed cell/type support refers to this common reference, with unseen cell/type reference mass reported for each crossed cell.

all player and pair contrasts retain full player and response covariance. defense is negated once into suppression at the content boundary. the meaningful band is `±.05` of the relevant population's league team rate; it is neither an allowed-error budget nor a goals threshold. intervals are pointwise 95% gaussian working-posterior intervals, conditional on fitted scales, covariance shape and references. scenario envelopes remain separate.

the three figures show the preselected players' scalar contrasts and meaningful band, their maps on common axes/scales with matched scalars, and the direct/product valuation scatter with equality line. tables cover all current players and five-season coverage. recorded counts, fitted associations, simulated truth and provisional goal-rate effects retain distinct labels.

## limits and decision

the statistical costs are gaussian and separable working uncertainty, scalar-selected spatial shrinkage, unsmoothed maps, selective coverage, omitted deployment mechanisms, age-neutral drift and common-reference extrapolation. conditional intervals omit scale selection, dependence, misspecification and chance-model uncertainty. neither borrowing nor apparent precision proves repeatable ability or causal isolation.

the decision will separately answer which populations are usable, which meaningful differences resolve under this working model, and which conclusions change under the prescribed stresses. it will recommend one next step with dependencies. every result remains `admission:not_admitted,handoff:null`. [player-consequence budgets](../../issues/player-consequence-budgets.md) remains open; unit stresses cannot close it.
