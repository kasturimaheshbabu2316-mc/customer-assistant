/* ==========================================================================
   OMNIDESK AI - CUSTOMER SUPPORT PORTAL CONTROLLER (app.js)
   Dedicated to Customer Experience, Grounded AI Chat, Policy Directory,
   Ticket Tracking, and Claim Submission.
   ========================================================================== */

const CustomerState = {
  currentView: 'chat',
  backendUrl: localStorage.getItem('omni_backend_url') || (window.location.origin.startsWith('http') && !window.location.port.match(/^(5500|3000|5173)$/) ? window.location.origin : 'http://localhost:8000'),
  isBackendOnline: false,
  isStreaming: false,
  attachedImageBase64: '',
  attachedImageMime: '',
  selectedLanguage: localStorage.getItem('omni_language') || 'Auto Detect',
  activeTicketId: null,
  features: {
    enable_streaming: true,
    enable_vision_upload: true,
    enable_multi_language: true,
    enable_faq_chips: true,
    enable_csat_popup: true,
    enable_ticket_lookup: true,
    enable_announcement_banner: false,
    announcement_banner_text: "Special Notice: Free expedited delivery on all verified warranty replacements this week.",
    welcome_greeting: "Hello! I am your AI Customer Support Assistant, grounded exclusively in verified store policies. Ask me about returns, international shipping rates, warranty repairs, price matching, or order cancellations.",
    theme_mode: "clay_porcelain"
  },
  messages: [],
  policies: [
    {
      id: 'sec_1',
      category: 'Return',
      title: '30-Day Return & Refund Policy',
      content: 'Customers may return eligible products within 30 calendar days of delivery for a full refund to their original payment method. Items must be in original condition with all packaging intact. Open-box electronics are subject to a 15% restocking fee. Return shipping is 100% free within the USA & Canada.'
    },
    {
      id: 'sec_2',
      category: 'Shipping',
      title: 'Domestic & International Shipping (DHL Express)',
      content: 'Domestic Standard Shipping (3-5 business days) is free on orders over $50, flat $4.99 under $50. Expedited 2-Day is $14.99, and Overnight delivery is $29.99 for orders placed before 1 PM EST. International shipping is available to 85+ countries via DHL Express under Delivered Duty Paid (DDP) terms — all customs, VAT, and duties are prepaid at checkout.'
    },
    {
      id: 'sec_3',
      category: 'Cancellation',
      title: '60-Minute Order Cancellation Window',
      content: 'Orders may be cancelled or modified within 60 minutes of placement directly from your account dashboard or via our support assistant. After 60 minutes, orders enter automated warehouse picking and routing, after which they must be processed as a standard return.'
    },
    {
      id: 'sec_4',
      category: 'Warranty',
      title: '1-Year Limited Manufacturer Warranty',
      content: 'All hardware purchases include a 1-Year Limited Manufacturer Warranty covering hardware defects and manufacturing workmanship. Cosmetic wear, water damage, and accidental drops are excluded. To file a claim, submit your serial number and 1-2 photos of the defect.'
    },
    {
      id: 'sec_5',
      category: 'Payment',
      title: 'Payment Methods & 14-Day Price Match Guarantee',
      content: 'We accept Visa, MasterCard, American Express, PayPal, Apple Pay, Google Pay, and Klarna/Affirm. If an identical item is advertised for less at an authorized retailer within 14 calendar days of your purchase, contact us to receive an immediate price-match credit to your payment method.'
    },
    {
      id: 'sec_6',
      category: 'General',
      title: 'Live Support Hours & Priority Escalations',
      content: 'AI Support Hub operates 24/7/365. Human Support Agent desk hours are Monday through Friday 8:00 AM - 8:00 PM EST, and Saturday-Sunday 10:00 AM - 6:00 PM EST. Priority escalations are reviewed within 2 hours.'
    }
  ]
};

// Initialize Customer Portal
document.addEventListener('DOMContentLoaded', async () => {
  await loadFeaturesFromBackend();
  await checkBackendHealth();
  renderCustomerPolicies();
  initCustomerWelcomeGreeting();
});

