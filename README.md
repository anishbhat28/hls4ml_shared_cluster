# hls4ml on a shared cluster: what it costs to build and validate on an Alveo U55C

This repository holds everything behind the paper *Deploying hls4ml neural networks on data-center FPGAs in a
shared cluster* (in preparation): the Kubernetes job files, the predictions we wrote before each run, the raw
measurements, and the scripts that turn them into the paper's numbers and figures.

**In one paragraph.** We ran 46 hls4ml builds for the AMD Alveo U55C as Kubernetes Jobs on the National Research
Platform (NRP) and measured what each build cost: memory, CPU, time, and how often it failed. Then we loaded every
bitstream onto a card and checked its outputs against hls4ml's own `predict`. Before each round of jobs we wrote
down what we expected and committed it here, so every result can be checked against a prediction made in advance.

**Which version to use:** tag `data-freeze-4`. It contains all the data the paper uses.

---

## 1. What we found

| Question | Answer |
|---|---|
| How much memory does a build need? | 24.5–31.0 GiB for every small model, whatever the reuse factor, precision or strategy; 33.4 GiB for a model 10× larger. The U55C platform sets it, not the model. **8 CPU and 40 Gi worked for every build.** |
| When is memory highest? | In the first 5–46 minutes of the Vivado link, while about 80 platform and kernel modules are synthesized in parallel. Placement and routing need much less. |
| How long does a build take? | The link is 91–97% of it: 1–4.5 hours for builds that succeed. The same design took 62, 120 and 170 minutes on three node types; a second build on the same node changed this by under 7%. |
| How much is lost to failed builds? | About half of all memory-hours charged went to builds that failed routing. Failed links ran up to 13.5 hours; no successful link took more than 4.3 hours. |
| Can failures be caught early? | Placement failures, yes: they show in the HLS report (too many DSPs for one die). Routing failures, no; a time limit on the link handles them instead. |
| Does the hardware match `predict`? | Yes, bit for bit, for all 27 designs that built, on 22,610 inputs including overflow and ±Inf/NaN, on two different cards. Checking takes about 10 seconds of card time per design. |
| Can someone else reproduce it? | A rerun from an empty directory reproduced one design bit for bit: data, trained weights, HLS reports, simulation and card outputs. |

## 2. How the study ran

The work happened in rounds. Each round has a predictions file, written and committed before its jobs started.

| Round | When | Builds | What it tested | Predictions | Results |
|---|---|---|---|---|---|
| Run week | Oct 17–19 | 31 | Cost of each hls4ml setting; repeats; an undersized job; with and without the SLR pin | `predictions_v1.md` + three amendments | `analysis/scorecard.md` |
| Held-out | Oct 18 | 4 | Whether the job sizing derived from the run week holds for new designs | `predictions_heldout.md` | `analysis/scorecard.md` |
| Card sessions | Oct 19–20 | — | Hardware vs `predict` for every built design, on two cards | in `predictions_v1.md` (C1–C8) | `analysis/scorecard.md` |
| Gate round | Oct 19 | 5 | A two-step build that checks the HLS report before the expensive link | `predictions_gate.md` | `analysis/scorecard_gate.md` |
| Clean room | Oct 21 | 1 | Rebuilding one design from nothing | `predictions_cleanroom.md` | `analysis/scorecard_cleanroom.md` |
| Larger model | Oct 22–23 | 2 | Whether the results hold for a model 10× larger | `predictions_large.md` | `analysis/scorecard_large.md` |
| Node sharing | Oct 24 | 3 | Whether a second build on the same node slows the link (one build alone, two started together) | `predictions_solo.md`, `predictions_pair.md` | `analysis/scorecard_solo.md` |

To see what we expected and what happened, read a predictions file and then its scorecard.

## 3. A walk through the repository

### 3.1 Top level: the job files

These are the files that ran on the cluster, in the order they are used.

1. **`job-rw-prep.yaml`** sets everything up once. It downloads hls4ml at a fixed commit (8912ed2) and builds it,
   downloads the jet dataset and checks its checksum, and trains the five models.
   `job-rw-prep-large.yaml` trains the sixth, larger model later.
