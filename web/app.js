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

  // PTZ key map: key code → [panDir, tiltDir]
  const PTZ_KEY_MAP = {
    KeyJ: [-1,  0],  // pan left
    KeyL: [ 1,  0],  // pan right
    KeyI: [ 0, -1],  // tilt up
    KeyK: [ 0,  1],  // tilt down
  };
  const ptzTimers = {};

  function startPtzKey(code) {
    if (ptzTimers[code]) return;
    const [panDir, tiltDir] = PTZ_KEY_MAP[code];
    const tick = () => {
      currentPan  = Math.max(0, Math.min(180, currentPan  + panDir  * PTZ_STEP_DEG));
      currentTilt = Math.max(0, Math.min(180, currentTilt + tiltDir * PTZ_STEP_DEG));
      sendPanTilt(currentPan, currentTilt);
    };
    tick();
    ptzTimers[code] = setInterval(tick, PTZ_TICK_MS);
  }

  function stopPtzKey(code) {
    clearInterval(ptzTimers[code]);
    delete ptzTimers[code];
  }

  document.addEventListener("keydown", e => {
    if (PTZ_KEY_MAP[e.code]) {
      e.preventDefault();
      startPtzKey(e.code);
      return;
    }
    const action = KEY_MAP[e.code];
    if (!action || keysDown.has(e.code)) return;
    e.preventDefault();
    keysDown.add(e.code);
    setActive(action);
    sendCommand(action, currentSpeed);
  });

  document.addEventListener("keyup", e => {
    if (PTZ_KEY_MAP[e.code]) {
      e.preventDefault();
      stopPtzKey(e.code);
      return;
    }
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

  // ── Pan / tilt overlay ────────────────────────────────────────────────────

  const PTZ_STEP_DEG  = 3;   // degrees per tick
  const PTZ_TICK_MS   = 80;  // repeat interval while held

  let currentPan  = 90;
  let currentTilt = 90;

  async function sendPanTilt(pan, tilt) {
    try {
      await fetch("/pan_tilt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pan, tilt }),
      });
    } catch (e) {
      console.error("sendPanTilt failed:", e);
    }
  }

  document.querySelectorAll(".ptz-btn").forEach(btn => {
    const panDir  = parseInt(btn.dataset.pan,  10);
    const tiltDir = parseInt(btn.dataset.tilt, 10);
    let timer = null;

    function tick() {
      currentPan  = Math.max(0, Math.min(180, currentPan  + panDir  * PTZ_STEP_DEG));
      currentTilt = Math.max(0, Math.min(180, currentTilt + tiltDir * PTZ_STEP_DEG));
      sendPanTilt(currentPan, currentTilt);
    }

    btn.addEventListener("pointerdown", e => {
      e.preventDefault();
      btn.setPointerCapture(e.pointerId);
      btn.classList.add("active");
      tick();
      timer = setInterval(tick, PTZ_TICK_MS);
    });

    function stop() {
      clearInterval(timer);
      timer = null;
      btn.classList.remove("active");
    }

    btn.addEventListener("pointerup",     stop);
    btn.addEventListener("pointercancel", stop);
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
      if (data.pan  != null) currentPan  = data.pan;
      if (data.tilt != null) currentTilt = data.tilt;
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
