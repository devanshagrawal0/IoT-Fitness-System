import os
import csv
import time
import json
from datetime import datetime

from sensor import HallPulseCounter
from analytics import RepEstimator
from client_http import HttpTelemetryClient


# ====== CONFIG via ENV VARS ======
GPIO_PIN = int(os.getenv("SMARTGYM_GPIO_PIN", "17"))          # BCM pin
PULSES_PER_REP = int(os.getenv("SMARTGYM_PULSES_PER_REP", "1"))

ENDPOINT_URL = os.getenv("SMARTGYM_ENDPOINT_URL", "")        # optional
API_KEY = os.getenv("SMARTGYM_API_KEY", "")                  # optional

LOOP_HZ = float(os.getenv("SMARTGYM_LOOP_HZ", "4"))          # loop rate
WINDOW_SECONDS = float(os.getenv("SMARTGYM_WINDOW_SECONDS", "5.0"))

DATA_DIR = os.getenv("SMARTGYM_DATA_DIR", "./data")
CSV_PATH = os.path.join(DATA_DIR, "telemetry.csv")
# ================================


def ensure_csv(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow([
                "iso_time",
                "reps_total",
                "reps_per_min",
                "est_power_watts",
                "freq_hz",
                "pulses_in_window",
                "total_pulses"
            ])


def append_csv(path: str, row: dict):
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            row["iso_time"],
            f"{row['reps_total']:.3f}",
            f"{row['reps_per_min']:.3f}",
            f"{row['est_power_watts']:.3f}",
            f"{row['freq_hz']:.3f}",
            int(row["pulses_in_window"]),
            int(row["total_pulses"]),
        ])


def main():
    ensure_csv(CSV_PATH)

    sensor = HallPulseCounter(gpio_pin=GPIO_PIN, debounce_ms=5, window_seconds=WINDOW_SECONDS)
    estimator = RepEstimator(pulses_per_rep=PULSES_PER_REP, smoothing=0.25)

    client = None
    if ENDPOINT_URL.strip():
        client = HttpTelemetryClient(endpoint_url=ENDPOINT_URL, api_key=API_KEY or None)

    period = 1.0 / max(0.1, LOOP_HZ)

    try:
        while True:
            pulse_stats = sensor.read()
            metrics = estimator.update(pulse_stats)

            payload = {
                "device_id": os.getenv("SMARTGYM_DEVICE_ID", "pi-001"),
                "iso_time": datetime.utcfromtimestamp(metrics.ts).isoformat() + "Z",
                "reps_total": metrics.reps_total,
                "reps_per_min": metrics.reps_per_min,
                "est_power_watts": metrics.est_power_watts,
                "freq_hz": pulse_stats["freq_hz"],
                "pulses_in_window": pulse_stats["pulses_in_window"],
                "total_pulses": pulse_stats["total_pulses"],
            }

            # local CSV log
            append_csv(CSV_PATH, payload)

            # optional network send
            if client:
                ok = client.send(payload)
                print(json.dumps({"sent": ok, **payload}))

            time.sleep(period)

    except KeyboardInterrupt:
        pass
    finally:
        sensor.cleanup()


if __name__ == "__main__":
    main()
