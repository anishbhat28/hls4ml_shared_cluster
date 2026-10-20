"""Score the pre-registered run-week predictions (B, C, H) and make the paper figures.
Inputs: data/builds5.csv, data/card_A.csv, data/card_B.csv. Outputs: scorecard.md, tables/*.csv, fig/*.pdf|png."""
import os, sys
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

D = os.path.dirname(os.path.abspath(__file__))
b = pd.read_csv(f"{D}/data/builds5.csv")
A = pd.read_csv(f"{D}/data/card_A.csv").set_index("design")
Bc = pd.read_csv(f"{D}/data/card_B.csv").set_index("design")
# gate-round card sessions (ga on the session-A host, gb on the session-B host); only built designs
for _f, _which in (("card_ga.csv", "A"), ("card_gb.csv", "B")):
    if os.path.exists(f"{D}/data/{_f}"):
        _g = pd.read_csv(f"{D}/data/{_f}").set_index("design"); _g = _g[_g.status == "ok"]
        if _which == "A": A = pd.concat([A, _g[A.columns.intersection(_g.columns)]])
        else: Bc = pd.concat([Bc, _g[Bc.columns.intersection(_g.columns)]])
os.makedirs(f"{D}/fig", exist_ok=True); os.makedirs(f"{D}/tables", exist_ok=True)

b["ho"] = b.name.str.startswith("rw-ho-")
b["built"] = b.outcome.eq("built")
b["t_build_min"] = b[["t_generate_min", "t_csynth_min", "t_package_min", "t_link_min"]].sum(axis=1, min_count=1)
b["link_frac"] = b.t_link_min / b.t_build_min
b["w8"] = b.prec.str.startswith("w8")
b["p16"] = b.prec.eq("ap_fixed<16,6>")
# smoke reference (pre-registered v1 values)
SMOKE = dict(link_min=3361 / 60, peak_cg=32.7, peak_anon=28.3)

out = []
def P(code, verdict, text):
    out.append(f"| {code} | {verdict} | {text} |")

ok = b[b.built]
nonoom = b[b.outcome != "OOM"]
stopped = b.outcome.str.startswith("no log")

# ---------------- B ----------------
lf = ok.link_frac
P("B1", "held" if (lf >= .8).all() else "failed",
  f"link / build time over {len(ok)} completed builds: min {lf.min():.3f} ({ok.loc[lf.idxmin(),'name']}), median {lf.median():.3f}")
ps = b.peak_stage.value_counts().to_dict()
P("B2", "held" if set(ps) == {"link"} else "failed", f"stage of peak process memory: {ps} (all {len(b)} build dirs incl. failed/OOM)")
t = b[b.model == "tiny"].iloc[0]
r1, r2, r3 = t.t_link_min / SMOKE["link_min"], t.peak_cg_GiB / SMOKE["peak_cg"], t.peak_anon_GiB / SMOKE["peak_anon"]
P("B3", "held" if r1 >= .7 and r2 >= .85 else "failed",
  f"tiny link {t.t_link_min:.0f} min = {r1:.2f}× smoke (≥0.70); peak cgroup {r2:.2f}× (anon {r3:.2f}×) smoke (≥0.85). Link time is node-confounded (tiny on E5-2698 v4)")
# B4
rows = []
for (m, pr, st), g in b[b.t_csynth_min.notna()].groupby(["model", "prec", "strat"]):
    g = g[~g.name.str.contains("noslr|rep|under|ho-") & g.rf.isin([1, 4, 8])].drop_duplicates("rf").sort_values("rf")
    if len(g) >= 2:
        mono = (np.diff(g.t_csynth_min.values) < 0).all()
        rows.append((m, pr, st, dict(zip(g.rf, g.t_csynth_min)), mono))
nmono = sum(r[4] for r in rows)
P("B4", "failed" if nmono < len(rows) else "held",
  f"csynth time decreasing with RF in {nmono}/{len(rows)} model/precision/strategy series: "
  + "; ".join(f"{m} {pr} {st} {d}{'' if mono else ' ✗'}" for m, pr, st, d, mono in rows)
  + ". csynth time is node-confounded (same design up to 2× across CPUs)")
# B5
jc = nonoom[nonoom.model.isin(["jet", "cnn"]) & ~stopped]
for col in ["peak_anon_GiB", "peak_cg_GiB"]:
    m = jc[col].mean(); dev = ((jc[col] - m) / m).abs().max()
    out_b5 = (col, jc[col].min(), jc[col].max(), m, dev)
    if col == "peak_anon_GiB": b5a = out_b5
    else: b5c = out_b5