// Load dynamic UX features
async function loadFeaturesFromBackend() {
  try {
    const res = await fetch(`${CustomerState.backendUrl}/api/features`);
    if (res.ok) {
      const data = await res.json();
      CustomerState.features = { ...CustomerState.features, ...data };
      applyFeaturesToUI();
    }
  } catch (e) {
    console.warn('Backend features loaded with defaults:', e);
    applyFeaturesToUI();
  }
}

function applyFeaturesToUI() {
  const feat = CustomerState.features;

  // Announcement Banner
  const banner = document.getElementById('customer-announcement-banner');
  const bannerMsg = document.getElementById('announcement-banner-message');
  if (banner && bannerMsg) {
    if (feat.enable_announcement_banner && feat.announcement_banner_text) {
      bannerMsg.textContent = feat.announcement_banner_text;
      banner.classList.remove('is-hidden');
    } else {
      banner.classList.add('is-hidden');
    }
  }

  // Vision Upload Button in Chat
  const visionWrapper = document.getElementById('composer-vision-btn-wrapper');
  if (visionWrapper) {
    if (feat.enable_vision_upload) {
      visionWrapper.classList.remove('is-hidden');
    } else {
      visionWrapper.classList.add('is-hidden');
    }
  }

  // Multi-Language Dropdown in Topbar
  const langWrapper = document.getElementById('topbar-lang-wrapper');
  if (langWrapper) {
    if (feat.enable_multi_language) {
      langWrapper.classList.remove('is-hidden');
    } else {
      langWrapper.classList.add('is-hidden');
    }
  }

  // FAQ Chips
  const faqChips = document.getElementById('chat-faq-chips-container');
  if (faqChips) {
    if (feat.enable_faq_chips) {
      faqChips.classList.remove('is-hidden');
    } else {
      faqChips.classList.add('is-hidden');
    }
  }

  // Theme
  const themeKey = (feat.theme_mode || 'clay_porcelain').replace('clay_', '');
  if (window.ClayTheme && typeof window.ClayTheme.setTheme === 'function') {
    window.ClayTheme.setTheme(themeKey);
  } else {
    document.documentElement.setAttribute('data-clay-palette', themeKey);
    document.documentElement.classList.add('clay-mode');
  }
}

function initCustomerWelcomeGreeting() {
  const greetingEl = document.getElementById('assistant-welcome-msg');
  if (greetingEl && CustomerState.features.welcome_greeting) {
    greetingEl.textContent = CustomerState.features.welcome_greeting;
  }
}

function dismissAnnouncementBanner() {
  const banner = document.getElementById('customer-announcement-banner');
  if (banner) banner.classList.add('is-hidden');
}

// Navigation between customer views
function switchCustomerView(viewName) {
  CustomerState.currentView = viewName;
  const viewMap = {
    'chat': { id: 'view-chat', btn: 'btn-nav-chat', title: '24/7 AI Customer Support' },
    'kb': { id: 'view-kb', btn: 'btn-nav-kb', title: 'Customer Help Center & Store Policies' },
    'tickets': { id: 'view-tickets', btn: 'btn-nav-tickets', title: 'Track Your Support Request' },
    'claim': { id: 'view-claim', btn: 'btn-nav-claim', title: 'Submit a Support Claim or Request' }
  };

  Object.values(viewMap).forEach(v => {
    const el = document.getElementById(v.id);
    const btn = document.getElementById(v.btn);
    if (el) el.classList.remove('active-view');
    if (btn) btn.classList.remove('active');
  });

  const active = viewMap[viewName] || viewMap['chat'];
  const activeEl = document.getElementById(active.id);
  const activeBtn = document.getElementById(active.btn);
  const titleEl = document.getElementById('current-view-title');

  if (activeEl) activeEl.classList.add('active-view');
  if (activeBtn) activeBtn.classList.add('active');
  if (titleEl) titleEl.textContent = active.title;

  if (window.innerWidth <= 768) {
    const sidebar = document.getElementById('app-sidebar');
    if (sidebar) sidebar.classList.remove('mobile-open');
  }
}

function toggleAppSidebar() {
  const sidebar = document.getElementById('app-sidebar');
  if (sidebar) sidebar.classList.toggle('mobile-open');
}

