#!/bin/bash
# Writes the build Job files. Run on your Mac, in the folder with job-rw-build-TEMPLATE.yaml.
#   ./make_builds.sh            -> waves 1-3 (26 files)
#   ./make_builds.sh heldout    -> wave 4, the held-out designs (run Sunday Oct 18, after writing predictions)
# hls4ml main 8912ed2 (Alveo support merged in #1573), used unmodified: board='alveo-u55c', driver='xrt'.
# kernel_slr: board default SLR2; 'none' below = kernel_slr=False. clock_period=3.333 (jet tagger ships at 237 MHz).
CLK=3.333 # HLS clock period in ns
# Default job size. NRP policy: memory use must stay within 20-150% of the request and CPU use within 20-200%,
# so after the smoke test set these from its measured peak (I'll tell you the numbers), then rerun this script.
MEM_DEFAULT=64Gi
CPU_DEFAULT=8
DISK_DEFAULT=10Gi   # node-local scratch per build; smoke build used 1.67 GB
# 8-bit weights/biases (16-bit everything else). Integer bits from the largest |weight| of each model (csimcheck2):
# jet max|w| 1.28, big 1.39 -> ap_fixed<8,2> (range +-2); cnn max|w| 2.35 -> ap_fixed<8,3> (range +-4)
w8() { case $1 in cnn|tiny) echo w8i3;; *) echo w8i2;; esac; }
UNDER_MEM=16Gi   # the deliberately undersized build: set to ~0.6 x the smoke-test peak

mk() {  # name model rf precision strategy [memory] [kernel SLR: default SLR2, "none" = no slr= line]
  sed -e "s|__NAME__|$1|g" -e "s|__MODEL__|$2|g" -e "s|__RF__|$3|g" \
      -e "s|__PREC__|$4|g" -e "s|__STRAT__|$5|g" -e "s|__CLK__|$CLK|g" \
      -e "s|__MEM__|${6:-$MEM_DEFAULT}|g" -e "s|__CPU__|$CPU_DEFAULT|g" -e "s|__DISK__|$DISK_DEFAULT|g" -e "s|__SLR__|$( [ "${7:-SLR2}" = none ] && echo "" || echo "${7:-SLR2}" )|g" \
      job-rw-build-TEMPLATE.yaml > "job-$1.yaml"
  echo "wrote job-$1.yaml"
}

if [ "$1" = "heldout" ]; then
  # wave 4: designs NOT in the main matrix, used to test the guidance.
  # Memory request 40Gi = the guidance derived from waves 1-3 (max anon 31.0 GiB, max cgroup 35.6 GiB), not 64Gi.
  mk rw-ho-jet-r2-p16-lat  jet  2 'ap_fixed<16,6>' Latency 40Gi
  mk rw-ho-big-r2-w8-lat   big  2 "$(w8 big)"      Latency 40Gi
  mk rw-ho-cnn-r2-p16-lat  cnn  2 'ap_fixed<16,6>' Latency 40Gi
  mk rw-ho-wide-r4-p16-lat wide 4 'ap_fixed<16,6>' Latency 40Gi
  exit 0
fi

# waves 1 and 2: dense models, 12 designs
for m in jet big; do
  # big at RF=1, 16-bit is NOT built: the PR timing runs already showed it fails placement in SLR2
  # (Place 30-859, after ~14 h) and takes >22 h without the SLR pin (timing-bigslr2 / timing-bignoslr).
  [ $m = jet ] && mk rw-$m-r1-p16-lat $m 1 'ap_fixed<16,6>' Latency
  mk rw-$m-r1-w8-lat  $m 1 "$(w8 $m)"           Latency
  mk rw-$m-r4-p16-lat $m 4 'ap_fixed<16,6>' Latency
  mk rw-$m-r4-w8-lat  $m 4 "$(w8 $m)"           Latency
  mk rw-$m-r4-p16-res $m 4 'ap_fixed<16,6>' Resource
  mk rw-$m-r4-w8-res  $m 4 "$(w8 $m)"           Resource
done
mk rw-jet-r8-p16-lat jet 8 'ap_fixed<16,6>' Latency   # third RF point for the scaling trend
mk rw-tiny-r1-p16-lat tiny 1 'ap_fixed<16,6>' Latency # build-cost floor (platform/shell cost)

# wave 3: second hls4ml code path (conv), repeats for error bars, one deliberately undersized build
mk rw-cnn-r1-p16-lat cnn 1 'ap_fixed<16,6>' Latency
mk rw-cnn-r1-w8-lat  cnn 1 "$(w8 cnn)"           Latency
mk rw-cnn-r4-p16-lat cnn 4 'ap_fixed<16,6>' Latency
mk rw-cnn-r4-w8-lat  cnn 4 "$(w8 cnn)"           Latency
mk rw-cnn-r8-p16-lat cnn 8 'ap_fixed<16,6>' Latency
# repeats: 3 runs of jet-r4-p16-res in total (the original + 2) -> spread. jet-r1-p16 cannot be placed with the kernel in SLR2.
mk rw-rep-jet-r4-p16-res  jet 4 'ap_fixed<16,6>' Resource
mk rw-rep2-jet-r4-p16-res jet 4 'ap_fixed<16,6>' Resource
mk rw-rep-big-r4-p16-lat  big 4 'ap_fixed<16,6>' Latency
mk rw-under-jet-r4-p16-res jet 4 'ap_fixed<16,6>' Resource $UNDER_MEM

# wave 3b: same designs with the OTHER link configuration (no SLR placement), to show which results depend on it
mk rw-noslr-jet-r1-p16-lat jet 1 'ap_fixed<16,6>' Latency "" none
mk rw-noslr-jet-r4-w8-lat  jet 4 "$(w8 jet)"           Latency "" none
mk rw-noslr-cnn-r1-p16-lat cnn 1 'ap_fixed<16,6>' Latency "" none
# follow-up (added after the SLR2 routing failures, not pre-registered): does removing the SLR pin make the
# 16-bit Latency RF=4/8 designs routable?
mk rw-noslr-jet-r4-p16-lat jet 4 'ap_fixed<16,6>' Latency "" none
mk rw-noslr-big-r4-p16-lat big 4 'ap_fixed<16,6>' Latency "" none
