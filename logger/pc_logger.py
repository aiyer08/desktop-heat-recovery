"""
PC-side logger + repeatable workload.

WHAT IT DOES: loads every CPU core with the SAME fixed math task and, every few seconds, records
how much work got done (throughput), CPU temperature, clock speed, and (on Linux/Intel/AMD) CPU power.
WHY: "work done per second" is how you detect thermal throttling — if the heat-recovery loop
makes the CPU hotter and it slows down, throughput drops compared to the baseline.

Usage:
    pip install psutil
    python pc_logger.py --minutes 60 --out baseline_01.csv
    python pc_logger.py --minutes 60 --out recovery_01.csv
Windows note: psutil can't read CPU temperature on Windows. Run LibreHardwareMonitor or HWiNFO
alongside and export its log; the analysis script can merge it (see README).
"""
import argparse, csv, glob, multiprocessing as mp, os, time
from datetime import datetime
import psutil

def worker(counter, stop):
    """Fixed, repeatable job: the same arithmetic forever. Each batch done adds 1 to the counter."""
    x = 0
    while not stop.is_set():
        for i in range(200_000):
            x = (x * 1103515245 + 12345 + i) & 0xFFFFFFFF
        with counter.get_lock():
            counter.value += 1

def cpu_temp():
    try:
        t = psutil.sensors_temperatures()
        for key in ("coretemp", "k10temp", "zenpower", "cpu_thermal", "acpitz"):
            if key in t and t[key]:
                return max(s.current for s in t[key])
    except (AttributeError, OSError):
        pass
    return None

class RAPL:
    """Reads CPU package energy from Linux's RAPL counter (Intel & most modern AMD). Gives watts."""
    def __init__(self):
        p = glob.glob("/sys/class/powercap/intel-rapl:0/energy_uj")
        self.path = p[0] if p else None; self.last = None
    def watts(self):
        if not self.path: return None
        try:
            e, t = int(open(self.path).read()), time.time()
        except PermissionError:
            return None                      # needs sudo on newer kernels
        prev, self.last = self.last, (e, t)
        if not prev or e < prev[0]: return None
        return (e - prev[0]) / 1e6 / (t - prev[1])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=60)
    ap.add_argument("--interval", type=float, default=5)
    ap.add_argument("--threads", type=int, default=os.cpu_count())
    ap.add_argument("--out", default=f"pc_{datetime.now():%Y%m%d_%H%M%S}.csv")
    a = ap.parse_args()

    counter, stop = mp.Value("q", 0), mp.Event()
    procs = [mp.Process(target=worker, args=(counter, stop), daemon=True) for _ in range(a.threads)]
    for p in procs: p.start()
    rapl, t0, last = RAPL(), time.time(), 0
    rapl.watts()
    print(f"Running workload on {a.threads} threads for {a.minutes} min -> {a.out}")
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "elapsed_s", "cpu_temp_c", "cpu_freq_mhz", "cpu_util_pct",
                    "cpu_power_w", "batches_per_s"])
        try:
            while time.time() - t0 < a.minutes * 60:
                time.sleep(a.interval)
                done = counter.value; rate = (done - last) / a.interval; last = done
                freq = psutil.cpu_freq()
                row = [datetime.now().isoformat(timespec="seconds"), round(time.time() - t0, 1),
                       cpu_temp(), round(freq.current) if freq else None,
                       psutil.cpu_percent(), rapl.watts(), round(rate, 2)]
                w.writerow(row); f.flush(); print(row)
        except KeyboardInterrupt:
            print("Stopped early.")
    stop.set()
    for p in procs: p.join(timeout=2)

if __name__ == "__main__":
    main()
