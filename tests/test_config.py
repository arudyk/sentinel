"""Unit tests for config loading."""

import tempfile
from pathlib import Path

import pytest

from sentinel.config import (
    CameraConfig,
    Config,
    MotorConfig,
    ServerConfig,
    load_config,
)


def write_toml(content: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False)
    tmp.write(content)
    tmp.flush()
    return Path(tmp.name)


class TestDefaults:
    def test_missing_file_returns_defaults(self):
        cfg = load_config(Path("/nonexistent/config.toml"))
        assert isinstance(cfg, Config)
        assert cfg.motor.in1 == 17
        assert cfg.camera.width == 640
        assert cfg.server.port == 8080

    def test_default_motor(self):
        m = MotorConfig()
        assert m.in1 == 17
        assert m.default_speed == 75
        assert m.pwm_frequency == 1000

    def test_default_camera(self):
        c = CameraConfig()
        assert c.width == 640
        assert c.height == 480
        assert c.framerate == 15

    def test_default_server(self):
        s = ServerConfig()
        assert s.host == "0.0.0.0"
        assert s.port == 8080
        assert s.debug is False


class TestParsing:
    def test_full_config(self):
        p = write_toml("""
[motor]
in1 = 10
in2 = 11
ena = 12
in3 = 13
in4 = 14
enb = 15
default_speed = 60
pwm_frequency = 500

[camera]
width = 320
height = 240
framerate = 10
jpeg_quality = 50
rotation = 180

[server]
host = "127.0.0.1"
port = 9090
debug = true
""")
        cfg = load_config(p)
        assert cfg.motor.in1 == 10
        assert cfg.motor.default_speed == 60
        assert cfg.motor.pwm_frequency == 500
        assert cfg.camera.width == 320
        assert cfg.camera.rotation == 180
        assert cfg.server.port == 9090
        assert cfg.server.debug is True

    def test_partial_config_uses_defaults(self):
        p = write_toml("""
[motor]
default_speed = 50
""")
        cfg = load_config(p)
        assert cfg.motor.default_speed == 50
        assert cfg.motor.in1 == 17  # default
        assert cfg.camera.width == 640  # default

    def test_empty_file_uses_defaults(self):
        p = write_toml("")
        cfg = load_config(p)
        assert cfg.motor.in1 == 17
        assert cfg.server.port == 8080
