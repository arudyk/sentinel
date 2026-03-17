# First-Boot / SD Card Setup

## Recommended: Raspberry Pi Imager

1. Download **Raspberry Pi Imager** from raspberrypi.com/software
2. Choose **Raspberry Pi Zero 2 W** as the device
3. Choose **Raspberry Pi OS Lite (64-bit)** as the OS
4. Choose your SD card
5. Click the **gear icon (⚙)** / "Edit Settings" before writing:

   | Setting      | Value                         |
   |--------------|-------------------------------|
   | Hostname     | `sentinel`                    |
   | Enable SSH   | ✓ (password or public key)    |
   | Username     | `pi`                          |
   | Password     | (choose a strong password)    |
   | WiFi SSID    | your network name             |
   | WiFi password| your WiFi password            |
   | WiFi country | your country code (e.g. `US`) |
   | Locale       | your timezone                 |

6. Click **Save** then **Write**

## First SSH Login

Once the Pi boots (LED stops flashing continuously):

```bash
ssh pi@sentinel.local
# or: ssh pi@<ip-address>
```

If `sentinel.local` doesn't resolve, find the IP from your router's DHCP
table or use `nmap -sn 192.168.1.0/24`.

## Deploy Sentinel

```bash
# On the Pi:
git clone https://github.com/youruser/sentinel.git
cd sentinel
bash setup.sh
```

## Manual Alternative (no Imager GUI)

Write the OS image with `dd`, then mount the `bootfs` partition and create:

**`/boot/firstrun.sh`** — runs on first boot via the `firstrun` service.
Or use `custom.toml` if your Pi OS version supports it (Bookworm+).

The Imager approach is simpler and less error-prone.

## Verify Camera

```bash
libcamera-hello --timeout 5000
```

Should display a preview window or log frames to the terminal (Lite mode
shows frame info without a GUI).

## Verify GPIO

```bash
python3 -c "import RPi.GPIO as GPIO; print(GPIO.RPI_INFO)"
```
