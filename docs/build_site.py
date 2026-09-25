"""Fills docs/template.html with CAD previews + results and writes docs/index.html.
Re-run after real experiments:  python build_site.py --pi ... --pc ... --info ... --baseline ..."""
import argparse, base64, json, math, os, sys
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "analysis")); import analyze

D = os.path.join(ROOT, "data")
ap = argparse.ArgumentParser()
ap.add_argument("--pi", default=f"{D}/sample_pi_recovery.csv"); ap.add_argument("--pc", default=f"{D}/sample_pc_recovery.csv")
ap.add_argument("--info", default=f"{D}/sample_run.json"); ap.add_argument("--baseline", default=f"{D}/sample_pc_baseline.csv")
ap.add_argument("--repo", default="https://github.com/aiyer08/desktop-heat-recovery")
a = ap.parse_args()

r = analyze.run(a.pi, a.pc, a.info, a.baseline, plot=os.path.join(D, "results.png"))
pi, pc, b = pd.read_csv(a.pi), pd.read_csv(a.pc), pd.read_csv(a.baseline)
step = max(1, len(pc) // 60)
chart = {"min": [round(x / 60) for x in pc["elapsed_s"][::step]],
         "tank": list(analyze.tank_temp(pi)[::step].round(2)), "cpu": list(pc["cpu_temp_c"][::step]),
         "base": list(b["cpu_temp_c"][::step])}

svg = open(os.path.join(HERE, "loops.svg")).read()
html = open(os.path.join(HERE, "template.html")).read()
for part in ("tank_lid", "tube_probe_clip", "hx_pump_tray"):
    img = base64.b64encode(open(os.path.join(ROOT, "cad", "previews", f"{part}.png"), "rb").read()).decode()
    html = html.replace(f"IMG_{part}", "data:image/png;base64," + img)
rep = {"SVG_DIAGRAM": svg, "CHART_DATA": json.dumps(chart), "#REPO_URL": a.repo,
       "R_CAPTURED": f'{r["heat_captured_wh"]:.0f}', "R_PUMP": f'{r["pump_wh"]:.1f}',
       "R_TMAX": f'{r["cpu_temp_max_c"]:.0f}', "R_BTMAX": f'{r["baseline_cpu_temp_max_c"]:.0f} °C',
       "R_THRU": f'{r["throughput_change_pct"]:+.1f}', "R_TCEIL": f'{math.ceil(r["cpu_temp_max_c"])}'}
for k, v in rep.items(): html = html.replace(k, v)
open(os.path.join(HERE, "index.html"), "w").write(html); print("wrote docs/index.html")
