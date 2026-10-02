# saved chance-model diagnosis

the later-game goal excess is concentrated in attempts with supported recent context, especially preceding giveaways, takeaways and blocked shots, and is largest in january. the historical direct benchmarks share much of it. shooters unobserved in the applied training state have larger residual rates, but most excess predicted goals occur among shooters observed in that state. these associations locate the error; they do not identify its cause.

this diagnosis replays the three saved 03e models once, under clean `3f7bc37f93fb583cd5a59cb04660c68e839ad282` and the original [frozen protocol](/Users/nnandal/Documents/code/hockey-stats-03f-runs/inputs/protocol.md), sha256 `2bf44beb8d8f4bd5755d8541aa08af868706f3b8c428fae1b209e44937446d71`. the [authoritative receipt](/Users/nnandal/Documents/code/hockey-stats-03f-runs/review-notes/diagnosis-receipt.json) binds [diagnosis](/Users/nnandal/Documents/code/hockey-stats-03f-runs/diagnoses/development/diagnosis.json), sha256 `4d935109146351bcc47cc69128e3f2f3ef586ba84a789203459eafdfed5b447a`, source identities, six factual streams and every reported metric/group/bin. all three later-game evaluations reconcile to saved schema-3 counts and probability/loss sums. extracted component probabilities match native predictions exactly. training is in-sample; opportunity values are not used.

training covers complete 2023–24 and 2024–25 games through 2024-12-31: 1,912 selected games, 231,428 recognized attempts, 49,364 outside scope, 917 unavailable and 181,147 eligible. one selected game contributes no eligible attempts. assessment covers the remaining 712 games of 2024–25: 85,317 recognized attempts, 16,270 outside scope, 272 unavailable and 68,775 eligible. no selected capture is missing. `context_unavailable` appears on 1,506 training and 569 assessment recognized rows; reasons can overlap each other and outside-scope status. unavailable context never becomes no recent action. complete exclusion/reason ledgers remain in the receipt.

| quantity | training applicable / observed positives | later-game applicable / observed positives |
|---|---:|---:|
| unblocked conversion; positive = recorded goal | 128,679 / 7,614 | 49,014 / 2,804 |
| all-attempt goal probability; positive = recorded goal | 181,147 / 7,614 | 68,775 / 2,804 |
| marginal-unblocked probability; positive = recorded unblocked attempt | 181,147 / 128,679 | 68,775 / 49,014 |

conversion retains recorded-proxy location and conditions on an eligible unblocked attempt. the candidate's all-attempt probability integrates origin, avoidance and conversion without the focal location; its direct benchmark predicts the same recorded goal label from context and actors. marginal-unblocked probability integrates origin and avoidance and predicts a different outcome. their losses and residuals must remain separate.

loss below is pooled mean log loss in nats per applicable attempt; residual is predicted minus observed rate in percentage points. displayed values are rounded; the receipt retains full precision, counts, observed/predicted sums and brier scores. `stronger` remains the independently selected historical direct comparator for both goal quantities; the other direct rows are diagnostics, not replacement comparators.

| quantity | predictor | training loss | training residual, pp | later-game loss | later-game residual, pp |
|---|---|---:|---:|---:|---:|
| all-attempt goal | anchor candidate | 0.16164612 | +0.014984 | 0.16182977 | +0.204330 |
| all-attempt goal | anchor direct | 0.16142375 | +0.000012 | 0.16207751 | +0.194070 |
| all-attempt goal | weaker candidate | 0.16096530 | +0.011119 | 0.16218286 | +0.200357 |
| all-attempt goal | weaker direct | 0.16070308 | -0.000036 | 0.16249212 | +0.185306 |
| all-attempt goal | stronger candidate | 0.16232561 | +0.017556 | 0.16168078 | +0.204310 |
| all-attempt goal | stronger direct | 0.16214978 | -0.000103 | 0.16189285 | +0.198516 |
| conversion | anchor candidate | 0.18769068 | -0.000002 | 0.18991237 | +0.208873 |
| conversion | anchor direct | 0.18925498 | +0.000004 | 0.18985321 | +0.226341 |
| conversion | weaker candidate | 0.18607522 | -0.000051 | 0.19041667 | +0.195807 |
| conversion | weaker direct | 0.18821337 | +0.000052 | 0.19029672 | +0.212194 |
| conversion | stronger candidate | 0.18944938 | -0.000066 | 0.18997836 | +0.217063 |
| conversion | stronger direct | 0.19031489 | -0.000020 | 0.18974534 | +0.234532 |
| marginal unblocked | anchor candidate | 0.57027808 | -0.002277 | 0.57224968 | -0.189397 |
| marginal unblocked | weaker candidate | 0.56983824 | +0.001421 | 0.57266996 | -0.170865 |
| marginal unblocked | stronger candidate | 0.57094619 | +0.004028 | 0.57220128 | -0.226781 |

