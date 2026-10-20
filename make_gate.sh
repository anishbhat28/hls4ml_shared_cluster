#!/bin/bash
# Two-stage builds: stage 1 (generate + csynth + package + gate, small job) and stage 2 (link only, large job).
#   ./make_gate.sh   -> job-rw-g-*-s1.yaml and job-rw-g-*-s2.yaml
CLK_DEFAULT=3.333
w8() { case $1 in cnn|tiny) echo w8i3;; *) echo w8i2;; esac; }
mk() {  # name model rf precision strategy [clock_ns]
  for s in 1 2; do
    sed -e "s|__NAME__|$1|g" -e "s|__MODEL__|$2|g" -e "s|__RF__|$3|g" -e "s|__PREC__|$4|g" -e "s|__STRAT__|$5|g" \
        -e "s|__CLK__|${6:-$CLK_DEFAULT}|g" -e "s|__SLR__|SLR2|g" \
        -e "s|__CPU1__|2|g" -e "s|__MEM1__|8Gi|g" -e "s|__DISK1__|6Gi|g" \
        -e "s|__CPU__|8|g" -e "s|__MEM__|40Gi|g" -e "s|__DISK__|10Gi|g" \
        job-rw-gate-s$s-TEMPLATE.yaml > "job-$1-s$s.yaml"
  done
  echo "wrote job-$1-s1.yaml job-$1-s2.yaml"
}
# new designs, not built before (tested by the gate, then linked anyway to check the gate)
mk rw-g-jet-r4-p16-lat-c5 jet  4 'ap_fixed<16,6>' Latency 5.0   # same as a failed design, 200 MHz HLS target
mk rw-g-big-r2-p16-lat    big  2 'ap_fixed<16,6>' Latency
mk rw-g-wide-r4-w8-lat    wide 4 "$(w8 wide)"     Latency
mk rw-g-wide-r8-p16-res   wide 8 'ap_fixed<16,6>' Resource
mk rw-g-jet-r2-w8-lat     jet  2 "$(w8 jet)"      Latency
