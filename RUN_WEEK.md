# Run plan — hls4ml on a shared cluster (U55C, NRP)

Everything is run **on your Mac** from `~/hls4ml-paper/runweek`. Open a terminal and `cd ~/hls4ml-paper/runweek` before every command.
Check jobs any time: `kubectl -n hls4ml-nrp get jobs | grep rw-`

**Setup used by every build:** unmodified hls4ml main at `8912ed2` (includes the merged #1573),
`board='alveo-u55c', driver='xrt'`, `clock_period=3.333`, kernel in SLR2 (board default) unless the build name has `noslr` (`kernel_slr=False`).

**Rule for every step:** if the output doesn't match what's described, stop and send me the output.

---

## Day 1 (Sat Oct 17) — setup, prep, smoke test

1. **Folder** (once):
   ```bash
   cd ~/Downloads && unzip runweek.zip && mkdir -p ~/hls4ml-paper && mv runweek ~/hls4ml-paper/
   cd ~/hls4ml-paper/runweek && chmod +x make_builds.sh collect.sh run_queue.sh && ls
   ```
   `ls` shows 9 files. Then check the cluster:
   ```bash
   kubectl -n hls4ml-nrp get jobs
   kubectl -n hls4ml-nrp get pvc
   ```
   PVCs `hls4ml-work` and `xilinx-tools` are `Bound`. Note the CAPACITY of `hls4ml-work`.
   Save logs of old finished jobs you still want (`kubectl -n hls4ml-nrp logs job/NAME > old-NAME.log`), then delete them. Leave running jobs alone.

2. **Send the message to Daniel** (bottom of this file). Nothing below waits for his reply.

3. **Prep job** (~45 min). Clones hls4ml, builds its wheel, downloads the jet dataset, writes test + stress inputs, trains 5 models.
   ```bash
   kubectl -n hls4ml-nrp delete job rw-prep --ignore-not-found
   kubectl apply -f job-rw-prep.yaml
   kubectl -n hls4ml-nrp get pods | grep rw-prep        # wait for Running (image pull can take ~10 min)
   kubectl -n hls4ml-nrp logs -f job/rw-prep
   ```
   Expected, in order: `df -h /work` line (**write down `Avail` = FREE**), a `hls4ml-*.whl` filename, a commit line starting `8912ed2`, `stress set (3110, 16)`, five `test accuracy` lines (jet, big, cnn, tiny, wide; roughly 0.70–0.77), `=== prep done ===`.
   If it fails at `fetch_openml`, stop and send me the error.
   When `kubectl -n hls4ml-nrp get job rw-prep` shows `1/1`:
   ```bash
   mkdir -p results && kubectl -n hls4ml-nrp logs job/rw-prep > results/rw-prep.log
   grep -E "Avail|/work|\.whl|^8912ed2|stress set|test accuracy" results/rw-prep.log
   ```
   **Send me that output.**

4. **Smoke-test build** (one small design, ~3–5 h):
   ```bash
   ./make_builds.sh
   kubectl apply -f job-rw-jet-r4-p8-lat.yaml
   ```
   After ~20 min:
   ```bash
   kubectl -n hls4ml-nrp logs job/rw-jet-r4-p8-lat | grep -E "STAGE|ERROR|WARNING: Invalid|Estimated Fmax|sp=|slr="
   ```
   Expected: `STAGE generate → csynth → package`, two `sp=...HBM[...]` lines, one `slr=...:SLR2` line, then `STAGE link`. No `WARNING: Invalid ReuseFactor`.

5. **Once it shows `STAGE link`, start the long build** (14–24 h; may fail placement in SLR2 like the 16-bit version did — that is a result):
   ```bash
   kubectl apply -f job-rw-big-r1-p8-lat.yaml
   ```

## Day 2 (Sun Oct 18) — smoke results, sizing, predictions, start the queue

6. When `rw-jet-r4-p8-lat` shows `1/1`:
   ```bash
   kubectl -n hls4ml-nrp logs job/rw-jet-r4-p8-lat > results/rw-jet-r4-p8-lat.log
   sed -n '/RESULT/,/END/p' results/rw-jet-r4-p8-lat.log
   sed 's/__TAG__/smoke/g' job-rw-card.yaml > job-rw-card-smoke.yaml
   kubectl apply -f job-rw-card-smoke.yaml
   sleep 10 && kubectl -n hls4ml-nrp logs -f job/rw-card-smoke
   ```
   **Paste both outputs to me.** The RESULT block has `disk_bytes_before_cleanup` (= DISK) and `memory_peak_bytes`. The card job should show a kernel clock in `card_clocks`, `test_hw_eq_csim_exact_frac` = 1.0, accuracy near Keras, and the batch-size timings.

7. **Size the jobs.** I'll reply with `MEM_DEFAULT`, `CPU_DEFAULT`, `UNDER_MEM` (from the measured peak; NRP requires memory use within 20–150% of the request, CPU within 20–200%) and **N**, the number of builds to run at once: N = (FREE × 0.7) / (DISK × 1.5), rounded down, at most 5. Edit the three values at the top of `make_builds.sh`, then:
   ```bash
   ./make_builds.sh && grep -h "memory:" job-rw-jet-r1-p16-lat.yaml
   ```

8. **Predictions before the builds.** I'll draft `predictions_v1.md`; commit it:
   ```bash
   git init -q 2>/dev/null; git add predictions_v1.md && git commit -qm "Predictions before builds" && git log -1 --format='%H %cd'
   ```

9. **Start the queue** (24 builds; runs for ~2 days, N at a time; safe to Ctrl-C and rerun — it skips jobs that already exist):
   ```bash
   caffeinate -i ./run_queue.sh N job-rw-jet-*.yaml job-rw-big-r4-*.yaml job-rw-tiny-*.yaml job-rw-cnn-*.yaml job-rw-rep*.yaml job-rw-under-*.yaml job-rw-noslr-*.yaml
   ```
   (replace `N`). Keep the terminal open. Monitor in another terminal: `kubectl -n hls4ml-nrp get jobs | grep rw-`.
   `rw-under-jet-r1-p16-lat` is meant to be killed (OOMKilled). Any other `Failed`: `kubectl -n hls4ml-nrp describe job NAME | tail -20` and send me the output.
   Disk check while builds run: `kubectl apply -f pod-rw-peek.yaml; kubectl -n hls4ml-nrp exec rw-peek -- df -h /work` (delete the pod after: `kubectl -n hls4ml-nrp delete pod rw-peek`). If `Avail` falls below 15% of capacity, Ctrl-C the queue and rerun it with a smaller N once builds finish.

## Day 3–4 (Mon Oct 19 – Tue Oct 20) — queue finishes, guidance, held-out

10. When the queue prints `all submitted` and all builds are `1/1` (or the expected failure): `./collect.sh` and send me `results/`. We derive the sizing guidance and the csynth→link predictor.
11. I write `predictions_heldout.md`; commit it **before** launching:
    ```bash
    git add predictions_heldout.md && git commit -qm "Held-out predictions" && git log -1 --format='%H %cd'
    ./make_builds.sh heldout
    caffeinate -i ./run_queue.sh N job-rw-ho-*.yaml
    ```

## Day 5 (Wed Oct 21, evening) — card session A

12. ```bash
    sed 's/__TAG__/a/g' job-rw-card.yaml > job-rw-card-a.yaml
    kubectl apply -f job-rw-card-a.yaml
    sleep 10 && kubectl -n hls4ml-nrp logs -f job/rw-card-a
    ```

## Day 6 (Thu Oct 22) — card session B, collect, freeze

13. ```bash
    sed 's/__TAG__/b/g' job-rw-card.yaml > job-rw-card-b.yaml
    kubectl apply -f job-rw-card-b.yaml
    ./collect.sh
    ```
    Don't delete jobs before `collect.sh`. Fri Oct 23 is spare for reruns.

---

## What gets saved (PVC `/work/rw/`)

| File | Used for |
|---|---|
| `builds/<name>/stages.csv` | time of each hls4ml build stage |
| `builds/<name>/mem.csv`, `peak_bytes.txt` | memory over time, peak vs request |
| `builds/<name>/vivado_steps.txt` | synth / place / route inside the link |
| `builds/<name>/disk_bytes_before_cleanup.txt` | storage per build |
| `builds/<name>/link_system.cfg` | the link config hls4ml generated (for the paper's methods) |
| `builds/<name>/hls_fmax.txt`, `*csynth.rpt`, `*timing_summary*`, `*full_util*`, `xclbin_info.txt` | HLS estimate, routed timing |
| `card_results_<tag>.csv` | kernel clock on the card, load/reload/run time, hardware == hls4ml `predict` on test and stress inputs, accuracy |
| `results/` on your Mac | job logs + pod records (start/finish times, node, OOMKilled) |

---

## Message to Daniel

> Hi Daniel, my hls4ml PR adding U55C/Alveo support was merged this week, and I'm writing a short manuscript on what it takes to run hls4ml on a shared cluster with data-center cards: what each hls4ml build costs (time, memory, CPU, licence seat) as a function of the hls4ml settings, and how much card time it takes to validate a design. The paper writes the cluster side as a few parameters any cluster has, with NRP as the measured example. Qibin suggested I check with you. I've read the policies and FPGA pages; these are the values I couldn't find there:
>
> 1. **Licence seats:** how many concurrent Vivado/Vitis seats does the xilinxd server have, and are they shared across all namespaces?
> 2. **Build nodes:** what is the largest memory a single batch pod can get, and roughly how many nodes have that much? Is there a max runtime for batch Jobs (some links run 14–24 h)?
> 3. **Request accuracy:** Vivado links have long single-threaded phases and a late memory peak. How are the 20–150% memory / 20–200% CPU rules applied to batch Jobs like this?
> 4. **Cards:** how many U55Cs are schedulable now (docs say 23 of 32), and is there a limit on how long a pod may hold one?
> 5. **Demand (only if quick):** from k8s accounting, last month's card-hours allocated to FPGA pods, and roughly how many users ran FPGA or Vivado/Vitis jobs.
> 6. Is it OK to name NRP, and what acknowledgment / grant numbers should I cite? I'll send the cluster paragraph to check.
>
> Thanks!
