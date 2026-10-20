# Results (draft, Oct 19 — gate round scored)

Numbers come from `score_and_figs.py` (inputs `builds5.csv`, `card_results_session_A/B.csv`); verdicts against the
pre-registered predictions are in `scorecard.md`. Figure numbers are placeholders.

## Setup recap (for the methods section)
35 build directories, all with hls4ml main 8912ed2 (VitisUnified backend, board `alveo-u55c`, XRT driver),
`clock_period=3.333` ns, kernel pinned to SLR2 unless labelled no-SLR. Models: tiny (16→8→5), jet (16→64→32→32→5),
big (16→64→64→32→5), wide (16→128→64→5), cnn (Conv1D). Precisions: `ap_fixed<16,6>` (p16), 8-bit weights and biases with
16-bit everything else (w8; integer bits from max |w|), and all-8-bit `ap_fixed<8,3>` (p8, the smoke build). RF 1–8,
Latency and Resource strategies. Each build is one Kubernetes Job (8 CPU, 64 Gi; 40 Gi for the held-out round) on
node-local scratch. 115.5 build-hours in total; 25 builds produced an xclbin.

## B. Build cost on the shared cluster

**Memory is set by the platform, not the model (Fig. memory).** Peak process memory was 24.5–31.0 GiB for every design
that ran to completion or to a placement/routing failure — tiny to wide, RF 1–8, 8/16-bit, both strategies — and the
cgroup peak (process + page cache) never exceeded 35.6 GiB. The peak was reached in the link stage in all 35 builds.
Across the jet and cnn families the process peak varies by at most 12% from the mean (B5). A 16 Gi request is
OOM-killed during link (B9); the 40 Gi request derived from waves 1–3 was used for the four held-out builds without an
OOM (H1). Accounting charges requested memory × wall time, so 40 Gi instead of 64 Gi reduces the charged GB-hours of
the run-week builds by 35%.

**Link dominates build time; the node sets the link time.** Link is 91–97% of the build wall time of every completed
build (median 95%, B1). Completed links took 56–260 min. Vivado used 2.6–4.4 of the 8 requested cores on average
during link (B7 failed only marginally, on two long failing routes at 4.06 and 4.37). The same design
(jet-r4-p16-res) linked in 62 min on an EPYC 9555 node and 121/122 min on two EPYC 7402P nodes (Fig. link-by-CPU): the
two runs on the same CPU type agree within 0.7%, the cross-node spread is 2× (B10 failed on time, held on memory).
Builds landed on 8 CPU types. A linear predictor of link time from the csynth LUT/FF/DSP estimates misses the held-out
builds by −41% to +150% (B13); the same predictor gives peak memory within 4%. Link time therefore cannot be planned
from the hls4ml report alone on a heterogeneous cluster; memory can.

**Failed builds are the main cost.** 8 builds failed in placement or routing and used 51.5 h, 45% of all build-hours.
Their csynth reports were available 5–30 min into each job.
- *Placement.* jet RF=1 p16 needs 3365 DSPs (csynth) / 3354 (Vivado); the SLR2 dynamic region has 2879
  (`VPL 30-859`). Without the SLR pin the same design placed 3358 DSPs across SLRs and shipped at 248.2 MHz (B14).
  8-bit weights cut the DSP count about 4× (jet RF=1: 3365 → 761) and both RF=1 w8 designs placed in SLR2 (B15 failed).
- *Routing.* Every dense p16 Latency design with RF > 1 except one failed routing (`VPL 35-2` overlaps or
  `VPL 35-3` congestion), pinned or not: jet RF 4/8, big RF 4 (twice), wide RF 4, and the no-SLR jet/big RF 4 follow-ups.
  The exception, held-out jet RF=2, built but at 206.6 MHz (WNS −1.505 ns vs 300 MHz). The same models build with the
  Resource strategy (jet/big RF=4: 300 / 298.5 MHz) or with 8-bit weights (234.8–300 MHz).
- *No single csynth threshold separates routable from unroutable.* The post-hoc RISK region (LUT > 165k and FF > 88k)
  classifies all 33 waves 1–3 + held-out builds except jet RF=2 (Table gate-region), but its FF edge sits between
  85.4k (big RF=1 w8, built) and 88.5k (jet RF=8 p16, failed), a 3.6% margin, and the gate-round design
  jet-r4-p16-lat at 5.0 ns (FF 63k, outside RISK) failed routing. A LUT-only rule at 165k would mark five built designs
  as failures (big w8 at 234.8–281.6 MHz, big p8 at 300 MHz). What the failing designs share is structural: dense
  layers, Latency strategy, 16-bit weights, RF > 1.