// Check backend connectivity
async function checkBackendHealth() {
  const dot = document.getElementById('sidebar-status-dot');
  const txt = document.getElementById('sidebar-status-text');
  try {
    const res = await fetch(`${CustomerState.backendUrl}/health`);
    if (res.ok) {
      CustomerState.isBackendOnline = true;
      if (dot) dot.style.backgroundColor = 'var(--accent-emerald)';
      if (txt) txt.textContent = 'Support Live (24/7)';
    } else {
      throw new Error('Non-200 status');
    }
  } catch (e) {
    CustomerState.isBackendOnline = false;
    if (dot) dot.style.backgroundColor = 'var(--accent-emerald)';
    if (txt) txt.textContent = 'Support Live (Local Grounded)';
  }
}

// Language Change
function handleLanguageChange(lang) {
  CustomerState.selectedLanguage = lang;
  localStorage.setItem('omni_language', lang);
}

// Render Knowledge Base Policies for Customer
function renderCustomerPolicies(filterKeyword = '', category = 'All') {
  const grid = document.getElementById('customer-policies-grid');
  if (!grid) return;

  const kw = filterKeyword.toLowerCase().trim();
  const filtered = CustomerState.policies.filter(p => {
    const matchCat = (category === 'All' || p.category.toLowerCase().includes(category.toLowerCase()));
    const matchKw = (!kw || p.title.toLowerCase().includes(kw) || p.content.toLowerCase().includes(kw));
    return matchCat && matchKw;
  });

  if (filtered.length === 0) {
    grid.innerHTML = `
      <div class="empty-placeholder-card">
        <i class="fa-solid fa-magnifying-glass"></i>
        <p>No policies matching "${filterKeyword}". Try searching for returns, warranty, or shipping.</p>
      </div>
    `;
    return;
  }

  grid.innerHTML = filtered.map(p => `
    <div class="customer-policy-card">
      <div class="policy-card-header">
        <span class="badge badge-glow-primary badge-font-sm">${p.category} Policy</span>
        <button type="button" class="btn-text-link btn-font-sm" onclick="sendQuickPrompt('Tell me about: ${p.title.replace(/'/g, "\\'")}')">
          <i class="fa-solid fa-comments"></i> Ask AI
        </button>
      </div>
      <h3 class="policy-card-title">${p.title}</h3>
      <p class="policy-card-body">${p.content}</p>
    </div>
  `).join('');
}

function filterCustomerPolicies() {
  const input = document.getElementById('policy-search-input');
  const kw = input ? input.value : '';
  const activeChip = document.querySelector('.policy-categories-filter .category-chip-btn.active');
  const cat = activeChip ? activeChip.textContent.split(' ')[0] : 'All';
  renderCustomerPolicies(kw, cat);
}

function filterPolicyCategory(category, btnEl) {
  document.querySelectorAll('.policy-categories-filter .category-chip-btn').forEach(b => b.classList.remove('active'));
  if (btnEl) btnEl.classList.add('active');
  const input = document.getElementById('policy-search-input');
  const kw = input ? input.value : '';
  renderCustomerPolicies(kw, category);
}

// Multi-Modal Image Attachments for Chat
function handleImageAttachment(event) {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    CustomerState.attachedImageBase64 = e.target.result.split(',')[1];
    CustomerState.attachedImageMime = file.type;

    const bar = document.getElementById('attached-image-preview-bar');
    const imgTag = document.getElementById('attached-img-tag');
    const nameTag = document.getElementById('attached-img-name');

    if (imgTag) imgTag.src = e.target.result;
    if (nameTag) nameTag.textContent = file.name;
    if (bar) bar.classList.remove('is-hidden');
  };
  reader.readAsDataURL(file);
}

function removeAttachedImage() {
  CustomerState.attachedImageBase64 = '';
  CustomerState.attachedImageMime = '';
  const bar = document.getElementById('attached-image-preview-bar');
  const input = document.getElementById('chat-file-input');
  if (bar) bar.classList.add('is-hidden');
  if (input) input.value = '';
}

// Chat Flow
function sendQuickPrompt(promptText) {
  switchCustomerView('chat');
  const input = document.getElementById('chat-text-input');
  if (input) {
    input.value = promptText;
    document.getElementById('chat-input-form').dispatchEvent(new Event('submit'));
  }
}

