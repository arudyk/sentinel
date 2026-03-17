# Remote Access via Tailscale

Tailscale creates a private WireGuard mesh network so you can reach Sentinel
from anywhere without port forwarding or a VPN server.

## Install on the Pi

```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

## Authenticate

```bash
sudo tailscale up --authkey=tskey-auth-XXXX --hostname=sentinel
```

Replace `tskey-auth-XXXX` with a reusable auth key from:
**Tailscale Admin → Settings → Keys → Generate auth key**

Check the box for **Reusable** if you may re-image the Pi later.

## Find the Tailscale IP

```bash
tailscale ip -4
# e.g. 100.64.0.5
```

Or open the Tailscale admin console: **Machines → sentinel**.

## Access the Web UI

```
http://<tailscale-ip>:8080
```

Example: `http://100.64.0.5:8080`

No firewall rules needed — Tailscale handles NAT traversal automatically.

## Auto-start on Boot

The installer enables the Tailscale daemon as a systemd service automatically:

```bash
sudo systemctl status tailscaled   # should be active
```

## RAM Usage

Tailscale uses ~20–30 MB RAM at idle, which is acceptable on the Pi Zero 2 W
(512 MB total). If you're tight on memory, check `free -m` and optionally
reduce camera resolution in `config.toml`.

## Security Notes

- Only devices in your Tailscale network can reach Sentinel.
- The web UI has no authentication — add Tailscale ACLs if needed.
- Revoke the auth key from the admin console if the Pi is lost or stolen.
