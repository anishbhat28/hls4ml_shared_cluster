# Clean-room rerun scorecard (predictions_cleanroom.md, commit f837cbe; results_cr.zip, collected Oct 21)

Fresh /work/rw2: hls4ml clone at 8912ed2, wheel, dataset download, model training, one build, one card session.
Jobs: rw2-prep (tu.gp-engine.greatplains.net, AMD EPYC 7713, 03:45–03:57 UTC Oct 21), rw2-jet-r4-p16-res
(chi-dgx-node02, Xeon E5-2698 v4, 04:01–07:03 UTC), rw2-card-cr (prp-gpu-2, 07:17 UTC, 9 s).

| id | verdict | evidence |
|---|---|---|
| CR1 | held | prep 11 min; hls4ml 8912ed2; dataset md5 b0cade1d…; X_test, Y_test, X_stress bit-identical to /work/rw |
| CR2 | failed (better than predicted) | all five retrained models bit-identical to the run-week models (max abs diff 0.0), although trained on a different CPU (EPYC 7713); predicted not identical |
| CR3b | held | every csynth report identical to the run-week build except the date line; layers.json and link_system.cfg byte-identical |
| CR4 | held | built; achieved 300 MHz; WNS 0.003 ns (same as all three run-week builds) |
| CR5 | held | link 170.2 min on Xeon E5-2698 v4 (130–200 predicted); process peak 28.1 GiB, in link (cgroup peak 32.6 GiB); link mean cores 3.66; build tree 1.47 GB |
| CR6a | held | card: bit-exact with this build's C-sim on 20,000 test + 2,610 stress rows, 0 mismatches |
| CR6b | held | this build's C-sim outputs bit-identical to all three run-week builds (rw-, rep-, rep2-jet-r4-p16-res), test and stress; card accuracy 0.7668 (same), 300 MHz, 4.88 M inf/s, load 7.3 s, single call 73 µs |
| CR7 | held | total wall 3.2 h (prep 0.18 h, build 3.03 h, card 9 s) |

## Same design, four builds, three CPU types (jet-r4-p16-res)
| run | CPU | link (min) | process peak (GiB) | clock |
|---|---|---|---|---|
| rw-jet-r4-p16-res | AMD EPYC 9555 | 62.4 | 29.44 | 300 |
| rw-rep-jet-r4-p16-res | AMD EPYC 7402P | 121.0 | 29.67 | 300 |
| rw-rep2-jet-r4-p16-res | AMD EPYC 7402P | 121.9 | 28.50 | 300 |
| rw2-jet-r4-p16-res (clean room) | Xeon E5-2698 v4 | 170.2 | 28.12 | 300 |

Link time spans 2.7× across CPU types for an identical design (csynth, link config and C-sim outputs identical);
same-CPU repeats agree within 0.7%; process peak memory within ±3%.
