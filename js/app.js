/* ==========================================================================
   OMNIDESK AI — CUSTOMER SUPPORT PORTAL CONTROLLER (app.js)
   Synchronized Desktop-First Two-Window UI (Window 1)
   Features: RAG Chat + Collapsible Sources, Order Tracking,
   My Support Tickets, Visual Claim Inspection, and Live Agent Sync.
   ========================================================================== */

const CustomerState = {
  currentView: 'chat',
  backendUrl: window.location.origin.startsWith('http') && !window.location.port.match(/^(5500|3000|5173)$/)
    ? window.location.origin
    : 'http://127.0.0.1:8000',
  activeTicketId: localStorage.getItem('omni_active_ticket_id') || null,
  activeTicketData: null,
  lastKnownMessageCount: 0,
  claimImageBase64: '',
  claimImageMime: 'image/jpeg',
  claimDiagnosis: null,
  pollTimer: null
};

// ==========================================================================
// INITIALIZATION
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
  checkBackendHealth();
  setupDragAndDrop();

  // Restore active ticket sync if one exists
  if (CustomerState.activeTicketId) {
    updateSyncIndicator(CustomerState.activeTicketId);
    startLiveTicketPolling(CustomerState.activeTicketId);
  }

  // Pre-load default order display
  lookupOrder('ORD-1001', false);
});

// Check Server Health
async function checkBackendHealth() {
  const dot = document.getElementById('sidebar-status-dot');
  const text = document.getElementById('sidebar-status-text');
  try {
    const res = await fetch(`${CustomerState.backendUrl}/health`);
    if (res.ok) {
      if (dot) dot.className = 'pulse-dot';
      if (text) text.textContent = 'Support Live (24/7)';
    } else {
      throw new Error('Non-200');
    }
  } catch (e) {
    if (dot) dot.className = 'pulse-dot pulse-offline';
    if (text) text.textContent = 'Offline (Reconnecting)';
  }
}

// ==========================================================================
// NAVIGATION CONTROLLER
// ==========================================================================
function switchCustomerView(viewName) {
  CustomerState.currentView = viewName;
  const viewMap = {
    'chat': { id: 'view-chat', btn: 'btn-nav-chat', title: 'AI Policy Assistant' },
    'orders': { id: 'view-orders', btn: 'btn-nav-orders', title: 'Customer Order Tracking' },
    'tickets': { id: 'view-tickets', btn: 'btn-nav-tickets', title: 'My Support Tickets' },
    'claim': { id: 'view-claim', btn: 'btn-nav-claim', title: 'Visual Claim Inspection' }
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

  if (viewName === 'tickets' && CustomerState.activeTicketId) {
    loadTicketDetails(CustomerState.activeTicketId);
  }
}

// ==========================================================================
// 1. AI CHAT WORKSPACE & GROUNDED RESPONSES
// ==========================================================================
function sendQuickPrompt(promptText) {
  switchCustomerView('chat');
  const input = document.getElementById('chat-text-input');
  if (input) {
    input.value = promptText;
    document.getElementById('chat-input-form').dispatchEvent(new Event('submit'));
  }
}

function handleTextareaKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    document.getElementById('chat-input-form').dispatchEvent(new Event('submit'));
  }
}

function autoResizeTextarea(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = Math.min(textarea.scrollHeight, 140) + 'px';
}

