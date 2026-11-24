# Predictions — wa-hls4ml exemplar round (wa-*), written before any job runs

Commit this file and the whole folder BEFORE `./launch_wa.sh prep`.

**Sample.** `sample_wa.py` (seed 20261124) on `exemplar_models.json` (sha256 1fc8c355…, wa-hls4ml HuggingFace dataset).
Frame: 6 scientific models × 18 hls4ml configurations (precision 2/8/16 bit × RF 1/128/1024 × Latency/Resource) = 108.
BiPC excluded before drawing (residual Add layers whose inputs the flat layer list does not give). 2 configurations per
model drawn uniformly → 12 designs (`wa_sample.json`). Weights: fixed-seed random (no trained weights in the dataset);
inputs: 2,000 N(0,1) rows + 520 stress rows (zeros, ×50, ±1000, ±Inf, NaN). Hashes in /work/wa/manifest.json.

**Build.** Same as the run week except: two stages (s1 convert + HLS + package + gate at 1 CPU / 6 Gi; s2 link at
8 CPU / 40 Gi; s3 card at 1 CPU / 4 Gi + 1 U55C), image vivado-vitis@sha256:92345d9a… with `with-udev-stub`,
hls4ml 8912ed2 + quantizers<2, Vitis 2024.2, 3.333 ns, kernel pinned to SLR2, io_stream. No time limits (safety: 2 days
per stage). Batch 1 and batch 2 of 6 designs each, so at most 6 links run at once.

| id | prediction | confidence |
|---|---|---|
| W1 | Every design that reaches the link peaks at 24.5–32 GiB process memory (anon), in the first hour of the link | high |
| W2 | Stage 1 (1 CPU / 6 Gi) never runs out of memory | high |
| W3 | The DSP gate (csynth-report DSP count vs. the 2,879 DSPs of SLR2): no design that passes it fails placement for lack of DSPs | high |
| W4 | The three Resource designs whose RF exceeds their smallest layer input width (anomaly-r1024-res, jet-r1024-res, cookie-r128-res) take ≥10× the median HLS time of the other designs, or do not finish HLS | medium |
| W5 | Every design whose csynth LUT estimate is ≤ 165k routes (pre-registered test of the post-hoc LUT rule) | medium-high |
| W6 | The two small Latency / 16-bit / RF>1 designs (quarks-r128-p16-lat, automlp-r1024-p16-lat) route: the routing-failure rule depends on layer size, not the setting alone | medium |
| W7 | At most 2 of the 12 fail routing; if any does, it is wa-anomaly-r1-p16-lat | low |
| W8 | Every bitstream equals its own C-simulation bit for bit on all 2,520 inputs | high |
| W9 | Every successful link takes 0.8–4.5 h | medium |
| W10 | wa-particle-r1-p2-res (2-bit) builds with 0 DSPs | high |

Outcomes are recorded per design as gate_stop / s1_error (incl. HLS never finishing) / place_fail / route_fail / ok,
with the HLS time, link time, peak memory and, for built designs, clock and bit-exactness.
