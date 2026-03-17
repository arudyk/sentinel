"""PiSugar 3 battery monitor.

Primary:  queries pisugar-server via Unix socket (/tmp/pisugar-server.sock)
Fallback: direct I2C read (register 0x2A @ address 0x57)
Dev mode: returns None for all values when neither is available.
"""

from __future__ import annotations

import logging
import socket
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

_SOCKET_PATH = "/tmp/pisugar-server.sock"
_I2C_BUS = 1
_I2C_ADDR = 0x57
_REG_PERCENTAGE = 0x2A
_REG_STATUS = 0x02  # bit 7 = external power, bit 6 = charging


@dataclass
class BatteryStatus:
    percentage: Optional[float]   # 0.0 – 100.0
    voltage: Optional[float]      # volts
    plugged_in: Optional[bool]    # external power connected
    charging: Optional[bool]      # actively charging


def _query_socket(command: str) -> Optional[str]:
    """Send a single command to pisugar-server and return the value string.

    Responses are in the form "key: value" — we return only the value part.
    """
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            s.connect(_SOCKET_PATH)
            s.sendall((command + "\n").encode())
            data = s.recv(256).decode().strip()
            # Strip "key: " prefix e.g. "battery: 85.5" → "85.5"
            if ": " in data:
                data = data.split(": ", 1)[1]
            return data
    except (OSError, socket.timeout):
        return None


def _read_via_socket() -> Optional[BatteryStatus]:
    pct_raw   = _query_socket("get battery")
    volt_raw  = _query_socket("get battery_v")
    plugged   = _query_socket("get battery_power_plugged")
    charging  = _query_socket("get battery_charging")

    if pct_raw is None:
        return None

    def to_float(s: Optional[str]) -> Optional[float]:
        try:
            return float(s) if s else None
        except ValueError:
            return None

    def to_bool(s: Optional[str]) -> Optional[bool]:
        return s.strip() == "true" if s else None

    return BatteryStatus(
        percentage=to_float(pct_raw),
        voltage=to_float(volt_raw),
        plugged_in=to_bool(plugged),
        charging=to_bool(charging),
    )


def _read_via_i2c() -> Optional[BatteryStatus]:
    try:
        import smbus2  # type: ignore[import]
    except ImportError:
        try:
            import smbus as smbus2  # type: ignore[import,no-redef]
        except ImportError:
            return None

    try:
        bus = smbus2.SMBus(_I2C_BUS)
        pct_raw    = bus.read_byte_data(_I2C_ADDR, _REG_PERCENTAGE)
        volt_high  = bus.read_byte_data(_I2C_ADDR, 0x22)
        volt_low   = bus.read_byte_data(_I2C_ADDR, 0x23)
        status_reg = bus.read_byte_data(_I2C_ADDR, _REG_STATUS)
        bus.close()

        voltage = ((volt_high << 8) | volt_low) / 1000.0  # mV → V
        plugged  = bool(status_reg & 0x80)
        charging = bool(status_reg & 0x40)

        return BatteryStatus(
            percentage=float(pct_raw),
            voltage=voltage,
            plugged_in=plugged,
            charging=charging,
        )
    except Exception as exc:
        logger.debug("I2C battery read failed: %s", exc)
        return None


class BatteryMonitor:
    """Reads PiSugar 3 battery status. Thread-safe (stateless reads)."""

    def __init__(self) -> None:
        # Probe once at startup to log which backend is active
        status = self.read()
        if status and status.percentage is not None:
            logger.info(
                "Battery monitor active — %.0f%% (%.2fV) plugged=%s charging=%s",
                status.percentage,
                status.voltage or 0.0,
                status.plugged_in,
                status.charging,
            )
        else:
            logger.warning("Battery monitor unavailable (pisugar-server not running and I2C not accessible)")

    def read(self) -> Optional[BatteryStatus]:
        status = _read_via_socket()
        if status is not None:
            return status
        status = _read_via_i2c()
        return status  # may be None in dev mode
