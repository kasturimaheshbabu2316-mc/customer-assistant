/* ==========================================================================
   OMNIDESK AI — CLAYMORPHISM THEME & TACTILE AUDIO ENGINE
   Pure Claymorphic Design System: Porcelain Cloud | Marshmallow Candy | Mint Sage | Midnight Slate
   Includes Web Audio API Tactile Bubble/Pop Synthesizer
   ========================================================================== */

(function () {
  'use strict';

  // Clear legacy retro-theme storage so the fresh Claymorphism design takes full priority
  try {
    if (localStorage.getItem('omnidesk_retro_theme')) {
      localStorage.removeItem('omnidesk_retro_theme');
    }
    if (localStorage.getItem('omnidesk_retro_scanlines')) {
      localStorage.removeItem('omnidesk_retro_scanlines');
    }
    if (localStorage.getItem('omnidesk_retro_flicker')) {
      localStorage.removeItem('omnidesk_retro_flicker');
    }
    // Remove CRT overlay if present
    const oldCrt = document.getElementById('retro-crt-overlay');
    if (oldCrt) oldCrt.remove();
    const oldDock = document.getElementById('retro-theme-dock');
    if (oldDock) oldDock.remove();
  } catch (e) {}

  // --- 1. Synthesized Tactile Bubble / Clay Pop Audio Engine ---
  class ClayAudioEngine {
    constructor() {
      this.ctx = null;
      this.enabled = localStorage.getItem('omnidesk_clay_sound') !== 'false';
    }

    _initContext() {
      if (!this.ctx) {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (AudioContext) {
          this.ctx = new AudioContext();
        }
      }
      if (this.ctx && this.ctx.state === 'suspended') {
        this.ctx.resume();
      }
    }

    toggleSound(forceState) {
      if (typeof forceState === 'boolean') {
        this.enabled = forceState;
      } else {
        this.enabled = !this.enabled;
      }
      localStorage.setItem('omnidesk_clay_sound', this.enabled);
      if (this.enabled) {
        this.playPop();
      }
      return this.enabled;
    }

    // Soft tactile clay bubble pop
    playPop(freq = 520) {
      if (!this.enabled) return;
      try {
        this._initContext();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, now);
        osc.frequency.exponentialRampToValueAtTime(freq * 1.8, now + 0.035);
        osc.frequency.exponentialRampToValueAtTime(freq * 0.5, now + 0.08);

        gain.gain.setValueAtTime(0.12, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.085);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.09);
      } catch (e) {}
    }

    // Bubbly chat message send
    playSend() {
      if (!this.enabled) return;
      try {
        this._initContext();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        [440, 660, 880].forEach((f, i) => {
          const osc = this.ctx.createOscillator();
          const gain = this.ctx.createGain();
          const t = now + i * 0.04;

          osc.type = 'sine';
          osc.frequency.setValueAtTime(f, t);
          osc.frequency.exponentialRampToValueAtTime(f * 1.4, t + 0.05);

          gain.gain.setValueAtTime(0.09, t);
          gain.gain.exponentialRampToValueAtTime(0.001, t + 0.06);

          osc.connect(gain);
          gain.connect(this.ctx.destination);

          osc.start(t);
          osc.stop(t + 0.065);
        });
      } catch (e) {}
    }

    // Gentle incoming message bubble
    playReceive() {
      if (!this.enabled) return;
      try {
        this._initContext();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        [780, 620, 920].forEach((f, i) => {
          const osc = this.ctx.createOscillator();
          const gain = this.ctx.createGain();
          const t = now + i * 0.045;

          osc.type = 'sine';
          osc.frequency.setValueAtTime(f, t);

          gain.gain.setValueAtTime(0.08, t);
          gain.gain.exponentialRampToValueAtTime(0.001, t + 0.07);

          osc.connect(gain);
          gain.connect(this.ctx.destination);

          osc.start(t);
          osc.stop(t + 0.075);
        });
      } catch (e) {}
    }

    // Success chime
    playSuccess() {
      if (!this.enabled) return;
      try {
        this._initContext();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        [523.25, 659.25, 783.99, 1046.50].forEach((freq, idx) => {
          const osc = this.ctx.createOscillator();
          const gain = this.ctx.createGain();
          const start = now + idx * 0.06;

          osc.type = 'sine';
          osc.frequency.setValueAtTime(freq, start);

          gain.gain.setValueAtTime(0.1, start);
          gain.gain.exponentialRampToValueAtTime(0.001, start + 0.12);

          osc.connect(gain);
          gain.connect(this.ctx.destination);

          osc.start(start);
          osc.stop(start + 0.13);
        });
      } catch (e) {}
    }
  }

  // --- 2. Claymorphic Theme Manager ---
  class ClayThemeManager {
    constructor() {
      this.sound = new ClayAudioEngine();
      this.activeTheme = localStorage.getItem('omnidesk_clay_theme') || 'porcelain';

      this.themes = [
        { id: 'porcelain', name: 'Porcelain Cloud', icon: 'fa-cloud', color: '#6366f1', desc: 'Soft Ceramic White & Indigo Clay' },
        { id: 'marshmallow', name: 'Candy Marshmallow', icon: 'fa-candy-cane', color: '#ec4899', desc: 'Pastel Bubblegum & Lilac Clay' },
        { id: 'mint', name: 'Mint & Eucalyptus', icon: 'fa-leaf', color: '#10b981', desc: 'Fresh Soothing Sage Clay' },
        { id: 'peach', name: 'Warm Peach & Coral', icon: 'fa-sun', color: '#f97316', desc: 'Sunny Warm Bisque Clay' },
        { id: 'midnight', name: 'Midnight Velvet', icon: 'fa-moon', color: '#818cf8', desc: 'Deep Velvet Obsidian Dark Clay' }
      ];

      this.init();
    }

    init() {
      this.applyTheme(this.activeTheme, false);

      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => this.injectUI());
      } else {
        this.injectUI();
      }

      this.attachSoundListeners();
    }

    applyTheme(themeId, playSound = true) {
      this.activeTheme = themeId;
      localStorage.setItem('omnidesk_clay_theme', themeId);

      if (themeId === 'porcelain') {
        document.documentElement.removeAttribute('data-theme');
      } else {
        document.documentElement.setAttribute('data-theme', themeId);
      }

      // Sync any admin dropdown if present
      const adminSelects = [
        document.getElementById('setting-clay-theme-palette'),
        document.getElementById('feat-theme-mode')
      ];
      adminSelects.forEach(select => {
        if (!select) return;
        if (Array.from(select.options).some(o => o.value === themeId)) {
          select.value = themeId;
        } else if (Array.from(select.options).some(o => o.value === 'clay_' + themeId)) {
          select.value = 'clay_' + themeId;
        }
      });

      this.updateDockButtons();

      if (playSound) {
        this.sound.playPop(620);
      }

      window.dispatchEvent(new CustomEvent('omnidesk:themechange', { detail: { theme: themeId } }));
    }

    injectUI() {
      if (document.getElementById('clay-theme-dock')) return;

      const dock = document.createElement('div');
      dock.id = 'clay-theme-dock';
      dock.className = 'clay-theme-dock';
      dock.innerHTML = `
        <!-- Floating Clay Trigger Pill -->
        <button type="button" class="clay-dock-trigger" id="clay-dock-toggle-btn" title="Customize Claymorphism Style" aria-label="Customize Claymorphism Style">
          <span class="clay-dock-icon">🫧</span>
          <span class="clay-dock-label">Clay Studio</span>
          <span class="clay-dock-badge" id="clay-dock-current-theme">${this.getThemeName(this.activeTheme)}</span>
        </button>

        <!-- Floating Clay Control Drawer -->
        <div class="clay-dock-panel" id="clay-dock-panel">
          <div class="clay-dock-header">
            <div class="clay-dock-title">
              <span class="clay-bubble-icon">🎨</span> Claymorphism Studio
            </div>
            <button type="button" class="clay-dock-close" id="clay-dock-close-btn" title="Close" aria-label="Close">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>

          <div class="clay-dock-body">
            <div class="clay-section-label">Tactile Clay Palettes</div>
            <div class="clay-theme-grid">
              ${this.themes.map(t => `
                <button type="button" class="clay-theme-btn ${this.activeTheme === t.id ? 'is-active' : ''}" data-theme-id="${t.id}" title="${t.desc}">
                  <span class="clay-swatch" style="background: ${t.color};"></span>
                  <span class="clay-btn-name">${t.name}</span>
                </button>
              `).join('')}
            </div>

            <div class="clay-section-label" style="margin-top: 14px;">Tactile Audio Feedback</div>
            <div class="clay-fx-row">
              <button type="button" class="clay-fx-btn ${this.sound.enabled ? 'is-active' : ''}" id="clay-toggle-sound" title="Toggle Tactile Pop Audio">
                <i class="fa-solid ${this.sound.enabled ? 'fa-volume-high' : 'fa-volume-xmark'}"></i>
                <span>Tactile Pops</span>
              </button>
              <button type="button" class="clay-fx-btn" id="clay-test-pop-btn" title="Audition Bubbly Sound">
                <i class="fa-solid fa-wand-magic-sparkles"></i>
                <span>Sample Pop</span>
              </button>
            </div>
          </div>

          <div class="clay-dock-footer">
            <span class="clay-footer-tag">OmniDesk Clay UI v3.0</span>
            <span class="clay-footer-pill">Tactile 3D</span>
          </div>
        </div>
      `;

      document.body.appendChild(dock);

      const toggleBtn = document.getElementById('clay-dock-toggle-btn');
      const panel = document.getElementById('clay-dock-panel');
      const closeBtn = document.getElementById('clay-dock-close-btn');

      if (toggleBtn && panel) {
        toggleBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          this.sound.playPop(580);
          panel.classList.toggle('is-open');
        });
      }

      if (closeBtn && panel) {
        closeBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          this.sound.playPop(480);
          panel.classList.remove('is-open');
        });
      }

      document.addEventListener('click', (e) => {
        if (panel && panel.classList.contains('is-open')) {
          if (!dock.contains(e.target)) {
            panel.classList.remove('is-open');
          }
        }
      });

      const themeBtns = dock.querySelectorAll('.clay-theme-btn');
      themeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          const tId = btn.getAttribute('data-theme-id');
          if (tId) {
            this.applyTheme(tId, true);
          }
        });
      });

      const soundBtn = document.getElementById('clay-toggle-sound');
      if (soundBtn) {
        soundBtn.addEventListener('click', () => {
          const state = this.sound.toggleSound();
          soundBtn.classList.toggle('is-active', state);
          const icon = soundBtn.querySelector('i');
          if (icon) {
            icon.className = `fa-solid ${state ? 'fa-volume-high' : 'fa-volume-xmark'}`;
          }
        });
      }

      const testPopBtn = document.getElementById('clay-test-pop-btn');
      if (testPopBtn) {
        testPopBtn.addEventListener('click', () => {
          this.sound.playSuccess();
        });
      }

      this.updateDockButtons();
    }

    getThemeName(themeId) {
      const found = this.themes.find(t => t.id === themeId);
      return found ? found.name : 'Porcelain';
    }

    updateDockButtons() {
      const badge = document.getElementById('clay-dock-current-theme');
      if (badge) {
        badge.textContent = this.getThemeName(this.activeTheme);
      }

      const btns = document.querySelectorAll('.clay-theme-btn');
      btns.forEach(b => {
        if (b.getAttribute('data-theme-id') === this.activeTheme) {
          b.classList.add('is-active');
        } else {
          b.classList.remove('is-active');
        }
      });
    }

    attachSoundListeners() {
      document.addEventListener('click', (e) => {
        const target = e.target.closest('button, a.btn, .chip-btn, .sidebar-item-btn, .tab-btn, .msg-btn-action, .rating-star-btn');
        if (target && !target.closest('#clay-theme-dock')) {
          if (target.classList.contains('rating-star-btn') || target.textContent.includes('Submit') || target.textContent.includes('Resolve')) {
            this.sound.playSuccess();
          } else {
            this.sound.playPop(540 + Math.random() * 80);
          }
        }
      });

      document.addEventListener('submit', (e) => {
        if (e.target.id === 'chat-input-form' || e.target.id === 'lead-capture-form' || e.target.id === 'ticket-claim-form') {
          this.sound.playSend();
        }
      });
    }
  }

  window.ClayEngine = new ClayThemeManager();
})();
