# Predictions — clean-room rerun (written before any rw2-* job runs)

Purpose: check that the released kit reproduces a run-week result from scratch, and add a third CPU type for one
design. Everything is rebuilt under /work/rw2 (fresh hls4ml clone at 8912ed2, fresh wheel, fresh dataset download,
retrained models). /work/rw is only read, for comparison. Jobs: rw2-prep (8 CPU, 16 Gi), rw2-jet-r4-p16-res
(jet, RF=4, ap_fixed<16,6>, Resource, SLR2, 3.333 ns; 8 CPU, 40 Gi; pinned to chi-dgx-node02, Xeon E5-2698 v4),
rw2-card-cr (any U55C host).

Reference (run week, jet-r4-p16-res, 3 runs): csynth DSP 1066 / LUT 56,981 / FF 66,823 / BRAM 51; built at 300 MHz,
WNS 0.003; link 62.4 min (EPYC 9555), 121.0 and 121.9 min (EPYC 7402P); process peak 28.5–29.7 GiB; card accuracy
0.7668, bit-exact with C-sim.

| id | prediction | confidence |
|---|---|---|
| CR1 | Prep completes in < 1 h; hls4ml commit 8912ed2; X_test, Y_test, X_stress bit-identical to /work/rw | high |
| CR2 | Retrained model weights are NOT bit-identical to the run-week models (multi-threaded CPU training on a different node); jet test accuracy within ±0.01 of 0.7671. If they are identical, CR3b–CR6b apply | medium |
| CR3a | If weights differ: csynth DSP within ±2% of 1066, LUT and FF within ±10% | medium |
| CR3b | If weights identical: csynth DSP/LUT/FF identical to the run week | high |
| CR4 | Build completes; achieved clock 300 MHz, WNS ≥ 0 | high |
| CR5 | Link time on Xeon E5-2698 v4 between 130 and 200 min (slower than both earlier CPU types); process peak 28.0–31.0 GiB; link mean cores 2.6–4.0; build tree < 2 GB | medium |
| CR6a | Card: hardware bit-exact with this build's own C-sim on all 20,000 test and 2,610 stress rows | high |
| CR6b | If weights identical: this build's C-sim outputs bit-identical to the run-week build's y_csim_test/y_csim_stress, card accuracy 0.7668 | high |
| CR7 | Total cluster wall time for all three jobs < 5 h | medium |

Lost pod (node failure) does not count either way: rerun the same job.
