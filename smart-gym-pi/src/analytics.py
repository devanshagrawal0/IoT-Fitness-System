from dataclasses import dataclass

# Sampling intervals outside this range are treated as clock trouble rather
# than measurements. The loop runs at a few Hz, so anything under a
# millisecond is not a real interval, and anything over a minute means the
# process stalled or the clock jumped.
MIN_INTERVAL_S = 0.001
MAX_INTERVAL_S = 60.0


@dataclass
class RepMetrics:
    reps_total: float
    reps_per_min: float
    est_power_watts: float
    ts: float


class RepEstimator:
    """
    Converts pulse counts into estimated reps and cadence.

    A note on est_power_watts: the Hall-effect sensor observes movement only.
    Mechanical power requires force as well as motion, and this hardware cannot
    see load. est_power_watts is therefore cadence multiplied by an assumed
    work-per-rep constant, not a measurement. It is zero unless
    joules_per_rep is configured for the specific machine.
    """

    def __init__(self, pulses_per_rep: int = 1, smoothing: float = 0.25,
                 joules_per_rep: float = 0.0):
        self.pulses_per_rep = max(1, int(pulses_per_rep))
        self.smoothing = min(1.0, max(0.0, float(smoothing)))
        self.joules_per_rep = max(0.0, float(joules_per_rep))

        self._last_total_pulses = 0
        # Deliberately None, not time.time(). A rate needs two samples, and the
        # gap between construction and the first reading is not a measurement
        # interval. Seeding it with a clock reading makes the first cadence
        # wrong by however long startup took.
        self._last_ts = None
        self._rpm_ema = 0.0
        self._reps_total = 0.0

    def update(self, pulse_stats: dict) -> RepMetrics:
        now = pulse_stats["ts"]
        total_pulses = int(pulse_stats["total_pulses"])

        # First reading: record the baseline, report no cadence. There is
        # nothing to measure an interval against yet.
        if self._last_ts is None:
            self._last_ts = now
            self._last_total_pulses = total_pulses
            return RepMetrics(reps_total=self._reps_total, reps_per_min=0.0,
                              est_power_watts=0.0, ts=now)

        raw_dt = now - self._last_ts

        # A Raspberry Pi has no real-time clock. Its wall clock is wrong at
        # boot and steps when NTP syncs - sometimes backwards. A backwards or
        # implausibly small step would otherwise divide by ~zero and report an
        # absurd cadence. Skip the sample and re-baseline instead.
        if raw_dt <= 0.0 or raw_dt < MIN_INTERVAL_S:
            self._last_ts = now
            self._last_total_pulses = total_pulses
            return RepMetrics(reps_total=self._reps_total,
                              reps_per_min=self._rpm_ema,
                              est_power_watts=(self._rpm_ema / 60.0) * self.joules_per_rep,
                              ts=now)

        # A very long gap means the process stalled or the clock jumped
        # forward. Cap it so one pause cannot distort the average.
        dt = min(raw_dt, MAX_INTERVAL_S)

        # Clamped at 0 so a counter reset cannot produce negative reps.
        dP = max(0, total_pulses - self._last_total_pulses)

        d_reps = dP / self.pulses_per_rep
        self._reps_total += d_reps

        reps_per_min_instant = (d_reps / dt) * 60.0

        # Exponential moving average: raw cadence is noisy because a sample
        # window may catch one extra pulse or one fewer. alpha weights the
        # newest reading; 1 - alpha carries the history forward.
        alpha = self.smoothing
        self._rpm_ema = alpha * reps_per_min_instant + (1.0 - alpha) * self._rpm_ema

        # Proxy only. See the class docstring.
        est_power_watts = (self._rpm_ema / 60.0) * self.joules_per_rep

        # Advance the baseline. Without this, dt and dP grow without bound
        # and every reading after the first is wrong.
        self._last_total_pulses = total_pulses
        self._last_ts = now

        return RepMetrics(
            reps_total=self._reps_total,
            reps_per_min=self._rpm_ema,
            est_power_watts=est_power_watts,
            ts=now,
        )
