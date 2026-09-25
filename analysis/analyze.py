"""
Turns your logged CSVs into the headline numbers.

    heat captured (Wh) ≈ 1.16 × litres × temperature rise (°C)
WHY 1.16? Water needs 4186 J to warm 1 kg by 1 °C. 1 Wh = 3600 J. 4186/3600 = 1.163 Wh per litre per °C.

Usage:
    python analyze.py run  --pi pi_run01.csv --pc pc_run01.csv --info run01.json [--baseline pc_baseline01.csv]
    python analyze.py cooldown --pi pi_cooldown.csv        # measures how fast the tank loses heat
"""
import argparse, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

WH_PER_L_PER_C = 4186 / 3600  # = 1.163

def tank_temp(df):
    """Average top & bottom probes so a warm layer at the top doesn't fool us (stratification)."""
    cols = [c for c in ("tank_top", "tank_bottom", "tank") if c in df]
    return df[cols].mean(axis=1)

def cooldown(pi_csv):
    """Newton's law of cooling: (T - T_room) shrinks exponentially. The slope of ln(T - T_room)
    vs time gives k. Bigger k = leakier insulation."""
    df = pd.read_csv(pi_csv); T = tank_temp(df); room = df["room"].mean() if "room" in df else 22.0
    hours = df["elapsed_s"] / 3600; y = np.log((T - room).clip(lower=0.05))
    k = -np.polyfit(hours, y, 1)[0]
    print(f"Tank loss constant k = {k:.4f} per hour  (put this in run.json as loss_k_per_h)")
    return k

def run(pi_csv, pc_csv, info_json, baseline_csv=None, plot="results.png"):
    info = json.load(open(info_json)); L = info["litres"]
    pi, pc = pd.read_csv(pi_csv), pd.read_csv(pc_csv)
    T = tank_temp(pi); room = pi["room"] if "room" in pi else pd.Series(22.0, index=pi.index)
    hours = (pi["elapsed_s"] - pi["elapsed_s"].iloc[0]) / 3600

    rise = T.iloc[-5:].mean() - T.iloc[:5].mean()          # average 5 samples at each end = less noise
    stored_wh = WH_PER_L_PER_C * L * rise
    k = info.get("loss_k_per_h", 0.0)                       # heat that leaked out during the run
    lost_wh = WH_PER_L_PER_C * L * k * np.trapezoid((T - room).clip(lower=0), hours)
    captured_wh = stored_wh + lost_wh

    run_h = hours.iloc[-1]
    pump_wh = info.get("pump_watts", 0) * run_h
    wall_wh = round((info["wall_kwh_end"] - info["wall_kwh_start"]) * 1000, 1) if "wall_kwh_end" in info else None
    res = {
        "label": info.get("label", "run"), "duration_h": round(run_h, 2), "litres": L,
        "tank_rise_c": round(rise, 2), "heat_stored_wh": round(stored_wh, 1),
        "heat_lost_wh": round(lost_wh, 1), "heat_captured_wh": round(captured_wh, 1),
        "pump_wh": round(pump_wh, 1), "wall_wh": wall_wh,
        "cpu_temp_max_c": pc["cpu_temp_c"].max(), "cpu_temp_mean_c": round(pc["cpu_temp_c"].mean(), 1),
        "throughput_mean": round(pc["batches_per_s"].mean(), 2),
        "heat_per_pump_wh": round(captured_wh / pump_wh, 1) if pump_wh else None,
    }
    if baseline_csv:
        b = pd.read_csv(baseline_csv)
        res["baseline_cpu_temp_max_c"] = b["cpu_temp_c"].max()
        res["baseline_throughput_mean"] = round(b["batches_per_s"].mean(), 2)
        res["throughput_change_pct"] = round(100 * (res["throughput_mean"] / res["baseline_throughput_mean"] - 1), 2)
        res["cpu_temp_max_change_c"] = round(res["cpu_temp_max_c"] - res["baseline_cpu_temp_max_c"], 1)

    fig, ax = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    ax[0].plot(hours * 60, T, label="tank (avg)"); ax[0].plot(pc["elapsed_s"] / 60, pc["cpu_temp_c"], label="CPU")
    if baseline_csv: ax[0].plot(b["elapsed_s"] / 60, b["cpu_temp_c"], "--", alpha=.6, label="CPU baseline")
    ax[0].set_ylabel("°C"); ax[0].legend(); ax[0].grid(alpha=.3)
    ax[1].plot(pc["elapsed_s"] / 60, pc["batches_per_s"], label="recovery")
    if baseline_csv: ax[1].plot(b["elapsed_s"] / 60, b["batches_per_s"], "--", alpha=.6, label="baseline")
    ax[1].set_ylabel("work / s"); ax[1].set_xlabel("minutes"); ax[1].legend(); ax[1].grid(alpha=.3)
    plt.tight_layout(); plt.savefig(plot, dpi=120)

    print(json.dumps(res, indent=2, default=float))
    print(f'\nResume line: "Recovered {captured_wh:.0f} Wh of heat during a {run_h*60:.0f}-minute workload while keeping '
          f'CPU temperature below {np.ceil(res["cpu_temp_max_c"]):.0f}°C; secondary pump consumed {pump_wh:.1f} Wh."')
    return res

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("--pi", required=True); r.add_argument("--pc", required=True)
    r.add_argument("--info", required=True); r.add_argument("--baseline"); r.add_argument("--plot", default="results.png")
    c = sub.add_parser("cooldown"); c.add_argument("--pi", required=True)
    a = ap.parse_args()
    if a.cmd == "run": run(a.pi, a.pc, a.info, a.baseline, a.plot)
    else: cooldown(a.pi)