**Two-stage gate (pre-registered, 5 new designs).** Stage 1 (2 CPU, 8 Gi) runs generate + csynth + package and
issues STOP (pinned, csynth DSP > 2879), RISK (LUT > 165k and FF > 88k) or GO; stage 2 (8 CPU, 40 Gi) links.
All five designs were linked regardless of verdict, to score the gate.
- Outcomes followed the verdict for 4 of 5 (G1): big-r2-p16 STOP → `VPL 30-859` (3667 DSPs); wide-r4-w8 RISK → routing
  failed (13,016 overlaps); jet-r2-w8 GO → 295.9 MHz; wide-r8-p16-res GO → 300 MHz. The miss: jet-r4-p16-lat at
  `clock_period=5.0` was GO (FF 62.6k) and failed routing (21,338 overlaps).
- The HLS clock target did not change the link outcome (G2): Vitis implements against the 300 MHz platform clock, and
  the 5.0 ns build failed like the 3.333 ns one. Lowering the HLS clock moved the csynth FF estimate out of RISK without
  making the design routable, so FF is a weak routing signal for dense Latency designs.
- jet-r2-w8 (LUT 162.8k, FF 60.8k, built at 295.9 MHz) and jet-r4-p16-lat-c5 (LUT 172.9k, FF 62.6k, failed) have nearly
  the same csynth LUT/FF; they differ in weight precision (8 vs 16 bit) and DSP count (759 vs 1066). Conversely
  wide-r4-w8, 8-bit weights, failed: 8-bit weights did not rescue the wide model (LUT 322k), and RISK caught it where
  the structural rule would not.
- Cost (G3, G4): stage 1 took 7–23 min with peak process memory ≤ 4.9 GiB (cgroup ≤ 5.8 GiB). For the STOP design
  the cluster reserved 0.39 h × 8 Gi (3.1 GiB-h, 0.8 core-h) to reach the verdict, against 1.47 h × 40 Gi
  (58.7 GiB-h, 11.7 core-h) for the link that confirmed it. The gate miss cost 9.66 h × 40 Gi (386 GiB-h); confirming
  the RISK verdict cost 13.45 h × 40 Gi (538 GiB-h). Stage 2 process peaks were 28.2–29.5 GiB; on wide-r8-p16-res the
  cgroup (process + page cache) reached the 40 Gi limit during early link and was reclaimed without an OOM — the first
  build in which page cache pressed against the request.
- Stage-2 link times again tracked the node: 88–134 min on EPYC 7402P/7F72, 580 min (failing) on Xeon E5-2698 v4,
  807 min (failing) on Xeon Silver 4116. wide-r8-p16-res's first stage-2 pod was lost and rerun; the 132.8 min is the
  rerun.

**Kernel clock.** 15 of 25 built designs met 300 MHz; the rest shipped at 206.6–298.5 MHz via the U55C's scalable
clock. Pinning to SLR2 is not uniformly better: jet-r4-w8-lat shipped at 259.0 MHz pinned and 300 MHz unpinned
(post hoc, B12).

## C. Validation with minimal card time

All 25 run-week builds and the 2 gate-round builds that produced an xclbin (27 designs) were run on two different U55C
hosts (session A k8s-stratix-10-02, session B prp-gpu-2; gate builds in sessions ga/gb on the same two hosts) against
20,000 test inputs and 2,610 stress inputs (×16 overflow, zeros, tiny values, uniform ±50, ±Inf/NaN).
- Hardware output equals hls4ml `predict` (C-sim) bit for bit on every row of both sets, for every design, in both
  sessions (C1–C3). Every accuracy, agreement and clock value is identical between sessions (C7).
- Card accuracy equals C-sim accuracy for every design (C8), including the all-8-bit collapse (jet 0.3226, big 0.3977
  vs Keras 0.7671). Accuracy problems are therefore visible from `predict` before synthesis; the card adds no accuracy
  information beyond confirming bit-exactness.
- Hardware–Keras argmax agreement: 0.9876–0.9923 for p16, 0.8998–0.9441 for w8, 0.335/0.416 for all-8-bit (C4).
- What the card adds: the achieved clock (above), xclbin load 7.2–9.5 s (C6 predicted ≤ 2 s; reload of a loaded
  xclbin 0.08–0.14 s), single-call latency 64–107 µs, and time per input falling 104–1016× from batch 1 to batch 10,000
  (C5; Fig. batch sweep), for 1.2–12.3 M inferences/s. Total card time per design is ≤ 9.5 s, dominated by the load;
  the whole session for 35 designs (incl. 10 without an xclbin) took 4 min; the gate session (5 designs, 2 with an
  xclbin) took 20 s per host. Gate builds on the card: jet-r2-w8 295.9 MHz, 7.85–7.91 M inf/s; wide-r8-p16-res
  300 MHz, 4.76–4.84 M inf/s, accuracy 0.76835 (Keras 0.76955), both bit-exact on both hosts.

## Open items before the draft
- Lost first stage-2 pod of wide-r8-p16-res: its wall time is not in the pod records (≤ 7.1 h from the stage log);
  get it from the accounting MCP so the gate-round cost total is complete.
- Recheck NRP accounting for ho-wide-r4 and noslr-big-r4 (likely past the Oct 18 cutoff) and ingest card/gate pods.