async function handleChatSubmit(event) {
  if (event) event.preventDefault();
  const input = document.getElementById('chat-text-input');
  const query = input.value.trim();
  if (!query) return;

  input.value = '';
  autoResizeTextarea(input);

  // Append User Bubble
  appendChatMessage('user', query);

  // Loading Indicator
  const loadingId = 'loading-' + Date.now();
  appendChatMessage('assistant', '<i class="fa-solid fa-spinner fa-spin"></i> Checking official store policies in ChromaDB...', loadingId);

  try {
    const res = await fetch(`${CustomerState.backendUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        email: 'elena.r@techcorp.io'
      })
    });

    const loadingEl = document.getElementById(loadingId);
    if (loadingEl) loadingEl.remove();

    if (!res.ok) {
      throw new Error(`API Error (${res.status})`);
    }

    const data = await res.json();
    const answer = data.answer || data.response || "No response generated.";
    const sources = data.sources || [];
    const sections = data.sections || [];
    const order = data.order;
    const ticket = data.ticket;

    // Render Assistant Message with Collapsible Verified Sources
    renderAssistantChatReply(answer, sources, sections, order);

    // If query auto-escalated to a human ticket
    if (ticket && ticket.id) {
      handleAutoEscalationTrigger(ticket);
    }

  } catch (err) {
    const loadingEl = document.getElementById(loadingId);
    if (loadingEl) loadingEl.remove();
    appendChatMessage('assistant', `⚠️ Could not complete inquiry: ${err.message}. Please verify the server is running.`);
  }
}

function appendChatMessage(sender, htmlContent, elementId = null) {
  const feed = document.getElementById('chat-feed');
  const row = document.createElement('div');
  row.className = `chat-msg-row ${sender === 'user' ? 'user-msg' : sender === 'agent' ? 'agent-msg' : 'assistant-msg'}`;
  if (elementId) row.id = elementId;

  const avatar = document.createElement('div');
  avatar.className = `avatar-badge ${sender === 'user' ? 'avatar-user' : sender === 'agent' ? 'avatar-agent' : 'avatar-assistant'}`;
  avatar.innerHTML = sender === 'user'
    ? '<i class="fa-solid fa-user"></i>'
    : sender === 'agent'
      ? '<i class="fa-solid fa-headset"></i>'
      : '<i class="fa-solid fa-robot"></i>';

  const wrapper = document.createElement('div');
  wrapper.className = 'msg-content-wrapper';

  const label = document.createElement('div');
  label.className = 'msg-sender-label';
  label.textContent = sender === 'user' ? 'You' : sender === 'agent' ? 'OmniDesk Staff • Live Agent' : 'OmniDesk AI • Policy Assistant';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble-content';
  bubble.innerHTML = htmlContent;

  wrapper.appendChild(label);
  wrapper.appendChild(bubble);
  row.appendChild(avatar);
  row.appendChild(wrapper);

  feed.appendChild(row);
  feed.scrollTop = feed.scrollHeight;
}

function renderAssistantChatReply(answer, sources, sections, order) {
  const feed = document.getElementById('chat-feed');
  const row = document.createElement('div');
  row.className = 'chat-msg-row assistant-msg';

  const avatar = document.createElement('div');
  avatar.className = 'avatar-badge avatar-assistant';
  avatar.innerHTML = '<i class="fa-solid fa-robot"></i>';

  const wrapper = document.createElement('div');
  wrapper.className = 'msg-content-wrapper';

  const label = document.createElement('div');
  label.className = 'msg-sender-label';
  label.textContent = 'OmniDesk AI • Policy Assistant';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble-content';
  bubble.innerHTML = escapeHtml(answer).replace(/\n/g, '<br>');

  // Order Context Card if present
  if (order) {
    const orderBox = document.createElement('div');
    orderBox.className = 'chat-order-card';
    orderBox.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <strong><i class="fa-solid fa-box text-cyan"></i> Order #${order.id}</strong>
        <span class="status-badge badge-${(order.status || 'shipped').toLowerCase()}">${order.status}</span>
      </div>
      <div><strong>Items:</strong> ${escapeHtml(order.items || '')}</div>
      <div><strong>Tracking:</strong> <code style="color:var(--accent-cyan);">${order.tracking_number || 'N/A'}</code></div>
    `;
    bubble.appendChild(orderBox);
  }

  // Collapsible Verified Sources Box
  if (sources && sources.length > 0) {
    const sourcesBox = document.createElement('div');
    sourcesBox.className = 'verified-sources-box';

    const sourcesToggle = document.createElement('button');
    sourcesToggle.type = 'button';
    sourcesToggle.className = 'verified-sources-toggle';
    sourcesToggle.innerHTML = `
      <span><i class="fa-solid fa-shield-check"></i> Verified Policy Sources (${sources.length} matched clauses)</span>
      <i class="fa-solid fa-chevron-down" id="chevron-${Date.now()}"></i>
    `;

    const sourcesContent = document.createElement('div');
    sourcesContent.className = 'sources-details-content is-hidden';

    let chipsHtml = '';
    (sections.length ? sections : sources).forEach(sec => {
      chipsHtml += `<span class="source-item-chip"><i class="fa-solid fa-file-lines"></i> ${escapeHtml(sec)}</span>`;
    });
    sourcesContent.innerHTML = chipsHtml;

    sourcesToggle.onclick = () => {
      const isClosed = sourcesContent.classList.contains('is-hidden');
      sourcesContent.classList.toggle('is-hidden');
      sourcesToggle.querySelector('i.fa-chevron-down, i.fa-chevron-up').className = isClosed ? 'fa-solid fa-chevron-up' : 'fa-solid fa-chevron-down';
    };

    sourcesBox.appendChild(sourcesToggle);
    sourcesBox.appendChild(sourcesContent);
    bubble.appendChild(sourcesBox);

    // Update Right Panel Citations
    updateRightPaneCitations(sources, sections);
  }

  wrapper.appendChild(label);
  wrapper.appendChild(bubble);
  row.appendChild(avatar);
  row.appendChild(wrapper);

  feed.appendChild(row);
  feed.scrollTop = feed.scrollHeight;
}

function updateRightPaneCitations(sources, sections) {
  const container = document.getElementById('active-sources-list');
  if (!container) return;
  container.innerHTML = '';
  const displayList = sections.length ? sections : sources;
  displayList.slice(0, 3).forEach((item, idx) => {
    const card = document.createElement('div');
    card.className = 'source-item-card';
    card.innerHTML = `
      <h4>${escapeHtml(item)}</h4>
      <p style="color:var(--text-dim); font-size:11.5px;">Indexed in ChromaDB vector space. 100% factual policy clause.</p>
    `;
    container.appendChild(card);
  });
}

function exportChatTranscript() {
  const feed = document.getElementById('chat-feed');
  const text = feed.innerText;
  const blob = new Blob([text], { type: 'text/plain' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `omnidesk_chat_transcript_${Date.now()}.txt`;
  a.click();
}

function clearChatFeed() {
  const feed = document.getElementById('chat-feed');
  feed.innerHTML = `
    <div class="chat-msg-row assistant-msg">
      <div class="avatar-badge avatar-assistant"><i class="fa-solid fa-robot"></i></div>
      <div class="msg-content-wrapper">
        <div class="msg-sender-label">OmniDesk AI • Policy Assistant</div>
        <div class="msg-bubble-content">
          New session started. How can I assist you with your orders, returns, warranty, or delivery today?
        </div>
      </div>
    </div>
  `;
}

// ==========================================================================
// 2. ORDER TRACKING PANEL
// ==========================================================================
function quickLookupOrder(orderId) {
  document.getElementById('order-search-input').value = orderId;
  lookupOrder(orderId);
}

async function lookupOrder(explicitId = null, shouldSwitch = true) {
  const idInput = document.getElementById('order-search-input');
  const query = (explicitId || idInput.value).trim();
  if (!query) return;

  if (shouldSwitch) switchCustomerView('orders');

  const container = document.getElementById('order-result-container');
  container.innerHTML = `<div style="padding:20px; color:var(--text-muted);"><i class="fa-solid fa-spinner fa-spin"></i> Fetching order details...</div>`;

  try {
    const isEmail = query.includes('@');
    const url = isEmail
      ? `${CustomerState.backendUrl}/api/orders?email=${encodeURIComponent(query)}`
      : `${CustomerState.backendUrl}/api/orders/${encodeURIComponent(query)}`;

    const res = await fetch(url);
    if (!res.ok) throw new Error(`Order ${query} not found`);

    const data = await res.json();
    const orders = isEmail ? data.orders : [data.order];

    if (!orders || orders.length === 0) {
      container.innerHTML = `<div class="order-result-card" style="color:var(--accent-rose);"><i class="fa-solid fa-triangle-exclamation"></i> No orders found for "${query}".</div>`;
      return;
    }

    container.innerHTML = '';
    orders.forEach(order => {
      const card = document.createElement('div');
      card.className = 'order-result-card';
      const stClass = (order.status || 'processing').toLowerCase();
      card.innerHTML = `
        <div class="order-header-row">
          <div>
            <div class="order-id-title">${order.id}</div>
            <span style="color: var(--text-dim); font-size: 12px;">Customer: ${escapeHtml(order.customer_name || 'Valued Customer')} • Date: ${order.order_date || 'Recent'}</span>
          </div>
          <span class="status-badge badge-${stClass}">${order.status}</span>
        </div>
        <div>
          <strong style="font-size: 13px; color: var(--text-muted);">Items in Order:</strong>
          <p style="margin-top: 4px; font-size: 13.5px; color: var(--text-main);">${escapeHtml(order.items || 'Standard Product Package')}</p>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid var(--border-subtle); padding-top:12px;">
          <div>
            <span style="color: var(--text-dim); font-size: 12px;">Tracking Number:</span>
            <span style="font-family: var(--font-mono); color: var(--accent-cyan); font-weight: 600; margin-left: 6px;">${order.tracking_number || 'TRK-Pending'}</span>
          </div>
          <div style="font-size: 16px; font-weight: 700; color: #fff;">${order.total || '$0.00'}</div>
        </div>
      `;
      container.appendChild(card);
    });

  } catch (err) {
    container.innerHTML = `<div class="order-result-card" style="color:var(--accent-rose);"><i class="fa-solid fa-triangle-exclamation"></i> ${err.message}. Try ORD-1001, ORD-1042, ORD-2024, ORD-5521, or ORD-8841.</div>`;
  }
}

// ==========================================================================
// 3. MY SUPPORT TICKETS & BIDIRECTIONAL LIVE SYNC
// ==========================================================================
function lookupCustomerTicket() {
  const input = document.getElementById('cust-ticket-input');
  const val = input.value.trim();
  if (!val) return;
  loadTicketDetails(val);
}

async function loadTicketDetails(ticketId) {
  const box = document.getElementById('cust-ticket-details-box');
  try {
    const res = await fetch(`${CustomerState.backendUrl}/api/tickets/${encodeURIComponent(ticketId)}/State`);
    if (!res.ok) throw new Error(`Ticket ${ticketId} not found`);

    const data = await res.json();
    const t = data.ticket || data.state;
    CustomerState.activeTicketId = t.id;
    CustomerState.activeTicketData = t;
    localStorage.setItem('omni_active_ticket_id', t.id);

    // Update UI elements
    document.getElementById('cust-ticket-display-id').textContent = t.id;
    document.getElementById('cust-ticket-display-subject').textContent = t.subject || t.query;

    const stPill = document.getElementById('cust-ticket-status-pill');
    stPill.textContent = t.status;
    stPill.className = `status-badge badge-${t.status === 'Resolved' ? 'delivered' : t.status === 'In Progress' ? 'shipped' : 'processing'}`;

    const slaPill = document.getElementById('cust-ticket-sla-pill');
    if (t.sla_details) {
      slaPill.textContent = t.sla_details.label || 'SLA Active';
    }

    renderTicketConversationStream(t.messages || []);
    box.classList.remove('is-hidden');

    // Activate live polling
    updateSyncIndicator(t.id);
    startLiveTicketPolling(t.id);

  } catch (e) {
    alert(e.message);
  }
}

function renderTicketConversationStream(messages) {
  const stream = document.getElementById('cust-ticket-messages-stream');
  if (!stream) return;
  stream.innerHTML = '';
  CustomerState.lastKnownMessageCount = messages.length;

  messages.forEach(m => {
    const isStaff = m.sender !== 'Valued Customer' && m.sender !== 'Customer' && !m.sender.toLowerCase().includes('elena') && !m.sender.toLowerCase().includes('user');
    const msgDiv = document.createElement('div');
    msgDiv.style.cssText = `
      padding: 10px 14px;
      border-radius: var(--radius-sm);
      font-size: 13px;
      line-height: 1.5;
      background: ${isStaff ? 'rgba(6, 182, 212, 0.12)' : 'var(--bg-surface)'};
      border: 1px solid ${isStaff ? 'rgba(6, 182, 212, 0.3)' : 'var(--border-subtle)'};
    `;
    msgDiv.innerHTML = `
      <div style="display:flex; justify-content:space-between; margin-bottom:4px; font-size:11px; color:var(--text-dim);">
        <strong style="color:${isStaff ? 'var(--accent-cyan)' : 'var(--text-main)'};">${escapeHtml(m.sender)}</strong>
        <span>${m.timestamp || ''}</span>
      </div>
      <div>${escapeHtml(m.text || '')}</div>
    `;
    stream.appendChild(msgDiv);
  });
  stream.scrollTop = stream.scrollHeight;
}

async function sendCustomerTicketReply(event) {
  event.preventDefault();
  const input = document.getElementById('cust-reply-text');
  const text = input.value.trim();
  if (!text || !CustomerState.activeTicketId) return;

  const btn = document.getElementById('btn-cust-reply');
  btn.disabled = true;

  try {
    const res = await fetch(`${CustomerState.backendUrl}/api/tickets/${CustomerState.activeTicketId}/reply`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sender: 'Elena Rostova',
        text: text
      })
    });
    if (!res.ok) throw new Error('Failed to send reply');

    input.value = '';
    await loadTicketDetails(CustomerState.activeTicketId);
  } catch (e) {
    alert(e.message);
  } finally {
    btn.disabled = false;
  }
}

