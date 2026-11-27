# Batch 2 — 12 more random designs, two other Vitis releases, hls4ml main, and the Alveo U250

Run everything on your Mac from this folder. It uses the namespace of your current kubectl context and the
`hls4ml-pipe` service account that already exists there (from the pipeline kit). Set the context once:

    kubectl config set-context --current --namespace=<your-namespace>

Steps:

1. **Commit first (pre-registration):**
   `git add . && git commit -m "batch 2: sample, predictions, jobs" && git push`
2. **Build the 12 new models and inputs:** `./launch_b2.sh prep`, then `kubectl logs -f job/b2-prep`.
   It ends with the lists of /work/wa2/models and /work/wa2/data (12 entries each).
3. **Smoke test the new toolchains (stage 1 only, minutes each):** `./launch_b2.sh smoke`.
   Check each with `kubectl logs job/pipe-<design> | tail -3`: `gate GO` means that toolchain works.
   A stage-1 failure is a result (T1, T3, T4); send me the log before starting that group.
4. **Group 1:** `./launch_b2.sh g1` (6 random designs). Watch with `./launch_b2.sh status`.
5. When group 1's links are done: `./launch_b2.sh g2`, then `g3`, then `g4`. At most 6 links run at once.
6. When everything is done: `./collect.sh`, then `zip -r results_b2.zip results` and send it.

Resources per design: stage 1 = 1 CPU / 6 Gi (one retry at 16 Gi if OOMKilled), stage 2 = 8 CPU / 40 Gi,
stage 3 = 1 CPU / 4 Gi + 1 U55C for about a minute. The U250 designs have no card stage.
Every Job deletes itself 14 days after it finishes.
