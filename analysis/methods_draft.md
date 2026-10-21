# Methods (draft, Oct 20) + discussion guidance table + limitations

Placeholders in [brackets]. Commit hashes refer to `anishbhat28/hls4ml_shared_cluster` unless marked hls4ml.

## 2 Methods

### 2.1 Toolchain and design flow
All designs are generated with unmodified hls4ml main (commit 8912ed2) using the VitisUnified backend with
`board='alveo-u55c'` and `driver='xrt'` (Alveo support added in hls4ml PR #1573). HLS synthesis and the system link
use Vitis/Vivado 2024.2 (`v++ v2024.2`) from the cluster's shared tools volume, targeting the platform
`xilinx_u55c_gen3x16_xdma_3_202210_1`. The HLS clock target is `clock_period=3.333` ns (300 MHz, the platform kernel
clock) unless stated; one gate-round design uses 5.0 ns. The kernel is placed in SLR2 by a `slr=` connectivity line
(`kernel_slr='SLR2'`), next to the HBM-adjacent... [check wording: SLR0 holds the HBM; SLR2 pin chosen in PR #1573
for timing]; designs labelled no-SLR omit the line.

### 2.2 Design matrix
Five Keras models trained on the hls4ml jet-tagging dataset (16 inputs, 5 classes): tiny (16→8→5), jet
(16→64→32→32→5), big (16→64→64→32→5), wide (16→128→64→5) and a Conv1D model (cnn). Settings: ReuseFactor 1, 2, 4, 8;
strategy Latency or Resource; three precisions: `ap_fixed<16,6>` everywhere (p16); 8-bit weights and biases with
integer bits set from max|w| per model (`ap_fixed<8,2>` jet/big/wide, `ap_fixed<8,3>` cnn) and 16-bit activations
(w8); and `ap_fixed<8,3>` everywhere (p8, the smoke-test configuration). RF values were restricted to those hls4ml
accepts for every layer of the model [one sentence on the RF validity rule]. The matrix (waves 1–3, 29 builds incl.
three repeats, one undersized-memory build and five no-SLR follow-ups), a held-out round (4 builds) and a gate round
(5 builds) are listed in Table [builds].

### 2.3 Running builds on the shared cluster
Each build is a Kubernetes Job in namespace `hls4ml-nrp` on the NRP Nautilus cluster, requesting equal requests
and limits (8 CPU, 64 Gi in waves 1–3; 40 Gi for the held-out and gate rounds; 16 Gi for the undersized test). The
Vivado working tree lives on node-local `emptyDir` scratch (10 Gi); only reports, logs and the xclbin are copied to
a CephFS volume (`/work/rw`). Jobs were submitted by a small in-cluster queue (a Job with a namespace-scoped
ServiceAccount that keeps N builds running), so no workstation had to stay connected. Nodes were not selected:
builds ran wherever the scheduler placed them (8 CPU models across [n] hosts). At most 6 links ran concurrently;
no licence errors occurred.

The gate round splits a build into two Jobs. Stage 1 (2 CPU, 8 Gi) runs hls4ml `write`, C-simulation, csynth and
packaging, then reads the csynth report and writes a verdict: STOP if the kernel is SLR-pinned and the csynth DSP
estimate exceeds the 2879 DSPs of the SLR2 dynamic region, RISK if LUT > 165k and FF > 88k, else GO. Stage 2
(8 CPU, 40 Gi) unpacks the packaged kernel and runs the link only. For scoring, all five stage-2 Jobs were run
regardless of the verdict.

### 2.4 Instrumentation
Each Job writes `stages.csv` (UNIX time at the start of each hls4ml/Vitis stage) and samples the pod cgroup every
15 s into `mem.csv`: `memory.current` (process + page cache, "cgroup"), the `anon` field of `memory.stat`
("process"), and `cpu.stat usage_usec` (mean cores = Δusage/Δt over the link). Vivado step times, routed timing
(WNS) and utilisation come from the implementation reports; the achieved kernel clock from `xclbinutil --info`.
Job logs and pod records (node, start/finish, termination reason) are saved by `collect.sh` within a day of
completion, since finished Jobs are removed by the cluster after about a day [cite Daniel / docs].
Independently, NRP's accounting service (queried 2026-10-19 and 2026-10-20 [and final date]) records per-pod
requested CPU and memory × wall time; its wall time matches our logs within 6% for 32 of 35 run-week builds
(total 117.8 h vs 115.5 h; exceptions explained by a lost pod and 5-min sampling).

### 2.5 Card validation
Each xclbin is loaded on a U55C through XRT's Python bindings in a fresh process per design (so the device is
released between xclbins). Inputs: 20,000 test-set jets and 2,610 stress inputs (inputs ×16 to force overflow,
zeros, values near zero, uniform ±50, ±Inf/NaN). Outputs are compared element-wise with hls4ml `predict` (C-sim)
for the same inputs, computed before synthesis and stored with the build; we report the fraction of rows that are
bit-identical and the maximum absolute difference. We also record xclbin load and reload time, single-call latency
and per-input time at batch 1–10,000. Every built design was validated in two sessions on two different U55C hosts
(k8s-stratix-10-02 and prp-gpu-2) [host XRT versions per NRP docs: 2.16.204 and 2.19.194 — confirm from xbutil];
the gate-round builds in sessions ga/gb on the same two hosts. Card jobs request 4 CPU, 16 Gi and one FPGA.