P("B5", "held" if max(b5a[4], b5c[4]) < .25 else "failed",
  f"jet+cnn (n={len(jc)}, excl. undersized): process peak {b5a[1]:.1f}–{b5a[2]:.1f} GiB, max dev from mean {b5a[4]*100:.1f}%; cgroup {b5c[1]:.1f}–{b5c[2]:.1f}, {b5c[4]*100:.1f}%")
top = nonoom.sort_values("peak_anon_GiB", ascending=False).head(4)
P("B6", "failed (first half)",
  f"no design > 48 GiB (max process {nonoom.peak_anon_GiB.max():.2f}, cgroup {nonoom.peak_cg_GiB.max():.2f}), so the second half is vacuous; "
  f"largest process peaks: {', '.join(f'{r.name[3:]} {r.peak_anon_GiB}' for r in top.itertuples())} — big RF=1 is not among the largest")
lc = nonoom[~stopped].link_cores
bad = nonoom[~stopped & ((lc < 2) | (lc > 4))]
P("B7", "failed (marginal)" if len(bad) else "held",
  f"link mean cores {lc.min():.2f}–{lc.max():.2f}; outside 2–4: " + ", ".join(f"{r.name[3:]} {r.link_cores}" for r in bad.itertuples())
  + " (all long failing Latency routes)")
P("B8", "held" if ok.disk_GB.max() < 5 else "failed", f"build tree max {ok.disk_GB.max()} GB")
u = b[b.outcome == "OOM"]
P("B9", "held" if len(u) == 1 else "failed",
  f"{u.name.iloc[0][3:]} OOM-killed in {u.peak_stage.iloc[0]} (16 Gi limit; process peak {u.peak_anon_GiB.iloc[0]} GiB)")
rep = b[b.name.str.contains("jet-r4-p16-res") & b.built]
lm = rep.t_link_min; am = rep.peak_anon_GiB; cm = rep.peak_cg_GiB
P("B10", "failed (time) / held (process mem)",
  f"3 runs link {list(lm)} min: max dev {((lm-lm.mean())/lm.mean()).abs().max()*100:.0f}% (±15% predicted); "
  f"run on EPYC 9555 vs two on EPYC 7402P, which agree within {abs(lm.iloc[1]-lm.iloc[2])/lm.iloc[1:].mean()*100:.1f}%. "
  f"process peak max dev {((am-am.mean())/am.mean()).abs().max()*100:.1f}% (±5% held); cgroup {((cm-cm.mean())/cm.mean()).abs().max()*100:.1f}%")
pairs = []
for m in ["jet", "big"]:
    for pr in ["ap_fixed<16,6>", "w8i2"]:
        l = b[(b.model == m) & (b.prec == pr) & (b.rf == 4) & (b.strat == "Latency") & (b.kernel_slr == "SLR2") & ~b.name.str.contains("rep")]
        r = b[(b.model == m) & (b.prec == pr) & (b.rf == 4) & (b.strat == "Resource") & ~b.name.str.contains("rep")]
        if len(l) and len(r):
            pairs.append(f"{m} {pr}: DSP Lat {l.hls_dsp.iloc[0]} / Res {r.hls_dsp.iloc[0]}")
P("B11", "failed", "Resource DSP estimate is not lower than Latency at RF=4: " + "; ".join(pairs)
  + ". Latency 16-bit RF=4 builds did not complete, so the link-time half is untestable for p16")
sl = []
for core in ["cnn-r1-p16-lat", "jet-r4-w8-lat", "jet-r1-p16-lat", "jet-r4-p16-lat", "big-r4-p16-lat"]:
    s = b[b.name == f"rw-{core}"].iloc[0]; n = b[b.name == f"rw-noslr-{core}"].iloc[0]
    sl.append(f"{core}: SLR2 {s.outcome}{'' if pd.isna(s.wns) else f' WNS {s.wns}'} vs no-SLR {n.outcome}{'' if pd.isna(n.wns) else f' WNS {n.wns}'}")
P("B12", "failed (post hoc pairs)", "; ".join(sl) + ". jet-r4-w8-lat: pinned build is worse (259.0 vs 300 MHz). No-SLR builds were added post hoc (amendment 3)")

