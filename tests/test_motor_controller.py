"""Unit tests for MotorController — GPIO is mocked."""

import sys
import types
from unittest.mock import MagicMock, call, patch

import pytest

# ---------------------------------------------------------------------------
# Provide a fake RPi.GPIO module before importing motor_controller
# ---------------------------------------------------------------------------

_gpio_mock = MagicMock()
_gpio_mock.BCM = 11
_gpio_mock.OUT = 0
_gpio_mock.HIGH = 1
_gpio_mock.LOW = 0

# Inject into sys.modules so motor_controller can import it
sys.modules.setdefault("RPi", types.ModuleType("RPi"))
sys.modules.setdefault("RPi.GPIO", _gpio_mock)

from sentinel.config import MotorConfig  # noqa: E402
from sentinel.motor_controller import MotorController  # noqa: E402


@pytest.fixture()
def cfg():
    return MotorConfig(
        in1=17, in2=27, ena=18,
        in3=22, in4=23, enb=19,
        default_speed=75,
        pwm_frequency=1000,
    )


@pytest.fixture()
def mc(cfg):
    """MotorController with GPIO mocked."""
    gpio = MagicMock()
    gpio.BCM = 11
    gpio.OUT = 0
    gpio.HIGH = 1
    gpio.LOW = 0
    pwm_left = MagicMock()
    pwm_right = MagicMock()
    gpio.PWM.side_effect = [pwm_left, pwm_right]

    with patch("sentinel.motor_controller._GPIO_AVAILABLE", True), \
         patch("sentinel.motor_controller.GPIO", gpio):
        controller = MotorController(cfg)
        controller._gpio = gpio  # stash for assertions
        yield controller, gpio, pwm_left, pwm_right
        controller.cleanup()


class TestDryRunMode:
    def test_dry_run_no_gpio_import(self, cfg):
        """MotorController should work without raising when GPIO unavailable."""
        with patch("sentinel.motor_controller._GPIO_AVAILABLE", False):
            ctrl = MotorController(cfg)
            assert ctrl._dry_run is True
            ctrl.forward()
            ctrl.reverse()
            ctrl.turn_left()
            ctrl.turn_right()
            ctrl.stop()
            ctrl.brake()
            ctrl.cleanup()

    def test_dry_run_action_tracking(self, cfg):
        with patch("sentinel.motor_controller._GPIO_AVAILABLE", False):
            ctrl = MotorController(cfg)
            ctrl.forward()
            assert ctrl.current_action == "forward"
            ctrl.stop()
            assert ctrl.current_action == "stop"


class TestMotorCommands:
    def test_forward_sets_pins(self, mc):
        ctrl, gpio, pwm_l, pwm_r = mc
        ctrl.forward()
        gpio.output.assert_any_call(ctrl._cfg.in1, gpio.HIGH)
        gpio.output.assert_any_call(ctrl._cfg.in2, gpio.LOW)
        gpio.output.assert_any_call(ctrl._cfg.in3, gpio.HIGH)
        gpio.output.assert_any_call(ctrl._cfg.in4, gpio.LOW)
        assert ctrl.current_action == "forward"

    def test_reverse_sets_pins(self, mc):
        ctrl, gpio, pwm_l, pwm_r = mc
        ctrl.reverse()
        gpio.output.assert_any_call(ctrl._cfg.in1, gpio.LOW)
        gpio.output.assert_any_call(ctrl._cfg.in2, gpio.HIGH)
        gpio.output.assert_any_call(ctrl._cfg.in3, gpio.LOW)
        gpio.output.assert_any_call(ctrl._cfg.in4, gpio.HIGH)
        assert ctrl.current_action == "reverse"

    def test_turn_left_right_motor_forward(self, mc):
        ctrl, gpio, pwm_l, pwm_r = mc
        ctrl.turn_left()
        # Left motor reverse, right motor forward
        gpio.output.assert_any_call(ctrl._cfg.in1, gpio.LOW)
        gpio.output.assert_any_call(ctrl._cfg.in3, gpio.HIGH)
        assert ctrl.current_action == "turn_left"

    def test_turn_right_left_motor_forward(self, mc):
        ctrl, gpio, pwm_l, pwm_r = mc
        ctrl.turn_right()
        gpio.output.assert_any_call(ctrl._cfg.in1, gpio.HIGH)
        gpio.output.assert_any_call(ctrl._cfg.in3, gpio.LOW)
        assert ctrl.current_action == "turn_right"

    def test_stop_zeros_pwm(self, mc):
        ctrl, gpio, pwm_l, pwm_r = mc
        ctrl.forward()
        ctrl.stop()
        pwm_l.ChangeDutyCycle.assert_called_with(0)
        pwm_r.ChangeDutyCycle.assert_called_with(0)
        assert ctrl.current_action == "stop"

    def test_brake_full_duty(self, mc):
        ctrl, gpio, pwm_l, pwm_r = mc
        ctrl.brake()
        pwm_l.ChangeDutyCycle.assert_called_with(100)
        pwm_r.ChangeDutyCycle.assert_called_with(100)
        assert ctrl.current_action == "brake"


class TestSpeedControl:
    def test_default_speed(self, cfg):
        with patch("sentinel.motor_controller._GPIO_AVAILABLE", False):
            ctrl = MotorController(cfg)
            assert ctrl.speed == 75

    def test_set_speed_clamps_high(self, cfg):
        with patch("sentinel.motor_controller._GPIO_AVAILABLE", False):
            ctrl = MotorController(cfg)
            ctrl.set_speed(150)
            assert ctrl.speed == 100

    def test_set_speed_clamps_low(self, cfg):
        with patch("sentinel.motor_controller._GPIO_AVAILABLE", False):
            ctrl = MotorController(cfg)
            ctrl.set_speed(-10)
            assert ctrl.speed == 0

    def test_forward_with_custom_speed(self, mc):
        ctrl, gpio, pwm_l, pwm_r = mc
        ctrl.forward(speed=50)
        assert ctrl.speed == 50
        pwm_l.ChangeDutyCycle.assert_called_with(50)
        pwm_r.ChangeDutyCycle.assert_called_with(50)


class TestContextManager:
    def test_context_manager_calls_cleanup(self, cfg):
        with patch("sentinel.motor_controller._GPIO_AVAILABLE", False):
            with MotorController(cfg) as ctrl:
                ctrl.forward()
            # No exception means cleanup ran fine