// ==========================================================================
// LIVE SYNC POLLER (WINDOW 1 <-> WINDOW 2)
// ==========================================================================
function updateSyncIndicator(ticketId) {
  const syncBadge = document.getElementById('active-ticket-sync-indicator');
  const syncLabel = document.getElementById('sync-ticket-label');
  if (syncBadge && syncLabel) {
    syncBadge.style.display = 'inline-flex';
    syncLabel.textContent = `Live Sync: ${ticketId}`;
  }
}

function startLiveTicketPolling(ticketId) {
  if (CustomerState.pollTimer) clearInterval(CustomerState.pollTimer);

  CustomerState.pollTimer = setInterval(async () => {
    try {
      const res = await fetch(`${CustomerState.backendUrl}/api/tickets/${ticketId}/State`);
      if (!res.ok) return;

      const data = await res.json();
      const t = data.ticket || data.state;
      const messages = t.messages || [];

      // Check if new agent message arrived
      if (messages.length > CustomerState.lastKnownMessageCount) {
        const newMsgs = messages.slice(CustomerState.lastKnownMessageCount);
        CustomerState.lastKnownMessageCount = messages.length;

        newMsgs.forEach(m => {
          if (!m.is_internal_note) {
            // Live toast & chat injection
            const isAgent = m.sender !== 'Elena Rostova' && m.sender !== 'Customer';
            if (isAgent) {
              appendChatMessage('agent', `<strong>[Agent ${escapeHtml(m.sender)}]</strong>: ${escapeHtml(m.text)}`);
              showLiveEscalationAlert(ticketId, m.sender, m.text);
            }
          }
        });

        // If currently in tickets view, re-render stream
        if (CustomerState.currentView === 'tickets') {
          renderTicketConversationStream(messages);
        }
      }
    } catch (e) {
      // Quiet background poll error
    }
  }, 3000);
}

