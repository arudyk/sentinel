class SentinelCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._hass = null;
    this._config = {};
    this._built = false;
    this._boundKeyDown = this._onKeyDown.bind(this);
    this._boundKeyUp = this._onKeyUp.bind(this);
  }

  setConfig(config) {
    this._config = { entity_prefix: 'sentinel', ...config };
  }

  connectedCallback() {
    window.addEventListener('keydown', this._boundKeyDown);
    window.addEventListener('keyup', this._boundKeyUp);
  }

  disconnectedCallback() {
    window.removeEventListener('keydown', this._boundKeyDown);
    window.removeEventListener('keyup', this._boundKeyUp);
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._built) {
      this._build();
      this._built = true;
    }
    this._update();
  }

  // Build entity ID from domain + suffix
  _e(domain, name) {
    return `${domain}.${this._config.entity_prefix}_${name}`;
  }

  _streamUrl() {
    if (this._config.stream_url) return this._config.stream_url;
    const entityId = this._e('camera', 'camera');
    const state = this._hass && this._hass.states[entityId];
    const token = state && state.attributes && state.attributes.access_token;
    const base = `/api/camera_proxy_stream/${entityId}`;
    return token ? `${base}?token=${token}` : base;
  }

  _build() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          --bg: #0d1117;
          --surface: #161b22;
          --border: #30363d;
          --accent: #238636;
          --accent-hover: #2ea043;
          --danger: #da3633;
          --text: #c9d1d9;
          --text-dim: #8b949e;
          --btn: 64px;
          --radius: 8px;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }

        .card {
          background: var(--bg);
          border-radius: 12px;
          overflow: hidden;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          color: var(--text);
          -webkit-user-select: none;
          user-select: none;
        }

        /* ── Camera ── */
        .stream-wrap {
          position: relative;
          width: 100%;
          aspect-ratio: 4 / 3;
          background: #000;
        }
        .stream-wrap img {
          width: 100%;
          height: 100%;
          object-fit: contain;
          display: block;
        }

        /* ── Pan/tilt overlay ── */
        .ptz-overlay {
          position: absolute;
          inset: 0;
          pointer-events: none;
        }
        .ptz-btn {
          position: absolute;
          pointer-events: all;
          background: rgba(0,0,0,0.35);
          border: 1px solid rgba(255,255,255,0.18);
          border-radius: 6px;
          color: rgba(255,255,255,0.8);
          font-size: 1.1rem;
          cursor: pointer;
          touch-action: manipulation;
          width: 44px;
          height: 44px;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background 0.08s;
        }
        .ptz-btn:active, .ptz-btn.active {
          background: rgba(35,134,54,0.7);
          border-color: rgba(46,160,67,0.8);
        }
        .ptz-up    { top: 8px;    left: 50%; transform: translateX(-50%); }
        .ptz-down  { bottom: 30px; left: 50%; transform: translateX(-50%); }
        .ptz-left  { left: 8px;   top: 50%;  transform: translateY(-50%); }
        .ptz-right { right: 8px;  top: 50%;  transform: translateY(-50%); }

        /* ── Overlay status bar on the camera ── */
        .status-bar {
          position: absolute;
          bottom: 0; left: 0; right: 0;
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 5px 10px;
          background: linear-gradient(transparent, rgba(0,0,0,0.7));
          font-size: 0.75rem;
          color: var(--text-dim);
        }
        #status-action {
          text-transform: uppercase;
          font-weight: 600;
          color: var(--text);
          letter-spacing: 0.06em;
        }
        .battery { font-variant-numeric: tabular-nums; }
        .battery.charging { color: #e3b341; }
        .battery.low      { color: var(--danger); }

        /* ── Controls panel ── */
        .controls {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 12px;
          padding: 14px 14px 16px;
          background: var(--surface);
        }

        /* ── D-pad ── */
        .dpad {
          display: grid;
          grid-template-columns: repeat(3, var(--btn));
          grid-template-rows: repeat(3, var(--btn));
          gap: 6px;
        }
        .btn {
          width: var(--btn);
          height: var(--btn);
          background: #1c2128;
          border: 1px solid var(--border);
          border-radius: var(--radius);
          color: var(--text);
          font-size: 1.3rem;
          cursor: pointer;
          touch-action: manipulation;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 3px;
          transition: background 0.08s, transform 0.05s;
        }
        .btn kbd {
          font-size: 0.58rem;
          font-family: inherit;
          color: var(--text-dim);
          line-height: 1;
        }
        .btn:active, .btn.active {
          background: var(--accent);
          border-color: var(--accent-hover);
          transform: scale(0.93);
        }
        .btn:active kbd, .btn.active kbd { color: rgba(255,255,255,0.6); }
        .btn.stop { border-color: var(--danger); font-size: 1.1rem; }
        .btn.stop:active, .btn.stop.active {
          background: var(--danger);
          border-color: var(--danger);
        }
        .btn.up    { grid-column: 2; grid-row: 1; }
        .btn.left  { grid-column: 1; grid-row: 2; }
        .btn.stop  { grid-column: 2; grid-row: 2; }
        .btn.right { grid-column: 3; grid-row: 2; }
        .btn.down  { grid-column: 2; grid-row: 3; }

        /* ── Speed slider ── */
        .speed-row {
          display: flex;
          align-items: center;
          gap: 10px;
          width: calc(var(--btn) * 3 + 12px);
          font-size: 0.78rem;
          color: var(--text-dim);
        }
        .speed-row input[type=range] {
          flex: 1;
          accent-color: var(--accent);
          cursor: pointer;
          touch-action: manipulation;
        }
        #speed-val {
          min-width: 36px;
          text-align: right;
          font-variant-numeric: tabular-nums;
        }
      </style>

      <div class="card">
        <div class="stream-wrap">
          <img id="stream" alt="Camera">
          <div class="ptz-overlay">
            <button class="ptz-btn ptz-up"    data-pan="0"  data-tilt="-1">▲</button>
            <button class="ptz-btn ptz-down"  data-pan="0"  data-tilt="1">▼</button>
            <button class="ptz-btn ptz-left"  data-pan="-1" data-tilt="0">◀</button>
            <button class="ptz-btn ptz-right" data-pan="1"  data-tilt="0">▶</button>
          </div>
          <div class="status-bar">
            <span id="status-action">idle</span>
            <span id="status-battery" class="battery">–</span>
          </div>
        </div>

        <div class="controls">
          <div class="dpad">
            <button class="btn up"    data-action="forward">    ▲<kbd>↑</kbd></button>
            <button class="btn left"  data-action="turn_left">  ◀<kbd>←</kbd></button>
            <button class="btn stop"  data-action="stop">       ■</button>
            <button class="btn right" data-action="turn_right"> ▶<kbd>→</kbd></button>
            <button class="btn down"  data-action="reverse">    ▼<kbd>↓</kbd></button>
          </div>

          <div class="speed-row">
            <span>Speed</span>
            <input id="speed-slider" type="range" min="0" max="100" step="5" value="75">
            <span id="speed-val">75%</span>
          </div>
        </div>
      </div>
    `;

    // Stream: set initial src + reconnect on error
    const imgEl = this.shadowRoot.getElementById('stream');
    imgEl.src = this._streamUrl();
    imgEl.addEventListener('error', () => {
      setTimeout(() => { imgEl.src = this._streamUrl(); }, 2000);
    });

    // Hold-to-move on D-pad buttons
    this.shadowRoot.querySelectorAll('[data-action]').forEach(btn => {
      btn.addEventListener('pointerdown', e => {
        e.preventDefault();
        btn.setPointerCapture(e.pointerId);
        this._press(btn.dataset.action);
        btn.classList.add('active');
      });
      btn.addEventListener('pointerup', () => {
        const action = btn.dataset.action;
        if (action !== 'stop' && action !== 'brake') this._press('stop');
        btn.classList.remove('active');
      });
      btn.addEventListener('pointercancel', () => btn.classList.remove('active'));
    });

    // Pan/tilt overlay — hold to move
    const PTZ_STEP = 3;
    const PTZ_MS   = 80;
    this._pan  = 90;
    this._tilt = 90;
    this.shadowRoot.querySelectorAll('.ptz-btn').forEach(btn => {
      const panDir  = parseInt(btn.dataset.pan,  10);
      const tiltDir = parseInt(btn.dataset.tilt, 10);
      let timer = null;
      const tick = () => {
        this._pan  = Math.max(0, Math.min(180, this._pan  + panDir  * PTZ_STEP));
        this._tilt = Math.max(0, Math.min(180, this._tilt + tiltDir * PTZ_STEP));
        this._hass.callService('number', 'set_value', {
          entity_id: this._e('number', 'pan'),
          value: this._pan,
        });
        this._hass.callService('number', 'set_value', {
          entity_id: this._e('number', 'tilt'),
          value: this._tilt,
        });
      };
      btn.addEventListener('pointerdown', e => {
        e.preventDefault();
        btn.setPointerCapture(e.pointerId);
        btn.classList.add('active');
        tick();
        timer = setInterval(tick, PTZ_MS);
      });
      const stop = () => { clearInterval(timer); timer = null; btn.classList.remove('active'); };
      btn.addEventListener('pointerup',     stop);
      btn.addEventListener('pointercancel', stop);
    });

    // Speed slider
    const slider = this.shadowRoot.getElementById('speed-slider');
    slider.addEventListener('input', () => {
      const v = parseInt(slider.value);
      this.shadowRoot.getElementById('speed-val').textContent = `${v}%`;
      this._hass.callService('number', 'set_value', {
        entity_id: this._e('number', 'speed'),
        value: v,
      });
    });
  }

  _press(action) {
    this._hass.callService('button', 'press', {
      entity_id: this._e('button', action),
    });
  }

  _onKeyDown(e) {
    if (e.repeat) return;
    // PTZ keys — hold to move
    const ptzMap = { j: [-1, 0], l: [1, 0], i: [0, -1], k: [0, 1] };
    const ptz = ptzMap[e.key.toLowerCase()];
    if (ptz) {
      e.preventDefault();
      if (!this._ptzTimers) this._ptzTimers = {};
      if (this._ptzTimers[e.key]) return;
      const [panDir, tiltDir] = ptz;
      const PTZ_STEP = 3, PTZ_MS = 80;
      const tick = () => {
        this._pan  = Math.max(0, Math.min(180, this._pan  + panDir  * PTZ_STEP));
        this._tilt = Math.max(0, Math.min(180, this._tilt + tiltDir * PTZ_STEP));
        this._hass.callService('number', 'set_value', { entity_id: this._e('number', 'pan'),  value: this._pan });
        this._hass.callService('number', 'set_value', { entity_id: this._e('number', 'tilt'), value: this._tilt });
      };
      tick();
      this._ptzTimers[e.key] = setInterval(tick, PTZ_MS);
      return;
    }
    // Drive keys
    const map = { ArrowUp: 'forward', ArrowLeft: 'turn_left', ArrowDown: 'reverse', ArrowRight: 'turn_right', ' ': 'stop' };
    const action = map[e.key];
    if (!action) return;
    e.preventDefault();
    this._press(action);
    const btn = this.shadowRoot.querySelector(`[data-action="${action}"]`);
    if (btn) btn.classList.add('active');
  }

  _onKeyUp(e) {
    // PTZ keys
    if (this._ptzTimers && this._ptzTimers[e.key]) {
      e.preventDefault();
      clearInterval(this._ptzTimers[e.key]);
      delete this._ptzTimers[e.key];
      return;
    }
    // Drive keys
    const map = { ArrowUp: 'forward', ArrowLeft: 'turn_left', ArrowDown: 'reverse', ArrowRight: 'turn_right' };
    const action = map[e.key];
    if (!action) return;
    this._press('stop');
    const btn = this.shadowRoot.querySelector(`[data-action="${action}"]`);
    if (btn) btn.classList.remove('active');
  }

  _update() {
    if (!this._built) return;

    // Refresh stream src when token changes (HA restart etc.)
    const cameraState = this._hass.states[this._e('camera', 'camera')];
    const token = cameraState && cameraState.attributes && cameraState.attributes.access_token;
    const imgEl = this.shadowRoot.getElementById('stream');
    if (imgEl && token && imgEl._sentinelToken !== token) {
      imgEl._sentinelToken = token;
      imgEl.src = this._streamUrl();
    }

    // Battery
    const bat     = this._hass.states[this._e('sensor', 'battery')];
    const charging = this._hass.states[this._e('binary_sensor', 'charging')];
    const plugged  = this._hass.states[this._e('binary_sensor', 'plugged_in')];
    const batEl = this.shadowRoot.getElementById('status-battery');
    if (bat && bat.state !== 'unavailable') {
      const pct = parseFloat(bat.state);
      const isCharging = charging?.state === 'on';
      const isPlugged  = plugged?.state === 'on';
      const icon = isCharging ? '⚡' : isPlugged ? '🔌' : '🔋';
      batEl.textContent = `${icon} ${pct.toFixed(0)}%`;
      batEl.className = `battery${isCharging ? ' charging' : pct < 20 ? ' low' : ''}`;
    }

    // Pan/tilt — sync from HA state
    const panState  = this._hass.states[this._e('number', 'pan')];
    const tiltState = this._hass.states[this._e('number', 'tilt')];
    if (panState  && panState.state  !== 'unavailable') this._pan  = parseFloat(panState.state);
    if (tiltState && tiltState.state !== 'unavailable') this._tilt = parseFloat(tiltState.state);

    // Speed slider — sync from HA state without fighting an active drag
    const speedState = this._hass.states[this._e('number', 'speed')];
    if (speedState && speedState.state !== 'unavailable') {
      const slider = this.shadowRoot.getElementById('speed-slider');
      if (slider && !slider.matches(':active')) {
        const v = parseFloat(speedState.state);
        slider.value = v;
        this.shadowRoot.getElementById('speed-val').textContent = `${v}%`;
      }
    }
  }

  getCardSize() { return 5; }

  static getStubConfig() {
    return { entity_prefix: 'sentinel' };
  }
}

customElements.define('sentinel-card', SentinelCard);
