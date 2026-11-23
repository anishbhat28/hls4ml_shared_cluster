# Rigor round (rg-*) — 11 builds + 1 card job, namespace hls4ml-nrp, PVC hls4ml-work

All commands run on your Mac, from this folder. Nothing here touches anything outside /work/rw/builds/rg-* and
/work/rw/card_*_rg*; the selection-bias study's files are not read or written.

1. Unzip into the run-week repo:   cd ~/hls4ml-paper/runweek && unzip ~/Downloads/rigor_round.zip && cd rigor_round
2. Pin the image:                  ./pin_image.sh     (same vivado-vitis digest your pipeline/tool runs passed on)
3. Pre-register:                   git add . && git commit -m "rigor round: predictions and job specs" && git push
4. Check the pinned nodes:         ./check_nodes.sh
      gpu08 needs 32 CPU + 160Gi free, chi-dgx-node02 16 CPU + 80Gi, cpu03 8 CPU + 40Gi.
      If a node is gone or full, tell Claude before launching (the substitute must be decided before the run).
5. Launch:                         ./launch.sh phase1
6. Watch:                          ./status.sh        (q/p jobs ~1-3 h, t1 ~5-6 h, r jobs up to 16 h)
7. When rg-t1 has finished:        ./launch.sh t2     (~4-5 h)
8. When every build has finished:  ./launch.sh card   (one U55C, ~3 min)
9. Collect:                        ./collect.sh       then zip results_rg and send it
10. Clean up after collect:         kubectl -n hls4ml-nrp get jobs -o name | grep /rg- | xargs kubectl -n hls4ml-nrp delete

Jobs: r1-r3 = failed designs relinked with a congestion strategy; t1/t2 = time limit on the slowest node;
q1-q4 = four copies at once on the EPYC 9555 node; p1-p2 = two copies at once on the Xeon E5-2698 v4 node.
Each job has a deadline (16 h for r/t, 8 h for q/p) so a stuck job cannot hold resources indefinitely.

libudev: the image ships the stub at /opt/udev-stub/libudev.so.1 but not on the default path (without it the link
hangs). Every v++ / vitis-run line goes through the image's `with-udev-stub` wrapper; Python never sees the stub.
There is no /work/fakelib fallback: if the pinned image lacks the wrapper the job stops at once (exit 3).
launch.sh refuses to start unless every job is pinned to the same digest; collect.sh lists the stub each build used.
Finished Jobs are kept 14 days (ttlSecondsAfterFinished), so collect.sh can still read their logs.
