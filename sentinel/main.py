"""Flask web server — entry point for Sentinel sentry bot."""

from __future__ import annotations

import logging
import os
import signal
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory

from .battery_monitor import BatteryMonitor
from .camera_stream import CameraStream
from .config import load_config
from .motor_controller import MotorController

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_WEB_DIR = Path(__file__).parent.parent / "web"


def _pi_uptime() -> float:
    """Seconds since the Pi booted, from /proc/uptime."""
    try:
        return float(Path("/proc/uptime").read_text().split()[0])
    except Exception:
        return 0.0

# ---------------------------------------------------------------------------
# App factory / startup
# ---------------------------------------------------------------------------

config = load_config()
motors = MotorController(config.motor)
camera = CameraStream(config.camera)
battery = BatteryMonitor()

app = Flask(__name__, static_folder=None)


def _shutdown(signum, frame):
    logger.info("Received signal %d — shutting down", signum)
    camera.stop()
    motors.cleanup()
    os._exit(0)


signal.signal(signal.SIGTERM, _shutdown)
signal.signal(signal.SIGINT, _shutdown)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

_VALID_ACTIONS = {"forward", "reverse", "turn_left", "turn_right", "stop", "brake"}


@app.get("/")
def index():
    return send_from_directory(_WEB_DIR, "index.html")


@app.get("/static/<path:filename>")
def static_files(filename: str):
    return send_from_directory(_WEB_DIR, filename)


@app.get("/stream")
def stream():
    return Response(
        camera.generate(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.post("/command")
def command():
    data = request.get_json(silent=True) or {}
    action = data.get("action", "stop")
    speed = data.get("speed")

    if action not in _VALID_ACTIONS:
        return jsonify({"error": f"unknown action: {action}"}), 400

    if speed is not None:
        try:
            speed = int(speed)
        except (ValueError, TypeError):
            return jsonify({"error": "speed must be an integer"}), 400

    dispatch = {
        "forward": motors.forward,
        "reverse": motors.reverse,
        "turn_left": motors.turn_left,
        "turn_right": motors.turn_right,
        "stop": motors.stop,
        "brake": motors.brake,
    }
    fn = dispatch[action]
    if speed is not None and action not in ("stop", "brake"):
        fn(speed)
    else:
        fn()

    return jsonify({"ok": True, "action": action, "speed": motors.speed})


@app.get("/status")
def status():
    bat = battery.read()
    return jsonify({
        "action": motors.current_action,
        "speed": motors.speed,
        "camera_ok": camera.available,
        "uptime_s": round(_pi_uptime()),
        "battery_pct": round(bat.percentage, 1) if bat and bat.percentage is not None else None,
        "battery_v": round(bat.voltage, 2) if bat and bat.voltage is not None else None,
        "battery_plugged": bat.plugged_in if bat else None,
        "battery_charging": bat.charging if bat else None,
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    app.run(
        host=config.server.host,
        port=config.server.port,
        debug=config.server.debug,
        threaded=True,
    )


if __name__ == "__main__":
    main()
