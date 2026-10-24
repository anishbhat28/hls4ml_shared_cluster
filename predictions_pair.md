# Predictions - node-sharing pair (written before rw-pair1/rw-pair2 run)

Question: does a second build on the same node slow the link? Baseline: rw-jet-r4-p16-res ran alone on
nautilus-it-gpu08 (AMD EPYC 9555), link 62.4 min. The rep pair on igrok-la (EPYC 7402P) ran together: 121.0 / 121.9 min.
Design: jet RF=4 16-bit Resource SLR2, 8 CPU / 40 Gi, same as the baseline. Both pods pinned to nautilus-it-gpu08 and started together.

| id | prediction | confidence |
|---|---|---|
| P1 | Both links 55-75 min (sharing a node does not slow the link; the 121 min on igrok-la is the CPU) | medium |
| P2 | If either link is > 90 min, sharing a node slows the link and the 62 vs 121 min comparison is confounded | - |
| P3 | Peak process memory 28-30.5 GiB, in the first 60 min of the link; both built at 300 MHz | high |
| P4 | HLS reports and C-sim identical to rw-jet-r4-p16-res | high |

The test counts only if both pods ran on nautilus-it-gpu08 and their links overlapped for >= 45 min; otherwise it is reported as not run.
