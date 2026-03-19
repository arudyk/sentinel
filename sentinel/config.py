"""Load config.toml into typed dataclasses. Falls back to safe defaults if file is missing."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent.parent / "config.toml"


@dataclass
class MotorConfig:
    in1: int = 17
    in2: int = 27
    ena: int = 18
    in3: int = 22
    in4: int = 23
    enb: int = 19
    default_speed: int = 75
    pwm_frequency: int = 1000


@dataclass
class CameraConfig:
    width: int = 640
    height: int = 480
    framerate: int = 15
    jpeg_quality: int = 70
    rotation: int = 0


@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False


@dataclass
class CameraControlConfig:
    i2c_bus: int = 1
    i2c_addr: int = 64  # 0x40 — PCA9685 default


@dataclass
class Config:
    motor: MotorConfig = field(default_factory=MotorConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    camera_control: CameraControlConfig = field(default_factory=CameraControlConfig)


def load_config(path: Path = _CONFIG_PATH) -> Config:
    if not path.exists():
        return Config()

    with open(path, "rb") as f:
        raw = tomllib.load(f)

    motor          = MotorConfig(**raw.get("motor", {}))
    camera         = CameraConfig(**raw.get("camera", {}))
    server         = ServerConfig(**raw.get("server", {}))
    camera_control = CameraControlConfig(**raw.get("camera_control", {}))
    return Config(motor=motor, camera=camera, server=server, camera_control=camera_control)