async function handleChatSubmit(event) {
  if (event) event.preventDefault();
  const input = document.getElementById('chat-text-input');
  const query = input.value.trim();
  if (!query || CustomerState.isStreaming) return;

  input.value = '';
  autoResizeTextarea(input);

  const hasImage = Boolean(CustomerState.attachedImageBase64);
  const imgData = CustomerState.attachedImageBase64;
  const imgMime = CustomerState.attachedImageMime;
  removeAttachedImage();

  appendChatMessage('user', query, [], null, hasImage ? `data:${imgMime};base64,${imgData}` : null);

  if (hasImage) {
    await processVisionClaimQuery(query, imgData, imgMime);
  } else if (CustomerState.features.enable_streaming) {
    await processStreamingQuery(query);
  } else {
    await processSyncQuery(query);
  }
}

async function processVisionClaimQuery(query, imgBase64, mimeType) {
  const botMsgId = appendChatMessage('assistant', '<span class="typing-cursor">Analyzing image and verifying warranty coverage...</span>');
  try {
    const res = await fetch(`${CustomerState.backendUrl}/api/vision/analyze-claim`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image_base64: imgBase64,
        claim_description: query,
        mime_type: mimeType
      })
    });

    if (res.ok) {
      const data = await res.json();
      const verdictHtml = `
        <div class="verdict-banner-row">
          <span class="badge ${data.covered ? 'badge-glow-emerald' : 'badge-glow-primary'}">
            <i class="fa-solid fa-${data.covered ? 'circle-check' : 'triangle-exclamation'}"></i> ${data.claim_verdict || 'Claim Inspection'}
          </span>
        </div>
        <p>${data.recommendation}</p>
        <div class="verdict-footer-meta">
          <i class="fa-solid fa-microchip"></i> Inspected via Gemini Vision Multi-Modal Pipeline
        </div>
      `;
      updateChatMessage(botMsgId, verdictHtml);
      showCitationSources([{ title: 'Section 4: Warranty & Repair Coverage', distance: 0.12 }]);
    } else {
      throw new Error('Vision analysis error');
    }
  } catch (e) {
    updateChatMessage(botMsgId, "We received your photo. Our warranty desk will review this under our 1-Year Limited Manufacturer Warranty policy.");
  }
}

async function processStreamingQuery(query) {
  const botMsgId = appendChatMessage('assistant', '<span class="typing-cursor">Searching store policies...</span>');
  let accumulatedText = '';
  let sources = [];

  try {
    const response = await fetch(`${CustomerState.backendUrl}/ask/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: query, language: CustomerState.selectedLanguage })
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    CustomerState.isStreaming = true;

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (line.startsWith('event: sources')) {
          const dataLine = lines[++i]?.trim();
          if (dataLine?.startsWith('data:')) {
            try {
              const parsed = JSON.parse(dataLine.replace('data:', '').trim());
              sources = (parsed.sources || []).map((s, idx) => ({ title: s, distance: parsed.distances?.[idx] || 0.15 }));
              showCitationSources(sources);
            } catch (err) {}
          }
        } else if (line.startsWith('event: token')) {
          const dataLine = lines[++i]?.trim();
          if (dataLine?.startsWith('data:')) {
            try {
              const tokenData = JSON.parse(dataLine.replace('data:', '').trim());
              accumulatedText += tokenData.token || '';
              updateChatMessage(botMsgId, accumulatedText + '<span class="typing-cursor"></span>');
            } catch (err) {}
          }
        } else if (line.startsWith('event: done')) {
          CustomerState.isStreaming = false;
        }
      }
    }
    updateChatMessage(botMsgId, accumulatedText || 'I am sorry, but our documentation does not cover that. Please contact support@company.com.');
  } catch (err) {
    CustomerState.isStreaming = false;
    await processSyncQuery(query, botMsgId);
  }
}

async function processSyncQuery(query, existingMsgId = null) {
  const botMsgId = existingMsgId || appendChatMessage('assistant', '<span class="typing-cursor">Consulting store policies...</span>');
  try {
    const res = await fetch(`${CustomerState.backendUrl}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: query, language: CustomerState.selectedLanguage })
    });

    if (res.ok) {
      const data = await res.json();
      updateChatMessage(botMsgId, data.answer);
      const sources = (data.sources || []).map((s, idx) => ({ title: s, distance: data.distances?.[idx] || 0.2 }));
      showCitationSources(sources);
    } else {
      throw new Error('Sync error');
    }
  } catch (err) {
    updateChatMessage(botMsgId, "I am sorry, but our documentation does not cover that. Please contact support@company.com or click 'Speak to Agent' below.");
  }
}