# B13: predictor fitted on waves 1-3 (non-held-out) csynth LUT/FF/DSP, plain OLS, no feature selection
tr = b[~b.ho & b.built & b.hls_lut.notna()]
te = b[b.ho & b.built]
def ols(y_tr, y_te_true, Xtr, Xte):
    Xa = np.c_[np.ones(len(Xtr)), Xtr]; c, *_ = np.linalg.lstsq(Xa, y_tr, rcond=None)
    pred = np.c_[np.ones(len(Xte)), Xte] @ c
    return pred, (pred - y_te_true) / y_te_true
feat = ["hls_lut", "hls_ff", "hls_dsp"]
plink, elink = ols(tr.t_link_min.values, te.t_link_min.values, tr[feat].values / 1e3, te[feat].values / 1e3)
trm = b[~b.ho & b.hls_lut.notna() & (b.outcome != "OOM") & ~stopped]
tem = b[b.ho]
pmem, emem = ols(trm.peak_anon_GiB.values, tem.peak_anon_GiB.values, trm[feat].values / 1e3, tem[feat].values / 1e3)
P("B13", "failed (time) / held (memory)",
  "OLS on csynth LUT/FF/DSP (form fixed now, not pre-specified in v1). Link time, trained on "
  f"{len(tr)} completed: held-out errors " + ", ".join(f"{n[6:]} {e*100:+.0f}%" for n, e in zip(te.name, elink))
  + f". Process peak memory, trained on {len(trm)}: " + ", ".join(f"{n[6:]} {e*100:+.1f}%" for n, e in zip(tem.name, emem))
  + ". Node effect on link time (~2×) is not in the features")
j1 = b[b.name == "rw-jet-r1-p16-lat"].iloc[0]; n1 = b[b.name == "rw-noslr-jet-r1-p16-lat"].iloc[0]
P("B14", "held", f"jet-r1-p16 csynth DSP {j1.hls_dsp} > 2879 → pinned build failed placement ({j1.dsp_required_slr} required); "
  f"no-SLR build placed {n1.impl_dsp_total} DSPs and built at {n1.fmax_achieved} MHz")
w = b[b.name.isin(["rw-jet-r1-w8-lat", "rw-big-r1-w8-lat"])]
P("B15", "failed", "both RF=1 w8 builds placed in SLR2: " + ", ".join(f"{r.name[3:]} csynth DSP {r.hls_dsp}, {r.fmax_achieved} MHz" for r in w.itertuples())
  + " (8-bit weights cut DSPs ~4×; jet 3365 → 761)")

# ---------------- C ----------------
ids = sorted(set(A.index) & set(Bc.index))
assert set(A.index) == set(Bc.index)
cA = A.loc[ids]; cB = Bc.loc[ids]
def all_eq(c, col, v): return (c[col] == v).all()
c1 = all_eq(cA, "test_hw_eq_csim_bitexact_frac", 1) and all_eq(cB, "test_hw_eq_csim_bitexact_frac", 1) and (cA.test_n_mismatch_rows.eq(0).all() and cB.test_n_mismatch_rows.eq(0).all())
c2 = all_eq(cA, "stress_hw_eq_csim_bitexact_frac", 1) and all_eq(cB, "stress_hw_eq_csim_bitexact_frac", 1)
P("C1", "held" if c1 else "failed", f"{len(ids)} designs × 20,000 test inputs × 2 sessions, 0 mismatching rows, max |hw − csim| = {max(cA.test_hw_vs_csim_max_abs.max(), cB.test_hw_vs_csim_max_abs.max())}")
P("C2", "held" if c2 else "failed", f"2,610 stress rows per design, 0 mismatches in either session")
P("C3", "held" if c2 else "failed", "±Inf/NaN rows are part of the stress set; bit-exact (hardware and C-sim agree on these rows too)")
prec = pd.concat([b.set_index(b.name).prec, pd.Series({"rw-g-jet-r2-w8-lat": "w8i2", "rw-g-wide-r8-p16-res": "ap_fixed<16,6>"})]).reindex(ids)
agw8 = cA.test_hw_vs_keras_argmax_agree[prec.str.startswith("w8")]
agp16 = cA.test_hw_vs_keras_argmax_agree[prec.eq("ap_fixed<16,6>")]
P("C4", "held", f"hw–Keras argmax agreement: 16-bit {agp16.min():.4f}–{agp16.max():.4f}, w8 {agw8.min():.4f}–{agw8.max():.4f}, all-8-bit 0.3353/0.4163; equals C-sim agreement (C1)")
lat = pd.concat([cA.latency_1_us, cB.latency_1_us])
spd = (cA.batch1_s / (cA.batch10000_s / 1e4))
P("C5", "held" if lat.min() >= 50 and spd.min() >= 10 else "failed",
  f"single-call latency {lat.min():.0f}–{lat.max():.0f} µs; per-input time batch 1 → 10,000 falls {spd.min():.0f}–{spd.max():.0f}×")
