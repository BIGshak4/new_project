"""Educational local tracking core, not a complete or qualified motor controller.

Quadrants: top-left, top-right, bottom-left, bottom-right. Positive azimuth
command moves the panel normal toward the sensor's right side; positive
elevation moves upward. Real wiring/calibration must establish these signs.
Outputs are requested angular rates in degrees/second, not GPIO/PWM writes.
"""
from math import isfinite


class TrackingCore:
    def __init__(self):
        self.fault = False

    def reset_after_check(self):
        self.fault = False

    def step(self, sample, now):
        stop = {"mode": "FAULT", "az_rate": 0.0, "el_rate": 0.0}
        if self.fault:
            return stop
        try:
            stamp = sample["stamp"]
            azimuth, elevation = sample["angles"]
            tl, tr, bl, br = sample["light"]
            confident = sample["confident"]
            scalars = (now, stamp, azimuth, elevation, tl, tr, bl, br)
            if (any(type(v) not in (int, float) or not isfinite(v) for v in scalars)
                    or type(confident) is not bool
                    or not 0 <= now - stamp <= 0.5
                    or not -90 <= azimuth <= 90 or not 0 <= elevation <= 90
                    or min(tl, tr, bl, br) < 0):
                raise ValueError("invalid or stale measurement")
            total = tl + tr + bl + br
            if not isfinite(total):
                raise ValueError("sensor total overflow")
        except (KeyError, TypeError, ValueError, OverflowError):
            self.fault = True
            return stop
        if total < 1.0:
            return {"mode": "HOLD_DARK", "az_rate": 0.0, "el_rate": 0.0}
        if not confident:
            return {"mode": "HOLD_UNCERTAIN", "az_rate": 0.0, "el_rate": 0.0}
        ex = ((tr + br) - (tl + bl)) / total
        ey = ((tl + tr) - (bl + br)) / total

        def rate(error):
            return 0.0 if abs(error) <= 0.02 else max(-2.0, min(2.0, 4.0 * error))

        az_rate, el_rate = rate(ex), rate(ey)
        if (azimuth <= -90 and az_rate < 0) or (azimuth >= 90 and az_rate > 0):
            az_rate = 0.0
        if (elevation <= 0 and el_rate < 0) or (elevation >= 90 and el_rate > 0):
            el_rate = 0.0
        return {"mode": "TRACK_LOCAL", "az_rate": az_rate, "el_rate": el_rate}