near-zero pooled training residuals conceal conditional discrepancies. later conversion and all-attempt goals overpredict across all three recipes, while pooled marginal unblocked underpredicts. that negative marginal residual does not exonerate avoidance/origin behavior in recent-context cohorts, where its residual is positive.

the following named groups show anchor's later-game all-attempt goal predictions and the historical stronger direct benchmark on the same source-defined groups. observed goals are counts; predicted goals are probability sums. rows from different group families overlap and must not be added.

| group | attempts | observed goals | anchor predicted goals | anchor residual, pp | stronger direct residual, pp |
|---|---:|---:|---:|---:|---:|
| no recent action | 47,638 | 1,951 | 1904.393 | -0.097836 | -0.061716 |
| recent action | 21,137 | 853 | 1040.135 | +0.885345 | +0.785019 |
| preceding faceoff | 5,303 | 79 | 66.042 | -0.244352 | -0.284720 |
| preceding hit | 2,955 | 68 | 86.492 | +0.625771 | +0.778919 |
| preceding giveaway | 3,216 | 89 | 171.676 | +2.570763 | +2.987996 |
| preceding takeaway | 823 | 26 | 54.041 | +3.407126 | +3.822565 |
| preceding shot-on-goal | 3,958 | 368 | 401.803 | +0.854038 | +0.214790 |
| preceding missed-shot | 2,161 | 117 | 108.797 | -0.379573 | -0.652933 |
| preceding blocked-shot | 2,721 | 106 | 151.285 | +1.664288 | +1.325465 |
| 2025-01 | 21,827 | 830 | 928.217 | +0.449981 | +0.448231 |
| 2025-02 | 11,895 | 502 | 511.134 | +0.076789 | +0.058388 |
| 2025-03 | 22,356 | 930 | 955.460 | +0.113883 | +0.101125 |
| 2025-04 | 12,697 | 542 | 549.717 | +0.060779 | +0.071993 |
| avoidance shooter: observed_in_state | 66,316 | 2,733 | 2842.704 | +0.165426 | +0.160506 |
| avoidance shooter: other_seasons_only | 1,366 | 35 | 53.616 | +1.362812 | +1.282715 |
| avoidance shooter: unseen | 1,093 | 36 | 48.208 | +1.116939 | +1.149703 |

recent-context all-attempt residuals are +0.881–+0.885 pp across the three candidates, against −0.096–−0.102 pp without recent action. anchor's recent rows supply 187.135 excess predicted goals; no-recent rows offset 46.607, leaving 140.528 net. anchor's conversion likewise overpredicts recent rows (+0.862744 pp; 14,852 attempts) and underpredicts no-recent rows (−0.075399 pp; 34,162). stronger's direct conversion shares this split (+0.879259/−0.045765 pp). preceding giveaway and takeaway conversion residuals are +3.570344 and +4.537395 pp; preceding shot-on-goal conversion is only +0.037097 pp despite +0.854038 pp for all-attempt goals. its marginal-unblocked residual is −0.503248 pp. the same joint discrepancy need not have the same component association in every context.

recent owner and delay summaries also distinguish the error: all-attempt residuals are +1.398079 pp after an opponent action (5,837 attempts), versus +0.689736 pp after a same-team action (15,300). all six recorded delay groups overpredict; their anchor residuals range from +0.444894 pp at one second to +1.587930 pp at five seconds. the direct benchmark shares positive errors across these delay groups. owner, kind and delay summaries overlap; they do not establish that any one missing interaction is responsible.

january's excess appears in conversion too (+0.488793 pp; 15,461 attempts), and the direct conversion benchmark shares it (+0.511584 pp). all-attempt residuals are larger away (+0.312931 pp; 33,795 attempts) than home (+0.099408 pp; 34,980), and for forwards (+0.280747 pp; 44,247) than defenders (+0.065640 pp; 24,523). stronger direct shares the away/forward excess. five eligible unknown-role attempts are too sparse to support a role conclusion; their residual remains recorded.

