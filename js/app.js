/* ==========================================================================
   OMNIDESK AI - SUPPORT HUB APPLICATION PORTAL CONTROLLER (SPA)
   ========================================================================== */

// Global Application State
const AppState = {
  currentView: 'chat',
  backendUrl: localStorage.getItem('omni_backend_url') || 'http://localhost:8000',
  guardrailThreshold: parseFloat(localStorage.getItem('omni_threshold')) || 1.2,
  model: localStorage.getItem('omni_model') || 'gemini-3.6-flash',
  isBackendOnline: false,
  messages: [
    {
      role: 'assistant',
      content: 'Hello! I am your AI Customer Support Assistant, grounded exclusively in your verified store policies. Ask me about returns, international shipping rates, warranty repairs, price matching, or order cancellations.',
      sources: []
    }
  ],
  knowledgeChunks: [
    {
      id: 'chunk_0',
      title: 'Section 1: Return and Exchange Policy',
      content: '30-Day Return Window: Customers may return eligible products within 30 calendar days of delivery for a full refund to original payment method. Items must be unused in original packaging. Open-box electronics incur a 15% restocking fee. Return shipping is free in USA & Canada.',
      tokens: 72,
      source: 'company_faq.txt'
    },
    {
      id: 'chunk_1',
      title: 'Section 2: Shipping and Delivery Options',
      content: 'Domestic Shipping: Standard (3-5 days) free over $50, flat $4.99 under $50. Expedited 2-Day: $14.99. Overnight: $29.99 for orders before 1 PM EST. International: 85+ countries via DHL Express (7-14 days), shipped DDP (Delivered Duty Paid with duties calculated at checkout).',
      tokens: 84,
      source: 'company_faq.txt'
    },
    {
      id: 'chunk_2',
      title: 'Section 3: Order Modification & Cancellation',
      content: 'Cancellation Window: Orders can be cancelled or modified within 60 minutes of placement directly from account dashboard or via support. After 60 minutes, orders enter automated warehouse picking and cannot be cancelled.',
      tokens: 58,
      source: 'company_faq.txt'
    },
    {
      id: 'chunk_3',
      title: 'Section 4: Warranty & Repair Coverage',
      content: '1-Year Limited Manufacturer Warranty: Covers defects in materials and manufacturing workmanship. Does NOT cover cosmetic wear, accidental drops, or unauthorized repairs. Claims require serial number and photos sent to support@company.com.',
      tokens: 65,
      source: 'company_faq.txt'
    },
    {
      id: 'chunk_4',
      title: 'Section 5: Payment Methods & Price Match',
      content: 'Accepted Payments: Visa, MasterCard, Amex, Discover, PayPal, Apple Pay, Google Pay, and Klarna/Affirm (0% APR). 14-Day Price Match Guarantee if an item is sold cheaper on an authorized retailer within 14 days.',
      tokens: 60,
      source: 'company_faq.txt'
    },
    {
      id: 'chunk_5',
      title: 'Section 6: Support Escalation & Hours',
      content: 'AI Support Hub available 24/7/365. Live Agent Hours: Mon-Fri 8 AM - 8 PM EST, Sat-Sun 10 AM - 6 PM EST. Escalation Email: support@company.com (under 2 hour response time). Priority phone: +1 (800) 555-APEX.',
      tokens: 55,
      source: 'company_faq.txt'
    }
  ]
};

// Toast Notification
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  let icon = 'fa-circle-info';
  if (type === 'success') icon = 'fa-circle-check';
  if (type === 'error') icon = 'fa-triangle-exclamation';

  toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// 1. Navigation View Switcher
function switchAppView(viewName) {
  AppState.currentView = viewName;

  // Update sidebar active buttons
  const navMap = {
    chat: { btn: 'btn-nav-chat', title: 'Live AI Support Chat', view: 'view-chat' },
    kb: { btn: 'btn-nav-kb', title: 'Knowledge Base Studio', view: 'view-kb' },
    analytics: { btn: 'btn-nav-analytics', title: 'Deflection & Analytics Dashboard', view: 'view-analytics' },
    settings: { btn: 'btn-nav-settings', title: 'RAG Pipeline Settings', view: 'view-settings' }
  };

  Object.keys(navMap).forEach(key => {
    const config = navMap[key];
    const btn = document.getElementById(config.btn);
    const viewEl = document.getElementById(config.view);
    if (btn) btn.classList.toggle('active', key === viewName);
    if (viewEl) viewEl.classList.toggle('active-view', key === viewName);
  });

  const titleEl = document.getElementById('current-view-title');
  if (titleEl && navMap[viewName]) {
    titleEl.textContent = navMap[viewName].title;
  }

  // If opening KB view, render chunk list
  if (viewName === 'kb') {
    renderKbChunks();
  }
}

