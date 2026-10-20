# Run-week prediction scorecard (computed from builds5.csv, card_A/B.csv)

| id | verdict | evidence |
|---|---|---|
| B1 | held | link / build time over 25 completed builds: min 0.914 (rw-jet-r4-p8-lat), median 0.947 |
| B2 | held | stage of peak process memory: {'link': 35} (all 35 build dirs incl. failed/OOM) |
| B3 | held | tiny link 140 min = 2.50× smoke (≥0.70); peak cgroup 0.86× (anon 0.90×) smoke (≥0.85). Link time is node-confounded (tiny on E5-2698 v4) |
| B4 | failed | csynth time decreasing with RF in 3/6 model/precision/strategy series: big w8i2 Latency {1: 7.5, 4: 13.9} ✗; cnn ap_fixed<16,6> Latency {1: 3.3, 4: 2.5, 8: 1.9}; cnn w8i3 Latency {1: 2.8, 4: 2.1}; jet ap_fixed<16,6> Latency {1: 9.9, 4: 5.8, 8: 4.8}; jet ap_fixed<8,3> Latency {1: 4.3, 4: 4.5} ✗; jet w8i2 Latency {1: 5.1, 4: 11.0} ✗. csynth time is node-confounded (same design up to 2× across CPUs) |
| B5 | held | jet+cnn (n=22, excl. undersized): process peak 24.4–31.0 GiB, max dev from mean 12.0%; cgroup 26.3–35.5, 17.4% |
| B6 | failed (first half) | no design > 48 GiB (max process 31.02, cgroup 35.55), so the second half is vacuous; largest process peaks: jet-r1-p16-lat 31.02, ho-wide-r4-p16-lat 31.0, jet-r4-p16-lat 30.99, big-r4-p16-res 30.35 — big RF=1 is not among the largest |
| B7 | failed (marginal) | link mean cores 2.59–4.37; outside 2–4: jet-r4-p16-lat 4.06, noslr-jet-r4-p16-lat 4.37 (all long failing Latency routes) |
| B8 | held | build tree max 2.56 GB |
| B9 | held | under-jet-r4-p16-res OOM-killed in link (16 Gi limit; process peak 12.19 GiB) |
| B10 | failed (time) / held (process mem) | 3 runs link [62.4, 121.0, 121.9] min: max dev 39% (±15% predicted); run on EPYC 9555 vs two on EPYC 7402P, which agree within 0.7%. process peak max dev 2.4% (±5% held); cgroup 6.4% |
| B11 | failed | Resource DSP estimate is not lower than Latency at RF=4: jet ap_fixed<16,6>: DSP Lat 1066 / Res 1066; jet w8i2: DSP Lat 734 / Res 1065; big ap_fixed<16,6>: DSP Lat 1834 / Res 1834; big w8i2: DSP Lat 882 / Res 1834. Latency 16-bit RF=4 builds did not complete, so the link-time half is untestable for p16 |
| B12 | failed (post hoc pairs) | cnn-r1-p16-lat: SLR2 built WNS 0.003 vs no-SLR built WNS 0.003; jet-r4-w8-lat: SLR2 built WNS -0.527 vs no-SLR built WNS 0.003; jet-r1-p16-lat: SLR2 place: DSP > SLR vs no-SLR built WNS -0.695; jet-r4-p16-lat: SLR2 route: overlaps vs no-SLR route: overlaps; big-r4-p16-lat: SLR2 route: congestion vs no-SLR route: overlaps. jet-r4-w8-lat: pinned build is worse (259.0 vs 300 MHz). No-SLR builds were added post hoc (amendment 3) |
| B13 | failed (time) / held (memory) | OLS on csynth LUT/FF/DSP (form fixed now, not pre-specified in v1). Link time, trained on 22 completed: held-out errors big-r2-w8-lat +150%, cnn-r2-p16-lat -41%, jet-r2-p16-lat +24%. Process peak memory, trained on 29: big-r2-w8-lat -0.1%, cnn-r2-p16-lat +3.5%, jet-r2-p16-lat +3.4%, wide-r4-p16-lat +1.8%. Node effect on link time (~2×) is not in the features |
| B14 | held | jet-r1-p16 csynth DSP 3365 > 2879 → pinned build failed placement (3354.0 required); no-SLR build placed 3358.0 DSPs and built at 248.2 MHz |
| B15 | failed | both RF=1 w8 builds placed in SLR2: big-r1-w8-lat csynth DSP 899, 239.9 MHz, jet-r1-w8-lat csynth DSP 761, 300.0 MHz (8-bit weights cut DSPs ~4×; jet 3365 → 761) |
| C1 | held | 27 designs × 20,000 test inputs × 2 sessions, 0 mismatching rows, max |hw − csim| = 0.0 |
| C2 | held | 2,610 stress rows per design, 0 mismatches in either session |
| C3 | held | ±Inf/NaN rows are part of the stress set; bit-exact (hardware and C-sim agree on these rows too) |
| C4 | held | hw–Keras argmax agreement: 16-bit 0.9876–0.9923, w8 0.8998–0.9441, all-8-bit 0.3353/0.4163; equals C-sim agreement (C1) |
| C5 | held | single-call latency 64–107 µs; per-input time batch 1 → 10,000 falls 104–1016× |
| C6 | half (load failed) | xclbin load 7.2–9.5 s (≤2 s predicted); measured card time per design (load+test+stress+sweep) ≤ 9.5 s (<1 min held); reload of the same xclbin 0.08–0.14 s |
| C7 | held | session A (k8s-stratix-10-02.sdsc.optiputer.net) vs B (prp-gpu-2.t2.ucsd.edu): all accuracy/agreement/clock columns identical for 27 designs |
| C8 | held | card accuracy = C-sim accuracy for every design (incl. the all-8-bit collapse 0.3226/0.3977) |
| H1 | held | 40 Gi, no OOM; process peaks big-r2-w8-lat 28.5, cnn-r2-p16-lat 25.19, jet-r2-p16-lat 28.53, wide-r4-p16-lat 31.0 GiB, all in link |
| H2 | held | link cores big-r2-w8-lat 2.85, cnn-r2-p16-lat 3.53, jet-r2-p16-lat 3.42, wide-r4-p16-lat 2.67 |
| H3 | partly | csynth big-r2-w8-lat 5.6 min, cnn-r2-p16-lat 4.9 min, jet-r2-p16-lat 7.7 min, wide-r4-p16-lat 29.7 min (<20 predicted: wide failed); disk big-r2-w8-lat 2.56 GB, cnn-r2-p16-lat 1.12 GB, jet-r2-p16-lat 2.26 GB |
| H4 | 3/4 | jet-r2-p16 predicted routing fail, built at 206.6 MHz (WNS −1.505 vs 300); big-r2-w8, cnn-r2-p16 built; wide-r4-p16 failed routing (congestion) |
| H5 | 1/2 | big-r2-w8 281.6 MHz (225–250 predicted); cnn-r2-p16 300.0 MHz (250–300) |
| H6 | held | completed links big-r2-w8-lat 1.3 h, cnn-r2-p16-lat 2.8 h, jet-r2-p16-lat 3.0 h; failing wide spent 7.89 h |
| G1 | 4/5 | big-r2-p16-lat STOP → place: DSP > SLR; jet-r2-w8-lat GO → built 295.9 MHz; jet-r4-p16-lat-c5 GO → route: overlaps (21338 overlaps) ✗; wide-r4-w8-lat RISK → route: overlaps (13016 overlaps); wide-r8-p16-res GO → built 300.0 MHz |
| G2 | core held / exception clause failed | at 5.0 ns the design still failed routing (21338 overlaps vs 79,957 at 3.333 ns); csynth FF fell 91.3k → 62.6k (out of RISK), LUT 172.9k, yet it failed |
| G3 | held (process) / cgroup touched limit | stage 1: ≤ 23.0 min, peak process 4.91 GiB, cgroup 5.78 GiB (< 8 Gi); stage 2: peak process 28.21–29.46 GiB; cgroup reached the 40 Gi limit (page cache) on wide-r8-p16-res without OOM |
| G4 | held | STOP design: stage 1 = 0.39 h × 8 Gi (3.1 GiB-h, 0.8 core-h) vs its stage 2, run to confirm, 1.47 h × 40 Gi (58.7 GiB-h, 11.7 core-h) before VPL 30-859 (link 87.9 min, below the 1.5–12 h range quoted in G4). Gate miss c5: 9.66 h × 40 Gi (386 GiB-h); RISK wide-r4-w8 run to confirm: 13.45 h × 40 Gi (538 GiB-h) |

