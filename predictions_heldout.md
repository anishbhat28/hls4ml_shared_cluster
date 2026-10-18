# Held-out predictions (written from waves 1–3, before any held-out build starts)

Held-out designs (defined in `make_builds.sh` before wave 1 started; not built until now):

| build | model | RF | precision | strategy |
|---|---|---|---|---|
| rw-ho-jet-r2-p16-lat | jet 16→64→32→32→5 | 2 | ap_fixed<16,6> | Latency |
| rw-ho-big-r2-w8-lat | big 16→64→64→32→5 | 2 | 8-bit weights (ap_fixed<8,2>), 16-bit rest | Latency |
| rw-ho-cnn-r2-p16-lat | cnn Conv1D | 2 | ap_fixed<16,6> | Latency |
| rw-ho-wide-r4-p16-lat | wide 16→128→64→5 (new architecture) | 4 | ap_fixed<16,6> | Latency |

All four run with the job size the guidance recommends: **40 Gi memory** (not the 64 Gi used in waves 1–3), 8 CPU,
10 Gi node-local disk, kernel pinned to SLR2 (board default).

## Guidance derived from waves 1–3 (what is being tested)

G1. Memory: every build's peak process memory was 24.5–31.0 GiB and every cgroup peak ≤ 35.6 GiB, always in the link
    stage, independent of model, RF, precision and strategy (the U55C platform dominates). A 40 Gi request suffices.
G2. CPU: Vivado uses 2.6–4.1 cores on average during link; 8 requested cores are 30–50% used.
G3. Disk: build tree ≤ 2.6 GB.
G4. Pre-link feasibility check from the csynth report (available after ≤ 20 min):
    - R1 (placement): if the csynth DSP estimate exceeds 2879 (DSPs available to the dynamic region in SLR2),
      the pinned build fails placement (`VPL 30-859`).
    - R2 (routing): a dense model with the Latency strategy, 16-bit weights, RF > 1 and a csynth LUT estimate above
      150k fails routing in SLR2 (`VPL 35-2` / `VPL 35-3`). With 8-bit weights or the Resource strategy the same
      models build.
G5. Link time depends on the node: the same design took 62 min on an EPYC 9555 node and 121 min on EPYC 7402P nodes.

## Predictions

H1. No held-out build is OOM-killed at 40 Gi; peak process memory of each is 24–33 GiB, reached in link.
H2. Mean cores in use during link are 2.4–4.5 for each.
H3. csynth takes < 20 min for each; disk < 3 GB for each that completes.
H4. R1/R2 evaluated on each held-out csynth report give the outcome of that build:
    - rw-ho-jet-r2-p16-lat: csynth DSP < 2879 (placement possible) but R2 applies → **fails routing**.
    - rw-ho-big-r2-w8-lat: R1 and R2 do not apply → **builds**.
    - rw-ho-cnn-r2-p16-lat: R1 and R2 do not apply (LUT estimate well below 150k) → **builds**.
    - rw-ho-wide-r4-p16-lat: R2 applies → **fails routing** (as big-r4-p16-lat did).
H5. Achieved kernel clock: big-r2-w8 225–250 MHz (timing not met at 300 MHz, clock scaled, as big-r1-w8 and
    big-r4-w8 did); cnn-r2-p16 250–300 MHz.
H6. Link time of the builds that complete is 1–5 h; a failing build spends 1.5–8 h before it fails.