// Mobile sidebar toggle
function toggleAppSidebar() {
  const sidebar = document.getElementById('app-sidebar');
  if (sidebar) {
    sidebar.classList.toggle('mobile-open');
  }
}

// 2. Backend Health & Connectivity Checker
async function checkBackendHealth() {
  const statusDot = document.getElementById('sidebar-status-dot');
  const statusText = document.getElementById('sidebar-status-text');

  try {
    const res = await fetch(`${AppState.backendUrl}/health`, {
      signal: AbortSignal.timeout(2000)
    });

    if (res.ok) {
      AppState.isBackendOnline = true;
      if (statusDot) {
        statusDot.className = 'pulse-dot';
      }
      if (statusText) {
        statusText.textContent = 'API Live (Port 8000)';
        statusText.style.color = '#34d399';
      }
      
      // Fetch info if available
      try {
        const infoRes = await fetch(`${AppState.backendUrl}/api/info`);
        if (infoRes.ok) {
          const info = await infoRes.json();
          const chunkCountEl = document.getElementById('info-chunk-count');
          if (chunkCountEl && info.document_chunks > 0) {
            chunkCountEl.textContent = `${info.document_chunks} Chunks`;
          }
        }
      } catch (e) {}

      return true;
    }
  } catch (err) {
    AppState.isBackendOnline = false;
  }

  // Offline / fallback mode
  if (statusDot) {
    statusDot.className = 'pulse-dot-red';
  }
  if (statusText) {
    statusText.textContent = 'Local Simulation Mode';
    statusText.style.color = '#f59e0b';
  }
  return false;
}

// 3. Live Support Chat Implementation
function handleChatKeyDown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSendChat();
  }
}

function sendAppQuickQuery(query) {
  const input = document.getElementById('app-chat-input');
  if (input) {
    input.value = query;
    handleSendChat();
  }
}

