/* ==========================================================================
   OMNIDESK AI — RETRO THEME & AUDIO ENGINE
   Multi-Theme Retro Suite: Synthwave 80s | CRT Terminal | Win95 Classic | 90s Arcade
   Includes Web Audio API 8-bit sound chip synthesizer & CRT scanlines engine
   ========================================================================== */

(function () {
  'use strict';

  // --- 1. Synthesized 8-Bit Web Audio API Sound Chip ---
  class RetroSoundEngine {
    constructor() {
      this.ctx = null;
      this.enabled = localStorage.getItem('omnidesk_retro_sound') !== 'false';
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
      localStorage.setItem('omnidesk_retro_sound', this.enabled);
      if (this.enabled) {
        this.playBeep();
      }
      return this.enabled;
    }

    // 8-Bit Click / Keystroke / Chip Blip
    playClick() {
      if (!this.enabled) return;
      try {
        this._initContext();
        if (!this.ctx) return;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        const now = this.ctx.currentTime;

        osc.type = 'square';
        osc.frequency.setValueAtTime(650, now);
        osc.frequency.exponentialRampToValueAtTime(320, now + 0.04);

        gain.gain.setValueAtTime(0.08, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.045);
      } catch (e) {
        // Audio playback error handled silently
      }
    }

    // 8-Bit Blip / Soft Menu navigation
    playBeep() {
      if (!this.enabled) return;
      try {
        this._initContext();
        if (!this.ctx) return;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        const now = this.ctx.currentTime;

        osc.type = 'triangle';
        osc.frequency.setValueAtTime(880, now);
        osc.frequency.setValueAtTime(1100, now + 0.03);

        gain.gain.setValueAtTime(0.09, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.07);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.075);
      } catch (e) {}
    }

    // 8-Bit Laser Shoot / Message Send
    playSend() {
      if (!this.enabled) return;
      try {
        this._initContext();
        if (!this.ctx) return;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        const now = this.ctx.currentTime;

        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(1200, now);
        osc.frequency.exponentialRampToValueAtTime(180, now + 0.12);

        gain.gain.setValueAtTime(0.12, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.13);
      } catch (e) {}
    }

    // 8-Bit Response Incoming / Arpeggio Chime
    playReceive() {
      if (!this.enabled) return;
      try {
        this._initContext();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6

        notes.forEach((freq, idx) => {
          const osc = this.ctx.createOscillator();
          const gain = this.ctx.createGain();
          const start = now + idx * 0.04;

          osc.type = 'square';
          osc.frequency.setValueAtTime(freq, start);

          gain.gain.setValueAtTime(0.07, start);
          gain.gain.exponentialRampToValueAtTime(0.001, start + 0.06);

          osc.connect(gain);
          gain.connect(this.ctx.destination);

          osc.start(start);
          osc.stop(start + 0.065);
        });
      } catch (e) {}
    }

    // 8-Bit Victory Fanfare / Level-Up / Ticket Resolved / 5-Star Rating
    playSuccess() {
      if (!this.enabled) return;
      try {
        this._initContext();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const notes = [523.25, 659.25, 783.99, 1046.50, 1318.51]; // C5, E5, G5, C6, E6

        notes.forEach((freq, idx) => {
          const osc = this.ctx.createOscillator();
          const gain = this.ctx.createGain();
          const start = now + idx * 0.055;

          osc.type = 'triangle';
          osc.frequency.setValueAtTime(freq, start);

          gain.gain.setValueAtTime(0.1, start);
          gain.gain.exponentialRampToValueAtTime(0.001, start + 0.1);

          osc.connect(gain);
          gain.connect(this.ctx.destination);

          osc.start(start);
          osc.stop(start + 0.11);
        });
      } catch (e) {}
    }

    // 8-Bit Alarm / SLA Warning / Error
    playWarning() {
      if (!this.enabled) return;
      try {
        this._initContext();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const notes = [440, 370, 440, 370];

        notes.forEach((freq, idx) => {
          const osc = this.ctx.createOscillator();
          const gain = this.ctx.createGain();
          const start = now + idx * 0.07;

          osc.type = 'sawtooth';
          osc.frequency.setValueAtTime(freq, start);

          gain.gain.setValueAtTime(0.08, start);
          gain.gain.exponentialRampToValueAtTime(0.001, start + 0.06);

          osc.connect(gain);
          gain.connect(this.ctx.destination);

          osc.start(start);
          osc.stop(start + 0.065);
        });
      } catch (e) {}
    }

    // 8-Bit Retro Theme Switch Powerup Boot
    playThemeSwitch() {
      if (!this.enabled) return;
      try {
        this._initContext();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const notes = [330, 440, 554.37, 659.25, 880];

        notes.forEach((freq, idx) => {
          const osc = this.ctx.createOscillator();
          const gain = this.ctx.createGain();
          const start = now + idx * 0.035;

          osc.type = 'square';
          osc.frequency.setValueAtTime(freq, start);

          gain.gain.setValueAtTime(0.08, start);
          gain.gain.exponentialRampToValueAtTime(0.001, start + 0.06);

          osc.connect(gain);
          gain.connect(this.ctx.destination);

          osc.start(start);
          osc.stop(start + 0.065);
        });
      } catch (e) {}
    }
  }

  // --- 2. Retro Theme Manager Engine ---
  class RetroThemeManager {
    constructor() {
      this.sound = new RetroSoundEngine();
      this.activeTheme = localStorage.getItem('omnidesk_retro_theme') || 'synthwave';
      this.scanlinesEnabled = localStorage.getItem('omnidesk_retro_scanlines') !== 'false';
      this.flickerEnabled = localStorage.getItem('omnidesk_retro_flicker') === 'true';

      this.themes = [
        { id: 'synthwave', name: 'Synthwave 80s', icon: 'fa-sun', desc: 'Neon Pink, Electric Cyan & Outrun Grid' },
        { id: 'terminal', name: 'CRT Terminal', icon: 'fa-terminal', desc: 'Phosphor Green Monospace Cyberdeck' },
        { id: 'win95', name: 'Windows 95', icon: 'fa-window-restore', desc: 'Classic Beveled 3D Desktop OS' },
        { id: 'arcade', name: 'Arcade 90s', icon: 'fa-gamepad', desc: 'Neo-Brutalist Pop & 16-Bit Badges' },
        { id: 'cyber_dark', name: 'Cyber Modern', icon: 'fa-moon', desc: 'Obsidian Glassmorphic Slate' },
        { id: 'light', name: 'Clean Light', icon: 'fa-sun-bright', desc: 'Minimal Enterprise High-Contrast' }
      ];

      this.init();
    }

    init() {
      // 1. Apply saved theme & FX immediately to avoid flash
      this.applyTheme(this.activeTheme, false);
      this.applyScanlines(this.scanlinesEnabled);
      this.applyFlicker(this.flickerEnabled);

      // 2. Inject DOM elements when ready
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => this.injectUI());
      } else {
        this.injectUI();
      }

      // 3. Attach sound event listeners globally
      this.attachSoundListeners();
    }

    applyTheme(themeId, playSound = true) {
      this.activeTheme = themeId;
      localStorage.setItem('omnidesk_retro_theme', themeId);

      // Set data-theme on <html>
      if (themeId === 'cyber_dark') {
        document.documentElement.removeAttribute('data-theme');
      } else {
        document.documentElement.setAttribute('data-theme', themeId);
      }

      // Sync Admin dropdown if present
      const adminSelect = document.getElementById('feat-theme-mode');
      if (adminSelect && adminSelect.value !== themeId) {
        // If option exists, select it
        if (Array.from(adminSelect.options).some(o => o.value === themeId)) {
          adminSelect.value = themeId;
        }
      }

      // Update active state in Retro Dock
      this.updateDockButtons();

      // Play retro switch audio
      if (playSound) {
        this.sound.playThemeSwitch();
      }

      // Dispatch custom event for app/admin reactivity
      window.dispatchEvent(new CustomEvent('omnidesk:themechange', { detail: { theme: themeId } }));
    }

    applyScanlines(enabled) {
      this.scanlinesEnabled = enabled;
      localStorage.setItem('omnidesk_retro_scanlines', enabled);

      let overlay = document.getElementById('retro-crt-overlay');
      if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'retro-crt-overlay';
        overlay.className = 'retro-crt-overlay';
        overlay.setAttribute('aria-hidden', 'true');
        document.body.appendChild(overlay);
      }

      if (enabled) {
        overlay.classList.add('is-active');
      } else {
        overlay.classList.remove('is-active');
      }

      this.updateDockFX();
    }

    applyFlicker(enabled) {
      this.flickerEnabled = enabled;
      localStorage.setItem('omnidesk_retro_flicker', enabled);

      let overlay = document.getElementById('retro-crt-overlay');
      if (overlay) {
        if (enabled) {
          overlay.classList.add('flicker-active');
        } else {
          overlay.classList.remove('flicker-active');
        }
      }

      this.updateDockFX();
    }

    injectUI() {
      // 1. Ensure CRT overlay exists
      this.applyScanlines(this.scanlinesEnabled);
      this.applyFlicker(this.flickerEnabled);

      // 2. Inject Floating Retro Dock Widget if not present
      if (!document.getElementById('retro-theme-dock')) {
        const dock = document.createElement('div');
        dock.id = 'retro-theme-dock';
        dock.className = 'retro-theme-dock';
        dock.innerHTML = `
          <!-- Collapsed Trigger Pill -->
          <button type="button" class="retro-dock-trigger" id="retro-dock-toggle-btn" title="Toggle Retro Design Suite & Themes" aria-label="Toggle Retro Design Suite">
            <span class="retro-dock-icon">🕹️</span>
            <span class="retro-dock-label">Retro Themes</span>
            <span class="retro-dock-badge" id="retro-dock-current-theme">${this.getThemeName(this.activeTheme)}</span>
          </button>

          <!-- Expanded Retro Control Panel -->
          <div class="retro-dock-panel" id="retro-dock-panel">
            <div class="retro-dock-header">
              <div class="retro-dock-title">
                <i class="fa-solid fa-gamepad"></i> Retro Style Suite
              </div>
              <button type="button" class="retro-dock-close" id="retro-dock-close-btn" title="Close Dock" aria-label="Close Dock">
                <i class="fa-solid fa-xmark"></i>
              </button>
            </div>

            <div class="retro-dock-body">
              <div class="retro-section-label">Aesthetic Presets</div>
              <div class="retro-theme-grid">
                ${this.themes.map(t => `
                  <button type="button" class="retro-theme-btn ${this.activeTheme === t.id ? 'is-active' : ''}" data-theme-id="${t.id}" title="${t.desc}">
                    <i class="fa-solid ${t.icon}"></i>
                    <span class="retro-btn-name">${t.name}</span>
                  </button>
                `).join('')}
              </div>

              <div class="retro-section-label" style="margin-top: 12px;">Retro FX & Audio</div>
              <div class="retro-fx-row">
                <button type="button" class="retro-fx-btn ${this.scanlinesEnabled ? 'is-active' : ''}" id="fx-toggle-scanlines" title="Toggle CRT Scanline Overlay">
                  <i class="fa-solid fa-tv"></i>
                  <span>Scanlines</span>
                </button>
                <button type="button" class="retro-fx-btn ${this.sound.enabled ? 'is-active' : ''}" id="fx-toggle-sound" title="Toggle 8-Bit Web Audio Synthesizer">
                  <i class="fa-solid ${this.sound.enabled ? 'fa-volume-high' : 'fa-volume-xmark'}"></i>
                  <span>8-Bit SFX</span>
                </button>
                <button type="button" class="retro-fx-btn ${this.flickerEnabled ? 'is-active' : ''}" id="fx-toggle-flicker" title="Toggle CRT Screen Glow & Flicker">
                  <i class="fa-solid fa-bolt"></i>
                  <span>CRT Glow</span>
                </button>
              </div>
            </div>

            <div class="retro-dock-footer">
              <span class="retro-footer-tag">OmniDesk Retro Engine v2.0</span>
              <button type="button" class="retro-test-sound-btn" id="retro-test-sound-btn" title="Test 8-bit sound chip">
                <i class="fa-solid fa-music"></i> Test SFX
              </button>
            </div>
          </div>
        `;

        document.body.appendChild(dock);

        // Bind Dock Events
        const toggleBtn = document.getElementById('retro-dock-toggle-btn');
        const panel = document.getElementById('retro-dock-panel');
        const closeBtn = document.getElementById('retro-dock-close-btn');

        if (toggleBtn && panel) {
          toggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.sound.playClick();
            panel.classList.toggle('is-open');
          });
        }

        if (closeBtn && panel) {
          closeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.sound.playClick();
            panel.classList.remove('is-open');
          });
        }

        // Click outside to close dock
        document.addEventListener('click', (e) => {
          if (panel && panel.classList.contains('is-open')) {
            if (!dock.contains(e.target)) {
              panel.classList.remove('is-open');
            }
          }
        });

        // Theme buttons inside dock
        const themeBtns = dock.querySelectorAll('.retro-theme-btn');
        themeBtns.forEach(btn => {
          btn.addEventListener('click', () => {
            const tId = btn.getAttribute('data-theme-id');
            if (tId) {
              this.applyTheme(tId, true);
            }
          });
        });

        // FX Toggles
        const scanlineBtn = document.getElementById('fx-toggle-scanlines');
        if (scanlineBtn) {
          scanlineBtn.addEventListener('click', () => {
            this.applyScanlines(!this.scanlinesEnabled);
            this.sound.playClick();
          });
        }

        const soundBtn = document.getElementById('fx-toggle-sound');
        if (soundBtn) {
          soundBtn.addEventListener('click', () => {
            const state = this.sound.toggleSound();
            this.updateDockFX();
          });
        }

        const flickerBtn = document.getElementById('fx-toggle-flicker');
        if (flickerBtn) {
          flickerBtn.addEventListener('click', () => {
            this.applyFlicker(!this.flickerEnabled);
            this.sound.playClick();
          });
        }

        const testSoundBtn = document.getElementById('retro-test-sound-btn');
        if (testSoundBtn) {
          testSoundBtn.addEventListener('click', () => {
            this.sound.playSuccess();
          });
        }
      }

      this.updateDockButtons();
      this.updateDockFX();
    }

    getThemeName(themeId) {
      const found = this.themes.find(t => t.id === themeId);
      return found ? found.name : 'Retro';
    }

    updateDockButtons() {
      const badge = document.getElementById('retro-dock-current-theme');
      if (badge) {
        badge.textContent = this.getThemeName(this.activeTheme);
      }

      const btns = document.querySelectorAll('.retro-theme-btn');
      btns.forEach(b => {
        if (b.getAttribute('data-theme-id') === this.activeTheme) {
          b.classList.add('is-active');
        } else {
          b.classList.remove('is-active');
        }
      });
    }

    updateDockFX() {
      const scanlineBtn = document.getElementById('fx-toggle-scanlines');
      if (scanlineBtn) {
        scanlineBtn.classList.toggle('is-active', this.scanlinesEnabled);
      }

      const soundBtn = document.getElementById('fx-toggle-sound');
      if (soundBtn) {
        soundBtn.classList.toggle('is-active', this.sound.enabled);
        const icon = soundBtn.querySelector('i');
        if (icon) {
          icon.className = `fa-solid ${this.sound.enabled ? 'fa-volume-high' : 'fa-volume-xmark'}`;
        }
      }

      const flickerBtn = document.getElementById('fx-toggle-flicker');
      if (flickerBtn) {
        flickerBtn.classList.toggle('is-active', this.flickerEnabled);
      }
    }

    attachSoundListeners() {
      // Global button and link click sound effect
      document.addEventListener('click', (e) => {
        const target = e.target.closest('button, a.btn, .chip-btn, .sidebar-item-btn, .tab-btn, .msg-btn-action, .rating-star-btn');
        if (target && !target.closest('#retro-theme-dock')) {
          if (target.classList.contains('rating-star-btn') || target.textContent.includes('Submit') || target.textContent.includes('Resolve')) {
            this.sound.playSuccess();
          } else {
            this.sound.playClick();
          }
        }
      });

      // Hook form submits (chat message send, lead capture, ticket submit)
      document.addEventListener('submit', (e) => {
        if (e.target.id === 'chat-input-form' || e.target.id === 'lead-capture-form' || e.target.id === 'ticket-claim-form') {
          this.sound.playSend();
        }
      });
    }
  }

  // Instantiate and expose globally
  window.RetroEngine = new RetroThemeManager();
})();