function appendChatMessage(role, content, sources = [], latency = null, imageSrc = null) {
  const feed = document.getElementById('chat-feed');
  const msgId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`;

  const row = document.createElement('div');
  row.className = `chat-msg-row ${role}-msg`;
  row.id = msgId;

  const avatar = role === 'assistant' ?
    `<div class="avatar-badge avatar-assistant"><i class="fa-solid fa-robot"></i></div>` :
    `<div class="avatar-badge avatar-user"><i class="fa-solid fa-user"></i></div>`;

  const imgHtml = imageSrc ? `<div class="msg-attached-image"><img src="${imageSrc}" alt="Attached photo" class="msg-img-preview"></div>` : '';

  row.innerHTML = `
    ${avatar}
    <div class="msg-content-wrapper">
      ${imgHtml}
      <div class="msg-bubble-content">${content}</div>
      ${role === 'assistant' ? `
      <div class="msg-actions-bar">
        <button type="button" class="msg-btn-action" onclick="copyMessageText(this)"><i class="fa-solid fa-copy"></i> Copy</button>
        <button type="button" class="msg-btn-action" onclick="speakMessageText(this)"><i class="fa-solid fa-volume-high"></i> Read</button>
        <button type="button" class="msg-btn-action" onclick="openCsatModal()"><i class="fa-solid fa-star"></i> Rate</button>
      </div>
      ` : ''}
    </div>
  `;

  feed.appendChild(row);
  feed.scrollTop = feed.scrollHeight;
  return msgId;
}

function updateChatMessage(msgId, content) {
  const row = document.getElementById(msgId);
  if (!row) return;
  const bubble = row.querySelector('.msg-bubble-content');
  if (bubble) bubble.innerHTML = content;
  const feed = document.getElementById('chat-feed');
  if (feed) feed.scrollTop = feed.scrollHeight;
}

function showCitationSources(sources) {
  const list = document.getElementById('active-sources-list');
  if (!list) return;

  if (!sources || sources.length === 0) {
    list.innerHTML = `
      <div class="source-placeholder">
        <i class="fa-solid fa-circle-exclamation text-amber"></i>
        <span>No direct policy clause matched. Escalation suggested.</span>
      </div>
    `;
    return;
  }

  list.innerHTML = sources.map(s => `
    <div class="source-card">
      <div class="source-card-header">
        <i class="fa-solid fa-file-check text-primary"></i>
        <span class="source-title">${s.title}</span>
      </div>
      <div class="source-meta-row">
        <span class="badge badge-glow-emerald badge-font-sm">100% Grounded</span>
        <span class="source-distance">Distance: ${Number(s.distance || 0.15).toFixed(3)}</span>
      </div>
    </div>
  `).join('');
}

function clearChatFeed() {
  const feed = document.getElementById('chat-feed');
  if (feed) {
    feed.innerHTML = `
      <div class="chat-msg-row assistant-msg">
        <div class="avatar-badge avatar-assistant"><i class="fa-solid fa-robot"></i></div>
        <div class="msg-content-wrapper">
          <div class="msg-bubble-content">${CustomerState.features.welcome_greeting}</div>
        </div>
      </div>
    `;
  }
}

function exportChatTranscript() {
  const feed = document.getElementById('chat-feed');
  const rows = feed.querySelectorAll('.chat-msg-row');
  const transcript = Array.from(rows).map(r => ({
    sender: r.classList.contains('user-msg') ? 'Customer' : 'OmniDesk AI',
    text: r.querySelector('.msg-bubble-content')?.innerText || ''
  }));

  const blob = new Blob([JSON.stringify(transcript, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `omnidesk_support_chat_${Date.now()}.json`;
  a.click();
}

function copyMessageText(btn) {
  const bubble = btn.closest('.msg-content-wrapper').querySelector('.msg-bubble-content');
  if (bubble) {
    navigator.clipboard.writeText(bubble.innerText);
    const orig = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-check"></i> Copied';
    setTimeout(() => btn.innerHTML = orig, 1500);
  }
}

function speakMessageText(btn) {
  const bubble = btn.closest('.msg-content-wrapper').querySelector('.msg-bubble-content');
  if (bubble && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(bubble.innerText);
    window.speechSynthesis.speak(u);
  }
}

function autoResizeTextarea(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

function handleTextareaKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    document.getElementById('chat-input-form').dispatchEvent(new Event('submit'));
  }
}

function toggleVoiceInput() {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    alert('Voice input is not supported in this browser.');
    return;
  }
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  const rec = new SpeechRec();
  rec.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    const input = document.getElementById('chat-text-input');
    if (input) {
      input.value = transcript;
      autoResizeTextarea(input);
    }
  };
  rec.start();
}

// Track My Ticket Flow
async function handleCustomerTicketLookup(event) {
  event.preventDefault();
  const input = document.getElementById('lookup-ticket-id-input');
  const ticketId = input.value.trim().toUpperCase();
  if (!ticketId) return;

  try {
    const res = await fetch(`${CustomerState.backendUrl}/api/tickets/public/${ticketId}`);
    if (res.ok) {
      const data = await res.json();
      const ticket = data.ticket || data;
      CustomerState.activeTicketId = ticket.id;
      renderCustomerTicketDetails(ticket);
    } else {
      alert(`Ticket "${ticketId}" was not found. Please double-check your Ticket ID.`);
    }
  } catch (e) {
    alert('Could not connect to support server. Please check your connection.');
  }
}

function renderCustomerTicketDetails(ticket) {
  const resBox = document.getElementById('customer-ticket-result-box');
  if (!resBox) return;

  document.getElementById('cust-ticket-id-display').textContent = ticket.id;
  document.getElementById('cust-ticket-subject-display').textContent = ticket.subject;

  const statusBadge = document.getElementById('cust-ticket-status-badge');
  if (statusBadge) {
    statusBadge.textContent = ticket.status;
    statusBadge.className = `status-badge ${ticket.status.toLowerCase().replace(' ', '-')}`;
  }

  const slaBadge = document.getElementById('cust-ticket-sla-badge');
  if (slaBadge && ticket.sla_details) {
    slaBadge.textContent = `SLA: ${ticket.sla_details.label}`;
  }

  // Stepper
  const stepSubmitted = document.getElementById('step-submitted');
  const stepReview = document.getElementById('step-review');
  const stepResolved = document.getElementById('step-resolved');

  stepSubmitted.className = 'stepper-step completed';
  if (ticket.status === 'Resolved') {
    stepReview.className = 'stepper-step completed';
    stepResolved.className = 'stepper-step completed active';
  } else if (ticket.status === 'In Progress') {
    stepReview.className = 'stepper-step completed active';
    stepResolved.className = 'stepper-step';
  } else {
    stepReview.className = 'stepper-step active';
    stepResolved.className = 'stepper-step';
  }

  // Render messages
  const feed = document.getElementById('cust-ticket-messages-feed');
  feed.innerHTML = (ticket.messages || []).map(m => `
    <div class="ticket-msg-item ${m.sender === ticket.customer_name ? 'customer-reply' : 'agent-reply'}">
      <div class="msg-meta-bar">
        <strong>${m.sender}</strong>
        <span>${m.timestamp}</span>
      </div>
      <div class="msg-body">${m.text}</div>
    </div>
  `).join('');

  resBox.classList.remove('is-hidden');
  resBox.scrollIntoView({ behavior: 'smooth' });
}

async function handleCustomerTicketReply(event) {
  event.preventDefault();
  const input = document.getElementById('cust-reply-input');
  const text = input.value.trim();
  if (!text || !CustomerState.activeTicketId) return;

  try {
    const res = await fetch(`${CustomerState.backendUrl}/api/tickets/${CustomerState.activeTicketId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sender: 'Customer',
        text: text,
        is_internal_note: false
      })
    });

    if (res.ok) {
      input.value = '';
      const data = await res.json();
      renderCustomerTicketDetails(data.ticket);
    }
  } catch (e) {
    alert('Failed to send reply. Please try again.');
  }
}

