# Larger-model round scorecard (predictions_large.md, commit 7959fc1; collected Oct 23)

Model `large`: 16→256→256→128→5, 103,685 parameters, 16-bit, Resource strategy, 8 CPU / 40 Gi.

| build | node CPU | HLS synthesis | link | outcome |
|---|---|---|---|---|
| rw-large-r16-p16-res (unpinned) | AMD EPYC 9555 | 21.1 min, peak 4.5 GiB; estimate 6,441 DSP (71% of device) / 232k LUT / 301k FF | 156.6 min | routing failed: VPL 35-3, global congestion level 7 |
| rw-large-r64-p16-res (SLR2) | AMD EPYC 7742 | did not finish in 11.4 h (1.0 core, peak 2.8 GiB); stopped by hand | — | no bitstream |

| id | verdict | evidence |
|---|---|---|
| L1 | held | Keras test accuracy 0.7672 vs big 0.7638 on the same full test set (the 20k-subset value needs a card run; none built) |
| L2 | not testable | r64 never produced an HLS report |
| L3 | held | r16 estimate 6,441 DSPs (6,000–6,700 predicted) > 2,879 → STOP if pinned |
| L4 | half | r16: 21 min, 4.5 GiB; r64: > 11.4 h |
| L5 | failed narrowly | r16 process peak 33.35 GiB (25–33 predicted), reached 12 min into the link (within the first hour, as predicted); but placement/routing ran at ~25 GiB, not < 20 GiB. Cgroup peak 38.5 GiB of the 40 Gi limit |
| L6 | failed | r64 never left HLS synthesis |
| L7 | failed | r16 routing congestion (first Resource-strategy routing failure) |
| L8 | not testable | no completed build |
| L9 | not testable | no completed build |

## Notes
- Memory peak: 33.35 GiB vs 24.5–31.0 GiB for all earlier builds (+8% over the previous maximum) for a design using
  71% of the device's DSPs; the early-link peak pattern holds, but placement/routing memory rose from 14–17 GiB to ~25 GiB.
  The 40 Gi request left 1.5 GiB of headroom on the cgroup peak.
- RF=64 exceeds the first layer's input width (16), so hls4ml used its `dense_resource_rf_gt_nin_rem0` implementation
  for that layer (the other layers and every RF=16 layer use `dense_resource_rf_leq_nin`). HLS synthesis then ran
  11.4 h at one core without finishing. Which part stalled is not known from the log.
- Data retrieval: the full work_rw.tgz stream broke repeatedly (kubectl exec EOF); the scoring files were fetched one by one.
