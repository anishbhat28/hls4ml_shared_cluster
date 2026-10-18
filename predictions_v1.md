# Predictions before the build matrix (v1)

Written after the smoke build only (rw-jet-r4-p8-lat, 16→64→32→32→5, RF=4, ap_fixed<8,3>, Latency, SLR2, 8 CPU / 64 Gi).
Committed before any other build in the matrix is started. Each prediction is checked against the final data and reported as held / failed.

Smoke reference values:
- stage times: generate 10 s, csynth 273 s, package 36 s, link 3361 s (link = 91% of build time)
- peak memory (cgroup, incl. page cache) 32.7 GiB, reached in link; csynth peak 5.2 GiB
- peak anonymous (process) memory 28.3 GiB; the rest of the cgroup peak is page cache
- mean cores in use during link 2.9 of 8
- build tree on disk before cleanup 1.67 GB
- routed WNS +0.003 ns (timing met)

## B — build cost vs hls4ml settings

B1. Link is ≥ 80% of build wall time for every design that completes.
B2. Peak memory is reached during link for every design, never in csynth or package.
B3. Shell floor: `tiny` (16→8→5) link time ≥ 70% of the smoke link time, and its peak memory ≥ 85% of the smoke peak. (For small hls4ml designs on the U55C the cost is set by the platform, not the model.)
B4. csynth time increases when RF decreases (RF 8 → 4 → 1) at fixed model and precision, for jet, big and cnn.
B5. Peak memory varies by less than ±25% across all jet and cnn designs (RF 1–8, 8/16-bit, Latency/Resource).
B6. The largest peaks are the RF=1 big design and the held-out wide design; any design exceeding 48 GiB is one of these.
B7. Mean cores in use during link stay between 2 and 4 for every design (the request of 8 is 25–50% used).
B8. Build tree on disk before cleanup is < 5 GB for every design.
B9. The undersized build (`rw-under-jet-r1-p16-lat`) is OOM-killed, during link.
B10. Repeats: link time of the three jet-r1-p16 runs is within ±15% of their mean; peak memory within ±5%.
B11. Resource strategy at RF=4 has lower csynth DSP estimate than Latency at RF=4, with link time within ±20%.
B12. SLR vs no-SLR (same design): the SLR2 build has routed WNS ≥ the no-SLR build; link time within ±25%.
B13. A csynth-report predictor (fitted on waves 1–3 from csynth LUT/FF/DSP estimates) predicts held-out link time within ±30% and peak memory within ±15%.

## C — validation with minimal card time

C1. Hardware output equals hls4ml `predict` (C-sim) bit for bit on 100% of the 20,000 test inputs for every design.
C2. Same on the stress set, including the ×16 / −×16 overflow rows and the zeros / tiny-value rows.
C3. ±Inf / NaN rows: hardware equals C-sim on these rows as well. (Least certain prediction; a mismatch here is reported as a finding, not hidden.)
C4. Hardware vs Keras argmax agreement < 100% for 8-bit designs and higher for 16-bit designs; it equals C-sim vs Keras agreement exactly (follows from C1).
C5. Single-input call time ≥ 50 µs (dominated by launch and DMA overhead), and time per input falls by ≥ 10× between batch 1 and batch 10,000.
C6. xclbin load ≤ 2 s; card time per design for the full validation (load + test + stress + batch sweep) < 1 minute.
C7. Session A and session B give identical numerical results for every design (repeatability on the card).
