"""
Raspberry Pi temperature logger for the heat-recovery rig.

WHAT IT DOES: every few seconds it reads each DS18B20 probe and appends one row to a CSV file.
WHY: the tank temperature rise is what we turn into "Wh of heat captured", so it needs a
clean, timestamped record.

One-time Pi setup (turns on the 1-Wire bus the probes talk over):
    sudo raspi-config  ->  Interface Options  ->  1-Wire  ->  Enable  ->  reboot
Wiring: probe red -> 3.3V, black -> GND, yellow -> GPIO4, plus a 4.7k resistor between yellow and 3.3V.

Usage:
    python3 pi_logger.py --list                      # show probe IDs so you can label them
    python3 pi_logger.py --out run01.csv             # log until Ctrl+C
    python3 pi_logger.py --simulate --out test.csv   # no hardware? fake data to test the pipeline
"""
import argparse, csv, glob, json, math, os, random, time
from datetime import datetime

W1 = "/sys/bus/w1/devices/28-*/w1_slave"   # every DS18B20 shows up as a folder starting with 28-
HERE = os.path.dirname(os.path.abspath(__file__))

def find_probes():
    return {p.split("/")[-2]: p for p in glob.glob(W1)}

def read_probe(path):
    """Returns °C, or None if the reading failed the checksum (the 'YES' check)."""
    with open(path) as f:
        lines = f.read().strip().splitlines()
    if len(lines) < 2 or not lines[0].endswith("YES"):
        return None
    return int(lines[1].split("t=")[-1]) / 1000.0

def load_names():
    """sensors.json maps probe IDs to human names, e.g. {"28-0123": "tank_top"}."""
    p = os.path.join(HERE, "sensors.json")
    return json.load(open(p)) if os.path.exists(p) else {}

class Simulator:
    """Fake probes that behave roughly like the real rig, so you can test logging + analysis."""
    names = ["tank_top", "tank_bottom", "hx_hot_in", "hx_hot_out", "hx_cold_in", "hx_cold_out", "room"]
    def __init__(self): self.t0 = time.time(); self.tank = 22.0
    def read(self):
        mins = (time.time() - self.t0) / 60
        self.tank = 22 + 12 * (1 - math.exp(-mins / 40))
        base = {"tank_top": self.tank + 0.3, "tank_bottom": self.tank - 0.3, "hx_hot_in": self.tank + 14,
                "hx_hot_out": self.tank + 9, "hx_cold_in": self.tank, "hx_cold_out": self.tank + 3, "room": 22}
        return {k: round(v + random.gauss(0, 0.06), 3) for k, v in base.items()}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=f"pi_{datetime.now():%Y%m%d_%H%M%S}.csv")
    ap.add_argument("--interval", type=float, default=5.0, help="seconds between readings")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--simulate", action="store_true")
    a = ap.parse_args()

    if a.simulate:
        sim = Simulator(); cols = sim.names; read_all = sim.read
    else:
        probes, names = find_probes(), load_names()
        if not probes:
            raise SystemExit("No DS18B20 probes found. Is 1-Wire enabled and is the 4.7k resistor fitted?")
        if a.list:
            for pid, path in probes.items():
                print(pid, names.get(pid, "(unnamed)"), read_probe(path), "°C")
            return
        cols = [names.get(pid, pid) for pid in probes]
        def read_all():
            return {names.get(pid, pid): read_probe(path) for pid, path in probes.items()}

    new = not os.path.exists(a.out)
    with open(a.out, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["timestamp", "elapsed_s"] + cols)
        if new: w.writeheader()
        t0 = time.time()
        print(f"Logging to {a.out} every {a.interval}s. Ctrl+C to stop.")
        try:
            while True:
                row = {"timestamp": datetime.now().isoformat(timespec="seconds"),
                       "elapsed_s": round(time.time() - t0, 1), **read_all()}
                w.writerow(row); f.flush()           # flush = save now, so a crash loses nothing
                print(row)
                time.sleep(a.interval)
        except KeyboardInterrupt:
            print("Stopped.")

if __name__ == "__main__":
    main()
