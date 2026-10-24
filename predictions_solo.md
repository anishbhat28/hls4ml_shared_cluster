# Prediction — solo repeat on igrok-la (written before the job runs)

Purpose: the two earlier builds of jet-r4-p16-res on igrok-la (AMD EPYC 7402P; 121.0 and 121.9 min link) ran at
the same time as each other and as other builds on that node. The 62.4 min (EPYC 9555) and 170.2 min (Xeon
E5-2698 v4) builds ran alone. This build repeats the same design on igrok-la with no other job of ours running,
to separate the CPU-type effect from co-tenancy. Same job as rw-rep-jet-r4-p16-res (jet, RF=4, ap_fixed<16,6>,
Resource, SLR2, 3.333 ns, 8 CPU / 40 Gi), pinned to igrok-la.cenic.net.

| id | prediction | confidence |
|---|---|---|
| S1 | HLS reports, link config and C-sim outputs identical to the four earlier builds of this design | high |
| S2 | Link time 100–125 min: co-tenancy inflated the earlier pair by less than 20%, and the 2× gap to the EPYC 9555 is mostly the CPU type. If instead < 90 min, co-tenancy accounted for most of the gap | medium |
| S3 | Process peak 28–30 GiB, in the first 60 min of the link; built at 300 MHz, WNS ≥ 0 | high |

Other users' pods on the node cannot be controlled; pod records and `kubectl top node` at start are saved for context.
