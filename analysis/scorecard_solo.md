# Node-sharing round scorecard (predictions_solo.md, predictions_pair.md; collected Oct 24)

Design: jet RF=4, ap_fixed<16,6>, Resource, SLR2, 3.333 ns, 8 CPU / 40 Gi (same as rw-jet-r4-p16-res).

| build | node (CPU) | ran with | csynth (min) | link (min) | process peak (GiB, min into link) | cgroup peak (GiB) | link mean cores | clock |
|---|---|---|---|---|---|---|---|---|
| rw-jet-r4-p16-res (Oct 18) | nautilus-it-gpu08 (EPYC 9555) | alone | | 62.4 | 29.44 at 5.1 | | | 300 MHz, WNS 0.003 |
| rw-pair1-jet-r4-p16-res | nautilus-it-gpu08 (EPYC 9555) | pair2 (same start, 21:28:07 UTC) | 4.3 | 63.0 | 29.97 at 6.0 | 32.37 | 2.85 | 300 MHz, WNS 0.003 |
| rw-pair2-jet-r4-p16-res | nautilus-it-gpu08 (EPYC 9555) | pair1 | 4.4 | 66.6 | 29.18 at 5.3 | 30.78 | 2.81 | 300 MHz, WNS 0.003 |
| rw-rep / rep2 (Oct 18) | igrok-la (EPYC 7402P) | each other | | 121.0 / 121.9 | 29.67 at 14.2 / 28.50 at 13.3 | | | 300 MHz |
| rw-solo-jet-r4-p16-res | igrok-la (EPYC 7402P) | no build of ours | 4.7 | 119.4 | 27.54 at 11.9 | 30.62 | 3.74 | 300 MHz, WNS 0.003 |

| id | verdict | evidence |
|---|---|---|
| S1 | half | csynth.rpt identical to rw-jet-r4-p16-res except the date line; layers.json identical; C-sim outputs (.npy) not collected |
| S2 | held | link 119.4 min (100–125 predicted); not < 90, so sharing did not cause the 2× gap |
| S3 | failed narrowly | peak 27.54 GiB (28–30 predicted) at 11.9 min into link; 300 MHz, WNS 0.003 ns |
| P1 | held | 63.0 and 66.6 min (55–75 predicted) vs 62.4 alone; both pods on gpu08, links fully overlapped |
| P2 | not triggered | neither link > 90 min |
| P3 | held | 29.97 and 29.18 GiB at 5–6 min; 300 MHz, WNS 0.003 ns |
| P4 | half | csynth.rpt identical except the date line; C-sim outputs not collected |

## Notes
- Conclusion: a second 8-CPU build on the same node lengthened the link by 1–7%; the 62 / 120 / 170 min spread for this
  design is the node. The pair on gpu08 is the direct test; the solo on igrok-la confirms it on the other node.
- Overlap audit (pod start/finish times, results_card_gate.zip): 18 earlier builds shared a node with another of ours
  for 0.2–4.5 h; all gpu08 builds ran alone. With the pair, 20 builds in total.
- Peak timing: across the 13 links with kept memory traces the process peak is 5–46 min into the link
  (the earlier "14–46" omitted rw-jet-r4-p16-res at 5.1 min).
- The solo pod waited ~1 h Pending (igrok-la had < 8 free cores) before starting at 20:51:47 UTC.
