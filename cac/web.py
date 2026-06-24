"""A tiny, dependency-free web UI for the pipeline.

Uses only Python's standard library (``http.server``) to stay true to the
project's "nothing to install" promise. Serves one HTML page plus a handful of
JSON endpoints that wrap the same functions the CLI uses:

    GET  /            -> the dashboard page
    GET  /api/state   -> current DB stats + the latest run's cohorts and lift
    POST /api/seed    -> generate + load synthetic data   (body: {customers, seed})
    POST /api/run     -> run the decisioning pipeline
    POST /api/reset   -> delete the database

Start it with:  python -m cac.cli serve
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from . import data, pipeline
from .db import connect, init_db, reset_db


def get_state() -> dict:
    """Read everything the dashboard needs in one shot."""
    conn = connect()
    init_db(conn)  # ensure tables exist (e.g. right after a reset)

    def count(table: str) -> int:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    stats = {
        "customers": count("customers"),
        "orders": count("orders"),
        "profiles": count("customer_profiles"),
        "decisions": count("decisions"),
    }

    latest = conn.execute(
        "SELECT run_id FROM measurements ORDER BY rowid DESC LIMIT 1"
    ).fetchone()
    run_id = latest["run_id"] if latest else None

    overall, cohorts, sample = None, [], []
    if run_id:
        row = conn.execute(
            "SELECT * FROM measurements WHERE run_id = ? AND scope = 'overall'",
            (run_id,),
        ).fetchone()
        overall = dict(row) if row else None

        meas = {
            m["label"]: m
            for m in conn.execute(
                "SELECT * FROM measurements WHERE run_id = ? AND scope = 'cohort'",
                (run_id,),
            ).fetchall()
        }
        rows = conn.execute(
            """SELECT cohort,
                      COUNT(*)                              AS size,
                      SUM(holdout_group = 'treatment')      AS sent,
                      SUM(holdout_group = 'control')        AS control,
                      SUM(holdout_group = 'suppressed')     AS suppressed,
                      SUM(converted)                        AS conversions
               FROM decisions WHERE run_id = ?
               GROUP BY cohort ORDER BY size DESC""",
            (run_id,),
        ).fetchall()
        for r in rows:
            m = meas.get(r["cohort"])
            cohorts.append({
                "cohort": r["cohort"],
                "size": r["size"],
                "sent": r["sent"] or 0,
                "control": r["control"] or 0,
                "suppressed": r["suppressed"] or 0,
                "conversions": r["conversions"] or 0,
                "treat_rate": m["treat_rate"] if m else None,
                "ctrl_rate": m["ctrl_rate"] if m else None,
                "abs_lift": m["abs_lift"] if m else None,
                "p_value": m["p_value"] if m else None,
            })

        sample = [
            dict(r)
            for r in conn.execute(
                """SELECT customer_id, cohort, holdout_group, discount, offer_code,
                          converted, revenue
                   FROM decisions WHERE run_id = ?
                   ORDER BY customer_id LIMIT 12""",
                (run_id,),
            ).fetchall()
        ]

    conn.close()
    return {"stats": stats, "run_id": run_id, "overall": overall,
            "cohorts": cohorts, "sample": sample}


class Handler(BaseHTTPRequestHandler):
    # HTTP/1.0 => connection closes per request, so the single-threaded server
    # never blocks on a kept-alive socket.
    protocol_version = "HTTP/1.0"

    def log_message(self, fmt: str, *args) -> None:  # quieter, single-line logs
        print(f"  {self.command} {self.path}")

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload: dict, status: int = 200) -> None:
        self._send(status, json.dumps(payload).encode(), "application/json")

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return {}

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self._send(200, PAGE.encode(), "text/html; charset=utf-8")
        elif self.path == "/api/state":
            self._json(get_state())
        elif self.path == "/favicon.ico":
            self._send(204, b"", "image/x-icon")
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        try:
            if self.path == "/api/seed":
                body = self._read_body()
                customers = int(body.get("customers") or 5000)
                seed = int(body.get("seed") or 7)
                counts = data.seed(max(1, customers), seed)
                self._json({"ok": True, **counts})
            elif self.path == "/api/run":
                self._json({"ok": True, **pipeline.run()})
            elif self.path == "/api/reset":
                reset_db()
                self._json({"ok": True})
            else:
                self._json({"error": "not found"}, 404)
        except Exception as exc:  # surface errors to the UI instead of a blank 500
            self._json({"error": str(exc)}, 500)


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = HTTPServer((host, port), Handler)
    url = f"http://{host}:{port}"
    print(f"CAC dashboard running at {url}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping…")
    finally:
        server.server_close()


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>CAC mini — decisioning</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 32px;
    font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #0d1117; color: #e6edf3;
  }
  .wrap { max-width: 980px; margin: 0 auto; }
  h1 { font-size: 22px; margin: 0 0 4px; }
  h2 { font-size: 15px; margin: 28px 0 10px; color: #c9d1d9; font-weight: 600; }
  .sub { color: #8b949e; margin: 0 0 24px; }
  .panel { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; }
  .controls { display: flex; flex-wrap: wrap; gap: 10px; align-items: flex-end; }
  .field { display: flex; flex-direction: column; gap: 4px; }
  .field label { font-size: 12px; color: #8b949e; }
  input {
    width: 110px; padding: 7px 9px; border-radius: 6px;
    border: 1px solid #30363d; background: #0d1117; color: #e6edf3; font-size: 14px;
  }
  button {
    padding: 8px 14px; border-radius: 6px; border: 1px solid #30363d;
    background: #21262d; color: #e6edf3; font-size: 14px; cursor: pointer;
  }
  button:hover:not(:disabled) { border-color: #8b949e; }
  button:disabled { opacity: .5; cursor: not-allowed; }
  button.primary { background: #1f6feb; border-color: #1f6feb; }
  button.danger { background: #21262d; border-color: #6e2630; color: #ff7b72; }
  .status { margin: 12px 0 0; color: #8b949e; min-height: 18px; font-size: 13px; }
  .strip { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 8px; }
  .stat { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px 14px; }
  .stat .v { font-size: 22px; font-weight: 600; }
  .stat .l { font-size: 12px; color: #8b949e; margin-top: 2px; }
  .big { display: flex; gap: 28px; flex-wrap: wrap; align-items: baseline; }
  .big .lift { font-size: 30px; font-weight: 700; color: #3fb950; }
  .big .meta { color: #8b949e; font-size: 13px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: right; padding: 8px 10px; border-bottom: 1px solid #21262d; }
  th:first-child, td:first-child { text-align: left; }
  th { color: #8b949e; font-weight: 500; }
  .tag { font-size: 11px; color: #d29922; border: 1px solid #5a4413; border-radius: 999px; padding: 1px 7px; }
  .muted { color: #6e7681; }
  .pos { color: #3fb950; } .neg { color: #ff7b72; }
  code { background: #0d1117; border: 1px solid #30363d; border-radius: 4px; padding: 1px 5px; font-size: 12px; }
</style>
</head>
<body>
<div class="wrap">
  <h1>CAC mini — customer decisioning</h1>
  <p class="sub">Seed synthetic data, run the pipeline, and read the incremental lift against the held-out control.</p>

  <div class="panel">
    <div class="controls">
      <div class="field"><label for="customers">Customers</label><input id="customers" type="number" value="5000" min="1" /></div>
      <div class="field"><label for="seed">Seed</label><input id="seed" type="number" value="7" /></div>
      <button id="btn-seed" onclick="doSeed()">Seed data</button>
      <button id="btn-run" class="primary" onclick="doRun()">Run pipeline</button>
      <span style="flex:1"></span>
      <button id="btn-reset" class="danger" onclick="doReset()">Reset</button>
    </div>
    <p id="status" class="status"></p>
  </div>

  <div class="strip" id="strip"></div>
  <div id="overall"></div>
  <h2>Cohorts &amp; lift</h2>
  <div class="panel" id="cohorts"></div>
  <h2>Sample decisions</h2>
  <div class="panel" id="sample"></div>
</div>

<script>
const $ = (id) => document.getElementById(id);
const fmt = (n) => n == null ? "—" : Number(n).toLocaleString();
const pct = (x) => x == null ? "—" : (x * 100).toFixed(1) + "%";
const pp  = (x) => x == null ? "—" : (x >= 0 ? "+" : "") + (x * 100).toFixed(1) + "pp";

let busy = false;
function setBusy(b, msg) {
  busy = b;
  ["btn-seed","btn-run","btn-reset"].forEach(id => $(id).disabled = b);
  if (msg !== undefined) $("status").textContent = msg;
}

async function api(path, body) {
  const opts = body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {};
  const res = await fetch(path, opts);
  const data = await res.json();
  if (!res.ok || data.error) throw new Error(data.error || ("HTTP " + res.status));
  return data;
}

async function doSeed() {
  if (busy) return;
  setBusy(true, "Seeding…");
  try {
    const r = await api("/api/seed", { customers: parseInt($("customers").value), seed: parseInt($("seed").value) });
    setBusy(false, `Seeded ${fmt(r.customers)} customers and ${fmt(r.orders)} orders. Now click “Run pipeline”.`);
    await refresh();
  } catch (e) { setBusy(false, "Error: " + e.message); }
}

async function doRun() {
  if (busy) return;
  setBusy(true, "Running pipeline…");
  try {
    const r = await api("/api/run", {});
    setBusy(false, `Run ${r.run_id} complete — ${fmt(r.targeted)} customers targeted.`);
    await refresh();
  } catch (e) { setBusy(false, "Error: " + e.message); }
}

async function doReset() {
  if (busy) return;
  if (!confirm("Delete the database (cac.db)?")) return;
  setBusy(true, "Resetting…");
  try {
    await api("/api/reset", {});
    setBusy(false, "Database reset. Seed again to start over.");
    await refresh();
  } catch (e) { setBusy(false, "Error: " + e.message); }
}

function renderStrip(s) {
  const st = s.stats;
  $("strip").innerHTML = [
    ["Customers", fmt(st.customers)],
    ["Orders", fmt(st.orders)],
    ["Profiles", fmt(st.profiles)],
    ["Run", s.run_id ? s.run_id : "—"],
  ].map(([l, v]) => `<div class="stat"><div class="v">${v}</div><div class="l">${l}</div></div>`).join("");
}

function renderOverall(s) {
  const o = s.overall;
  if (!o) { $("overall").innerHTML = ""; return; }
  const cls = o.abs_lift >= 0 ? "lift" : "lift neg";
  $("overall").innerHTML = `<div class="panel" style="margin-top:16px"><div class="big">
      <div><div class="${cls}">${pp(o.abs_lift)}</div><div class="meta">incremental lift</div></div>
      <div><div style="font-size:18px">${pct(o.treat_rate)}</div><div class="meta">treatment (${fmt(o.t_n)})</div></div>
      <div><div style="font-size:18px">${pct(o.ctrl_rate)}</div><div class="meta">control (${fmt(o.c_n)})</div></div>
      <div><div style="font-size:18px">${o.p_value == null ? "—" : o.p_value.toFixed(4)}</div><div class="meta">p-value</div></div>
    </div></div>`;
}

function renderCohorts(s) {
  if (!s.cohorts.length) { $("cohorts").innerHTML = `<span class="muted">No run yet. Seed, then run.</span>`; return; }
  const head = `<tr><th>Cohort</th><th>Size</th><th>Sent</th><th>Control</th><th>Suppressed</th><th>Treat</th><th>Ctrl</th><th>Lift</th><th>p</th></tr>`;
  const body = s.cohorts.map(c => {
    const quiet = c.sent === 0;
    const name = c.cohort + (quiet ? ' <span class="tag">stay quiet</span>' : '');
    const liftCls = c.abs_lift == null ? "" : (c.abs_lift >= 0 ? "pos" : "neg");
    return `<tr>
      <td>${name}</td><td>${fmt(c.size)}</td><td>${fmt(c.sent)}</td>
      <td>${fmt(c.control)}</td><td>${fmt(c.suppressed)}</td>
      <td>${pct(c.treat_rate)}</td><td>${pct(c.ctrl_rate)}</td>
      <td class="${liftCls}">${pp(c.abs_lift)}</td>
      <td>${c.p_value == null ? "—" : c.p_value.toFixed(3)}</td>
    </tr>`;
  }).join("");
  $("cohorts").innerHTML = `<table>${head}${body}</table>`;
}

function renderSample(s) {
  if (!s.sample.length) { $("sample").innerHTML = `<span class="muted">—</span>`; return; }
  const head = `<tr><th>Customer</th><th>Cohort</th><th>Group</th><th>Discount</th><th>Code</th><th>Converted</th><th>Revenue</th></tr>`;
  const body = s.sample.map(d => `<tr>
      <td>${d.customer_id}</td><td>${d.cohort}</td><td>${d.holdout_group}</td>
      <td>${d.discount ? d.discount + "%" : "—"}</td><td>${d.offer_code ? "<code>"+d.offer_code+"</code>" : "—"}</td>
      <td>${d.converted ? "yes" : "no"}</td><td>${d.revenue ? "$" + d.revenue.toFixed(2) : "—"}</td>
    </tr>`).join("");
  $("sample").innerHTML = `<table>${head}${body}</table>`;
}

async function refresh() {
  const s = await api("/api/state");
  renderStrip(s); renderOverall(s); renderCohorts(s); renderSample(s);
}

refresh().catch(e => $("status").textContent = "Error: " + e.message);
</script>
</body>
</html>"""
