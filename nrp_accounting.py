#!/usr/bin/env python3
"""Query the NRP accounting MCP server (read-only) and save everything to accounting.json.
Standard library only (plain JSON-RPC over HTTP, no `mcp` package needed).

Usage (on your Mac):
    python3 nrp_accounting.py            # optional: --token XXX if the server returns 401
"""
import json, sys, ssl, urllib.request, urllib.error, datetime as dt

URL = "https://nrp-accounting-mcp.nrp-nautilus.io/"
NS = "hls4ml-nrp"
TODAY = dt.date.today()
D = lambda days: (TODAY - dt.timedelta(days=days)).isoformat()
T = TODAY.isoformat()

# (tool, args) - args a tool doesn't accept are dropped; failures are recorded, not fatal
CALLS = [
    ("get_latest_data_date", {}),
    ("list_filter_values", {"field": "resource"}),
    ("list_filter_values", {"field": "node", "resource": "fpga", "start_date": D(90), "end_date": T}),
    # cluster-wide FPGA use (last 90 days)
    ("top_resource_consumers", {"resource": "fpga", "group_by": "namespace", "limit": 50, "start_date": D(90), "end_date": T}),
    ("top_resource_consumers", {"resource": "fpga", "group_by": "node", "limit": 50, "start_date": D(90), "end_date": T}),
    ("query_resource_usage", {"resource": "fpga", "group_by": ["node", "date"], "start_date": D(90), "end_date": T}),
    # our namespace (last 30 days)
    ("get_namespace_summary", {"namespace": NS, "start_date": D(30), "end_date": T}),
    *[("get_namespace_daily_trend", {"namespace": NS, "resource": r, "days": 30}) for r in ("cpu", "memory", "fpga")],
    *[("top_nodes_for_namespace", {"namespace": NS, "resource": r, "start_date": D(30), "end_date": T}) for r in ("cpu", "fpga")],
]

token = sys.argv[sys.argv.index("--token") + 1] if "--token" in sys.argv else None
session = None
_id = 0

def rpc(method, params=None, notify=False):
    global session, _id
    msg = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    if not notify:
        _id += 1
        msg["id"] = _id
    h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
         "MCP-Protocol-Version": "2025-03-26"}
    if session: h["Mcp-Session-Id"] = session
    if token:   h["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(URL, data=json.dumps(msg).encode(), headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120, context=ssl.create_default_context()) as r:
            session = r.headers.get("Mcp-Session-Id") or session
            body = r.read().decode()
            ctype = r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} on {method}: {e.read().decode()[:300]}")
    if notify:
        return None
    if "text/event-stream" in ctype:   # take the JSON-RPC response out of the SSE stream
        for line in body.splitlines():
            if line.startswith("data:"):
                d = json.loads(line[5:].strip())
                if d.get("id") == msg["id"]:
                    return d
        raise RuntimeError(f"no response in stream: {body[:300]}")
    return json.loads(body)

init = rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                          "clientInfo": {"name": "hls4ml-nrp-accounting", "version": "1"}})
print("server:", init.get("result", {}).get("serverInfo"))
rpc("notifications/initialized", notify=True)

out = {"queried_at": dt.datetime.now().isoformat(), "server": init.get("result"), "tools": {}, "calls": []}
for t in rpc("tools/list", {})["result"]["tools"]:
    out["tools"][t["name"]] = {"description": t.get("description"), "inputSchema": t.get("inputSchema")}
print("tools:", ", ".join(out["tools"]))

for name, args in CALLS:
    if name not in out["tools"]:
        print(f"skip {name} (not offered)"); continue
    props = (out["tools"][name]["inputSchema"] or {}).get("properties", {})
    a = {k: v for k, v in args.items() if k in props}
    try:
        r = rpc("tools/call", {"name": name, "arguments": a})
        if "error" in r:
            res, err = json.dumps(r["error"]), True
        else:
            res = "\n".join(c.get("text", "") for c in r["result"].get("content", []))
            err = bool(r["result"].get("isError"))
    except Exception as e:
        res, err = repr(e), True
    out["calls"].append({"tool": name, "args": a, "error": err, "result": res})
    print(("ERR  " if err else "ok   ") + f"{name} {a}" + (f": {res[:200]}" if err else ""))

json.dump(out, open("accounting.json", "w"), indent=1)
print("saved accounting.json - send it to Claude")
