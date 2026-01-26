import time
from collections import deque

try:
    import RPi.GPIO as GPIO
except Exception:
    GPIO = None  # Lets you import on Windows/Mac for editing


class HallPulseCounter:
    """
    Counts pulses from a Hall-effect sensor using GPIO interrupts.
    Tracks recent pulse timestamps to estimate frequency.
    """
    def __init__(self, gpio_pin: int, pull_up: bool = True, debounce_ms: int = 5, window_seconds: float = 5.0):
        if GPIO is None:
            raise RuntimeError("RPi.GPIO not available. Run this on a Raspberry Pi with RPi.GPIO installed.")

        self.gpio_pin = gpio_pin
        self.window_seconds = window_seconds
        self._pulse_times = deque()
        self._pulse_count_total = 0

        GPIO.setmode(GPIO.BCM)
        pud = GPIO.PUD_UP if pull_up else GPIO.PUD_DOWN
        GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=pud)

        GPIO.add_event_detect(
            self.gpio_pin,
            GPIO.FALLING,
            callback=self._on_pulse,
            bouncetime=debounce_ms
        )

    def _on_pulse(self, channel):
        now = time.time()
        self._pulse_count_total += 1
        self._pulse_times.append(now)

        cutoff = now - self.window_seconds
        while self._pulse_times and self._pulse_times[0] < cutoff:
            self._pulse_times.popleft()

    def read(self):
        now = time.time()
        cutoff = now - self.window_seconds
        while self._pulse_times and self._pulse_times[0] < cutoff:
            self._pulse_times.popleft()

        pulses_in_window = len(self._pulse_times)
        freq_hz = pulses_in_window / self.window_seconds if self.window_seconds > 0 else 0.0

        return {
            "total_pulses": self._pulse_count_total,
            "pulses_in_window": pulses_in_window,
            "freq_hz": freq_hz,
            "window_seconds": self.window_seconds,
            "ts": now,
        }

    def cleanup(self):
        if GPIO is not None:
            GPIO.cleanup()
