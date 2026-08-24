# CoST to Deepskin domain-shift report

## Observed shift

The CoST-only RBF-SVM achieved Macro F1 0.6587 in CoST subject-grouped cross-validation but only 0.1036 on the 315 Deepskin Gold trials. It predicted 209/315 Deepskin trials as STATIC_TOUCH. This collapse affected all three Deepskin operators and is therefore not explained by one participant.

The sensors differ in grid shape (8×8 versus 18×29), sampling rate (135 Hz versus about 53 Hz), pressure response, and capture protocol. The common feature implementation normalizes coordinates, pressure, time, and spatial pooling, but these transformations do not remove the observed action-definition and sensor-response shift.

## What transferred

- Direct source-only classification did not transfer.
- Low-weight E2 joint training improved pooled F0 Macro F1 but failed the per-operator fold gate.
- Seven continuous source scores were useful as weak auxiliary signals in E3 even though their standalone argmax labels were badly biased.
- CoST permutation-importance rankings did not provide a transferable feature-pruning rule in E4.

## Interpretation boundary

These results are a three-operator pilot and do not establish broad population generalization. They support using CoST only through a target-trained correction layer, not as a direct Deepskin classifier.

The current source set contains all 4,460 explicitly mapped captures. Capture-level compatibility filtering required by the frozen plan has not yet been implemented, so the transfer experiments must be rerun after that protocol gap is closed.

## Filtered rerun update

The frozen compatibility filter retained 3,427 captures and was then used in non-overwriting E1–E4 v2 reruns. CoST internal Macro F1 improved from 0.6587 to 0.7422, confirming better source-domain consistency. Deepskin source-only Macro F1 remained very low at 0.1172. E2, E3, and E4 did not beat their matched target-only baselines. The final transfer decision is therefore target-only.