model-type goal residuals span slap −0.432254 pp (7,556 attempts), backhand −0.148107 (4,121), wrist +0.133944 (35,067), snap +0.450714 (15,389), tip +0.874718 (5,763) and other +1.428008 (879). original labels expose differences within pooled types: tip-in contributes 287 observed versus 340.619 predicted goals on 4,854 attempts; deflected contributes 65 versus 61.791 on 909. wrap-around contributes 18 versus 37.377 on 463 and already overpredicts in training (+3.736687 pp). the stronger direct benchmark shares overprediction for model tips, snaps, wrists and other, but this does not validate either type grouping or recorded-proxy geometry.

actor evidence is stage-specific. avoidance-shooter groups above also match the direct all-attempt shooter's support population. most excess predicted goals nevertheless occurs in `observed_in_state`: 2,842.704 predicted versus 2,733 observed. conversion-stage support on the all-attempt population differs: 1,432 `other_seasons_only` shooter rows have +1.433674 pp residual and 1,162 `unseen` rows have +1.056450 pp; their groups must not be paired with the direct benchmark's own support groups. conversion-stage goalie residuals have the opposite pattern: +0.226929 pp on 67,709 observed-in-state rows, −0.988412 on 724 other-season rows and −1.744862 on 342 unseen rows. unseen denotes no applicable training evidence, not rookie status. these small support groups qualify averages; they do not explain the entire failure.

training already contains some joint conditional excess: preceding shot-on-goal +0.609366 pp, preceding blocked-shot +0.310629, recent same-team action +0.200462, and several original/model type discrepancies. it does not contain the full later pattern: giveaway and takeaway joint residuals are negative in training (−0.429924/−0.384172 pp), recent conversion is near zero (+0.005610 pp), and the historical direct benchmark's fitted context groups are near zero. training calendar-month residuals vary in both directions. a shared later-game context/time association is therefore a better description than a uniform pre-existing excess or a demonstrated latent-origin defect.

the paired goal cohort uses anchor's all-attempt probability in `[0.10,0.15)`, fixed across every candidate and benchmark. it contains 5,521 training attempts with 681 goals, and 2,089 later-game attempts with 201 goals. no cohort is selected on recorded block/goal status.

| all-attempt predictor | training predicted goals | training residual, pp | later-game predicted goals | later-game residual, pp |
|---|---:|---:|---:|---:|
| anchor candidate | 667.058 | -0.252531 | 251.991 | +2.440932 |
| anchor direct | 649.959 | -0.562242 | 244.252 | +2.070468 |
| weaker candidate | 675.983 | -0.090864 | 255.584 | +2.612911 |
| weaker direct | 656.100 | -0.451004 | 245.759 | +2.142601 |
| stronger candidate | 655.650 | -0.459162 | 247.624 | +2.231868 |
| stronger direct | 643.467 | -0.679827 | 242.667 | +1.994594 |

all six goal predictors in the table underpredict this training cohort and overpredict its later-game counterpart. within the later cohort, conversion applies to 1,662 unblocked rows with 201 goals: anchor predicts 242.028 (+2.468587 pp), and stronger direct conversion 237.458 (+2.193594 pp). anchor's marginal-unblocked prediction is 1,690.956 against 1,662 observed unblocked attempts on all 2,089 cohort rows (+1.386125 pp). these are three different probability quantities, not multiplicative explanations of one aggregate residual.

each predictor's own twenty fixed bins remains separate in the receipt, including empty bins. candidate all-attempt own `[0.10,0.15)` later-bin counts are 2,089 / 2,340 / 1,956 for anchor/weaker/stronger; stronger direct's own bin contains 1,935 attempts, 197 goals and 234.640 predicted goals. its predicted/observed rates are 12.126103%/10.180879%. that own-bin discrepancy is distinct from the stronger direct's +1.994594 pp on anchor's 2,089-row cohort. a cohort selected by another predictor is descriptive, not automatically that predictor's calibration failure.

the fixed screen can examine differentiated recent context and removal of the oldest season without claiming that either is the remedy. calendar drift, source/context representation, annual pooling and sparse actor evidence remain unresolved mechanisms; these summaries identify no unique cause. no aggregate component-error multiplication, conditional causal attribution, physical-origin claim or player-value conclusion follows. 03b remains rejected; 03e remains withheld. component screening does not admit a model or authorize 04/publication.
