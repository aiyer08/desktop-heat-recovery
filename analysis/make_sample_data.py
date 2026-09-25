"""Creates SIMULATED example data so you can test the analysis before building anything.
These numbers are made up (but physically reasonable). Replace them with your real runs."""
import json, math, random
import pandas as pd
random.seed(1)
L, room, dt, N = 2.0, 22.0, 5, 720               # 2 L tank, 1 hour at 5 s steps

def pc(offset_c, slow):
    rows = []
    for i in range(N):
        t = i * dt; warm = 1 - math.exp(-t / 120)
        rows.append(dict(elapsed_s=t, cpu_temp_c=round(38 + 30 * warm + offset_c * t / 3600 + random.gauss(0, .6), 1),
                         cpu_freq_mhz=4200, cpu_util_pct=100, cpu_power_w=round(95 + random.gauss(0, 2), 1),
                         batches_per_s=round(410 * (1 - slow * t / 3600) + random.gauss(0, 3), 2)))
    return pd.DataFrame(rows)

pc(0, 0).to_csv("../data/sample_pc_baseline.csv", index=False)
pc(3.5, 0.004).to_csv("../data/sample_pc_recovery.csv", index=False)

rows, T = [], room
for i in range(N):
    t = i * dt; T = room + 13.5 * (1 - math.exp(-t / 3600 / 1.1))
    rows.append(dict(elapsed_s=t, tank_top=round(T + .3 + random.gauss(0, .05), 2), tank_bottom=round(T - .3 + random.gauss(0, .05), 2),
                     hx_hot_in=round(T + 12, 2), hx_hot_out=round(T + 8, 2), hx_cold_in=round(T, 2), hx_cold_out=round(T + 3, 2), room=room))
pd.DataFrame(rows).to_csv("../data/sample_pi_recovery.csv", index=False)

rows = [dict(elapsed_s=i * 60, tank_top=round(room + 13 * math.exp(-0.18 * i / 60) + random.gauss(0, .04), 2),
             tank_bottom=round(room + 13 * math.exp(-0.18 * i / 60) + random.gauss(0, .04), 2), room=room) for i in range(180)]
pd.DataFrame(rows).to_csv("../data/sample_pi_cooldown.csv", index=False)

json.dump({"label": "SIMULATED sample run", "litres": L, "pump_watts": 4.0, "loss_k_per_h": 0.18,
           "wall_kwh_start": 12.300, "wall_kwh_end": 12.462}, open("../data/sample_run.json", "w"), indent=2)
print("Sample data written to ../data/")
