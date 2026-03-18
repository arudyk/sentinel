# Sentinel — Home Assistant Integration

Custom integration that exposes the Sentinel robot to Home Assistant.

## Entities

| Entity | Type | Description |
|--------|------|-------------|
| `camera.sentinel_camera` | Camera | Live MJPEG stream |
| `button.sentinel_forward` | Button | Drive forward |
| `button.sentinel_reverse` | Button | Drive reverse |
| `button.sentinel_turn_left` | Button | Turn left |
| `button.sentinel_turn_right` | Button | Turn right |
| `button.sentinel_stop` | Button | Coast stop |
| `button.sentinel_brake` | Button | Active brake |
| `number.sentinel_speed` | Number | Speed slider (0–100 %) |
| `sensor.sentinel_battery` | Sensor | Battery percentage |
| `sensor.sentinel_battery_voltage` | Sensor | Battery voltage (V) |
| `sensor.sentinel_speed` | Sensor | Current motor speed |
| `sensor.sentinel_uptime` | Sensor | Pi uptime (seconds) |
| `binary_sensor.sentinel_camera` | Binary sensor | Camera health |
| `binary_sensor.sentinel_plugged_in` | Binary sensor | External power connected |
| `binary_sensor.sentinel_charging` | Binary sensor | Battery charging |

## Installation

1. Copy `custom_components/sentinel/` into your HA `config/custom_components/` directory.
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration**, search for **Sentinel**.
4. Enter the robot's IP address and port (default `8080`).

## Requirements

- Sentinel must be reachable from the HA host on the local network.
- No extra Python packages required — uses `aiohttp` which HA bundles.
