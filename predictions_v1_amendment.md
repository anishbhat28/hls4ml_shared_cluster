# Amendment to predictions_v1 (before any 8-bit-weight build starts)

## What happened
The smoke build used `ap_fixed<8,3>` for every type in the model (weights, biases, activations, accumulators, softmax).
On the card it was bit-exact with hls4ml `predict` on all 20,000 test and 2,610 stress inputs, but its accuracy was
0.323 against 0.767 for Keras (argmax agreement 0.335). C-sim showed the same accuracy, so the collapse is a property of
the configuration, not of the hardware, and `predict` alone would have caught it before any synthesis.

## Change to the build matrix
The "8-bit" designs are redefined as **8-bit weights and biases, 16-bit everything else** (label `w8`), replacing the
all-8-bit `p8` designs. The integer bits of the 8-bit weight type are set per model from its largest weight magnitude,
so that no weight overflows: `ap_fixed<8,2>` (range ±2) for jet (max |w| 1.28) and big (1.39), `ap_fixed<8,3>` (±4)
for cnn (2.35). The two all-8-bit builds that had started (`rw-jet-r1-p8-lat`, `rw-big-r1-p8-lat`) were stopped. The
completed all-8-bit smoke build (`rw-jet-r4-p8-lat`) is kept and reported as the example of an accuracy collapse that
`predict` reveals before synthesis.

Chosen with C-sim only (no synthesis), before any `w8` build started (`csimcheck.json`, `csimcheck2.json`):

| model | Keras | 16-bit | w8, 1 int bit | w8, 2 int bits | w8, 3 int bits | all 8-bit |
|---|---|---|---|---|---|---|
| jet | 0.767 | 0.767 | 0.710 | **0.756** | 0.697 | 0.323 |
| big | 0.767 | 0.767 | 0.595 | **0.762** | 0.746 | 0.398 |
| cnn | 0.707 | 0.706 | 0.160 | 0.392 | **0.693** | 0.359 |
| tiny | 0.738 | 0.734 | 0.084 | 0.413 | 0.731 | 0.474 |
| wide | 0.770 | 0.768 | 0.536 | 0.754 | 0.673 | 0.169 |

Too few integer bits make out-of-range weights wrap around (hls4ml's default overflow mode for `ap_fixed` is wrap),
which collapses cnn and tiny at 2 integer bits; too many lose resolution (jet and wide at 3). The rule "fewest
integer bits that hold the largest weight" picks the best column for every model.

## Predictions affected
- The smoke reference values (build time, memory, CPU, disk) stay as the reference for B1–B13; the all-8-bit smoke
  build is a member of the jet family for B5.
- C4 now reads: hardware vs Keras argmax agreement is lower for `w8` than for 16-bit designs, and equals
  C-sim vs Keras agreement exactly (follows from C1).
- New, C8: for every design, the accuracy measured on the card equals the C-sim accuracy computed before synthesis
  (so an accuracy problem is always visible from `predict` before any card time is spent).
- All other predictions unchanged.