ld = pd.concat([cA.load_s, cB.load_s])
per = cA.load_s + cA.test_run_s + cA.stress_run_s + cA[[f"batch{n}_s" for n in [1, 10, 100, 1000, 10000]]].sum(axis=1)
P("C6", "half (load failed)", f"xclbin load {ld.min():.1f}–{ld.max():.1f} s (≤2 s predicted); measured card time per design (load+test+stress+sweep) ≤ {per.max():.1f} s (<1 min held); "
  "reload of the same xclbin 0.08–0.14 s")
num = ["test_hw_vs_keras_argmax_agree", "hw_accuracy", "csim_accuracy", "stress_hw_vs_keras_argmax_agree", "kernel_clock_mhz",
       "test_hw_vs_csim_max_abs", "stress_hw_vs_csim_max_abs"]
c7 = (cA[num].values == cB[num].values).all()
P("C7", "held" if c7 else "failed", f"session A ({cA.node.iloc[0]}) vs B ({cB.node.iloc[0]}): all accuracy/agreement/clock columns identical for {len(ids)} designs")
P("C8", "held" if (cA.hw_accuracy == cA.csim_accuracy).all() else "failed", "card accuracy = C-sim accuracy for every design (incl. the all-8-bit collapse 0.3226/0.3977)")

# ---------------- H ----------------
h = b[b.ho].set_index("name")
P("H1", "held" if (h.outcome != "OOM").all() and h.peak_anon_GiB.between(24, 33).all() else "failed",
  "40 Gi, no OOM; process peaks " + ", ".join(f"{n[6:]} {v}" for n, v in h.peak_anon_GiB.items()) + " GiB, all in link")
P("H2", "held" if h.link_cores.between(2.4, 4.5).all() else "failed", "link cores " + ", ".join(f"{n[6:]} {v}" for n, v in h.link_cores.items()))
P("H3", "partly", "csynth " + ", ".join(f"{n[6:]} {v} min" for n, v in h.t_csynth_min.items()) + " (<20 predicted: wide failed); disk "
  + ", ".join(f"{n[6:]} {v} GB" for n, v in h.disk_GB.dropna().items()))
P("H4", "3/4", "jet-r2-p16 predicted routing fail, built at 206.6 MHz (WNS −1.505 vs 300); big-r2-w8, cnn-r2-p16 built; wide-r4-p16 failed routing (congestion)")
P("H5", "1/2", f"big-r2-w8 {h.loc['rw-ho-big-r2-w8-lat','fmax_achieved']} MHz (225–250 predicted); cnn-r2-p16 {h.loc['rw-ho-cnn-r2-p16-lat','fmax_achieved']} MHz (250–300)")
P("H6", "held", "completed links " + ", ".join(f"{n[6:]} {v/60:.1f} h" for n, v in h[h.built].t_link_min.items())
  + f"; failing wide spent {h.loc['rw-ho-wide-r4-p16-lat','t_total_h']} h")