## Numbers for the text
- build dirs 35, completed 25, build-hours (t_total_h sum) 115.5
- placement/routing failures 8: 51.5 h = 45% of build-hours; csynth available after 5–30 min
- completed-build link time 56–260 min, median 129
- process peak (non-OOM, non-stopped) 24.45–31.02 GiB; cgroup max 35.55
- achieved clocks of built designs 206.6–300.0 MHz; at 300 MHz: 15/25
- throughput (A) 1.21–12.34 M inf/s
- RISK FF threshold margin: largest FF among built LUT>165k designs outside RISK 85448; smallest FF among routing failures 88483 (gap 3.6%); gate c5 failed at FF 63k → FF does not separate
- LUT>165k alone would misclassify 5 built designs: big-r1-p8-lat (186k, 300.0 MHz), big-r1-w8-lat (248k, 239.9 MHz), big-r4-w8-lat (249k, 234.8 MHz), ho-big-r2-w8-lat (249k, 281.6 MHz), ho-jet-r2-p16-lat (167k, 206.6 MHz)
- structural R2 (dense, Latency, 16-bit weights, RF>1): big-r4-p16-lat → route: congestion, ho-jet-r2-p16-lat → built, ho-wide-r4-p16-lat → route: congestion, jet-r4-p16-lat → route: overlaps, jet-r8-p16-lat → route: overlaps, noslr-big-r4-p16-lat → route: overlaps, noslr-jet-r4-p16-lat → route: overlaps, rep-big-r4-p16-lat → route: congestion; plus gate jet-r4-p16-lat-c5 → route fail
- gate round stage 2 link times: big-r2-p16-lat 87.9 min (AMD EPYC 7402P 24-Core), jet-r2-w8-lat 134.3 min (AMD EPYC 7402P 24-Core), jet-r4-p16-lat-c5 579.5 min (Xeon E5-2698 v4 @ 2.20GHz), wide-r4-w8-lat 806.8 min (Xeon Silver 4116 CPU @ 2.10GHz), wide-r8-p16-res 132.8 min (AMD EPYC 7F72 24-Core)
- wide-r4-w8-lat (8-bit weights, Latency, RF=4, LUT 322k) failed routing: 8-bit weights do not rescue the wide model, so the structural rule (16-bit weights) misses it; RISK caught it

## Gate regions applied to waves 1–3 + held-out (post hoc)

| row_0   |   built |   place: DSP > SLR |   route: congestion |   route: overlaps |
|:--------|--------:|-------------------:|--------------------:|------------------:|
| GO      |      24 |                  0 |                   0 |                 0 |
| RISK    |       1 |                  0 |                   3 |                 4 |
| STOP    |       0 |                  1 |                   0 |                 0 |
