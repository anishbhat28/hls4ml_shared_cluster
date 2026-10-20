# Gate-round scorecard (from results_gate.zip, collected Oct 19 15:45 PT)

## Gate round (predictions_gate.md, commit 4a5c8a5, Oct 19 00:38:58; stage 1 = 2 CPU / 8 Gi, stage 2 = link only, 8 CPU / 40 Gi)

| design | csynth DSP / LUT / FF | gate | stage 1 (min, peak GiB) | stage 2 outcome | link |
|---|---|---|---|---|---|
| big-r2-p16-lat | 3667 / 265k / 140k | STOP | 23.0, 4.8 | placement fail (VPL 30-859) | 1.47 h |
| jet-r2-w8-lat | 759 / 163k / 61k | GO | 7.2, 4.1 | built, 295.9 MHz (WNS −0.046) | 2.24 h |
| jet-r4-p16-lat-c5 (CLK 5.0 ns) | 1066 / 173k / 63k | GO | 7.8, 3.5 | routing fail (VPL 35-2, 21,338 overlaps) | 9.66 h |
| wide-r4-w8-lat | 1039 / 322k / 101k | RISK | 21.6, 6.0 | routing fail (VPL 35-2, 13,016 overlaps) | 13.45 h |
| wide-r8-p16-res | 1321 / 68k / 80k | GO | 10.2, 4.2 | built, 300.0 MHz (WNS 0.003); first pod lost after 7.08 h, rerun | 2.21 h |

| id | verdict | evidence |
|---|---|---|
| G1 | 4/5 | STOP→placement fail ✓; RISK→routing fail ✓; GO→built ≥230 MHz for jet-r2-w8 (295.9) ✓ and wide-r8-res (300.0) ✓; GO→routing fail for jet-r4-p16-lat-c5 ✗ |
| G2 | half | core claim held: 5.0 ns HLS target did not change the link outcome (failed routing like jet-r4-p16-lat). Escape clause failed: FF 91k→63k moved it out of RISK, still unroutable → FF does not separate routable from unroutable |
| G3 | held (process memory) | stage 1 7.2–23.0 min (<45), peak 3.5–6.0 GiB (<8); stage 2 process peak 28.2–29.5 GiB (<40); cgroup (process + page cache) reached the 40 Gi limit on wide-r8-p16-res early in link (page cache reclaimed, no OOM; value from mem_link.csv, since this build has no peak_link_bytes.txt after its first pod was lost); link mean cores 3.1–3.7 |
| G4 | held | STOP design reserved 8 Gi × 23 min ≈ 3.1 GiB-h, vs ≈ 74 GiB-h as one 40 Gi job (23 min + 88 min link before placement fail), 118 GiB-h at 64 Gi |

## Card validation of gate builds (sessions ga = k8s-stratix-10-02, gb = prp-gpu-2, Oct 20 04:17 UTC)
- jet-r2-w8-lat and wide-r8-p16-res: bit-exact with hls4ml `predict` on 20,000 test + 2,610 stress inputs on both hosts; ga = gb on every numeric column.
- jet-r2-w8: 295.9 MHz, accuracy 0.75585 (= C-sim), 7.85–7.91 M inf/s. wide-r8-p16-res: 300.0 MHz, accuracy 0.76835 (= C-sim; Keras 0.76955), 4.76–4.84 M inf/s.

Notes
- First 8-bit-weight design to fail routing: wide (16→128→64→5) Latency RF=4 w8. Failing nets are LUT multipliers (mul_16s_5ns/6ns) in the 128→64 layer; csynth LUT 322k. The earlier "w8 or Resource builds" finding holds for jet/big only.
- Routing-failure cost in this round: 9.66 h (gate miss) + 13.45 h (RISK, run on purpose to test the verdict) at 40 Gi.
- Lost pod: wide-r8-res first stage-2 attempt, 7.08 h of link lost (third lost pod of the run week).
