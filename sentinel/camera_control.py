"""PCA9685 pan-tilt servo controller for ArduCam pan-tilt kit (SKU B0283).

Wiring (Pi Zero 2 W):
  VCC  → Pin 4  (5 V)
  GND  → Pin 6  (GND)
  SDA  → Pin 3  (GPIO 2)
  SCL  → Pin 5  (GPIO 3)

Pan servo  → PCA9685 channel 0
Tilt servo → PCA9685 channel 1
"""

from __future__ import annotations

import logging
import time

from .config import CameraControlConfig

_LOGGER = logging.getLogger(__name__)

# PCA9685 registers
_MODE1     = 0x00
_PRESCALE  = 0xFE
_LED0_ON_L = 0x06  # channel n base = 0x06 + 4*n

_OSC_CLOCK = 25_000_000  # internal oscillator Hz
_FREQ_HZ   = 50          # standard servo PWM frequency

# Servo pulse range: 500 µs (0°) … 2500 µs (180°) over 20 ms period
_PULSE_MIN_US = 500
_PULSE_MAX_US = 2500
_PERIOD_US    = 1_000_000 // _FREQ_HZ  # 20 000 µs


def _angle_to_ticks(angle: int) -> int:
    """Map 0–180° to a 12-bit PCA9685 off-tick value."""
    pulse_us = _PULSE_MIN_US + (_PULSE_MAX_US - _PULSE_MIN_US) * angle / 180
    return round(pulse_us / _PERIOD_US * 4096)


class CameraControl:
    """Controls pan and tilt servos via PCA9685 over I2C."""

    def __init__(self, cfg: CameraControlConfig) -> None:
        self._addr = cfg.i2c_addr
        self._dry  = False
        try:
            import smbus2  # type: ignore[import]
            self._bus = smbus2.SMBus(cfg.i2c_bus)
            self._init_pca9685()
            _LOGGER.info("CameraControl: PCA9685 ready at I2C 0x%02X", self._addr)
        except Exception as exc:
            _LOGGER.warning("CameraControl: I2C unavailable (%s) — dry-run mode", exc)
            self._dry = True
            self._bus = None

        self._pan  = 90
        self._tilt = 90
        if not self._dry:
            self._write_servo(0, 90)
            self._write_servo(1, 90)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _write_reg(self, reg: int, val: int) -> None:
        self._bus.write_byte_data(self._addr, reg, val)

    def _init_pca9685(self) -> None:
        self._write_reg(_MODE1, 0x00)
        prescale = round(_OSC_CLOCK / (4096 * _FREQ_HZ)) - 1  # = 121 for 50 Hz
        mode1 = self._bus.read_byte_data(self._addr, _MODE1)
        self._write_reg(_MODE1, (mode1 & 0x7F) | 0x10)  # sleep to set prescale
        self._write_reg(_PRESCALE, prescale)
        self._write_reg(_MODE1, mode1)                   # wake
        time.sleep(0.005)
        self._write_reg(_MODE1, mode1 | 0xA1)            # auto-increment enabled

    def _write_servo(self, channel: int, angle: int) -> None:
        off  = _angle_to_ticks(angle)
        base = _LED0_ON_L + 4 * channel
        # ON count = 0, OFF count = ticks
        self._bus.write_i2c_block_data(
            self._addr, base, [0x00, 0x00, off & 0xFF, (off >> 8) & 0x0F]
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def pan_angle(self) -> int:
        return self._pan

    @property
    def tilt_angle(self) -> int:
        return self._tilt

    def pan(self, angle: int) -> None:
        angle = max(0, min(180, int(angle)))
        self._pan = angle
        if self._dry:
            _LOGGER.info("CameraControl dry-run: pan=%d", angle)
            return
        self._write_servo(1, angle)  # channel 1 = pan servo

    def tilt(self, angle: int) -> None:
        angle = max(0, min(180, int(angle)))
        self._tilt = angle
        if self._dry:
            _LOGGER.info("CameraControl dry-run: tilt=%d", angle)
            return
        self._write_servo(0, 180 - angle)  # channel 0 = tilt servo; inverted (higher PWM = camera up)

    def center(self) -> None:
        self.pan(90)
        self.tilt(90)

    def cleanup(self) -> None:
        if self._bus and not self._dry:
            try:
                self.center()
                self._bus.close()
            except Exception:
                pass
