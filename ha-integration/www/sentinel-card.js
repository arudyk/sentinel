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
          <div class="status-bar">
            <span id="status-action">idle</span>
            <span id="status-battery" class="battery">–</span>
          </div>
        </div>

        <div class="controls">
          <div class="dpad">
            <button class="btn up"    data-action="forward">    ▲<kbd>W</kbd></button>
            <button class="btn left"  data-action="turn_left">  ◀<kbd>A</kbd></button>
            <button class="btn stop"  data-action="stop">       ■</button>
            <button class="btn right" data-action="turn_right"> ▶<kbd>D</kbd></button>
            <button class="btn down"  data-action="reverse">    ▼<kbd>S</kbd></button>
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
    const map = { w: 'forward', a: 'turn_left', s: 'reverse', d: 'turn_right', ' ': 'stop' };
    const action = map[e.key.toLowerCase()];
    if (!action) return;
    e.preventDefault();
    this._press(action);
    const btn = this.shadowRoot.querySelector(`[data-action="${action}"]`);
    if (btn) btn.classList.add('active');
  }

  _onKeyUp(e) {
    const map = { w: 'forward', a: 'turn_left', s: 'reverse', d: 'turn_right' };
    const action = map[e.key.toLowerCase()];
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
