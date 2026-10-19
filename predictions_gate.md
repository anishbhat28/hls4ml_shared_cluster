# Gate predictions (committed before any rw-g-* job starts)

## The gate (stage 1, a small job: 2 CPU, 8 Gi)
hls4ml generate + csynth + package, then from the csynth report of the kernel (`myproject_axi_master`):
- **STOP (placement)** if the kernel is pinned to one SLR and csynth DSP > 2879 (DSPs available to the dynamic region of
  one U55C SLR, from VPL 30-859 in rw-jet-r1-p16-lat).
- **RISK (routing)** if csynth LUT > 165,000 and FF > 88,000.
- **GO** otherwise.

The RISK thresholds were chosen after waves 1–3 and the held-out round (post hoc, n = 33): every design in that region
failed routing (7) or built far below the 300 MHz target (rw-ho-jet-r2-p16-lat, 206.6 MHz); every design outside it
that passed R1 built. This round tests the gate on five designs that have not been built before.

## Predictions
G1. Each design's outcome follows its gate verdict: GO → builds with kernel clock ≥ 230 MHz;
    RISK → fails routing, or builds with kernel clock < 220 MHz; STOP → fails placement.
G2. rw-g-jet-r4-p16-lat-c5 (the design that failed routing at clock_period 3.333, now 5.0 ns): the HLS clock target
    does not change the link outcome — Vitis implements against the platform's 300 MHz kernel clock — so it fails
    routing like rw-jet-r4-p16-lat, unless its csynth LUT/FF move it out of the RISK region.
G3. Stage 1 peaks below 8 Gi and finishes in < 45 min for every design; stage 2 peaks below 40 Gi.
G4. Two-stage cost: for a design the gate stops, the cluster reserves ≤ 8 Gi for ≤ 45 min instead of 40–64 Gi for
    1.5–12 h (measured in waves 1–3).
