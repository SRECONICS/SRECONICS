#!/usr/bin/env python3
"""Real-time Flask dashboard for OBD-II telemetry."""
from flask import Flask, jsonify, render_template_string
import sqlite3, json

app = Flask(__name__)
DB  = "trips.db"

HTML = """
<!doctype html><html><head><meta charset=utf-8>
<title>Zero 2 W OBD Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  body{background:#0d1117;color:#e6edf3;font-family:monospace;padding:16px}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
  canvas{background:#161b22;border-radius:8px;padding:8px}
  .stat{background:#161b22;border-radius:8px;padding:16px;text-align:center}
  .val{font-size:2.5rem;color:#58a6ff}
</style></head><body>
<h2>🚗 OBD-II Live Dashboard — Pi Zero 2 W</h2>
<div class="grid" id="stats"></div>
<canvas id="chart" width="800" height="250"></canvas>
<script>
const labels=[],rpmData=[],spdData=[];
const ctx=document.getElementById('chart').getContext('2d');
const chart=new Chart(ctx,{type:'line',data:{labels,
  datasets:[{label:'RPM/10',data:rpmData,borderColor:'#58a6ff',tension:.3},
            {label:'Speed (km/h)',data:spdData,borderColor:'#3fb950',tension:.3}]},
  options:{animation:false,scales:{y:{beginAtZero:true}}}});
async function refresh(){
  const d=await(await fetch('/api/latest')).json();
  document.getElementById('stats').innerHTML=
    ['RPM','Speed (km/h)','Coolant (°C)','Throttle (%)'].map((k,i)=>
    `<div class=stat><div>${k}</div><div class=val>${[d.rpm?.toFixed(0),
      d.speed?.toFixed(1),d.coolant_temp?.toFixed(1),d.throttle?.toFixed(1)][i]??'—'}</div></div>`
    ).join('');
  if(labels.length>60){labels.shift();rpmData.shift();spdData.shift();}
  labels.push(d.ts?.slice(11,19)??' ');
  rpmData.push((d.rpm??0)/10);spdData.push(d.speed??0);
  chart.update();
}
setInterval(refresh,1000);refresh();
</script></body></html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/latest")
def latest():
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM telemetry ORDER BY id DESC LIMIT 1").fetchone()
    return jsonify(dict(row) if row else {})

@app.route("/api/trip")
def trip():
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM telemetry ORDER BY id DESC LIMIT 500").fetchall()
    return jsonify([dict(r) for r in rows])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
