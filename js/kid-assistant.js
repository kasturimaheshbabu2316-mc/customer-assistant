/* ==========================================================================
   OMNIDESK AI — "SPARKY" THE FLOATING AI KID MASCOT
   Interactive, Cute, Playful Chibi Robot Companion for OmniDesk AI
   Acts like a curious, enthusiastic kid ready to help!
   ========================================================================== */

(function () {
  'use strict';

  class SparkyKidMascot {
    constructor() {
      this.isAsleep = localStorage.getItem('sparky_asleep') === 'true';
      this.hasHighFived = false;
      this.dialogueIndex = 0;
      this.dialogues = [
        "Hiya friend! I'm Sparky! Need help with your order? 🚀",
        "Wheee! Look at all these cool store policies! ✨",
        "Psst! Did you know returns are super easy? 30 days! 🎁",
        "I'm super fast at looking up tracking codes! Vroom! 🏎️",
        "Got questions about warranty? Sparky knows it all! 🛠️",
        "Click me! Give Sparky a high five! ✋",
        "Need a human agent? You can escalate anytime! 🤝",
        "Sparky is watching over you! Have a super duper day! 🌟"
      ];
      this.audioCtx = null;
      this.init();
    }

    _getAudio() {
      if (!this.audioCtx) {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (AudioContext) this.audioCtx = new AudioContext();
      }
      if (this.audioCtx && this.audioCtx.state === 'suspended') {
        this.audioCtx.resume();
      }
      return this.audioCtx;
    }

    playGiggleSound() {
      try {
        const ctx = this._getAudio();
        if (!ctx) return;
        const now = ctx.currentTime;
        [580, 720, 880, 1100].forEach((freq, idx) => {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          const t = now + idx * 0.05;
          osc.type = 'sine';
          osc.frequency.setValueAtTime(freq, t);
          osc.frequency.exponentialRampToValueAtTime(freq * 1.5, t + 0.04);
          gain.gain.setValueAtTime(0.08, t);
          gain.gain.exponentialRampToValueAtTime(0.001, t + 0.07);
          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.start(t);
          osc.stop(t + 0.08);
        });
      } catch (e) {}
    }

    playCelebrationFanfare() {
      try {
        const ctx = this._getAudio();
        if (!ctx) return;
        const now = ctx.currentTime;
        [523.25, 659.25, 783.99, 1046.50, 1318.51].forEach((freq, idx) => {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          const t = now + idx * 0.07;
          osc.type = 'triangle';
          osc.frequency.setValueAtTime(freq, t);
          gain.gain.setValueAtTime(0.12, t);
          gain.gain.exponentialRampToValueAtTime(0.001, t + 0.16);
          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.start(t);
          osc.stop(t + 0.17);
        });
      } catch (e) {}
    }

    init() {
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => this.injectDOM());
      } else {
        this.injectDOM();
      }
    }

    injectDOM() {
      if (document.getElementById('sparky-mascot-root')) return;

      const container = document.createElement('div');
      container.id = 'sparky-mascot-root';
      container.className = 'sparky-mascot-root';

      container.innerHTML = `
        <!-- Floating Speech Bubble -->
        <div id="sparky-bubble" class="sparky-speech-bubble" style="${this.isAsleep ? 'display: none;' : ''}">
          <p class="sparky-speech-text" id="sparky-speech-text">${this.dialogues[0]}</p>
          <button type="button" class="sparky-speech-close" id="sparky-bubble-close" title="Dismiss" aria-label="Dismiss speech">✕</button>
        </div>

        <!-- Interactive Kid Menu Card -->
        <div id="sparky-menu" class="sparky-interactive-card is-hidden">
          <div class="sparky-menu-header">
            <span class="sparky-menu-title">
              <span>🎈</span> Sparky's Playful Hub
            </span>
            <span class="sparky-menu-badge">AI Kid Buddy</span>
          </div>
          <p class="sparky-menu-subtitle">I'm little, but I know all store secrets! Pick something fun:</p>
          
          <div class="sparky-action-chips">
            <button type="button" class="sparky-chip-btn high-five-btn" id="btn-sparky-highfive">
              <span>✋</span> <strong>Give High Five!</strong>
            </button>
            <button type="button" class="sparky-chip-btn" onclick="Sparky.askQuestion('Where is my package and delivery tracking status?')">
              <span>📦</span> Where's my package?
            </button>
            <button type="button" class="sparky-chip-btn" onclick="Sparky.askQuestion('What is your 30-day return policy and refund process?')">
              <span>💸</span> Can I get a refund?
            </button>
            <button type="button" class="sparky-chip-btn" onclick="Sparky.askQuestion('Do you offer a 14-day price match guarantee?')">
              <span>💳</span> Price Match Guarantee?
            </button>
            <button type="button" class="sparky-chip-btn" id="btn-sparky-secret">
              <span>🍦</span> Tell me a secret tip!
            </button>
            <button type="button" class="sparky-chip-btn" id="btn-sparky-sleep" style="margin-top: 4px; opacity: 0.8;">
              <span>💤</span> Nap Time (Minimize)
            </button>
          </div>
        </div>

        <!-- 3D Mascot Character Avatar -->
        <button type="button" class="sparky-avatar-btn" id="sparky-avatar-btn" title="Sparky the AI Kid Buddy" aria-label="Sparky the AI Kid Buddy">
          <div class="sparky-antenna">
            <div class="sparky-antenna-orb"></div>
          </div>
          <div class="sparky-face">
            <div class="sparky-eye" id="sparky-eye-left"></div>
            <div class="sparky-eye" id="sparky-eye-right"></div>
            <div class="sparky-blush-left"></div>
            <div class="sparky-blush-right"></div>
          </div>
        </button>
      `;

      document.body.appendChild(container);
      this.attachEvents();
      this.startDialogueCycle();
    }

    attachEvents() {
      const avatar = document.getElementById('sparky-avatar-btn');
      const bubble = document.getElementById('sparky-bubble');
      const closeBtn = document.getElementById('sparky-bubble-close');
      const menu = document.getElementById('sparky-menu');
      const highFiveBtn = document.getElementById('btn-sparky-highfive');
      const secretBtn = document.getElementById('btn-sparky-secret');
      const sleepBtn = document.getElementById('btn-sparky-sleep');

      if (avatar) {
        avatar.addEventListener('click', (e) => {
          e.stopPropagation();
          if (this.isAsleep) {
            this.wakeUp();
            return;
          }
          this.playGiggleSound();
          this.doJumpAnimation();
          if (menu) menu.classList.toggle('is-hidden');
        });
      }

      if (closeBtn) {
        closeBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          if (bubble) bubble.style.display = 'none';
        });
      }

      if (highFiveBtn) {
        highFiveBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          this.giveHighFive();
        });
      }

      if (secretBtn) {
        secretBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          this.tellSecret();
        });
      }

      if (sleepBtn) {
        sleepBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          this.goToSleep();
        });
      }

      // Close menu when clicking outside
      document.addEventListener('click', (e) => {
        if (menu && !menu.contains(e.target) && e.target !== avatar) {
          menu.classList.add('is-hidden');
        }
      });

      // Context sensitivity: Watch user typing in chat input
      const chatInput = document.getElementById('chat-text-input');
      if (chatInput) {
        let typedTimeout = null;
        chatInput.addEventListener('focus', () => {
          if (!this.isAsleep) {
            this.speak("Ooh! You're typing! Sparky is listening! 🤩", 5000);
          }
        });
        chatInput.addEventListener('input', () => {
          clearTimeout(typedTimeout);
          typedTimeout = setTimeout(() => {
            if (!this.isAsleep && chatInput.value.length > 5) {
              const eyeLeft = document.getElementById('sparky-eye-left');
              const eyeRight = document.getElementById('sparky-eye-right');
              if (eyeLeft && eyeRight) {
                eyeLeft.style.transform = 'scale(1.3)';
                eyeRight.style.transform = 'scale(1.3)';
                setTimeout(() => {
                  eyeLeft.style.transform = '';
                  eyeRight.style.transform = '';
                }, 1200);
              }
            }
          }, 300);
        });
      }
    }

    speak(text, duration = 8000) {
      if (this.isAsleep) return;
      const bubble = document.getElementById('sparky-bubble');
      const txt = document.getElementById('sparky-speech-text');
      if (bubble && txt) {
        txt.textContent = text;
        bubble.style.display = 'flex';
        bubble.style.animation = 'none';
        void bubble.offsetWidth; // trigger reflow
        bubble.style.animation = 'sparkyPopIn 0.35s cubic-bezier(0.34, 1.56, 0.64, 1)';

        if (this._speakTimer) clearTimeout(this._speakTimer);
        this._speakTimer = setTimeout(() => {
          if (bubble && !document.getElementById('sparky-menu')?.classList.contains('is-hidden')) return;
          if (bubble) bubble.style.display = 'none';
        }, duration);
      }
    }

    startDialogueCycle() {
      setInterval(() => {
        if (this.isAsleep) return;
        const menu = document.getElementById('sparky-menu');
        if (menu && !menu.classList.contains('is-hidden')) return;

        this.dialogueIndex = (this.dialogueIndex + 1) % this.dialogues.length;
        this.speak(this.dialogues[this.dialogueIndex]);
      }, 18000);
    }

    doJumpAnimation() {
      const avatar = document.getElementById('sparky-avatar-btn');
      if (!avatar) return;
      avatar.style.transform = 'translateY(-22px) scale(1.18) rotate(12deg)';
      setTimeout(() => {
        avatar.style.transform = 'translateY(-6px) scale(1.08) rotate(-8deg)';
        setTimeout(() => {
          avatar.style.transform = '';
        }, 220);
      }, 200);
    }

    giveHighFive() {
      this.playCelebrationFanfare();
      this.doJumpAnimation();
      this.speak("YAAAY! HIGH FIVE! Best friends forever! 💖✨", 9000);

      // Trigger floating confetti / heart particles
      const avatar = document.getElementById('sparky-avatar-btn');
      if (avatar) {
        const rect = avatar.getBoundingClientRect();
        const symbols = ['💖', '⭐', '🎈', '✨', '🎉', '🌟', '🧁'];
        for (let i = 0; i < 14; i++) {
          const p = document.createElement('div');
          p.className = 'sparky-particle';
          p.textContent = symbols[Math.floor(Math.random() * symbols.length)];
          p.style.left = (rect.left + rect.width / 2) + 'px';
          p.style.top = (rect.top + rect.height / 2) + 'px';
          const dx = (Math.random() - 0.5) * 220 + 'px';
          const dy = (-60 - Math.random() * 160) + 'px';
          p.style.setProperty('--dx', dx);
          p.style.setProperty('--dy', dy);
          document.body.appendChild(p);
          setTimeout(() => p.remove(), 1200);
        }
      }

      const menu = document.getElementById('sparky-menu');
      if (menu) menu.classList.add('is-hidden');
    }

    tellSecret() {
      this.playGiggleSound();
      const secrets = [
        "Secret tip: You have 14 whole days after purchase to claim a price difference match! 💰",
        "Did you know? Even opened electronics are covered if defective within 30 days! 🎧",
        "Pro tip: Mention 'Expedited DHL' in chat to see international delivery estimates! ✈️",
        "Secret: You can attach a damage photo directly using the camera button! 📸"
      ];
      const randomSecret = secrets[Math.floor(Math.random() * secrets.length)];
      this.speak(randomSecret, 11000);
      const menu = document.getElementById('sparky-menu');
      if (menu) menu.classList.add('is-hidden');
    }

    askQuestion(query) {
      this.playGiggleSound();
      const menu = document.getElementById('sparky-menu');
      if (menu) menu.classList.add('is-hidden');

      // Check if on app.html with chat view
      if (typeof window.switchCustomerView === 'function') {
        window.switchCustomerView('chat');
      }

      const input = document.getElementById('chat-text-input');
      const form = document.getElementById('chat-input-form');
      if (input && form) {
        input.value = query;
        if (typeof window.autoResizeTextarea === 'function') {
          window.autoResizeTextarea(input);
        }
        form.dispatchEvent(new Event('submit'));
        this.speak("Asking our verified AI right now! Vroom! 🚀", 6000);
      } else {
        // If on index or admin, redirect to app.html with query param
        window.location.href = `app.html?prompt=${encodeURIComponent(query)}`;
      }
    }

    goToSleep() {
      this.isAsleep = true;
      localStorage.setItem('sparky_asleep', 'true');
      const bubble = document.getElementById('sparky-bubble');
      const menu = document.getElementById('sparky-menu');
      const avatar = document.getElementById('sparky-avatar-btn');
      if (bubble) bubble.style.display = 'none';
      if (menu) menu.classList.add('is-hidden');
      if (avatar) {
        avatar.innerHTML = `<span style="font-size: 1.4rem;">💤</span>`;
        avatar.title = "Sparky is taking a nap. Click to wake up!";
      }
    }

    wakeUp() {
      this.isAsleep = false;
      localStorage.setItem('sparky_asleep', 'false');
      const avatar = document.getElementById('sparky-avatar-btn');
      if (avatar) {
        avatar.innerHTML = `
          <div class="sparky-antenna"><div class="sparky-antenna-orb"></div></div>
          <div class="sparky-face">
            <div class="sparky-eye" id="sparky-eye-left"></div>
            <div class="sparky-eye" id="sparky-eye-right"></div>
            <div class="sparky-blush-left"></div>
            <div class="sparky-blush-right"></div>
          </div>
        `;
        avatar.title = "Sparky the AI Kid Buddy";
      }
      this.playGiggleSound();
      this.doJumpAnimation();
      this.speak("Yawn! Sparky is awake and full of energy! 🎈🚀", 7000);
    }
  }

  // Expose global instance
  window.Sparky = new SparkyKidMascot();
})();
