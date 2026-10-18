# Amendment 3 — follow-up builds after the routing failures (post hoc, not pre-registered)

## What happened (waves 1–3, kernel pinned to SLR2)
- `rw-big-r4-p16-lat` and its repeat `rw-rep-big-r4-p16-lat`: `[VPL 35-3] Design is not routable as its global
  congestion level is 7` — same failure in both runs (after ~11 h and ~3.7 h).
- `rw-jet-r4-p16-lat`: routing finished with 79,957 node overlaps (`[VPL 35-2] not legally routed`).
- `rw-jet-r8-p16-lat`: routing finished with 211,595 node overlaps.
- The same models with the Resource strategy at RF=4 (`jet-r4-p16-res`, `big-r4-p16-res`) built in 67 and 175 min,
  and the same models with 8-bit weights and the Latency strategy (`big-r4-w8-lat`) built.
- `rw-big-r1-w8-lat` built in 179 min; B15 (predicted placement failure in SLR2) failed.
- `rw-under-jet-r4-p16-res` was OOM-killed in link (B9 held).

## Follow-up builds
Two builds are added to test whether the routing failures come from pinning the kernel to SLR2:
- `rw-noslr-jet-r4-p16-lat`, `rw-noslr-big-r4-p16-lat` (same designs, `kernel_slr=False`).

These are exploratory: they were added after seeing the failures and are reported as such, not as tests of the
pre-registered predictions.
