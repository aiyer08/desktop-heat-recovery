# Desktop Heat Recovery

Run a computer under a repeatable workload, move some of its cooling-loop heat into an insulated water tank,
and measure **what you gained** (Wh of heat) and **what it cost** (pump electricity, CPU temperature, speed).

```
Loop A (PC):    CPU → CPU water block → heat exchanger → radiator → pump/reservoir → CPU
Loop B (tank):  tank → small pump → heat exchanger → tank
```

## Folder map
| Folder | What's inside |
|---|---|
| `cad/scad/` | Editable OpenSCAD source (change the numbers at the top of each file) |
| `cad/stl/` | Ready-to-print STLs: tank lid, tube-probe clip (print 4), drip tray |
| `cad/build_stl.py` | Rebuilds the STLs in Python if you don't have OpenSCAD |
| `logger/pi_logger.py` | Raspberry Pi: reads DS18B20 probes → CSV |
| `logger/pc_logger.py` | PC: fixed workload + CPU temp/clock/power/throughput → CSV |
| `analysis/analyze.py` | Computes captured heat, pump cost, CPU trade-off, plot, résumé line |
| `data/` | **Simulated** sample data so you can test everything first |
| `docs/index.html` | Project website (works with GitHub Pages) |

## Quick start (test with fake data — no hardware)
```bash
pip install -r logger/requirements.txt
cd analysis
python make_sample_data.py
python analyze.py cooldown --pi ../data/sample_pi_cooldown.csv
python analyze.py run --pi ../data/sample_pi_recovery.csv --pc ../data/sample_pc_recovery.csv \
       --info ../data/sample_run.json --baseline ../data/sample_pc_baseline.csv
```

## Parts list (approx.)
| Item | Notes |
|---|---|
| Custom-loop PC parts | CPU block, pump/reservoir, 240 mm radiator, 10/13 mm soft tube, G1/4 fittings |
| Plate heat exchanger | Small brazed-plate unit with G1/4 or barb ports |
| Tank | 1–3 L food-safe container + foam/foil insulation, printed lid |
| Tank pump | 12 V DC mini pump, **fed from below** by the tank (never run dry) |
| 7 × DS18B20 waterproof probes | tank top, tank bottom, 4 at heat exchanger, 1 room |
| 4.7 kΩ resistor | 1-Wire pull-up between data and 3.3 V |
| Raspberry Pi | any model with GPIO |
| Wall-plug power meter | read kWh at start and end of each run |
| 12 V cartridge heater + PSU | stand-in heat source for the first dry-run tests |

## Probe wiring (all probes share 3 wires)
```
Probe red    → Pi pin 1  (3.3 V)
Probe black  → Pi pin 6  (GND)
Probe yellow → Pi pin 7  (GPIO4)   + 4.7 kΩ resistor from yellow to 3.3 V
```
Enable 1-Wire: `sudo raspi-config` → Interface Options → 1-Wire → reboot.
Run `python3 logger/pi_logger.py --list`, then copy `sensors.example.json` to `sensors.json` and fill in the IDs.

## Test procedure
1. **Baseline** – normal cooling: `python pc_logger.py --minutes 60 --out baseline_01.csv`. Note wall-meter kWh at start/end and room temp.
2. **Dry-run the plumbing** with the PC OFF (or with the 12 V heater). Leak-test for 24 h over paper towel.
3. **Recovery run** – same starting tank temperature every time. Run both loggers together:
   - Pi: `python3 pi_logger.py --out pi_run01.csv`
   - PC: `python pc_logger.py --minutes 60 --out pc_run01.csv`
4. **Cooldown test** – after a run, stop the pumps, log the tank for 2–3 h, then `analyze.py cooldown` gives `loss_k_per_h`.
5. **Fill in `run01.json`** (copy `data/sample_run.json`) and run `analyze.py run`.
6. **Repeat** ≥ 3 runs each and report the mean ± spread.

## The key formula
`heat captured (Wh) ≈ 1.163 × litres × temperature rise (°C)` (+ heat that leaked out, using `k`).
Captured heat is only "energy saved" if you use it for something that would otherwise need heating.

## Safety
Keep the tank and pump lower than and away from the PC, on the drip tray. Leak-test with the PC unplugged.
Never run a pump dry. Use a GFCI/RCD outlet if possible.

## Windows CPU temperature
`psutil` can't read CPU temperature on Windows. Log with HWiNFO or LibreHardwareMonitor at the same interval
and rename its CPU temperature column to `cpu_temp_c`.
