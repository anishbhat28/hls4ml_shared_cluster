# Amendment 2 to predictions_v1 (before the repeat and undersized builds start)

## What happened
`rw-jet-r1-p16-lat` (jet, RF=1, ap_fixed<16,6>, kernel pinned to SLR2) failed in placement after ~64 min of link:
`[VPL 30-859]` — 3354 DSPs required in `pblock_dynamic_SLR2`, 2879 available. This design cannot be built with the
kernel pinned to one SLR. It is kept as a result (failed build: time and resources spent before the failure).

## Change
The repeat builds and the undersized build were planned on jet-r1-p16 and would fail the same way, which gives neither
a spread of completed builds nor a memory-limit failure. They are moved to `jet-r4-p16-res`, which completed (67 min):
- `rw-rep-jet-r4-p16-res`, `rw-rep2-jet-r4-p16-res` (with the original: 3 runs of the same design)
- `rw-under-jet-r4-p16-res` (memory limit 16 Gi)

## Predictions affected
- B9 now refers to `rw-under-jet-r4-p16-res`: it is OOM-killed, during link.
- B10 now refers to the three jet-r4-p16-res runs: link time within ±15% of their mean; peak memory within ±5%.
- New, B14: designs whose csynth DSP estimate exceeds the DSPs available to the dynamic region of one SLR (2879)
  fail placement when the kernel is pinned to that SLR, and build without the pin if they fit the whole device.
  The `noslr-jet-r1-p16` build tests the second half.
- New, B15: the jet and big RF=1 builds with 8-bit weights also fail placement in SLR2 (8×16-bit products still map to
  one DSP each, so the DSP count does not drop).
