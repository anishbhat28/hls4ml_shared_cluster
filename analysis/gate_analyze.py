"""Gate round (rw-g-*): stage 1 (2 CPU / 8 Gi: generate+csynth+package+gate) and stage 2 (8 CPU / 40 Gi: link).
usage: python3 -I gate_analyze.py <extracted builds dir> <results dir with logs/pod json> <out csv>"""
import os, re, csv, glob, json, sys
B, R, OUT = sys.argv[1:4]

def rd(p):
    try: return open(p, errors="replace").read()
    except Exception: return ""
def f(x):
    try: return float(x)
    except Exception: return None
def stages(p):
    return [(int(t), s) for t, s in (l.split(",") for l in rd(p).split() if "," in l)]
def mem(p):
    return list(csv.DictReader(open(p))) if os.path.exists(p) else []
def pod(p):
    j = json.loads(rd(p) or "{}"); items = j.get("items", [j])
    for it in items:
        if "spec" in it:
            cs = (it.get("status", {}).get("containerStatuses") or [{}])[0]
            return it["spec"].get("nodeName"), (cs.get("state", {}).get("terminated") or {}).get("reason")
    return None, None

rows = []
for d in sorted(glob.glob(f"{B}/rw-g-*")):
    n = os.path.basename(d); r = {"name": n}
    g = json.loads(rd(f"{d}/gate.json"))
    r.update(gate=g["verdict"].split(":")[0], hls_dsp=g["dsp"], hls_lut=g["lut"], hls_ff=g["ff"])
    s1 = stages(f"{d}/stages.csv")
    r["s1_min"] = round((s1[-1][0] - s1[0][0]) / 60, 1)
    t = {s: s1[i + 1][0] - ts for i, (ts, s) in enumerate(s1[:-1])}
    r["s1_csynth_min"] = round(t.get("csynth", 0) / 60, 1)
    m1 = mem(f"{d}/mem.csv")
    r["s1_peak_anon_GiB"] = round(max(f(x["mem_anon_bytes"]) or 0 for x in m1) / 2**30, 2)
    r["s1_peak_cg_GiB"] = round(max(f(x["mem_current_bytes"]) or 0 for x in m1) / 2**30, 2)
    s2 = stages(f"{d}/stages_link.csv")
    # a lost pod leaves an earlier unpack/link pair; time the last link attempt only
    last_unpack = max(i for i, (_, s) in enumerate(s2) if s == "unpack")
    s2l = s2[last_unpack:]
    li = next(i for i, (_, s) in enumerate(s2l) if s == "link")
    r["s2_attempts"] = sum(1 for _, s in s2 if s == "unpack")
    r["link_min"] = round((s2l[li + 1][0] - s2l[li][0]) / 60, 1)
    m2 = [x for x in mem(f"{d}/mem_link.csv") if (f(x["unix_time"]) or 0) >= s2l[0][0]]
    r["s2_peak_anon_GiB"] = round(max(f(x["mem_anon_bytes"]) or 0 for x in m2) / 2**30, 2)
    r["s2_peak_cg_GiB"] = round(max(f(x["mem_current_bytes"]) or 0 for x in m2) / 2**30, 2)
    lk = [x for x in m2 if x["stage"] == "link" and f(x["cpu_usage_usec"])]
    dt = f(lk[-1]["unix_time"]) - f(lk[0]["unix_time"])
    r["link_cores"] = round((f(lk[-1]["cpu_usage_usec"]) - f(lk[0]["cpu_usage_usec"])) / 1e6 / dt, 2)
    r["s1_node"], _ = pod(f"{R}/{n}-s1.pod.json")
    r["s2_node"], r["s2_pod_end"] = pod(f"{R}/{n}-s2.pod.json")
    cpus = re.findall(r"Model name:\s+(.*)", rd(f"{d}/config_link.txt")); r["s2_cpu"] = cpus[0].strip() if cpus else ""
    lg = rd(f"{R}/{n}-s2.log")
    done = any(s == "done" for _, s in s2l)
    m = re.search(r"There are (\d+) node overlaps", lg)
    r["outcome"] = ("built" if done else "place: DSP > SLR" if "VPL 30-859" in lg else
                    "route: congestion" if "VPL 35-3" in lg else "route: overlaps" if "VPL 35-2" in lg else "other")
    r["overlaps"] = int(m.group(1)) if m else ""
    m = re.search(r"Achieved Freq:\s*([\d.]+)", rd(f"{d}/xclbin_info.txt")); r["fmax_achieved"] = float(m.group(1)) if m else ""
    tm = rd(next(iter(glob.glob(f"{d}/*timing_summary*routed*.rpt")), ""))
    m = re.search(r"WNS\(ns\).*?\n\s*-+.*?\n\s*(-?[\d.]+)", tm); r["wns"] = float(m.group(1)) if m else ""
    db = rd(f"{d}/disk_bytes_before_cleanup.txt").split(); r["disk_GB"] = round(int(db[0]) / 1e9, 2) if db else ""
    rows.append(r)

w = csv.DictWriter(open(OUT, "w", newline=""), fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for r in rows: print(r)
