"""Cluster cost by build outcome, from NRP accounting (requested resources x wall time, per pod).
usage: python3 cost_by_outcome.py data/accounting2_20261020.json  -> tables/cost_by_outcome.csv, fig/fig_cost_by_outcome.{pdf,png}"""
import json, re, sys, os, collections
import pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
D = os.path.dirname(os.path.abspath(__file__))
acct = json.load(open(sys.argv[1]))
rows = json.loads([c for c in acct["calls"] if c["args"].get("granularity") == "pod"][0]["result"])["rows"]
b = pd.read_csv(f"{D}/data/builds5.csv").set_index("name")
g = pd.read_csv(f"{D}/data/gate.csv").set_index("name")

P = collections.defaultdict(lambda: collections.defaultdict(float)); node = {}
for x in rows:
    if x["pod_name"].startswith("rw-"):
        P[x["pod_name"]][x["resource"]] += x["usage"]; node[x["pod_name"]] = x["node"]
jobs = collections.defaultdict(list)
for p in P: jobs[re.sub(r"-[a-z0-9]{5}$", "", p)].append(p)

def cls(outcome):
    if outcome == "built": return "built"
    if outcome.startswith("place"): return "placement failed"
    if outcome.startswith("route"): return "routing failed"
    if outcome == "OOM": return "OOM-killed"
    return "stopped (superseded)"

out = []
for j, ps in jobs.items():
    if j in b.index: outcome, phase = b.loc[j, "outcome"], "run week"
    elif j.startswith("rw-g-"):
        n = re.sub(r"-s[12]$", "", j)
        outcome = "gate stage 1" if j.endswith("-s1") else g.loc[n, "outcome"]; phase = "gate round"
    elif j.startswith("rw-card"): outcome, phase = "card validation", "card"
    else: continue                              # prep / peek / csimcheck
    # when a job has 2 pods, the shorter, earlier-ending one is the lost pod (its node went away)
    ps = sorted(ps, key=lambda p: P[p]["wall"])
    for i, p in enumerate(ps):
        lost = len(ps) > 1 and i == 0 and not j.startswith("rw-card")
        c = "lost pod" if lost else (outcome if outcome in ("gate stage 1", "card validation") else cls(outcome))
        out.append(dict(job=j, pod=p, node=node[p], phase=phase, category=c, wall_h=P[p]["wall"],
                        cpu_core_h=P[p]["cpu"], mem_GB_h=P[p]["memory"], fpga_h=P[p].get("fpga", 0.0)))
t = pd.DataFrame(out)
t.to_csv(f"{D}/tables/cost_by_pod.csv", index=False)
order = ["built", "routing failed", "placement failed", "lost pod", "OOM-killed", "stopped (superseded)", "gate stage 1", "card validation"]
s = t.groupby("category")[["wall_h", "cpu_core_h", "mem_GB_h", "fpga_h"]].sum().reindex(order).dropna(how="all").fillna(0)
s["pods"] = t.groupby("category").size()
s["mem_share_pct"] = 100 * s.mem_GB_h / s.mem_GB_h.sum()
s.round(2).to_csv(f"{D}/tables/cost_by_outcome.csv")
print(s.round(2).to_string()); print("total", s[["wall_h", "cpu_core_h", "mem_GB_h", "fpga_h"]].sum().round(1).to_dict())
print("lost pods:", t[t.category == "lost pod"][["job", "node", "wall_h"]].to_string(index=False))

plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#52514e",
                     "xtick.color": "#52514e", "ytick.color": "#52514e", "savefig.dpi": 300, "pdf.fonttype": 42})
col = {"built": "#2a78d6", "routing failed": "#eb6834", "placement failed": "#1baf7a", "lost pod": "#8a8984",
       "OOM-killed": "#8a8984", "stopped (superseded)": "#c3c2b7", "gate stage 1": "#6250d6", "card validation": "#6250d6"}
fig, ax = plt.subplots(figsize=(3.4, 2.3))
y = range(len(s))[::-1]
ax.barh(list(y), s.mem_GB_h / 1e3, color=[col[c] for c in s.index], height=0.62)
for yi, (c, r) in zip(y, s.iterrows()):
    ax.text(r.mem_GB_h / 1e3 + 0.08, yi, f"{r.mem_share_pct:.1f}% · {r.wall_h:.1f} h · {int(r.pods)} pod{'s' if r.pods != 1 else ''}", va="center", fontsize=6.3, color="#0b0b0b")
ax.set_yticks(list(y)); ax.set_yticklabels(s.index, fontsize=7)
ax.set_xlabel("memory charged by NRP (TB-h = request × wall)", fontsize=7); ax.set_xlim(0, s.mem_GB_h.max() / 1e3 * 2.05)
ax.grid(axis="x", color="#e4e3df", lw=0.6); ax.set_axisbelow(True)
fig.tight_layout(); fig.savefig(f"{D}/fig/fig_cost_by_outcome.pdf"); fig.savefig(f"{D}/fig/fig_cost_by_outcome.png"); plt.close(fig)