function showLiveEscalationAlert(ticketId, sender, text) {
  const banner = document.getElementById('chat-escalation-banner');
  const title = document.getElementById('escalation-banner-text');
  const sub = document.getElementById('escalation-banner-sub');
  if (banner && title && sub) {
    banner.classList.remove('is-hidden');
    title.textContent = `New Response from ${sender} (Ticket #${ticketId}):`;
    sub.textContent = text.slice(0, 120) + (text.length > 120 ? '...' : '');
  }
}

function handleAutoEscalationTrigger(ticket) {
  CustomerState.activeTicketId = ticket.id;
  localStorage.setItem('omni_active_ticket_id', ticket.id);
  updateSyncIndicator(ticket.id);
  startLiveTicketPolling(ticket.id);

  const banner = document.getElementById('chat-escalation-banner');
  const title = document.getElementById('escalation-banner-text');
  const sub = document.getElementById('escalation-banner-sub');
  if (banner && title && sub) {
    banner.classList.remove('is-hidden');
    title.textContent = `Support Ticket #${ticket.id} Created:`;
    sub.textContent = `Assigned Priority: ${ticket.priority || 'Urgent'}. Live sync connected with Admin Console.`;
  }
}

// ==========================================================================
// 4. VISUAL CLAIM INSPECTION & 1-CLICK TICKET FILING
// ==========================================================================
function setupDragAndDrop() {
  const zone = document.getElementById('claim-drop-zone');
  if (!zone) return;

  ['dragenter', 'dragover'].forEach(name => {
    zone.addEventListener(name, (e) => {
      e.preventDefault();
      zone.classList.add('drag-over');
    });
  });

  ['dragleave', 'drop'].forEach(name => {
    zone.addEventListener(name, (e) => {
      e.preventDefault();
      zone.classList.remove('drag-over');
    });
  });

  zone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      processClaimFile(files[0]);
    }
  });
}

