# Sentinel — Home Sentry Bot

A tracked robot controlled via Home Assistant or a local web app, served by a Raspberry Pi Zero 2 W. Two DC motors driven by an L298N H-bridge, live MJPEG camera stream via Pi Camera, battery powered by PiSugar 3.

---

## Hardware

| Component | Details |
|-----------|---------|
| Compute | Raspberry Pi Zero 2 W |
| OS | Raspberry Pi OS Lite 64-bit (Trixie) |
| Motors | 2× DC motors (tracked chassis) |
| Motor driver | L298N H-bridge |
| Camera | Pi Camera v1 (OV5647) |
| Battery | PiSugar 3 |

---

## Wiring

### L298N → Raspberry Pi Zero 2 W

| L298N Pin | BCM GPIO | Physical Pin | Function |
|-----------|----------|--------------|----------|
| IN1 | GPIO 23 | Pin 16 | Right motor direction A |
| IN2 | GPIO 22 | Pin 15 | Right motor direction B |
| ENA | GPIO 18 | Pin 12 | Right motor PWM (speed) |
| IN3 | GPIO 17 | Pin 11 | Left motor direction A |
| IN4 | GPIO 27 | Pin 13 | Left motor direction B |
| ENB | GPIO 19 | Pin 35 | Left motor PWM (speed) |
| GND | GND | Pin 6 | Shared ground |

### L298N Motor Outputs

| L298N Output | Motor |
|--------------|-------|
| OUT1 / OUT2 | Right motor |
| OUT3 / OUT4 | Left motor |

> **Power**: Motor battery pack connects to the L298N VCC and GND screw terminals. Never power motors from the Pi 5V rail.
>
> **ENA/ENB**: Remove the jumper caps and wire to Pi GPIO for PWM speed control. Leave jumpers on for always-on full speed.
>
> **Ground**: Pi GND (pin 6) must be connected to L298N GND, otherwise GPIO signals have no reference and the motors will not respond.

---

## Software Setup

### First-time Pi setup

Flash **Raspberry Pi OS Lite 64-bit** to a microSD card using Raspberry Pi Imager. See [`docs/first-boot.md`](docs/first-boot.md) for headless WiFi/SSH configuration.

After SSH-ing into the Pi:

```bash
git clone https://github.com/youruser/sentinel.git
cd sentinel
bash setup.sh
```

`setup.sh` will:
1. Install system packages (`picamera2`, `RPi.GPIO`, `python3-smbus2`, `i2c-tools`)
2. Install and start `pisugar-server` for battery monitoring
3. Create a Python virtualenv with `--system-site-packages`
4. Install Flask
5. Install and enable the `sentinel` systemd service

### Accessing the web UI

| Method | URL |
|--------|-----|
| Local network | `http://192.168.1.138:8080` |
| mDNS hostname | `http://sentinel.local:8080` |

For remote access, use the [Home Assistant integration](ha-integration/) — the HA camera proxy and controls work from anywhere HA is reachable.

### Managing the service

```bash
sudo systemctl status sentinel       # check status
sudo systemctl restart sentinel      # restart
sudo journalctl -u sentinel -f       # follow logs
```

---

## Development (no Pi required)

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m sentinel.main
# Open http://localhost:8080
```

GPIO falls back to dry-run mode (logs pin changes to stdout). Camera falls back to a placeholder JPEG frame. All routes and controls work normally.

```bash
python -m pytest tests/ -v    # run unit tests
```

---

## Configuration

All tunable parameters live in `config.toml`. Edit and restart the service to apply changes.

```toml
[motor]
in1 = 23           # Right motor dir A — BCM GPIO number
in2 = 22           # Right motor dir B — BCM GPIO number
ena = 18           # Right motor PWM   — BCM GPIO number
in3 = 17           # Left motor dir A  — BCM GPIO number
in4 = 27           # Left motor dir B  — BCM GPIO number
enb = 19           # Left motor PWM    — BCM GPIO number
default_speed = 75  # 0–100
pwm_frequency = 1000

[camera]
width = 640
height = 480
framerate = 15
jpeg_quality = 70
rotation = 180      # 0, 90, 180, or 270

[server]
host = "0.0.0.0"
port = 8080
debug = false
```

> **Pin numbers**: values are BCM GPIO numbers, not physical pin numbers. Use the wiring table above to cross-reference.

---

## Controls

### Keyboard

| Key | Action |
|-----|--------|
| `W` | Forward |
| `S` | Reverse |
| `A` | Turn left |
| `D` | Turn right |
| `Space` | Stop |

Hold the key to keep moving — releasing stops the robot.

### Mobile

Use the on-screen D-pad. Touch and hold to move, release to stop.

### Speed

Adjust the speed slider (0–100%) before or during movement.

---

## HTTP API

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/` | Web UI |
| `GET` | `/stream` | MJPEG live camera stream |
| `POST` | `/command` | Send a drive command |
| `GET` | `/status` | Current state (JSON) |

### POST /command

```bash
curl -X POST http://sentinel.local:8080/command \
  -H "Content-Type: application/json" \
  -d '{"action": "forward", "speed": 75}'
```

Valid actions: `forward`, `reverse`, `turn_left`, `turn_right`, `stop`, `brake`

### GET /status

```json
{
  "action": "forward",
  "speed": 75,
  "camera_ok": true,
  "uptime_s": 120,
  "battery_pct": 85.0,
  "battery_v": 4.05,
  "battery_plugged": false,
  "battery_charging": false
}
```

---

## Project Structure

```
sentinel/
├── config.toml                 Central configuration (GPIO pins, camera, server)
├── requirements.txt            Python dependencies (Flask only)
├── setup.sh                    One-shot Pi setup script
│
├── sentinel/                   Python package
│   ├── main.py                 Flask app and route definitions
│   ├── motor_controller.py     L298N GPIO/PWM driver
│   ├── camera_stream.py        picamera2 MJPEG streaming
│   ├── battery_monitor.py      PiSugar 3 battery reader
│   └── config.py               Loads config.toml into dataclasses
│
├── web/                        Frontend (no build step)
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── systemd/
│   └── sentinel.service        Systemd unit file
│
├── tests/
│   ├── test_motor_controller.py
│   └── test_config.py
│
└── docs/
    ├── wiring.md               Detailed wiring reference
    └── first-boot.md           SD card and headless setup
```
