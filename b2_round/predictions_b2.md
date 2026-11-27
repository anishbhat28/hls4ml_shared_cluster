# Predictions — batch 2 (b2), written before any job runs

Commit this folder (git add/commit/push) BEFORE `./launch_b2.sh prep`. Verdicts go in scorecard_b2.md afterwards.

## Setup (what is the same as before, what differs)

Same as the wa-hls4ml round unless a group says otherwise: image vivado-vitis@sha256:92345d9a… with `with-udev-stub`,
hls4ml 8912ed2 wheel + quantizers<2, Vitis 2024.2, U55C platform xilinx_u55c_gen3x16_xdma_3_202210_1, 3.333 ns,
kernel pinned to SLR2, io_stream, three Jobs per design (s1 1 CPU / 6 Gi; s2 8 CPU / 40 Gi; s3 1 CPU / 4 Gi + 1 U55C).

New for every batch-2 Job:
- **Stage-1 retry rule (decided now):** a stage 1 that is OOMKilled at 6 Gi is rerun once at 1 CPU / 16 Gi.
  Stage 1 has a 12 h limit (activeDeadlineSeconds); a stage 1 that hits it counts as "HLS did not finish".
- **No link time limit is enforced** (safety net 2 days), so that B2 below can be scored.
- Stage-2 logging adds node load (/proc/loadavg every 15 s) and a fixed single-thread CPU benchmark before the link.

Groups:

| group | designs | differs from the setup above |
|---|---|---|
| wa2 (12) | batch 2 of the random sample (`sample_b2.py`, seed 20261126, same frame as batch 1, batch-1 designs excluded before drawing) | models/inputs in /work/wa2, fixed-seed random weights as in batch 1 |
| hm (3) | jet-r4-p16-res, jet-r4-p16-lat, wa-quarks-r1-p16-lat | hls4ml upstream main 4073cfdd (Nov 26 2026) instead of 8912ed2 |
| v23 (3) | same three | Vitis/Vivado 2023.2 for HLS and link |
| v25 (3) | same three | Vitis/Vivado 2025.2 for HLS and link |
| u250 (3) | jet-r4-p16-res, big-r4-w8-res, wa-quarks-r1-p16-lat | Alveo U250, platform xilinx_u250_gen3x16_xdma_4_1_202210_1, kernel in SLR0, hls4ml with DDR board support (fork commit 3a25f70; upstream review pending), gate STOP above 85% of SLR0's 3,032 DSPs, no card stage |

Run-week reference outcomes for the repeated designs (hls4ml 8912ed2, Vitis 2024.2, U55C): jet-r4-p16-res built at
300 MHz in all 9 builds; jet-r4-p16-lat failed routing in all 4 attempts; wa-quarks-r1-p16-lat built at 300 MHz.
DDR reference (Nov 2026, 8 CPU / 64 Gi, cgroup memory incl. page cache only): U250 links 299–331 min, peak 31.6–35.3 GiB;
U200 link 192 min, 32.2 GiB.

## Random sample, batch 2 (wa2)

| id | prediction | confidence |
|---|---|---|
| B1 | Every U55C link in batch 2 (all groups except u250) peaks at 24.5–32 GiB process memory (anon) | high |
| B2 | No successful link in batch 2 takes longer than 6.5 h (the time limit proposed in the paper) | medium |
| B3 | Every link whose HLS LUT estimate is ≤ 165k routes | high |
| B4 | Every bitstream tested on a card equals its own C-simulation bit for bit on all test and stress inputs | high |
| B5 | Stage 1: at most 2 of the 12 random designs need the 16 Gi retry, and none hits the 12 h limit | medium |
| B6 | The slowest stage 1 of the 12 is one of the two anomaly designs (anomaly-r1024-p8-res, anomaly-r128-p2-res) | medium |
| B7 | Each of the six 2-bit designs has a DSP estimate of ≤ 10 | high |
| B8 | No random design is stopped by the gate (all DSP estimates far below 2,879) | high |
| B9 | At most 1 of the 12 random designs fails routing | medium |
| B10 | Exploratory: across all batch-2 links that built, link time and the CPU benchmark time are positively rank-correlated (Spearman ρ ≥ 0.5) | low |

## Toolchain variations (hm, v23, v25)

| id | prediction | confidence |
|---|---|---|
| T1 | hls4ml main runs in the same Job without changes (stage 1 completes for all three) | medium |
| T2 | With hls4ml main, each design has the same outcome as with 8912ed2 (built / routing failed) | medium-high |
| T3 | Vitis 2023.2 runs hls4ml 8912ed2's VitisUnified flow unchanged (stage 1 completes) | medium |
| T4 | Vitis 2025.2 runs it unchanged (stage 1 completes) | low-medium |
| T5 | Where a toolchain runs, each design has the same outcome as with 2024.2; jet-r4-p16-lat fails routing with every toolchain | medium |
| T6 | Every link in these groups peaks at 24.5–32 GiB process memory (part of B1) | medium |

## Second platform (u250)

| id | prediction | confidence |
|---|---|---|
| U1 | All three U250 designs build (no placement or routing failure) | medium |
| U2 | Every U250 link peaks at 24.5–32 GiB process memory, the same band as the U55C | medium |
| U3 | The three U250 peaks are within ±7% of each other (designs with ~280 to ~1,830 estimated DSPs) | medium |
| U4 | Every U250 link takes 2.5–6.5 h | medium |

Outcomes are recorded per design as gate_stop / s1_error / place_fail / route_fail / ok / built_no_card, with HLS time
and peak memory (including any 16 Gi retry), link time, link peak memory, node load and CPU benchmark, clock and,
for card-tested designs, bit-exactness.
