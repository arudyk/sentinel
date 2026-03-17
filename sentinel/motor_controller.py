"""L298N motor controller driver. Falls back to dry-run mode if RPi.GPIO is unavailable."""

from __future__ import annotations

import logging
import threading
from typing import Optional

from .config import MotorConfig

logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
    _GPIO_AVAILABLE = True
except ImportError:
    GPIO = None  # type: ignore[assignment]
    _GPIO_AVAILABLE = False
    logger.warning("RPi.GPIO not available — running in dry-run mode (no hardware output)")


class MotorController:
    """Controls two DC motors via an L298N H-bridge.

    In dry-run mode (no RPi.GPIO), all commands are logged to stdout instead
    of writing to GPIO pins, enabling full web server testing without hardware.
    """

    def __init__(self, config: MotorConfig) -> None:
        self._cfg = config
        self._speed = config.default_speed
        self._lock = threading.Lock()
        self._current_action = "stop"
        self._dry_run = not _GPIO_AVAILABLE

        if not self._dry_run:
            self._setup_gpio()
        else:
            self._pwm_left = None
            self._pwm_right = None

    # ------------------------------------------------------------------
    # GPIO setup
    # ------------------------------------------------------------------

    def _setup_gpio(self) -> None:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        pins = [
            self._cfg.in1, self._cfg.in2, self._cfg.ena,
            self._cfg.in3, self._cfg.in4, self._cfg.enb,
        ]
        GPIO.setup(pins, GPIO.OUT, initial=GPIO.LOW)

        self._pwm_left = GPIO.PWM(self._cfg.ena, self._cfg.pwm_frequency)
        self._pwm_right = GPIO.PWM(self._cfg.enb, self._cfg.pwm_frequency)
        self._pwm_left.start(0)
        self._pwm_right.start(0)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def forward(self, speed: Optional[int] = None) -> None:
        with self._lock:
            self._set_speed_internal(speed)
            self._drive(left_fwd=True, right_fwd=True)
            self._current_action = "forward"

    def reverse(self, speed: Optional[int] = None) -> None:
        with self._lock:
            self._set_speed_internal(speed)
            self._drive(left_fwd=False, right_fwd=False)
            self._current_action = "reverse"

    def turn_left(self, speed: Optional[int] = None) -> None:
        """Pivot turn: right motor forward, left motor reverse."""
        with self._lock:
            self._set_speed_internal(speed)
            self._drive(left_fwd=False, right_fwd=True)
            self._current_action = "turn_left"

    def turn_right(self, speed: Optional[int] = None) -> None:
        """Pivot turn: left motor forward, right motor reverse."""
        with self._lock:
            self._set_speed_internal(speed)
            self._drive(left_fwd=True, right_fwd=False)
            self._current_action = "turn_right"

    def stop(self) -> None:
        """Coast stop — all IN pins LOW."""
        with self._lock:
            self._current_action = "stop"
            if self._dry_run:
                logger.info("[dry-run] STOP (coast)")
                return
            GPIO.output([self._cfg.in1, self._cfg.in2, self._cfg.in3, self._cfg.in4], GPIO.LOW)
            self._pwm_left.ChangeDutyCycle(0)
            self._pwm_right.ChangeDutyCycle(0)

    def brake(self) -> None:
        """Active brake — both IN pins HIGH per motor."""
        with self._lock:
            self._current_action = "brake"
            if self._dry_run:
                logger.info("[dry-run] BRAKE (active)")
                return
            GPIO.output(self._cfg.in1, GPIO.HIGH)
            GPIO.output(self._cfg.in2, GPIO.HIGH)
            GPIO.output(self._cfg.in3, GPIO.HIGH)
            GPIO.output(self._cfg.in4, GPIO.HIGH)
            self._pwm_left.ChangeDutyCycle(100)
            self._pwm_right.ChangeDutyCycle(100)

    def set_speed(self, speed: int) -> None:
        with self._lock:
            self._set_speed_internal(speed)

    def cleanup(self) -> None:
        if not self._dry_run:
            try:
                self.stop()
                if self._pwm_left:
                    self._pwm_left.stop()
                if self._pwm_right:
                    self._pwm_right.stop()
                GPIO.cleanup()
            except Exception:
                pass
        logger.info("MotorController cleaned up")

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    @property
    def current_action(self) -> str:
        return self._current_action

    @property
    def speed(self) -> int:
        return self._speed

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "MotorController":
        return self

    def __exit__(self, *_) -> None:
        self.cleanup()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _set_speed_internal(self, speed: Optional[int]) -> None:
        if speed is not None:
            self._speed = max(0, min(100, speed))

    def _drive(self, left_fwd: bool, right_fwd: bool) -> None:
        duty = self._speed
        if self._dry_run:
            logger.info(
                "[dry-run] DRIVE left=%s right=%s speed=%d",
                "fwd" if left_fwd else "rev",
                "fwd" if right_fwd else "rev",
                duty,
            )
            return

        # Left motor
        GPIO.output(self._cfg.in1, GPIO.HIGH if left_fwd else GPIO.LOW)
        GPIO.output(self._cfg.in2, GPIO.LOW if left_fwd else GPIO.HIGH)
        # Right motor
        GPIO.output(self._cfg.in3, GPIO.HIGH if right_fwd else GPIO.LOW)
        GPIO.output(self._cfg.in4, GPIO.LOW if right_fwd else GPIO.HIGH)
        # PWM
        self._pwm_left.ChangeDutyCycle(duty)
        self._pwm_right.ChangeDutyCycle(duty)