# -------- extra numbers for text --------
fail = b[b.outcome.str.startswith(("place", "route"))]
ex = [
  f"- build dirs {len(b)}, completed {b.built.sum()}, build-hours (t_total_h sum) {b.t_total_h.sum():.1f}",
  f"- placement/routing failures {len(fail)}: {fail.t_total_h.sum():.1f} h = {fail.t_total_h.sum()/b.t_total_h.sum()*100:.0f}% of build-hours; csynth available after {fail.t_generate_min.add(fail.t_csynth_min).min():.0f}–{fail.t_generate_min.add(fail.t_csynth_min).max():.0f} min",
  f"- completed-build link time {ok.t_link_min.min():.0f}–{ok.t_link_min.max():.0f} min, median {ok.t_link_min.median():.0f}",
  f"- process peak (non-OOM, non-stopped) {nonoom[~stopped].peak_anon_GiB.min()}–{nonoom[~stopped].peak_anon_GiB.max()} GiB; cgroup max {nonoom.peak_cg_GiB.max()}",
  f"- achieved clocks of built designs {ok.fmax_achieved.min()}–{ok.fmax_achieved.max()} MHz; at 300 MHz: {(ok.fmax_achieved==300).sum()}/{len(ok)}",
  f"- throughput (A) {cA.inferences_per_s.min()/1e6:.2f}–{cA.inferences_per_s.max()/1e6:.2f} M inf/s",
]
# post-hoc gate RISK region check on waves1-3 + held-out
b["risk"] = (b.hls_lut > 165000) & (b.hls_ff > 88000)
b["stop"] = (b.kernel_slr == "SLR2") & (b.hls_dsp > 2879)
cl = b[b.outcome.isin(["built", "place: DSP > SLR", "route: congestion", "route: overlaps"])]
ct = pd.crosstab(np.where(cl.stop, "STOP", np.where(cl.risk, "RISK", "GO")), cl.outcome)
ct.to_csv(f"{D}/tables/gate_region_waves123_ho.csv")
fpos_ff = b[b.built & (b.hls_lut > 165000) & (b.hls_ff <= 88000)].hls_ff.max(); fneg_ff = b[b.outcome.str.startswith("route")].hls_ff.min()
ex.append(f"- RISK FF threshold margin: largest FF among built LUT>165k designs outside RISK {fpos_ff:.0f}; smallest FF among routing failures {fneg_ff:.0f} (gap {(fneg_ff/fpos_ff-1)*100:.1f}%); gate c5 failed at FF 63k → FF does not separate")
lut_only = b[(b.hls_lut > 165000) & b.built]
ex.append(f"- LUT>165k alone would misclassify {len(lut_only)} built designs: " + ", ".join(f"{r.name[3:]} ({r.hls_lut/1e3:.0f}k, {r.fmax_achieved} MHz)" for r in lut_only.itertuples()))
r2 = b[(b.model.isin(["jet", "big", "wide"])) & b.p16 & (b.strat == "Latency") & (b.rf > 1)]
ex.append("- structural R2 (dense, Latency, 16-bit weights, RF>1): " + ", ".join(f"{r.name[3:]} → {r.outcome}" for r in r2.itertuples()) + "; plus gate jet-r4-p16-lat-c5 → route fail")


# ---------------- G (gate round) ----------------
gp = f"{D}/data/gate.csv"
gt = pd.read_csv(gp) if os.path.exists(gp) else None
if gt is not None:
    def g1(r):
        if r.gate == "STOP": return r.outcome.startswith("place")
        if r.gate == "RISK": return r.outcome.startswith("route") or (r.outcome == "built" and r.fmax_achieved < 220)
        return r.outcome == "built" and r.fmax_achieved >= 230
    gt["g1"] = gt.apply(g1, axis=1)
    P("G1", f"{gt.g1.sum()}/{len(gt)}", "; ".join(f"{r.name[5:]} {r.gate} → {r.outcome}" + (f" {r.fmax_achieved} MHz" if r.outcome == "built" else "")
          + (f" ({int(r.overlaps)} overlaps)" if pd.notna(r.overlaps) and r.overlaps != "" else "") + ("" if r.g1 else " ✗") for r in gt.itertuples()))
    c5 = gt[gt.name.str.endswith("c5")].iloc[0]
    P("G2", "core held / exception clause failed", f"at 5.0 ns the design still failed routing ({int(c5.overlaps)} overlaps vs 79,957 at 3.333 ns); "
      f"csynth FF fell 91.3k → {c5.hls_ff/1e3:.1f}k (out of RISK), LUT {c5.hls_lut/1e3:.1f}k, yet it failed")
    P("G3", "held (process) / cgroup touched limit", f"stage 1: ≤ {gt.s1_min.max()} min, peak process {gt.s1_peak_anon_GiB.max()} GiB, cgroup {gt.s1_peak_cg_GiB.max()} GiB (< 8 Gi); "
      f"stage 2: peak process {gt.s2_peak_anon_GiB.min()}–{gt.s2_peak_anon_GiB.max()} GiB; cgroup reached the 40 Gi limit (page cache) on wide-r8-p16-res without OOM")
    st_ = gt[gt.gate == "STOP"].iloc[0]
    P("G4", "held", f"STOP design: stage 1 = 0.39 h × 8 Gi (3.1 GiB-h, 0.8 core-h) vs its stage 2, run to confirm, 1.47 h × 40 Gi (58.7 GiB-h, 11.7 core-h) before VPL 30-859 "
      f"(link {st_.link_min} min, below the 1.5–12 h range quoted in G4). Gate miss c5: 9.66 h × 40 Gi (386 GiB-h); RISK wide-r4-w8 run to confirm: 13.45 h × 40 Gi (538 GiB-h)")
    ex.append(f"- gate round stage 2 link times: " + ", ".join(f"{r.name[5:]} {r.link_min} min ({r.s2_cpu.split(' Processor')[0].replace('Intel(R) Xeon(R) CPU ','Xeon ').replace('Intel(R) Xeon(R) ','Xeon ')})" for r in gt.itertuples()))
    ex.append("- wide-r4-w8-lat (8-bit weights, Latency, RF=4, LUT 322k) failed routing: 8-bit weights do not rescue the wide model, so the structural rule (16-bit weights) misses it; RISK caught it")