2. **`job-rw-build-TEMPLATE.yaml`** is one complete build: hls4ml writes the project and runs its C simulation,
   HLS synthesis turns it into hardware, and the Vitis link produces the bitstream. Along the way it records the time
   of each stage and samples memory and CPU every 15 seconds.
   **`make_builds.sh`** fills in the template for every design, producing the **`job-rw-<design>.yaml`** files.
3. **`job-rw-gate-s1-TEMPLATE.yaml`** and **`job-rw-gate-s2-TEMPLATE.yaml`** split a build in two: a small job that
   runs up to HLS synthesis and gives a STOP / RISK / GO verdict, then a large job that only links.
   **`make_gate.sh`** writes the gate-round jobs from them.
4. **`job-rw-card.yaml`** checks bitstreams on a card. For each design it loads the bitstream, runs the test and stress
   inputs, compares every output with hls4ml's `predict`, and measures latency and throughput. The
   **`job-rw-card-*.yaml` / `.json`** files are the sessions that ran.
5. **`job-rw2-*.yaml`** is the clean-room rerun: the same steps in a fresh directory.
6. **`job-rw-large-*.yaml`** and **`job-rw-card-lg.yaml`** are the larger-model round.
7. **`job-rw-solo-*.yaml`** and **`job-rw-pair*-*.yaml`** are the node-sharing test: the same build pinned to one node, alone or two at once.

Supporting files:

- **`run_queue.sh`, `start_queue.sh`, `job-queue-TEMPLATE.yaml`, `queue-rbac.yaml`**: a small queue that runs inside the
  cluster and keeps a set number of builds going, so no laptop needs to stay connected.
- **`collect.sh`, `collect_cr.sh`**: run after jobs finish. They save each job's log and record (which node, start and
  end, why it ended) and download the measurements from the cluster's shared volume.
- **`pod-rw-peek.yaml`**: a tiny pod for looking at the shared volume.
- **`nrp_accounting.py`, `nrp_accounting2.py`**: ask NRP's accounting service what it charged for each pod. Python
  standard library only.
- **`RUN_WEEK.md`**: the original run plan, and what each file on the cluster's volume contains.

### 3.2 `data/`: raw measurements

| File | Contents |
|---|---|
| `results_card_gate.zip` | Logs, job records and per-build measurements for the run week, held-out round, gate round and all card sessions |
| `results_gate.zip` | The gate round as first collected |
| `results_cleanroom.zip` | The clean-room rerun |
| `results_large.zip` | The larger-model round |
| `results_solo.zip` | The node-sharing test |
| `accounting*_2026*.json` | NRP's own records: requested CPU and memory × wall time for every pod |
| `SHA256SUMS` | Checksums of the zip files |

Inside the zips, each build has its own folder with `stages.csv` (stage start times), `mem.csv` (memory and CPU
every 15 s), the HLS reports, and, for builds that finished, the routed timing report and the bitstream's clock.

### 3.3 `analysis/`: from data to paper

| File | What it does |
|---|---|
| `data/builds5.csv` | One row per run-week and held-out build: settings, outcome, times, memory, resources, clock |
| `data/gate.csv` | Same for the gate round |
| `data/card_*.csv` | One row per design per card session |
| `score_and_figs.py` | Scores the run-week, held-out and card predictions; writes `scorecard.md` and the figures |
| `gate_analyze.py` | Builds `data/gate.csv` from the gate-round folders |
| `cost_by_outcome.py` | Splits what NRP charged by build outcome (built, routing failed, …) |
| `csynth_predictor.py` | Searches the HLS reports for a rule that predicts routing failure. None held up on new designs. |
| `fig_link_profile.py` | Draws memory over time during the link |
| `scorecard*.md` | Every prediction with its verdict and the evidence |
| `fig/`, `tables/` | The paper's figures and tables |
| `results_draft.md`, `methods_draft.md` | Early text drafts (the current draft is kept elsewhere) |

### 3.4 Names you will see

A build name such as `rw-jet-r4-p16-res` reads as **model** `jet`, **reuse factor** 4, **precision** `p16`, **strategy**
`res`.

