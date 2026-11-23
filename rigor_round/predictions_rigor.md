# Predictions — rigor round (rg-*), written before any job runs

Commit this file (git add/commit/push) BEFORE `./launch.sh phase1`. Every design below was built in the run week with the
same hls4ml wheel (8912ed2), models, data, Vitis/Vivado 2024.2 (xilinx-tools PVC), 8 CPU / 40 Gi, 3.333 ns.
Differences from the run week: the vivado-vitis image has been rebuilt since (digest recorded per pod by collect.sh);
the libudev stub now comes from the image (/opt/udev-stub via `with-udev-stub`, per tool command) instead of /work/fakelib, and the image is pinned by digest; `quantizers<2` is pinned (2.0 breaks hls4ml 8912ed2).

## R — does routing failure survive a congestion-oriented implementation strategy?

Three designs that failed routing in the run week, relinked with
`--vivado.prop run.impl_1.strategy=Congestion_SpreadLogic_high`, SLR2, on any node except the three used below.
Run-week outcomes: jet-r4-p16-lat failed 3 times (SLR2 438 min; unpinned 585 min; 5.0 ns 9.7 h),
jet-r8-p16-lat failed once (339 min), big-r4-p16-lat failed twice on different CPUs (274 min, 95 min).

| id | prediction | confidence |
|---|---|---|
| R1 | HLS reports (csynth) of all three identical to the run-week builds of the same design, apart from dates | medium (image rebuilt) |
| R2 | strategy_check.txt shows Congestion_SpreadLogic_high was applied to impl_1 | high |
| R3 | All three fail routing again | medium |
| R4 | If any routes, it is jet-r8-p16-lat (lowest LUT estimate of the three, 168k), at < 250 MHz | low |
| R5 | Peak process memory 27–33 GiB for each, in the first 60 min of the link | high |

## T — the link time limit on the slowest node type (nautilus-it-cpu03, Xeon E5-2697 v3), one job at a time

T1 big-r4-w8-res (built in 242.6 min on an EPYC 7551P, 293.9 MHz). T2 noslr-jet-r1-p16-lat, the slowest successful
link of the study (259.7 min on this same node, 248.2 MHz). T2 starts only after T1 has finished.

| id | prediction | confidence |
|---|---|---|
| T1a | T1 builds, in 270–380 min, i.e. above the 270 min limit proposed in the paper | medium |
| T1b | T1 achieved clock and WNS identical to the run-week build (Vivado deterministic for identical inputs and thread count, across CPU types) | medium |
| T2a | T2 builds, link within ±10% of 259.7 min (234–286 min) | medium |
| T2b | T2 achieved clock and WNS identical to the run-week build (248.2 MHz) | medium-high |

## N — node sharing at higher density and on a third CPU type

jet-r4-p16-res (run-week links: 62.4 min alone and 63.0 / 66.6 min as a pair on nautilus-it-gpu08, EPYC 9555;
119.4 alone and 121.0 / 121.9 as a pair on igrok-la, EPYC 7402P; 170.2 min alone on a Xeon E5-2698 v4).

| id | prediction | confidence |
|---|---|---|
| N1 | Four copies started together on nautilus-it-gpu08: every link 62–75 min (at most +20% over the solo build) | medium |
| N2 | Two copies started together on chi-dgx-node02 (Xeon E5-2698 v4): every link 150–200 min | medium |
| N3 | All six built at 300 MHz, WNS ≥ 0, with identical routed results within each group | medium |
| N4 | Peak process memory 28–31 GiB for each | high |

## Card (rg-card, after all builds)

| id | prediction | confidence |
|---|---|---|
| K1 | Every new bitstream equals its own C-simulation bit for bit on 20,000 test and 2,610 stress inputs | high |
| K2 | C-simulation outputs of every repeat identical to the run-week C-simulation of the same design | high |

## Memory cross-check (all builds, exploratory)

| id | prediction | confidence |
|---|---|---|
| M1 | Vivado's largest logged "peak =" value is within ±15% of the 15-s cgroup anon peak of the same job | low (exploratory) |

Other users' pods on the pinned nodes cannot be controlled; `kubectl describe node` snapshots are saved at each launch.