function handleClaimFileSelect(event) {
  const files = event.target.files;
  if (files && files.length > 0) {
    processClaimFile(files[0]);
  }
}

function processClaimFile(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    const result = e.target.result;
    CustomerState.claimImageBase64 = result.split(',')[1] || '';
    CustomerState.claimImageMime = file.type || 'image/jpeg';

    const preview = document.getElementById('claim-preview-container');
    const img = document.getElementById('claim-preview-img');
    const name = document.getElementById('claim-preview-filename');

    if (preview && img && name) {
      img.src = result;
      name.textContent = file.name;
      preview.classList.remove('is-hidden');
    }
  };
  reader.readAsDataURL(file);
}

function clearClaimAttachment() {
  CustomerState.claimImageBase64 = '';
  document.getElementById('claim-preview-container').classList.add('is-hidden');
  document.getElementById('claim-file-input').value = '';
}

function handleImageAttachment(event) {
  const files = event.target.files;
  if (files && files.length > 0) {
    processClaimFile(files[0]);
    switchCustomerView('claim');
  }
}

async function submitVisualClaim() {
  const desc = document.getElementById('claim-desc-input').value.trim();
  if (!desc) {
    alert('Please enter a brief explanation of the damage or defect.');
    return;
  }

  const btn = document.getElementById('btn-run-vision');
  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing with Gemini Vision...';

  try {
    const res = await fetch(`${CustomerState.backendUrl}/api/analyze-image`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        claim_description: desc,
        image_base64: CustomerState.claimImageBase64,
        mime_type: CustomerState.claimImageMime
      })
    });

    if (!res.ok) throw new Error('Vision analysis failed');

    const data = await res.json();
    CustomerState.claimDiagnosis = data;

    const diagCard = document.getElementById('claim-diagnosis-card');
    const severityBadge = document.getElementById('diagnosis-severity-badge');
    const textContent = document.getElementById('diagnosis-text-content');

    const severity = data.severity || 'Medium';
    severityBadge.textContent = `${severity} Severity`;
    severityBadge.className = `priority-badge priority-${severity.toLowerCase() === 'high' || severity.toLowerCase() === 'severe' ? 'urgent' : 'medium'}`;

    textContent.innerHTML = `
      <p><strong>Recommendation:</strong> ${escapeHtml(data.recommendation || 'Proceed with manufacturer warranty replacement.')}</p>
      <p style="margin-top:8px;"><strong>Rationale:</strong> ${escapeHtml(data.rationale || data.analysis || 'Physical damage consistent with shipping impact. Covered under Section 4: Damaged or Defective Items.')}</p>
      <p style="margin-top:8px; font-size:12px; color:var(--text-dim);">Estimated Replacement Lead Time: <strong>2 Business Days via Expedited DHL</strong></p>
    `;

    diagCard.classList.remove('is-hidden');
    diagCard.scrollIntoView({ behavior: 'smooth' });

  } catch (e) {
    alert(`Vision inspection error: ${e.message}`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-brain"></i> Inspect Damage with Gemini Vision';
  }
}

