// Sentinel — vanilla JS controller (ES2020)

(() => {
  "use strict";

  const STOP_ACTION = "stop";
  const STATUS_POLL_MS = 2000;
  const STREAM_RECONNECT_MS = 2000;

  let currentAction = STOP_ACTION;
  let currentSpeed = 75;
  let statusTimer = null;

  // ── DOM refs ──────────────────────────────────────────────────────────────

  const streamImg    = document.getElementById("stream");
  const streamOverlay = document.getElementById("stream-overlay");
  const statusAction  = document.getElementById("status-action");
  const statusSpeed   = document.getElementById("status-speed");
  const statusCamera  = document.getElementById("status-camera");
  const statusBattery = document.getElementById("status-battery");
  const statusUptime  = document.getElementById("status-uptime");
  const speedSlider  = document.getElementById("speed-slider");
  const speedValue   = document.getElementById("speed-value");
  const dpadBtns     = document.querySelectorAll(".dpad-btn");

  // ── Command sender ────────────────────────────────────────────────────────

  async function sendCommand(action, speed = currentSpeed) {
    try {
      const res = await fetch("/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, speed }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        console.warn("Command error:", err);
      }
    } catch (e) {
      console.error("sendCommand failed:", e);
    }
  }

  // ── D-pad buttons ─────────────────────────────────────────────────────────

  function setActive(action) {
    dpadBtns.forEach(btn => {
      btn.classList.toggle("active", btn.dataset.action === action);
    });
    currentAction = action;
  }

  dpadBtns.forEach(btn => {
    const action = btn.dataset.action;

    btn.addEventListener("pointerdown", e => {
      e.preventDefault();
      btn.setPointerCapture(e.pointerId);
      setActive(action);
      sendCommand(action, currentSpeed);
    });

    btn.addEventListener("pointerup", e => {
      e.preventDefault();
      if (action !== STOP_ACTION) {
        setActive(STOP_ACTION);
        sendCommand(STOP_ACTION, currentSpeed);
      }
    });

    btn.addEventListener("pointercancel", () => {
      setActive(STOP_ACTION);
      sendCommand(STOP_ACTION, currentSpeed);
    });
  });

  // ── Keyboard controls ─────────────────────────────────────────────────────

  const KEY_MAP = {
    ArrowUp:    "forward",
    KeyW:       "forward",
    ArrowDown:  "reverse",
    KeyS:       "reverse",
    ArrowLeft:  "turn_left",
    KeyA:       "turn_left",
    ArrowRight: "turn_right",
    KeyD:       "turn_right",
    Space:      "stop",
  };

  const keysDown = new Set();

  document.addEventListener("keydown", e => {
    const action = KEY_MAP[e.code];
    if (!action || keysDown.has(e.code)) return;
    e.preventDefault();
    keysDown.add(e.code);
    setActive(action);
    sendCommand(action, currentSpeed);
  });

  document.addEventListener("keyup", e => {
    const action = KEY_MAP[e.code];
    if (!action) return;
    e.preventDefault();
    keysDown.delete(e.code);
    if (keysDown.size === 0 && action !== STOP_ACTION) {
      setActive(STOP_ACTION);
      sendCommand(STOP_ACTION, currentSpeed);
    }
  });

  // ── Speed slider ──────────────────────────────────────────────────────────

  speedSlider.addEventListener("input", () => {
    currentSpeed = parseInt(speedSlider.value, 10);
    speedValue.textContent = `${currentSpeed}%`;
    // Resend current non-stop action with new speed
    if (currentAction !== STOP_ACTION && currentAction !== "brake") {
      sendCommand(currentAction, currentSpeed);
    }
  });

  // ── Status polling ────────────────────────────────────────────────────────

  function formatUptime(seconds) {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  }

  async function pollStatus() {
    try {
      const res = await fetch("/status");
      if (!res.ok) return;
      const data = await res.json();

      statusAction.textContent = data.action ?? "?";
      statusSpeed.textContent  = `${data.speed ?? 0}%`;
      statusUptime.textContent = formatUptime(data.uptime_s ?? 0);

      if (data.camera_ok) {
        statusCamera.classList.add("ok");
        statusCamera.title = "Camera OK";
      } else {
        statusCamera.classList.remove("ok");
        statusCamera.title = "Camera unavailable";
      }

      if (data.battery_pct != null) {
        const pct = Math.round(data.battery_pct);
        const icon = data.battery_charging ? "⚡" : batteryIcon(pct);
        statusBattery.textContent = `${icon} ${pct}%`;
        statusBattery.classList.toggle("charging", !!data.battery_charging);
        statusBattery.classList.toggle("low", !data.battery_charging && pct <= 20);
        const v = data.battery_v != null ? ` (${data.battery_v}V)` : "";
        const plug = data.battery_plugged ? " · plugged in" : "";
        statusBattery.title = `Battery: ${pct}%${v}${plug}`;
      } else {
        statusBattery.textContent = "–";
        statusBattery.title = "Battery unavailable";
      }
    } catch (e) {
      // Server unreachable — silently ignore until next poll
    }
  }

  function batteryIcon(pct) {
    if (pct > 80) return "🔋";
    if (pct > 50) return "🔋";
    if (pct > 20) return "🪫";
    return "🪫";
  }

  statusTimer = setInterval(pollStatus, STATUS_POLL_MS);
  pollStatus();

  // ── MJPEG stream reconnect ────────────────────────────────────────────────

  streamImg.addEventListener("error", () => {
    streamOverlay.classList.remove("hidden");
    setTimeout(() => {
      streamImg.src = `/stream?t=${Date.now()}`;
      streamOverlay.classList.add("hidden");
    }, STREAM_RECONNECT_MS);
  });

  streamImg.addEventListener("load", () => {
    streamOverlay.classList.add("hidden");
  });

  // ── Send stop on page unload ──────────────────────────────────────────────

  window.addEventListener("beforeunload", () => {
    navigator.sendBeacon("/command", JSON.stringify({ action: "stop", speed: 0 }));
  });

})();
