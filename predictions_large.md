# Predictions — larger-model round (written before any rw-*-large* job runs)

Purpose: test whether the main results hold for a model about 10× larger than the run-week models.
Model `large`: 16→256→256→128→5, ReLU, softmax; ~104k parameters (jet: ~4.4k, wide: ~10.9k). Trained by
rw-prep-large on the run-week split and seed (asserts the same test inputs). Same toolchain as the run week
(hls4ml 8912ed2, Vitis 2024.2, `ap_fixed<16,6>`, Resource strategy, io_stream, 3.333 ns), 8 CPU / 40 Gi.
RF values checked against hls4ml's reuse-factor rule for every layer (valid for 16 and 64).

| build | RF | SLR pin | multipliers (n_in·n_out/RF) |
|---|---|---|---|
| rw-large-r64-p16-res | 64 | SLR2 | 1,610 |
| rw-large-r16-p16-res | 16 | none (6,440 > 2,879 DSPs of SLR2) | 6,440 |

| id | prediction | confidence |
|---|---|---|
| L1 | Keras test accuracy of `large` on the 20,000 run-week test jets ≥ that of `big` (0.7671) − 0.005 | medium |
| L2 | r64: csynth DSP estimate 1,500–1,750; the gate rule gives GO | high |
| L3 | r16: csynth DSP estimate 6,000–6,700; the gate rule would give STOP if pinned to SLR2 (B14 rule) | high |
| L4 | csynth for both builds finishes in < 60 min with peak process memory < 16 GiB | medium |
| L5 | **Main test.** Both builds that reach the link have peak process memory 25–33 GiB, reached in the link, within its first 60 min (module synthesis), with placement and routing below 20 GiB | medium |
| L6 | r64 builds, achieved clock ≥ 250 MHz | medium |
| L7 | r16 (unpinned) builds, achieved clock ≥ 200 MHz | low |
| L8 | Link time of each completed build is within 0.5–2× of the slowest earlier Resource build on the same CPU type, else within 60–300 min | low |
| L9 | Every completed build: hardware bit-exact with C-sim on all 20,000 test and 2,610 stress inputs; card accuracy = C-sim accuracy | high |

A lost pod (node failure) counts neither way: rerun the same job. If L5 fails, the paper reports where the
platform-set memory floor ends instead of claiming it holds for all hls4ml models.
