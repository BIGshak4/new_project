"""Five distinct observed error reports within a monotonic ten-second window.

Each 1 denotes one new incident; a sustained hardware level is a different input.
Default interval is (now-10s, now]; closed_left=True instead includes the cutoff.
"""

from collections import deque

TEN_SECONDS_NS = 10_000_000_000


class ErrorTimeWindow:
    def __init__(self, *, window_ns=TEN_SECONDS_NS, threshold=5, closed_left=False):
        if type(window_ns) is not int or window_ns <= 0 or type(threshold) is not int or threshold < 1:
            raise ValueError("Positive integer window and threshold required")
        self.window_ns = window_ns
        self.threshold = threshold
        self.closed_left = closed_left
        self.errors = deque(maxlen=threshold)
        self.last_now = None

    def observe(self, error, now_ns):
        if error not in (0, 1) or type(now_ns) is not int or now_ns < 0:
            raise ValueError("Binary report and nonnegative integer timestamp required")
        if self.last_now is not None and now_ns < self.last_now:
            raise ValueError("Timestamps must be monotonic, allowing ties")
        self.last_now = now_ns
        cutoff = now_ns - self.window_ns
        while self.errors and (self.errors[0] < cutoff if self.closed_left else self.errors[0] <= cutoff):
            self.errors.popleft()
        if error:
            self.errors.append(now_ns)
        return len(self.errors) == self.threshold


def wait_for_error_threshold(check_error, monotonic_ns):
    monitor = ErrorTimeWindow()
    while True:
        report = check_error()
        observed_at = monotonic_ns()
        if monitor.observe(report, observed_at):
            return observed_at
