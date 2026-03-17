# L298N Wiring Guide

## GPIO Pin Assignments

```
L298N Pin   →   RPi BCM GPIO   Physical Pin   Function
──────────────────────────────────────────────────────────────
IN1         →   GPIO 22        Pin 15         Right motor direction A (OUT1/OUT2)
IN2         →   GPIO 23        Pin 16         Right motor direction B (OUT1/OUT2)
ENA         →   GPIO 18        Pin 12         Right motor PWM (PWM0)
IN3         →   GPIO 17        Pin 11         Left motor direction A  (OUT3/OUT4)
IN4         →   GPIO 27        Pin 13         Left motor direction B  (OUT3/OUT4)
ENB         →   GPIO 19        Pin 35         Left motor PWM (PWM1)
GND         →   Pi GND         Pin 6/9/14/…
```

> **WARNING**: Motor power (battery pack) connects to the L298N VCC and GND
> screw terminals. **Never** power motors from the Pi 5V rail — it will
> brown-out or damage the Pi.

## ASCII Wiring Diagram

```
  Battery Pack
  +12V ──────────────── L298N VCC (motor power)
  GND  ──────────────── L298N GND ── Pi GND

  Raspberry Pi (BCM)         L298N
  ┌──────────────────┐       ┌─────────────────┐
  │ GPIO17 (pin 11)  │──────▶│ IN1             │
  │ GPIO27 (pin 13)  │──────▶│ IN2             │──── Left Motor
  │ GPIO18 (pin 12)  │──────▶│ ENA (PWM)       │
  │                  │       │                 │
  │ GPIO22 (pin 15)  │──────▶│ IN3             │
  │ GPIO23 (pin 16)  │──────▶│ IN4             │──── Right Motor
  │ GPIO19 (pin 35)  │──────▶│ ENB (PWM)       │
  │ GND    (pin 6)   │──────▶│ GND             │
  └──────────────────┘       └─────────────────┘
```

## Motor Direction Truth Table

| IN_A | IN_B | Motor      |
|------|------|------------|
| HIGH | LOW  | Forward    |
| LOW  | HIGH | Reverse    |
| LOW  | LOW  | Coast stop |
| HIGH | HIGH | Brake      |

## PWM Notes

- ENA and ENB must be connected to PWM-capable GPIO pins.
- GPIO 18 = hardware PWM0, GPIO 19 = hardware PWM1 on BCM numbering.
- PWM frequency default: 1000 Hz (configurable in `config.toml`).
- Duty cycle 0–100 maps to 0–100% speed.

## Jumpers

Some L298N modules have jumper caps on ENA/ENB that hard-wire them HIGH
(always enabled). **Remove those jumpers** and wire ENA/ENB to the Pi GPIO
pins above, otherwise PWM speed control will not work.