with open(f"{D}/scorecard.md", "w") as f:
    f.write("# Run-week prediction scorecard (computed from builds5.csv, card_A/B.csv)\n\n| id | verdict | evidence |\n|---|---|---|\n")
    f.write("\n".join(out) + "\n\n## Numbers for the text\n" + "\n".join(ex) + "\n\n## Gate regions applied to waves 1–3 + held-out (post hoc)\n\n" + ct.to_markdown() + "\n")

# ---------------- figures ----------------
plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": "#e4e3df",
                     "grid.linewidth": 0.6, "axes.edgecolor": "#52514e", "axes.labelcolor": "#0b0b0b", "xtick.color": "#52514e", "ytick.color": "#52514e",
                     "legend.frameon": False, "savefig.dpi": 300, "pdf.fonttype": 42})
C_BUILT, C_ROUTE, C_PLACE, C_GRAY = "#2a78d6", "#eb6834", "#1baf7a", "#8a8984"
def style(o):
    if o == "built": return dict(c=C_BUILT, marker="o", label="built")
    if o.startswith("route"): return dict(c=C_ROUTE, marker="X", label="routing failed")
    if o.startswith("place"): return dict(c=C_PLACE, marker="s", label="placement failed")
    if o == "OOM": return dict(c=C_GRAY, marker="v", label="OOM-killed (16 Gi)")
    return dict(c=C_GRAY, marker="^", label="stopped")
def legend_unique(ax, **kw):
    hs, ls = ax.get_legend_handles_labels(); d = dict(zip(ls, hs)); ax.legend(d.values(), d.keys(), **kw)

# Fig 1: peak memory per design
s = b.sort_values("peak_anon_GiB")
fig, ax = plt.subplots(figsize=(3.4, 5.0))
y = np.arange(len(s))
for yi, r in zip(y, s.itertuples()):
    st = style(r.outcome)
    ax.plot([r.peak_anon_GiB, r.peak_cg_GiB], [yi, yi], color="#c3c2b7", lw=1.5, zorder=1)
    ax.scatter(r.peak_anon_GiB, yi, s=22, color=st["c"], marker=st["marker"], label=st["label"], zorder=3, edgecolor="white", linewidth=0.5)
    ax.scatter(r.peak_cg_GiB, yi, s=10, color="#52514e", marker="|", zorder=2, label="cgroup peak (incl. page cache)")
ax.axvline(40 * 1.0737 / 1.0737, color="#0b0b0b", lw=0.8, ls="--"); ax.text(40.3, len(s) - 1, "40 Gi request", va="top", fontsize=7)
ax.axvline(16, color=C_GRAY, lw=0.8, ls=":"); ax.text(16.3, len(s) - 1, "16 Gi", va="top", fontsize=7, color=C_GRAY)
ax.set_yticks(y); ax.set_yticklabels([n[3:] for n in s.name], fontsize=5.5)
ax.set_xlabel("peak memory (GiB), reached in link"); ax.set_xlim(10, 44); ax.grid(axis="y", visible=False)
legend_unique(ax, loc="upper center", bbox_to_anchor=(0.35, -0.09), ncol=2, fontsize=6)
fig.tight_layout(); fig.savefig(f"{D}/fig/fig_memory.pdf"); fig.savefig(f"{D}/fig/fig_memory.png"); plt.close(fig)

