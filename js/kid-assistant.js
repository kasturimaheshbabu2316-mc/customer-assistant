/* ==========================================================================
   OMNIDESK AI — "SPARKY" THE FLOATING AI MASCOT & HUMAN-LIKE COMPANION
   Full Articulated Anatomy (Head, Visor, Torso, Moving Arms & Hands)
   Dynamic Floating Physics (Follows Mouse & Typing), Emotional Emojis & Audio
   ========================================================================== */

(function () {
  'use strict';

  class SparkyKidMascot {
    constructor() {
      this.isAsleep = false;
      try { localStorage.removeItem('sparky_asleep'); } catch (e) {}
      this.hasHighFived = false;
      this.dialogueIndex = 0;
      this.currentPose = 'idle';
      this.currentEmotion = '✨';

      // Full-Screen Floating Mascot Physics Engine State
      const savedX = parseFloat(localStorage.getItem('sparky_x'));
      const savedY = parseFloat(localStorage.getItem('sparky_y'));
      const defaultX = Math.max(30, window.innerWidth - 170);
      const defaultY = Math.max(50, window.innerHeight - 240);

      this.pos = {
        x: (!isNaN(savedX) && savedX > 20 && savedX < window.innerWidth - 110) ? savedX : defaultX,
        y: (!isNaN(savedY) && savedY > 20 && savedY < window.innerHeight - 130) ? savedY : defaultY
      };
      this.target = { x: this.pos.x, y: this.pos.y };
      this.anchor = { x: this.pos.x, y: this.pos.y };
      this.vel = { x: 0, y: 0 };

      this.mouse = { x: this.pos.x, y: this.pos.y };
      this.lastMouseMoveTime = Date.now();
      this.isDragging = false;
      this.hasDragged = false;
      this.dragOffset = { x: 0, y: 0 };
      this.dragStart = { x: 0, y: 0 };
      this.roamMode = 'follow'; // 'follow' (mouse escort companion) | 'pinned' (stays at anchor)

      this.isTyping = false;
      this.isStreaming = false;
      this.typingTimer = null;
      this.proximityCooldown = false;

      this.dialogues = [
        "Hiya friend! I'm Sparky! Need help with your order? 🚀",
        "Wheee! Look at all these cool store policies! ✨",
        "Psst! Did you know returns are super easy? 30 days! 🎁",
        "I'm super fast at looking up tracking codes! Vroom! 🏎️",
        "Got questions about warranty? Sparky knows it all! 🛠️",
        "Drag me anywhere on your screen! I can fly! 🛸",
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

    playChimeSound() {
      try {
        const ctx = this._getAudio();
        if (!ctx) return;
        const now = ctx.currentTime;
        [659.25, 830.61, 987.77, 1318.51].forEach((freq, idx) => {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          const t = now + idx * 0.06;
          osc.type = 'sine';
          osc.frequency.setValueAtTime(freq, t);
          gain.gain.setValueAtTime(0.09, t);
          gain.gain.exponentialRampToValueAtTime(0.001, t + 0.18);
          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.start(t);
          osc.stop(t + 0.19);
        });
      } catch (e) {}
    }

    playThinkingBlip() {
      try {
        const ctx = this._getAudio();
        if (!ctx) return;
        const now = ctx.currentTime;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(440, now);
        osc.frequency.exponentialRampToValueAtTime(660, now + 0.08);
        gain.gain.setValueAtTime(0.06, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.1);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.11);
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

    playPopTap() {
      try {
        const ctx = this._getAudio();
        if (!ctx) return;
        const now = ctx.currentTime;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(750, now);
        osc.frequency.exponentialRampToValueAtTime(320, now + 0.04);
        gain.gain.setValueAtTime(0.04, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.06);
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
      const existing = document.getElementById('sparky-mascot-root');
      if (existing) existing.remove();

      const container = document.createElement('div');
      container.id = 'sparky-mascot-root';
      container.className = 'sparky-mascot-root';

      container.innerHTML = `
        <!-- Floating Speech Bubble -->
        <div id="sparky-bubble" class="sparky-speech-bubble" style="${this.isAsleep ? 'display: none;' : ''}">
          <p class="sparky-speech-text" id="sparky-speech-text">${this.dialogues[0]}</p>
          <button type="button" class="sparky-speech-close" id="sparky-bubble-close" title="Dismiss" aria-label="Dismiss speech">✕</button>
        </div>

        <!-- Floating Emotional Mood Emoji Halo -->
        <div class="sparky-mood-halo" id="sparky-mood-halo" title="Sparky's Emotion (Click me!)">
          <span class="sparky-mood-emoji" id="sparky-mood-emoji">${this.currentEmotion}</span>
        </div>

        <!-- Interactive Kid Menu Card with Emotional Reactions -->
        <div id="sparky-menu" class="sparky-interactive-card is-hidden">
          <div class="sparky-menu-header">
            <span class="sparky-menu-title">
              <span>🎈</span> Sparky's Playful Hub
            </span>
            <span class="sparky-menu-badge">AI Humanoid Buddy</span>
          </div>
          <p class="sparky-menu-subtitle">Tap an emotion to watch me react, or pick a question:</p>

          <!-- Interactive Emotional Emojis Bar -->
          <div class="sparky-emotions-bar" id="sparky-emotions-bar">
            <button type="button" class="sparky-emotion-pill" data-emotion="🥰" title="Love & Joy">🥰</button>
            <button type="button" class="sparky-emotion-pill" data-emotion="🥳" title="Party Time!">🥳</button>
            <button type="button" class="sparky-emotion-pill" data-emotion="🤔" title="Deep Thought">🤔</button>
            <button type="button" class="sparky-emotion-pill" data-emotion="💡" title="Got an Idea!">💡</button>
            <button type="button" class="sparky-emotion-pill" data-emotion="💖" title="Warm Hug">💖</button>
            <button type="button" class="sparky-emotion-pill" data-emotion="🔥" title="Super Fast">🔥</button>
            <button type="button" class="sparky-emotion-pill" data-emotion="🚀" title="Vroom!">🚀</button>
            <button type="button" class="sparky-emotion-pill" data-emotion="😎" title="Cool AI">😎</button>
          </div>
          
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
            <button type="button" class="sparky-chip-btn" id="btn-sparky-roam">
              <span>🛸</span> <strong id="sparky-roam-label">Roam Mode: Screen Escort (ON)</strong>
            </button>
            <button type="button" class="sparky-chip-btn" id="btn-sparky-sleep" style="margin-top: 4px; opacity: 0.85;">
              <span>💤</span> Nap Time (Minimize)
            </button>
          </div>
        </div>

        <!-- Full Articulated Mascot Rig (Head, Visor, Body & Moving Hands) -->
        <button type="button" class="sparky-avatar-btn" id="sparky-avatar-btn" title="Sparky the AI Companion" aria-label="Sparky the AI Companion">
          <div class="sparky-rig pose-idle" id="sparky-rig">
            <!-- Left Arm with Hand & Thumb -->
            <div class="sparky-arm sparky-arm-left" id="sparky-arm-left">
              <div class="sparky-shoulder"></div>
              <div class="sparky-forearm"></div>
              <div class="sparky-hand" id="sparky-hand-left">
                <div class="sparky-thumb"></div>
              </div>
            </div>

            <!-- Central Column: Head, Torso, Thruster -->
            <div class="sparky-torso-column">
              <!-- Head with Antenna and Visor -->
              <div class="sparky-head-wrapper">
                <div class="sparky-antenna">
                  <div class="sparky-antenna-orb" id="sparky-antenna-orb"></div>
                </div>
                <div class="sparky-head" id="sparky-head">
                  <div class="sparky-face" id="sparky-face">
                    <div class="sparky-eyes-row">
                      <div class="sparky-eye" id="sparky-eye-left">
                        <div class="sparky-pupil" id="sparky-pupil-left"></div>
                      </div>
                      <div class="sparky-eye" id="sparky-eye-right">
                        <div class="sparky-pupil" id="sparky-pupil-right"></div>
                      </div>
                    </div>
                    <div class="sparky-mouth" id="sparky-mouth"></div>
                    <div class="sparky-blush-left"></div>
                    <div class="sparky-blush-right"></div>
                  </div>
                </div>
              </div>

              <!-- Humanoid Chassis Body with Core Reactor -->
              <div class="sparky-body" id="sparky-body">
                <div class="sparky-chest-core" id="sparky-chest-core">
                  <i class="fa-solid fa-bolt"></i>
                </div>
                <div class="sparky-belt"></div>
              </div>

              <!-- Anti-Gravity Hover Base -->
              <div class="sparky-hover-thruster">
                <div class="sparky-thrust-ring"></div>
                <div class="sparky-thrust-glow" id="sparky-thrust-glow"></div>
              </div>
            </div>

            <!-- Right Arm with Hand & Thumb -->
            <div class="sparky-arm sparky-arm-right" id="sparky-arm-right">
              <div class="sparky-shoulder"></div>
              <div class="sparky-forearm"></div>
              <div class="sparky-hand" id="sparky-hand-right">
                <div class="sparky-thumb"></div>
              </div>
            </div>
          </div>
        </button>
      `;

      document.body.appendChild(container);
      this.attachEvents();
      this.startDialogueCycle();
      this.startFloatingPhysicsLoop();
    }

    setPose(poseName, duration = null) {
      const rig = document.getElementById('sparky-rig');
      if (!rig) return;
      this.currentPose = poseName;
      rig.className = `sparky-rig pose-${poseName}`;

      const mouth = document.getElementById('sparky-mouth');
      if (mouth) {
        mouth.className = 'sparky-mouth';
        if (poseName === 'talking') mouth.classList.add('talking');
        else if (poseName === 'cheer' || poseName === 'waving') mouth.classList.add('happy');
        else if (poseName === 'thinking') mouth.classList.add('o-shape');
      }

      if (duration) {
        setTimeout(() => {
          if (this.currentPose === poseName && !this.isTyping && !this.isStreaming) {
            this.setPose('idle');
          }
        }, duration);
      }
    }

    setEmotion(emoji, customText = null, pose = null, playSound = true) {
      if (this.isAsleep) return;
      this.currentEmotion = emoji;
      const emojiEl = document.getElementById('sparky-mood-emoji');
      if (emojiEl) {
        emojiEl.textContent = emoji;
        emojiEl.style.animation = 'none';
        void emojiEl.offsetWidth;
        emojiEl.style.animation = 'sparkyMoodPop 0.35s cubic-bezier(0.34, 1.56, 0.64, 1)';
      }

      if (pose) this.setPose(pose);

      if (playSound) {
        if (emoji === '💡') this.playChimeSound();
        else if (emoji === '🤔') this.playThinkingBlip();
        else if (emoji === '🥳' || emoji === '🎉') this.playCelebrationFanfare();
        else this.playGiggleSound();
      }

      if (customText) {
        this.speak(customText, 7000);
      }
    }

    attachEvents() {
      const avatar = document.getElementById('sparky-avatar-btn');
      const bubble = document.getElementById('sparky-bubble');
      const closeBtn = document.getElementById('sparky-bubble-close');
      const menu = document.getElementById('sparky-menu');
      const moodHalo = document.getElementById('sparky-mood-halo');
      const highFiveBtn = document.getElementById('btn-sparky-highfive');
      const secretBtn = document.getElementById('btn-sparky-secret');
      const roamBtn = document.getElementById('btn-sparky-roam');
      const sleepBtn = document.getElementById('btn-sparky-sleep');
      const emotionsBar = document.getElementById('sparky-emotions-bar');
      const chatInput = document.getElementById('chat-text-input');
      const chatForm = document.getElementById('chat-input-form');

      // -----------------------------------------------------------------------
      // 1. DRAG & DROP ANYWHERE OVER ENTIRE SCREEN (Mouse & Touch)
      // -----------------------------------------------------------------------
      const onDragStart = (clientX, clientY) => {
        if (this.isAsleep) return;
        this.isDragging = true;
        this.hasDragged = false;
        this.dragStart = { x: clientX, y: clientY };
        this.dragOffset = { x: clientX - this.pos.x, y: clientY - this.pos.y };
        const root = document.getElementById('sparky-mascot-root');
        if (root) root.classList.add('is-dragging');
      };

      const onDragMove = (clientX, clientY) => {
        if (!this.isDragging) return;
        const dist = Math.hypot(clientX - this.dragStart.x, clientY - this.dragStart.y);
        if (dist > 18) {
          this.hasDragged = true;
        }
        const minX = 20, maxX = Math.max(minX, window.innerWidth - 130);
        const minY = 35, maxY = Math.max(minY, window.innerHeight - 145);
        this.pos.x = Math.max(minX, Math.min(maxX, clientX - this.dragOffset.x));
        this.pos.y = Math.max(minY, Math.min(maxY, clientY - this.dragOffset.y));
        this.target.x = this.pos.x;
        this.target.y = this.pos.y;
        this.anchor.x = this.pos.x;
        this.anchor.y = this.pos.y;
      };

      const onDragEnd = () => {
        if (!this.isDragging) return;
        this.isDragging = false;
        const root = document.getElementById('sparky-mascot-root');
        if (root) root.classList.remove('is-dragging');

        if (this.hasDragged) {
          try {
            localStorage.setItem('sparky_x', this.pos.x.toFixed(1));
            localStorage.setItem('sparky_y', this.pos.y.toFixed(1));
          } catch (e) {}
          this.anchor.x = this.pos.x;
          this.anchor.y = this.pos.y;
          this.doJumpAnimation();
          this.playGiggleSound();
          this.setEmotion('🚀', "Wheee! I love floating right here! ✨", 'cheer');
          setTimeout(() => { this.hasDragged = false; }, 150);
        } else {
          this.hasDragged = false;
        }
      };

      if (avatar) {
        avatar.addEventListener('mousedown', (e) => {
          if (e.button !== 0) return; // Left click only
          onDragStart(e.clientX, e.clientY);
        });

        avatar.addEventListener('touchstart', (e) => {
          if (e.touches && e.touches.length === 1) {
            onDragStart(e.touches[0].clientX, e.touches[0].clientY);
          }
        }, { passive: true });

        avatar.addEventListener('click', (e) => {
          e.stopPropagation();
          if (this.hasDragged) {
            return; // Don't trigger click at end of drag
          }
          if (this.isAsleep) {
            this.wakeUp();
            return;
          }
          this.playGiggleSound();
          this.doJumpAnimation();
          this.setEmotion('🥰', "Yay! You tapped me! How can I help you today? ✨", 'cheer');
          if (menu) {
            menu.classList.toggle('is-hidden');
          }
        });
      }

      window.addEventListener('mousemove', (e) => {
        if (this.isDragging) {
          onDragMove(e.clientX, e.clientY);
        }
      });

      window.addEventListener('touchmove', (e) => {
        if (this.isDragging && e.touches && e.touches.length === 1) {
          onDragMove(e.touches[0].clientX, e.touches[0].clientY);
        }
      }, { passive: true });

      window.addEventListener('mouseup', () => {
        if (this.isDragging) onDragEnd();
      });

      window.addEventListener('touchend', () => {
        if (this.isDragging) onDragEnd();
      });

      // -----------------------------------------------------------------------
      // 2. MOUSE ESCORT & EYE TRACKING ACROSS ENTIRE SCREEN
      // -----------------------------------------------------------------------
      window.addEventListener('mousemove', (e) => {
        this.mouse.x = e.clientX;
        this.mouse.y = e.clientY;
        this.lastMouseMoveTime = Date.now();

        if (this.isAsleep || this.isDragging) return;

        // When in companion roam mode, float smoothly near the cursor
        if (this.roamMode === 'follow' && !this.isTyping && !this.isStreaming) {
          let offsetX = 85;
          let offsetY = -35;

          // If too close to right viewport edge, flip to left of cursor
          if (e.clientX + offsetX > window.innerWidth - 130) {
            offsetX = -120;
          }
          // If too close to top edge, float slightly lower
          if (e.clientY + offsetY < 50) {
            offsetY = 30;
          }

          const targetX = Math.max(25, Math.min(window.innerWidth - 130, e.clientX + offsetX));
          const targetY = Math.max(45, Math.min(window.innerHeight - 145, e.clientY + offsetY));
          this.target.x = targetX;
          this.target.y = targetY;
          this.anchor.x = targetX;
          this.anchor.y = targetY;
        }

        const avatarEl = document.getElementById('sparky-avatar-btn');
        if (!avatarEl) return;

        const rect = avatarEl.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;

        const deltaX = (e.clientX - centerX);
        const deltaY = (e.clientY - centerY);
        const dist = Math.hypot(deltaX, deltaY);

        // Move Eye Pupils to look directly at cursor
        const pupilLeft = document.getElementById('sparky-pupil-left');
        const pupilRight = document.getElementById('sparky-pupil-right');
        if (pupilLeft && pupilRight) {
          const maxShift = 3;
          const shiftX = Math.max(-maxShift, Math.min(maxShift, (deltaX / 180) * maxShift));
          const shiftY = Math.max(-maxShift, Math.min(maxShift, (deltaY / 180) * maxShift));
          pupilLeft.style.transform = `translate(${shiftX}px, ${shiftY}px)`;
          pupilRight.style.transform = `translate(${shiftX}px, ${shiftY}px)`;
        }

        // Head and rig 3D perspective tilt
        const head = document.getElementById('sparky-head');
        if (head && !this.isTyping) {
          const tiltY = Math.max(-14, Math.min(14, (deltaX / 300) * 14));
          const tiltX = Math.max(-10, Math.min(10, -(deltaY / 300) * 10));
          head.style.transform = `rotateY(${tiltY}deg) rotateX(${tiltX}deg)`;
        }

        // Proximity Reaction: wave and perk up when mouse comes close (<130px)
        if (dist < 130 && !this.proximityCooldown && !this.isTyping && !this.isDragging) {
          this.proximityCooldown = true;
          this.setPose('waving', 2200);
          this.setEmotion('👋', null, null, false);
          setTimeout(() => { this.proximityCooldown = false; }, 6000);
        }
      });

      // -----------------------------------------------------------------------
      // 3. TYPING MAGNET: SWOOP TO QUERY INPUT WHEN USER TYPES OR FOCUSES
      // -----------------------------------------------------------------------
      const snapToChatInput = (isBobbing = false) => {
        if (!chatInput) return;
        const rect = chatInput.getBoundingClientRect();
        // Swoop directly near the query input box
        const targetX = Math.max(30, Math.min(window.innerWidth - 140, rect.right - 120));
        const bob = isBobbing ? (Math.sin(Date.now() / 70) * 7) : 0;
        const targetY = Math.max(50, rect.top - 125 + bob);
        this.target.x = targetX;
        this.target.y = targetY;
        this.anchor.x = targetX;
        this.anchor.y = targetY;
      };

      if (chatInput) {
        chatInput.addEventListener('focus', () => {
          if (!this.isAsleep) {
            this.isTyping = true;
            snapToChatInput(false);
            this.setPose('typing');
            this.setEmotion('🤔', "Ooh! What can I search for you? I'm listening! ✍️", null, false);
          }
        });

        chatInput.addEventListener('input', () => {
          if (this.isAsleep) return;
          this.isTyping = true;
          this.playPopTap();
          this.setPose('typing');
          snapToChatInput(true);

          const val = chatInput.value.toLowerCase();
          if (val.includes('return') || val.includes('refund')) {
            this.setEmotion('💸', null, null, false);
          } else if (val.includes('ship') || val.includes('tracking') || val.includes('order')) {
            this.setEmotion('📦', null, null, false);
          } else if (val.includes('warranty') || val.includes('broken') || val.includes('defect')) {
            this.setEmotion('🛠️', null, null, false);
          } else if (val.includes('price') || val.includes('discount')) {
            this.setEmotion('💳', null, null, false);
          } else if (val.length > 12) {
            this.setEmotion('💡', null, null, false);
          } else {
            this.setEmotion('✍️', null, null, false);
          }
        });

        chatInput.addEventListener('blur', () => {
          setTimeout(() => {
            if (!this.isStreaming && document.activeElement !== chatInput) {
              this.isTyping = false;
              this.setPose('idle');
              // Return smoothly to companion mouse position
              this.target.x = Math.max(30, Math.min(window.innerWidth - 130, this.mouse.x + 85));
              this.target.y = Math.max(50, Math.min(window.innerHeight - 150, this.mouse.y - 35));
              this.anchor.x = this.target.x;
              this.anchor.y = this.target.y;
            }
          }, 800);
        });
      }

      // -----------------------------------------------------------------------
      // 4. MENU CHIPS & CONTROLS
      // -----------------------------------------------------------------------
      if (moodHalo) {
        moodHalo.addEventListener('click', (e) => {
          e.stopPropagation();
          this.cycleRandomEmotion();
        });
      }

      if (emotionsBar) {
        emotionsBar.addEventListener('click', (e) => {
          const pill = e.target.closest('.sparky-emotion-pill');
          if (pill) {
            e.stopPropagation();
            const emoji = pill.getAttribute('data-emotion');
            this.handleEmotionPillClick(emoji);
          }
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

      if (roamBtn) {
        roamBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          const label = document.getElementById('sparky-roam-label');
          if (this.roamMode === 'follow') {
            this.roamMode = 'pinned';
            this.anchor.x = this.pos.x;
            this.anchor.y = this.pos.y;
            this.target.x = this.pos.x;
            this.target.y = this.pos.y;
            if (label) label.textContent = 'Roam Mode: Pinned Here (Anchor)';
            this.playChimeSound();
            this.setEmotion('⚓', "Anchored down! I'll guard this spot! You can drag me anytime! ⚓", 'idle');
          } else {
            this.roamMode = 'follow';
            if (label) label.textContent = 'Roam Mode: Screen Escort (ON)';
            this.playCelebrationFanfare();
            this.setEmotion('🛸', "Wheee! Full-screen escort active! Move your mouse anywhere! 🚀", 'cheer');
          }
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
        if (menu && !menu.contains(e.target) && !avatar?.contains(e.target) && !moodHalo?.contains(e.target)) {
          menu.classList.add('is-hidden');
        }
      });

      // -----------------------------------------------------------------------
      // 5. FORM SUBMIT & CHAT STREAMING INTERACTION
      // -----------------------------------------------------------------------
      if (chatForm) {
        chatForm.addEventListener('submit', () => {
          if (this.isAsleep) return;
          this.isTyping = false;
          this.doJumpAnimation();
          this.setPose('cheer', 1800);
          this.setEmotion('🚀', "Vroom! Query sent! Checking verified policies! 🌟", null, true);

          // Monitor streaming state
          this.isStreaming = true;
          setTimeout(() => {
            if (this.isStreaming) {
              this.setPose('talking');
              this.setEmotion('🗣️', null, null, false);
            }
          }, 400);
        });
      }

      // Observe response streaming completions in customer portal
      const messagesContainer = document.getElementById('chat-messages-scroll-area');
      if (messagesContainer) {
        const observer = new MutationObserver(() => {
          if (!this.isStreaming) return;
          const typingIndicator = messagesContainer.querySelector('.response-thinking-indicator, .typing-cursor');
          if (!typingIndicator && this.isStreaming) {
            // Streaming finished
            this.isStreaming = false;
            this.playCelebrationFanfare();
            this.setPose('cheer', 2500);
            this.setEmotion('🥳', "Tada! Policy answers verified! Need anything else? 💖", null, false);
            this.triggerParticles();
          }
        });
        observer.observe(messagesContainer, { childList: true, subtree: true });
      }

      // Keep mascot in bounds on window resize
      window.addEventListener('resize', () => {
        const minX = 20, maxX = Math.max(minX, window.innerWidth - 130);
        const minY = 35, maxY = Math.max(minY, window.innerHeight - 145);
        this.pos.x = Math.max(minX, Math.min(maxX, this.pos.x));
        this.pos.y = Math.max(minY, Math.min(maxY, this.pos.y));
        this.target.x = Math.max(minX, Math.min(maxX, this.target.x));
        this.target.y = Math.max(minY, Math.min(maxY, this.target.y));
        this.anchor.x = Math.max(minX, Math.min(maxX, this.anchor.x));
        this.anchor.y = Math.max(minY, Math.min(maxY, this.anchor.y));
      });
    }

    startFloatingPhysicsLoop() {
      const root = document.getElementById('sparky-mascot-root');
      const chatInput = document.getElementById('chat-text-input');

      const animate = () => {
        if (root && !this.isAsleep) {
          const now = Date.now();

          // Persistent typing magnet while chat input is actively focused
          if (chatInput && document.activeElement === chatInput) {
            this.isTyping = true;
            const rect = chatInput.getBoundingClientRect();
            const targetX = Math.max(30, Math.min(window.innerWidth - 140, rect.right - 120));
            const bob = Math.sin(now / 70) * 7;
            const targetY = Math.max(50, rect.top - 125 + bob);
            this.target.x = targetX;
            this.target.y = targetY;
            this.anchor.x = targetX;
            this.anchor.y = targetY;
          } else if (!this.isTyping && !this.isStreaming && !this.isDragging && (now - this.lastMouseMoveTime > 2200)) {
            // Autonomous idle hover when user is inactive
            const wanderX = Math.sin(now * 0.0013) * 55 + Math.cos(now * 0.0008) * 30;
            const wanderY = Math.cos(now * 0.0017) * 40 + Math.sin(now * 0.0010) * 22;

            const minX = 25, maxX = Math.max(minX, window.innerWidth - 130);
            const minY = 45, maxY = Math.max(minY, window.innerHeight - 145);

            this.target.x = Math.max(minX, Math.min(maxX, this.anchor.x + wanderX));
            this.target.y = Math.max(minY, Math.min(maxY, this.anchor.y + wanderY));
          }

          // Spring physics & velocity damping towards target position
          if (!this.isDragging) {
            const ax = (this.target.x - this.pos.x) * 0.055;
            const ay = (this.target.y - this.pos.y) * 0.055;
            this.vel.x = (this.vel.x + ax) * 0.82;
            this.vel.y = (this.vel.y + ay) * 0.82;
            this.pos.x += this.vel.x;
            this.pos.y += this.vel.y;
          } else {
            this.vel.x = 0;
            this.vel.y = 0;
          }

          // Strict viewport bounds clamp
          const minX = 20, maxX = Math.max(minX, window.innerWidth - 130);
          const minY = 35, maxY = Math.max(minY, window.innerHeight - 145);
          this.pos.x = Math.max(minX, Math.min(maxX, this.pos.x));
          this.pos.y = Math.max(minY, Math.min(maxY, this.pos.y));

          // Aerodynamic banking tilt when flying fast
          const tilt = Math.max(-20, Math.min(20, this.vel.x * 2.2));

          root.style.transform = `translate3d(${this.pos.x.toFixed(1)}px, ${this.pos.y.toFixed(1)}px, 0px) rotate(${tilt.toFixed(1)}deg)`;

          // Dynamically flip speech bubble & menu when in upper half of screen
          if (this.pos.y < 420) {
            root.classList.add('flip-down');
          } else {
            root.classList.remove('flip-down');
          }

          if (this.pos.x < 320) {
            root.classList.add('dock-left');
            root.classList.remove('dock-right');
          } else if (this.pos.x > window.innerWidth - 340) {
            root.classList.add('dock-right');
            root.classList.remove('dock-left');
          } else {
            root.classList.remove('dock-left', 'dock-right');
          }
        }
        requestAnimationFrame(animate);
      };
      requestAnimationFrame(animate);
    }

    cycleRandomEmotion() {
      const emotions = [
        { emoji: '🥰', text: "Aww! Sparky loves helping you! 💖", pose: 'cheer' },
        { emoji: '💡', text: "Eureka! I know all about our 30-day return policy! ✨", pose: 'talking' },
        { emoji: '🤔', text: "Hmm! Let me ponder that deeply... 💭", pose: 'thinking' },
        { emoji: '🥳', text: "Woohoo! High five party! 🎉", pose: 'cheer' },
        { emoji: '🔥', text: "Super speed! Sub-second grounded AI responses! ⚡", pose: 'waving' },
        { emoji: '😎', text: "Zero hallucinations, pure verified truth! Stay cool! 🕶️", pose: 'idle' }
      ];
      const selected = emotions[Math.floor(Math.random() * emotions.length)];
      this.setEmotion(selected.emoji, selected.text, selected.pose, true);
    }

    handleEmotionPillClick(emoji) {
      const map = {
        '🥰': { text: "Sparky gives you a giant warm hug! 🤗💖", pose: 'cheer' },
        '🥳': { text: "Yay! Time to celebrate! 🎊 Best customer ever!", pose: 'cheer' },
        '🤔': { text: "Analyzing store knowledge base with deep logic... 🧠", pose: 'thinking' },
        '💡': { text: "Aha! Pro-tip: Check Section 4 for 1-year warranty coverage!", pose: 'talking' },
        '💖': { text: "Much love from the OmniDesk team! 💖✨", pose: 'cheer' },
        '🔥': { text: "Fast like lightning! DHL Express worldwide! ⚡", pose: 'waving' },
        '🚀': { text: "Blasting off! Sub-second answers to your queries! 🛸", pose: 'cheer' },
        '😎': { text: "Chill out! All orders over $50 get free shipping! 🧊", pose: 'idle' }
      };

      const res = map[emoji] || { text: "Sparky is happy to help! ✨", pose: 'talking' };
      this.setEmotion(emoji, res.text, res.pose, true);
      if (emoji === '🥳' || emoji === '💖' || emoji === '🥰') {
        this.triggerParticles();
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
        void bubble.offsetWidth;
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
        if (this.isAsleep || this.isTyping || this.isStreaming) return;
        const menu = document.getElementById('sparky-menu');
        if (menu && !menu.classList.contains('is-hidden')) return;

        this.dialogueIndex = (this.dialogueIndex + 1) % this.dialogues.length;
        this.speak(this.dialogues[this.dialogueIndex]);
      }, 22000);
    }

    doJumpAnimation() {
      const rig = document.getElementById('sparky-rig');
      if (!rig) return;
      rig.style.transform = 'translateY(-24px) scale(1.15) rotate(8deg)';
      setTimeout(() => {
        rig.style.transform = 'translateY(-6px) scale(1.05) rotate(-6deg)';
        setTimeout(() => {
          rig.style.transform = '';
        }, 220);
      }, 200);
    }

    triggerParticles() {
      const avatar = document.getElementById('sparky-avatar-btn');
      if (!avatar) return;
      const rect = avatar.getBoundingClientRect();
      const symbols = ['💖', '⭐', '🎈', '✨', '🎉', '🌟', '🧁', '💡'];
      for (let i = 0; i < 16; i++) {
        const p = document.createElement('div');
        p.className = 'sparky-particle';
        p.textContent = symbols[Math.floor(Math.random() * symbols.length)];
        p.style.left = (rect.left + rect.width / 2) + 'px';
        p.style.top = (rect.top + rect.height / 2) + 'px';
        const dx = (Math.random() - 0.5) * 240 + 'px';
        const dy = (-60 - Math.random() * 180) + 'px';
        p.style.setProperty('--dx', dx);
        p.style.setProperty('--dy', dy);
        document.body.appendChild(p);
        setTimeout(() => p.remove(), 1200);
      }
    }

    giveHighFive() {
      this.playCelebrationFanfare();
      this.doJumpAnimation();
      this.setPose('cheer', 3000);
      this.setEmotion('🥳', "YAAAY! HIGH FIVE! Best friends forever! 💖✨", null, false);
      this.triggerParticles();

      const menu = document.getElementById('sparky-menu');
      if (menu) menu.classList.add('is-hidden');
    }

    tellSecret() {
      this.playChimeSound();
      this.setPose('talking', 4000);
      this.setEmotion('💡', null, null, false);
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
      this.setPose('cheer', 2000);
      this.setEmotion('🚀', "Asking our verified AI right now! Vroom! 🚀", null, false);
      const menu = document.getElementById('sparky-menu');
      if (menu) menu.classList.add('is-hidden');

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
      } else {
        window.location.href = `app.html?prompt=${encodeURIComponent(query)}`;
      }
    }

    goToSleep() {
      this.isAsleep = true;
      localStorage.setItem('sparky_asleep', 'true');
      const bubble = document.getElementById('sparky-bubble');
      const menu = document.getElementById('sparky-menu');
      const halo = document.getElementById('sparky-mood-halo');
      const rig = document.getElementById('sparky-rig');
      if (bubble) bubble.style.display = 'none';
      if (menu) menu.classList.add('is-hidden');
      if (halo) halo.style.display = 'none';
      if (rig) {
        rig.innerHTML = `<span style="font-size: 1.8rem; animation: sparkyMoodPop 0.3s;">💤</span>`;
        rig.title = "Sparky is taking a nap. Click to wake up!";
      }
    }

    wakeUp() {
      this.isAsleep = false;
      localStorage.setItem('sparky_asleep', 'false');
      const root = document.getElementById('sparky-mascot-root');
      if (root) root.remove();
      this.injectDOM();
      this.playCelebrationFanfare();
      this.doJumpAnimation();
      this.setPose('cheer', 3000);
      this.setEmotion('🌟', "Yawn! Sparky is awake and ready to help! 🎈🚀", null, false);
    }
  }

  // Expose global instance
  window.Sparky = new SparkyKidMascot();
})();
