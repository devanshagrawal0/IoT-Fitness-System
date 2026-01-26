import time
from dataclasses import dataclass


@dataclass
class RepMetrics:
    reps_total: float
    reps_per_min: float
    est_power_watts: float
    ts: float


class RepEstimator:
    """
    Converts pulse counts into estimated reps and cadence.
    """
    def __init__(self, pulses_per_rep: int = 1, smoothing: float = 0.25):
        self.pulses_per_rep = max(1, int(pulses_per_rep))
        self.smoothing = float(smoothing)

        self._last_total_pulses = 0
        self._last_ts = time.time()
        self._rpm_ema = 0.0
        self._reps_total = 0.0

    def update(self, pulse_stats: dict) -> RepMetrics:
        now = pulse_stats["ts"]
        total_pulses = int(pulse_stats["total_pulses"])

        dt = max(1e-6, now - self._last_ts)
        dP = max(0, total_pulses - self._last_total_pulses)

        d_reps = dP / self.pulses_per_rep
        self._reps_total += d_reps

        reps_per_min_instant = (d_reps / dt) * 60.0

        alpha = self.smoothing
        self._rp_