# Fig 2: link time by CPU model for completed builds (node effect) — design-normalised view via repeats
fig, ax = plt.subplots(figsize=(3.4, 2.6))
cpu_short = lambda s: s.replace("AMD EPYC ", "EPYC ").replace("Intel(R) Xeon(R) CPU ", "Xeon ").replace("Intel(R) Xeon(R) ", "Xeon ").split(" @")[0].replace(" 64-Core Processor", "").replace(" 24-Core Processor", "").replace(" 32-Core Processor", "")
okc = ok.assign(cpu=ok.cpu_model.map(cpu_short))
order = okc.groupby("cpu").t_link_min.median().sort_values().index
for i, c in enumerate(order):
    g = okc[okc.cpu == c]
    ax.scatter(np.full(len(g), i) + np.random.default_rng(i).uniform(-.12, .12, len(g)), g.t_link_min, s=16, color=C_BUILT, edgecolor="white", lw=0.4, zorder=3)
rep = okc[okc.name.str.contains("jet-r4-p16-res")]
for r in rep.itertuples():
    ax.scatter(list(order).index(r.cpu), r.t_link_min, s=40, facecolor="none", edgecolor=C_ROUTE, lw=1.2, zorder=4)
ax.scatter([], [], s=40, facecolor="none", edgecolor=C_ROUTE, lw=1.2, label="same design (jet-r4-p16-res), 3 runs")
ax.set_xticks(range(len(order))); ax.set_xticklabels([f"{c} (n={(okc.cpu==c).sum()})" for c in order], fontsize=6, rotation=35, ha="right")
ax.set_ylabel("link time (min), completed builds"); ax.grid(axis="x", visible=False); ax.legend(fontsize=6, loc="upper left")
fig.tight_layout(); fig.savefig(f"{D}/fig/fig_link_by_cpu.pdf"); fig.savefig(f"{D}/fig/fig_link_by_cpu.png"); plt.close(fig)

# Fig 3: csynth LUT vs FF, outcome; gate RISK box
fig, ax = plt.subplots(figsize=(3.4, 2.8))
for r in b[b.hls_lut.notna() & ~stopped].itertuples():
    st = style(r.outcome)
    ax.scatter(r.hls_lut / 1e3, r.hls_ff / 1e3, s=26, color=st["c"], marker=st["marker"], label=st["label"], edgecolor="white", lw=0.5, zorder=3 if r.outcome == "built" else 4)
if gt is not None:
    for r in gt.itertuples():
        st = style(r.outcome)
        ax.scatter(r.hls_lut / 1e3, r.hls_ff / 1e3, s=46, facecolor="none", edgecolor=st["c"], marker=st["marker"], lw=1.2, zorder=5)
    ax.scatter([], [], s=46, facecolor="none", edgecolor="#52514e", marker="o", lw=1.2, label="gate round (hollow; colour = outcome)")
ax.add_patch(plt.Rectangle((165, 88), 400, 200, color="#eb6834", alpha=0.07, zorder=0))
ax.text(280, 163, "gate RISK region\n(LUT>165k, FF>88k; post hoc)", fontsize=6, color="#52514e", ha="center", va="top")
ax.set_xlabel("csynth LUT estimate (k)"); ax.set_ylabel("csynth FF estimate (k)")
ax.set_xlim(0, 400); ax.set_ylim(0, 170)
legend_unique(ax, fontsize=6, loc="upper left")
fig.tight_layout(); fig.savefig(f"{D}/fig/fig_csynth_outcome.pdf"); fig.savefig(f"{D}/fig/fig_csynth_outcome.png"); plt.close(fig)

# Fig 4: batch sweep time per input (session A), all built designs, one gray line each + median
fig, ax = plt.subplots(figsize=(3.4, 2.4))
ns = np.array([1, 10, 100, 1000, 10000])
M = np.array([[cA.loc[d, f"batch{n}_s"] / n * 1e6 for n in ns] for d in ids])
for row in M: ax.plot(ns, row, color="#c3c2b7", lw=0.8)
ax.plot(ns, np.median(M, axis=0), color=C_BUILT, lw=2, marker="o", ms=4, label=f"median of {len(ids)} designs")
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("batch size (inputs per call)"); ax.set_ylabel("time per input (µs)")
ax.legend(fontsize=6)
fig.tight_layout(); fig.savefig(f"{D}/fig/fig_batch_sweep.pdf"); fig.savefig(f"{D}/fig/fig_batch_sweep.png"); plt.close(fig)
print(open(f"{D}/scorecard.md").read())
