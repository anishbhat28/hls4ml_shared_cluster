# wa-hls4ml round — 12 randomly drawn designs from the wa-hls4ml exemplar set

Run everything on your Mac from this folder (copy it to ~/hls4ml-paper/wa_round). It reuses your pipeline: the
`hls4ml-pipe` service account and RBAC from the pipeline kit must already exist in hls4ml-nrp (they do).

1. Commit first (pre-registration):  git add . && git commit -m "wa round: sample, predictions, jobs" && git push
2. Build models + inputs:            ./launch_wa.sh prep          then  kubectl -n hls4ml-nrp logs -f job/wa-prep
                                     (ends with "wrote /work/wa"; 12 lines "... params (wa-hls4ml: ...)", equal pairs)
3. Start the first six:              ./launch_wa.sh batch1        (the Mac can close; everything runs on the cluster)
4. Watch:                            ./launch_wa.sh status
                                     kubectl -n hls4ml-nrp logs job/pipe-<design> | tail -5
5. When batch 1's links are done:    ./launch_wa.sh batch2
6. When all 12 pipe-* jobs are done: ./collect.sh   then zip -r results_wa.zip results  and send it

Resources: stage 1 = 1 CPU / 6 Gi (HLS is single-threaded: 0.3–0.8 cores, 1.4–3.6 GiB median in the rigor round),
stage 2 = 8 CPU / 40 Gi (link only), stage 3 = 1 CPU / 4 Gi + 1 U55C for about a minute. Only stage 3 asks for a card.
No time limits; a stage that has not finished after 2 days is stopped as a safety net.