### 2.6 Pre-registration
Predictions for every build and card measurement were committed before the corresponding jobs started: waves 1–3
(727bff3), amendments for the 8-bit-weight change (ada1c54), repeats (amendment 2) and post-hoc no-SLR follow-ups
(amendment 3, labelled post hoc), the held-out round [hash], and the gate round (4a5c8a5, 2026-10-19 00:38:58 PT).
Each result is scored against its prediction (Tables [B], [C], [H], [G]). Rules derived after seeing data are marked
post hoc.

### 2.7 Data and code
Job templates, queue, collection and analysis scripts, raw logs, reports and CSVs: tag `data-freeze-2` [Zenodo DOI].
Note on one build: `rw-jet-r1-p8-lat` was stopped when the all-8-bit configuration was superseded; `rw-big-r1-p8-lat`
had completed before the stop and is kept, but its Job log was not collected.

## 5 Discussion — guidance table (draft)

| guidance | evidence | status |
|---|---|---|
| Request 8 CPU / 40 Gi for a U55C link, any hls4ml model tested | process peak 24.5–31.0 GiB in link for all 40 builds; 40 Gi held for 9 builds (H1, G3); 16 Gi OOM; link uses 2.6–4.4 cores | pre-registered (B5, B9, H1, H2, G3) |
| Expect page cache to fill the request | cgroup reached 40 Gi on wide-r8-p16-res (reclaimed, no OOM) | observed once |
| Split csynth from link; STOP if pinned and csynth DSP > 2879 | 2/2 STOP/DSP cases failed placement; STOP verdict costs 0.4 h × 8 Gi vs 1.5 h × 40 Gi for the failing link | pre-registered (B14, G1) |
| Treat dense Latency + 16-bit weights + RF > 1, or LUT > 165k ∧ FF > 88k, as routing risk | 8/9 and 7/8 correct on waves 1–3 + held-out; misses: jet-r4-p16-lat at 5 ns (GO, failed), wide-r4-w8 (structural rule misses), jet-r2-p16 (built at 206.6 MHz) | post hoc, incomplete |
| Lowering the HLS clock does not rescue routing | jet-r4-p16-lat at 5.0 ns failed like 3.333 ns | pre-registered (G2) |
| Use Resource strategy or 8-bit weights for dense jet/big at RF ≥ 2 | all such builds routed (234.8–300 MHz); not wide | observed |
| Don't plan by link time from csynth; plan by node | same design 62 vs 121 min across CPU types; predictor −41 % to +150 % | pre-registered (B10, B13) |
| Validate with `predict` + one short card session | 27/27 bit-exact on two hosts; card accuracy = C-sim; ~10 s card time per design, 0.17 card-h for 25 designs | pre-registered (C1–C8) |
| Collect logs within a day | finished Jobs removed after ~1 day | operational |

Cost context (Fig. cost): 47 % of the memory NRP charged for all build pods went to routing failures (73.4 h),
48 % to builds that produced an xclbin, 1.7 % placement failures, 1.3 % two lost pods (both on ucm-fiona01).

## Limitations (draft)
One card type (U55C, one shell), one Vitis release (2024.2) and one hls4ml commit; five small models from one
dataset. Each rule rests on few cases: the RISK thresholds were fitted on 33 builds and tested on 5. Build nodes
were not controlled, so link time mixes design and node effects; we report pairs on matched designs instead of a
fitted node term. Two pods were lost to node failures and rerun; their charged time is counted separately. The
accounting service records requested, not used, resources. The validation compares hardware with hls4ml's own
C-simulation; it shows the deployment preserves `predict` exactly, not that `predict` matches Keras (it does not
for 8-bit configurations).