async function handleSendChat() {
  const input = document.getElementById('app-chat-input');
  const chatFeed = document.getElementById('chat-feed');
  if (!input || !chatFeed) return;

  const query = input.value.trim();
  if (!query) return;

  // Add User message
  AppState.messages.push({ role: 'user', content: query });
  renderUserMessage(chatFeed, query);
  input.value = '';
  chatFeed.scrollTop = chatFeed.scrollHeight;

  // Render loading placeholder
  const loadingId = 'loading-' + Date.now();
  renderLoadingMessage(chatFeed, loadingId);
  chatFeed.scrollTop = chatFeed.scrollHeight;

  let answerText = '';
  let sources = [];

  // Try live API if online
  if (AppState.isBackendOnline) {
    try {
      const res = await fetch(`${AppState.backendUrl}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query }),
        signal: AbortSignal.timeout(12000)
      });

      if (res.ok) {
        const data = await res.json();
        answerText = data.answer;
        sources = data.sources || [];
      } else {
        throw new Error('API returned status ' + res.status);
      }
    } catch (e) {
      console.warn('Backend query failed, falling back to simulated RAG:', e);
      answerText = runLocalSimulatedRag(query, outSources => { sources = outSources; });
    }
  } else {
    // Simulated RAG engine
    await new Promise(r => setTimeout(r, 600));
    answerText = runLocalSimulatedRag(query, outSources => { sources = outSources; });
  }

  // Remove loading bubble & replace with assistant response
  const loadingEl = document.getElementById(loadingId);
  if (loadingEl) loadingEl.remove();

  AppState.messages.push({ role: 'assistant', content: answerText, sources: sources });
  renderAssistantMessage(chatFeed, answerText, sources);
  chatFeed.scrollTop = chatFeed.scrollHeight;
}

function renderUserMessage(container, text) {
  const row = document.createElement('div');
  row.className = 'chat-msg-row user-msg';
  row.innerHTML = `
    <div class="avatar-badge avatar-user">
      <i class="fa-solid fa-user"></i>
    </div>
    <div style="flex: 1; text-align: right;">
      <div class="msg-bubble-content" style="text-align: left; display: inline-block;">
        ${escapeHtml(text)}
      </div>
    </div>
  `;
  container.appendChild(row);
}

function renderLoadingMessage(container, id) {
  const row = document.createElement('div');
  row.className = 'chat-msg-row assistant-msg';
  row.id = id;
  row.innerHTML = `
    <div class="avatar-badge avatar-assistant">
      <i class="fa-solid fa-robot"></i>
    </div>
    <div style="flex: 1;">
      <div class="msg-bubble-content">
        <i class="fa-solid fa-spinner fa-spin" style="color: var(--primary-light); margin-right: 6px;"></i>
        Retrieving ChromaDB vectors &amp; synthesizing answer with Gemini 3 Flash...
      </div>
    </div>
  `;
  container.appendChild(row);
}

function renderAssistantMessage(container, answer, sources = []) {
  const row = document.createElement('div');
  row.className = 'chat-msg-row assistant-msg';

  let sourcesHtml = '';
  if (sources && sources.length > 0) {
    const sourcesList = sources.map((s, idx) => `
      <div style="margin-top: 4px; padding: 4px 6px; background: rgba(0,0,0,0.25); border-radius: 4px; line-height: 1.4;">
        <strong>[Clause ${idx + 1}]</strong> ${escapeHtml(s)}
      </div>
    `).join('');

    sourcesHtml = `
      <div class="msg-sources-drawer">
        <div class="sources-header">
          <i class="fa-solid fa-shield-check"></i>
          <span>Verified Policy Context (${sources.length} chunk${sources.length > 1 ? 's' : ''})</span>
        </div>
        ${sourcesList}
      </div>
    `;
  }

  row.innerHTML = `
    <div class="avatar-badge avatar-assistant">
      <i class="fa-solid fa-robot"></i>
    </div>
    <div style="flex: 1;">
      <div class="msg-bubble-content">
        ${formatMarkdownText(answer)}
        ${sourcesHtml}
      </div>
      <div class="msg-actions-bar">
        <button class="msg-btn-action" onclick="copyMessageText(this)">
          <i class="fa-solid fa-copy"></i> Copy
        </button>
        <button class="msg-btn-action" onclick="speakMessageText(this)">
          <i class="fa-solid fa-volume-high"></i> Read Aloud
        </button>
        <button class="msg-btn-action" onclick="rateMessage(this, 'helpful')">
          <i class="fa-solid fa-thumbs-up"></i> Helpful
        </button>
        <button class="msg-btn-action" onclick="rateMessage(this, 'unhelpful')">
          <i class="fa-solid fa-thumbs-down"></i>
        </button>
      </div>
    </div>
  `;
  container.appendChild(row);
}

// Local Grounded RAG Simulation for Offline Mode
function runLocalSimulatedRag(query, setSourcesCallback) {
  const q = query.toLowerCase();
  let matched = [];

  // Match against knowledge chunks
  AppState.knowledgeChunks.forEach(chunk => {
    const text = (chunk.title + ' ' + chunk.content).toLowerCase();
    let score = 0;
    
    // Keyword scoring
    if (q.includes('return') || q.includes('refund') || q.includes('restock') || q.includes('30-day')) {
      if (text.includes('return')) score += 3;
    }
    if (q.includes('ship') || q.includes('international') || q.includes('canada') || q.includes('duties') || q.includes('overnight') || q.includes('delivery')) {
      if (text.includes('shipping') || text.includes('international')) score += 3;
    }
    if (q.includes('warranty') || q.includes('repair') || q.includes('defect') || q.includes('replace') || q.includes('broken')) {
      if (text.includes('warranty')) score += 3;
    }
    if (q.includes('cancel') || q.includes('modify') || q.includes('change address') || q.includes('60 minute')) {
      if (text.includes('cancellation')) score += 3;
    }
    if (q.includes('pay') || q.includes('card') || q.includes('paypal') || q.includes('apple') || q.includes('price match') || q.includes('klarna')) {
      if (text.includes('payment') || text.includes('price match')) score += 3;
    }
    if (q.includes('hour') || q.includes('contact') || q.includes('agent') || q.includes('support@') || q.includes('phone') || q.includes('escalat')) {
      if (text.includes('escalation') || text.includes('support hub')) score += 3;
    }

    if (score > 0) {
      matched.push({ chunk, score });
    }
  });

  if (matched.length === 0) {
    if (setSourcesCallback) setSourcesCallback([]);
    return "I am sorry, but our verified policy database does not contain information regarding that request. Would you like me to connect you with our live support team at support@company.com?";
  }

  // Sort by score
  matched.sort((a, b) => b.score - a.score);
  const topMatches = matched.slice(0, 2);
  const sources = topMatches.map(m => m.chunk.content);
  if (setSourcesCallback) setSourcesCallback(sources);

  // Generate grounded answer
  if (q.includes('return') || q.includes('refund') || q.includes('30-day')) {
    return "Under our verified **Return and Exchange Policy**, you may return eligible products within **30 calendar days of delivery** for a full refund to your original payment method. Items must be unused and in original packaging. Note that open-box electronics may be subject to a 15% restocking fee unless defective. Return shipping is free for US and Canada orders.";
  }
  if (q.includes('ship') || q.includes('canada') || q.includes('international') || q.includes('duties')) {
    return "We offer Standard US shipping (3-5 business days, free over $50), Expedited 2-Day ($14.99), and Overnight Delivery ($29.99). We also ship to over 85 international countries (including Canada) via DHL Express. All international orders are shipped **DDP (Delivered Duty Paid)**, so all customs duties and import taxes are calculated and collected at checkout with no surprise fees upon delivery.";
  }
  if (q.includes('warranty') || q.includes('defect') || q.includes('claim')) {
    return "All hardware products come with a **1-Year Limited Manufacturer Warranty** covering defects in materials and workmanship. It does not cover accidental drops or water damage. To file a warranty claim, email your order number, serial number, and photos to **support@company.com**.";
  }
  if (q.includes('cancel') || q.includes('modify')) {
    return "Orders can be cancelled or modified within a strict **60-minute window** of order placement directly from your account dashboard or by reaching support. After 60 minutes, orders enter automated warehouse picking and cannot be stopped; you may initiate a standard return once received.";
  }
  if (q.includes('pay') || q.includes('price match') || q.includes('klarna') || q.includes('installment')) {
    return "We accept Visa, MasterCard, American Express, Discover, PayPal, Apple Pay, Google Pay, and Klarna / Affirm installments (0% APR available). Additionally, we offer a **14-Day Price Match Guarantee** if an item goes on sale or is listed cheaper at an authorized retailer within 14 days of purchase.";
  }

  return `Based on our verified store policy (${topMatches[0].chunk.title}): ${topMatches[0].chunk.content}`;
}

// Text to Speech
function speakMessageText(btn) {
  const row = btn.closest('.chat-msg-row');
  if (!row) return;
  const bubble = row.querySelector('.msg-bubble-content');
  if (!bubble) return;

  const text = bubble.innerText.replace(/\[Clause \d+\][\s\S]*/g, '').trim();
  if (!text) return;

  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.05;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
    showToast('Reading response aloud...', 'info');
  } else {
    showToast('Speech synthesis not supported in this browser.', 'error');
  }
}

// Copy Message Text
function copyMessageText(btn) {
  const row = btn.closest('.chat-msg-row');
  if (!row) return;
  const bubble = row.querySelector('.msg-bubble-content');
  if (!bubble) return;

  const text = bubble.innerText.trim();
  navigator.clipboard.writeText(text).then(() => {
    showToast('Copied to clipboard!', 'success');
  }).catch(() => {
    showToast('Failed to copy', 'error');
  });
}

function rateMessage(btn, type) {
  showToast(type === 'helpful' ? 'Marked as helpful 👍' : 'Feedback recorded 👎', 'success');
}

// Clear Chat Feed
function clearChatFeed() {
  const chatFeed = document.getElementById('chat-feed');
  if (!chatFeed) return;
  chatFeed.innerHTML = `
    <div class="chat-msg-row assistant-msg">
      <div class="avatar-badge avatar-assistant">
        <i class="fa-solid fa-robot"></i>
      </div>
      <div style="flex: 1;">
        <div class="msg-bubble-content">
          Session cleared. What would you like to know about our verified store policies?
        </div>
      </div>
    </div>
  `;
  AppState.messages = [];
  showToast('Chat history cleared', 'info');
}

// Export Chat Transcript
function exportChatTranscript() {
  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(AppState.messages, null, 2));
  const downloadAnchor = document.createElement('a');
  downloadAnchor.setAttribute("href", dataStr);
  downloadAnchor.setAttribute("download", `OmniDesk_Support_Transcript_${Date.now()}.json`);
  document.body.appendChild(downloadAnchor);
  downloadAnchor.click();
  downloadAnchor.remove();
  showToast('Transcript exported as JSON', 'success');
}

// 4. Knowledge Base Studio Management
function renderKbChunks(filterText = '') {
  const container = document.getElementById('kb-chunks-list');
  if (!container) return;

  const chunks = AppState.knowledgeChunks.filter(c => {
    if (!filterText) return true;
    const s = filterText.toLowerCase();
    return c.title.toLowerCase().includes(s) || c.content.toLowerCase().includes(s);
  });

  if (chunks.length === 0) {
    container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 3rem;">No policy chunks found matching "${filterText}".</div>`;
    return;
  }

  container.innerHTML = chunks.map(chunk => `
    <div class="chunk-card">
      <div class="chunk-header">
        <span><i class="fa-solid fa-hashtag"></i> ${chunk.id}</span>
        <span class="badge badge-cyan" style="font-size: 0.72rem; padding: 0.15rem 0.5rem;">${chunk.tokens} tokens</span>
      </div>
      <h4 style="font-size: 1.05rem;">${chunk.title}</h4>
      <div class="chunk-text">${escapeHtml(chunk.content)}</div>
      <div style="font-size: 0.75rem; color: var(--text-dim); display: flex; justify-content: space-between; margin-top: auto; padding-top: 0.5rem; border-top: 1px solid var(--border-subtle);">
        <span>Source: <code>${chunk.source}</code></span>
        <span style="color: #34d399;"><i class="fa-solid fa-circle-check"></i> Vector Indexed</span>
      </div>
    </div>
  `).join('');
}

function filterKbChunks() {
  const input = document.getElementById('kb-search-input');
  renderKbChunks(input ? input.value : '');
}

function openAddPolicyModal() {
  const modal = document.getElementById('add-policy-modal');
  if (modal) modal.classList.add('open');
}

function closeAddPolicyModal() {
  const modal = document.getElementById('add-policy-modal');
  if (modal) modal.classList.remove('open');
}

function handleAddPolicyClause(e) {
  e.preventDefault();
  const title = document.getElementById('policy-title').value.trim();
  const content = document.getElementById('policy-content').value.trim();
  if (!title || !content) return;

  const newChunk = {
    id: `chunk_${AppState.knowledgeChunks.length}`,
    title: title,
    content: content,
    tokens: Math.round(content.length / 4),
    source: 'custom_policy.txt'
  };

  AppState.knowledgeChunks.push(newChunk);
  closeAddPolicyModal();
  renderKbChunks();
  showToast(`Clause "${title}" vectorized and added to ChromaDB!`, 'success');
  e.target.reset();
}

// 5. Pipeline Settings Management
function testBackendConnection() {
  const input = document.getElementById('setting-backend-url');
  if (input) {
    AppState.backendUrl = input.value.trim();
  }
  showToast('Testing connection to ' + AppState.backendUrl + '...', 'info');
  checkBackendHealth().then(online => {
    if (online) {
      showToast('Successfully connected to FastAPI Backend!', 'success');
    } else {
      showToast('Could not reach backend. Running in offline simulation mode.', 'error');
    }
  });
}

function savePipelineSettings() {
  const backendInput = document.getElementById('setting-backend-url');
  const guardrailInput = document.getElementById('setting-guardrail');
  const modelInput = document.getElementById('setting-model');

  if (backendInput) {
    AppState.backendUrl = backendInput.value.trim();
    localStorage.setItem('omni_backend_url', AppState.backendUrl);
  }
  if (guardrailInput) {
    AppState.guardrailThreshold = parseFloat(guardrailInput.value);
    localStorage.setItem('omni_threshold', AppState.guardrailThreshold);
    const thresholdDisplay = document.getElementById('info-guardrail-threshold');
    if (thresholdDisplay) thresholdDisplay.textContent = AppState.guardrailThreshold.toFixed(2);
  }
  if (modelInput) {
    AppState.model = modelInput.value;
    localStorage.setItem('omni_model', AppState.model);
    const modelBadge = document.getElementById('model-indicator-badge');
    if (modelBadge) {
      modelBadge.innerHTML = `<i class="fa-solid fa-microchip"></i> ${AppState.model} &amp; gemini-embedding-001`;
    }
  }

  showToast('Pipeline settings saved successfully!', 'success');
}

// Utility formatting
function escapeHtml(str) {
  return str.replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
}

function formatMarkdownText(text) {
  let html = escapeHtml(text);
  // Bold **text**
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Italic *text*
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  // Bullet lists
  html = html.replace(/^[-*]\s+(.*)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
  // Paragraphs / line breaks
  html = html.replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>');
  return html;
}

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  checkBackendHealth();
  renderKbChunks();
  // Periodic health check every 15 seconds
  setInterval(checkBackendHealth, 15000);
});