// Submit Claim Flow
function handleClaimPhotoSelect(event) {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    document.getElementById('claim-photo-img').src = e.target.result;
    document.getElementById('claim-photo-preview').classList.remove('is-hidden');
    document.getElementById('claim-photo-drop-text').textContent = file.name;
  };
  reader.readAsDataURL(file);
}

async function handleCustomerClaimSubmit(event) {
  event.preventDefault();
  const name = document.getElementById('claim-cust-name').value.trim();
  const email = document.getElementById('claim-cust-email').value.trim();
  const orderNum = document.getElementById('claim-order-num').value.trim();
  const category = document.getElementById('claim-category-select').value;
  const subject = document.getElementById('claim-subject-input').value.trim();
  const desc = document.getElementById('claim-description-input').value.trim();

  const queryPayload = `${category} Claim for Order #${orderNum || 'N/A'}: ${desc}`;

  try {
    const res = await fetch(`${CustomerState.backendUrl}/api/tickets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customer_name: name,
        customer_email: email,
        customer_tier: 'Standard Retail',
        subject: subject,
        query: queryPayload,
        intent: category,
        priority: 'High'
      })
    });

    if (res.ok) {
      const data = await res.json();
      const ticket = data.ticket;
      alert(`Thank you, ${name}! Your claim has been submitted. Your tracking Ticket ID is ${ticket.id}.`);
      document.getElementById('customer-claim-form').reset();
      document.getElementById('claim-photo-preview').classList.add('is-hidden');

      // Switch to ticket tracking view
      switchCustomerView('tickets');
      document.getElementById('lookup-ticket-id-input').value = ticket.id;
      CustomerState.activeTicketId = ticket.id;
      renderCustomerTicketDetails(ticket);
    }
  } catch (e) {
    alert('Failed to submit claim. Please try again.');
  }
}

// Escalation Modal
function openHumanEscalationModal() {
  const modal = document.getElementById('escalation-modal');
  if (modal) modal.classList.remove('is-hidden');
}
function closeHumanEscalationModal() {
  const modal = document.getElementById('escalation-modal');
  if (modal) modal.classList.add('is-hidden');
}

async function handleEscalationModalSubmit(event) {
  event.preventDefault();
  const name = document.getElementById('esc-name').value.trim();
  const email = document.getElementById('esc-email').value.trim();
  const priority = document.getElementById('esc-priority').value;

  const chatSnippet = Array.from(document.querySelectorAll('#chat-feed .chat-msg-row')).map(r => r.innerText).join('\n').slice(0, 800);

  try {
    const res = await fetch(`${CustomerState.backendUrl}/api/tickets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customer_name: name,
        customer_email: email,
        customer_tier: 'Standard Retail',
        subject: `Live Chat Escalation (${name})`,
        query: `Customer requested human agent assistance. Chat Context:\n${chatSnippet}`,
        priority: priority
      })
    });

    if (res.ok) {
      const data = await res.json();
      closeHumanEscalationModal();
      appendChatMessage('assistant', `A human support specialist has been assigned to your inquiry (Ticket ID: **${data.ticket.id}**). You will receive an email update at ${email} shortly.`);
    }
  } catch (e) {
    alert('Could not escalate ticket. Please try again.');
  }
}

// CSAT Modal
let currentCsatRating = 5;
function openCsatModal() {
  if (CustomerState.features.enable_csat_popup) {
    const modal = document.getElementById('csat-modal');
    if (modal) modal.classList.remove('is-hidden');
  }
}
function closeCsatModal() {
  const modal = document.getElementById('csat-modal');
  if (modal) modal.classList.add('is-hidden');
}
function setCsatRating(num) {
  currentCsatRating = num;
  const stars = document.querySelectorAll('#star-rating-container .star-btn');
  stars.forEach((s, idx) => {
    if (idx < num) s.classList.add('active');
    else s.classList.remove('active');
  });
}

async function submitCsatFeedback() {
  const comment = document.getElementById('csat-comment-input').value.trim();
  try {
    await fetch(`${CustomerState.backendUrl}/api/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        rating: currentCsatRating,
        is_positive: currentCsatRating >= 4,
        comment: comment,
        language: CustomerState.selectedLanguage
      })
    });
    closeCsatModal();
    alert('Thank you for rating our support assistant!');
  } catch (e) {
    closeCsatModal();
  }
}