async function filePriorityReplacementTicket() {
  const desc = document.getElementById('claim-desc-input').value.trim();
  const btn = document.getElementById('btn-file-replacement');
  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Filing Ticket...';

  try {
    const diag = CustomerState.claimDiagnosis || {};
    const queryPayload = `[Visual Claim Inspection] Damage: ${desc}. Diagnosis: ${diag.recommendation || 'Approved replacement'}. Rationale: ${diag.rationale || 'Warranty verified'}`;

    const res = await fetch(`${CustomerState.backendUrl}/api/tickets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customer_name: 'Elena Rostova',
        customer_email: 'elena@enterprise.org',
        customer_tier: 'VIP Enterprise',
        priority: 'Urgent',
        subject: 'Warranty Claim: Hardware Replacement Needed',
        query: queryPayload
      })
    });

    if (!res.ok) throw new Error('Ticket submission failed');

    const data = await res.json();
    const t = data.ticket;
    CustomerState.activeTicketId = t.id;
    localStorage.setItem('omni_active_ticket_id', t.id);

    // Switch to tickets view immediately
    switchCustomerView('tickets');
    document.getElementById('cust-ticket-input').value = t.id;
    await loadTicketDetails(t.id);

    alert(`Priority Replacement Ticket #${t.id} filed successfully! Live agent queue has been notified.`);
  } catch (e) {
    alert(e.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-box-open"></i> File Priority Replacement Ticket';
  }
}

// ==========================================================================
// HUMAN ESCALATION MODAL
// ==========================================================================
function openHumanEscalationModal() {
  document.getElementById('escalation-modal').classList.remove('is-hidden');
}

function closeHumanEscalationModal() {
  document.getElementById('escalation-modal').classList.add('is-hidden');
}

async function handleEscalationModalSubmit(event) {
  event.preventDefault();
  const name = document.getElementById('esc-name').value.trim();
  const email = document.getElementById('esc-email').value.trim();
  const priority = document.getElementById('esc-priority').value;
  const query = document.getElementById('esc-query').value.trim();

  try {
    const res = await fetch(`${CustomerState.backendUrl}/api/tickets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customer_name: name,
        customer_email: email,
        customer_tier: 'VIP Enterprise',
        priority: priority,
        subject: `Live Escalation: ${query.slice(0, 40)}...`,
        query: query
      })
    });

    if (!res.ok) throw new Error('Failed to create ticket');

    const data = await res.json();
    const t = data.ticket;

    closeHumanEscalationModal();
    handleAutoEscalationTrigger(t);
    appendChatMessage('assistant', `✅ Ticket <strong>#${t.id}</strong> has been escalated to our human support desk with <strong>${priority}</strong> priority. An agent is reviewing your inquiry.`);

  } catch (e) {
    alert(e.message);
  }
}

// Utility: Escape HTML
function escapeHtml(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