- Models: `tiny` 16→8→5, `jet` 16→64→32→32→5, `big` 16→64→64→32→5, `wide` 16→128→64→5, `cnn` (Conv1D),
  `large` 16→256→256→128→5 (104k parameters).
- Precision: `p16` = 16-bit fixed point everywhere; `w8` = 8-bit weights, 16-bit everything else; `p8` = 8-bit
  everywhere.
- Strategy: `lat` = Latency (fully parallel), `res` = Resource (multipliers shared).
- Prefixes: `ho-` held-out, `noslr-` kernel not pinned to one die, `rep-`/`rep2-` repeats, `under-` deliberately too
  little memory, `g-` gate round, `rw2-` clean room, `large-` larger-model round, `solo-`/`pair1-`/`pair2-` node-sharing test.

## 4. Setup

- hls4ml main at commit 8912ed2, VitisUnified backend, `board='alveo-u55c'`, `driver='xrt'`, `io_stream`; kernel
  pinned to die SLR2 unless the name says `noslr`; target clock 3.333 ns (300 MHz)
- Vitis/Vivado 2024.2 from the cluster's `xilinx-tools` volume; platform `xilinx_u55c_gen3x16_xdma_3_202210_1`
- Container image `gitlab-registry.nrp-nautilus.io/nrp/coder-images/vivado-vitis`; Vivado works on node-local
  scratch; results go to the `hls4ml-work` volume under `/work/rw` (`/work/rw2` for the clean room)
- Data: the hls4ml LHC jet dataset (OpenML `hls4ml_lhc_jets_hlf`, checksum-verified)
- hls4ml is used unmodified. The Alveo support it needs is hls4ml pull request #1573 (merged).

## 5. Running it yourself

You need `kubectl` access to an NRP namespace with the `xilinx-tools` and a shared work volume, plus a U55C for the
card step. The files use the namespace `hls4ml-nrp`; change it if yours differs.

```bash
# 1. Set up: hls4ml, dataset, models (about 15 min)
kubectl apply -f job-rw-prep.yaml
kubectl -n hls4ml-nrp logs -f job/rw-prep

# 2. Build one design (1-4 h); any job-rw-<design>.yaml works the same way
kubectl apply -f job-rw-jet-r4-p16-res.yaml
kubectl -n hls4ml-nrp logs job/rw-jet-r4-p16-res | grep -E 'STAGE|RESULT|ERROR'

# 3. Check every finished design on a card (about 10 s each)
sed 's/__TAG__/mine/g' job-rw-card.yaml > job-rw-card-mine.yaml
kubectl apply -f job-rw-card-mine.yaml
kubectl -n hls4ml-nrp logs -f job/rw-card-mine

# 4. Save logs and measurements within a day (finished jobs are removed after about a day)
./collect.sh
```

To recompute the paper's numbers from the committed data (Python 3 with pandas, matplotlib and tabulate):

```bash
cd analysis
python3 score_and_figs.py
python3 cost_by_outcome.py data/accounting2_20261020.json
```

## 6. Things to know when reading the data

- **Two memory numbers.** `peak_anon_GiB` is the build process itself; `peak_cg_GiB` adds the file cache. The cluster
  charges the amount *requested*, not either of these.
- **Link times depend on the machine.** The scheduler picks the node, and nodes differ by up to 2.7× for the same
  design. Compare designs on the same CPU type (`cpu_model` column). Twenty builds shared a node with another of ours
  for part of their run; the node-sharing test shows this changes the link by under 7%.
- **Two builds are special.** `rw-jet-r1-p8-lat` was stopped when we replaced all-8-bit precision with 8-bit weights
  only, and is excluded. `rw-big-r1-p8-lat` had already finished and is kept, but has no job log.
- **Three pods were lost** when their node failed: two builds, both rerun and marked in the scorecards, and one setup job.
- **The larger model's RF=64 build never finished HLS synthesis.** We stopped it after 11.4 hours; see
  `analysis/scorecard_large.md`.

## Acknowledgment

This work used the National Research Platform, supported in part by NSF awards CNS-1730158, ACI-1540112,
ACI-1541349, OAC-1826967, OAC-2112167, CNS-2100237 and CNS-2120019.
