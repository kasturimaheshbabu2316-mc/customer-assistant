/* ==========================================================================
   OMNIDESK AI - ADMIN & UX CONTROL CENTER CONTROLLER (admin.js)
   Dedicated to UX Feature Toggles, Knowledge Base Vector Studio,
   Agent Escalation Queue, Copilot Replies, and Telemetry.
   ========================================================================== */

const AdminState = {
  currentView: 'ux',
  backendUrl: localStorage.getItem('omni_backend_url') || (window.location.origin.startsWith('http') && !window.location.port.match(/^(5500|3000|5173)$/) ? window.location.origin : 'http://localhost:8000'),
  apiKey: localStorage.getItem('omni_admin_key') || 'admin-secret-key-2026',
  isAuthenticated: false,
  activeTicketFilter: 'all',
  tickets: [],
  kbChunks: []
};

// Initialize Admin Console
document.addEventListener('DOMContentLoaded', async () => {
  checkExistingAuth();
  await checkBackendHealth();
  if (AdminState.isAuthenticated) {
    loadAllAdminData();
  }
});

// Authentication Gate
function checkExistingAuth() {
  const savedKey = localStorage.getItem('omni_admin_key');
  const authGate = document.getElementById('admin-auth-gate');
  if (savedKey) {
    AdminState.apiKey = savedKey;
    AdminState.isAuthenticated = true;
    if (authGate) authGate.classList.add('is-hidden');
  } else {
    if (authGate) authGate.classList.remove('is-hidden');
  }
}

async function handleAdminLogin(event) {
  event.preventDefault();
  const inputKey = document.getElementById('admin-key-input').value.trim();
  if (!inputKey) return;

  AdminState.apiKey = inputKey;
  localStorage.setItem('omni_admin_key', inputKey);
  AdminState.isAuthenticated = true;
  const authGate = document.getElementById('admin-auth-gate');
  if (authGate) authGate.classList.add('is-hidden');
  await loadAllAdminData();
}

function adminLogout() {
  localStorage.removeItem('omni_admin_key');
  AdminState.isAuthenticated = false;
  const authGate = document.getElementById('admin-auth-gate');
  if (authGate) authGate.classList.remove('is-hidden');
  const keyInput = document.getElementById('admin-key-input');
  if (keyInput) keyInput.value = '';
}

async function loadAllAdminData() {
  await loadFeatureSettings();
  await loadKnowledgeBaseChunks();
  await loadAdminTickets();
  await loadAnalyticsData();
  await loadPipelineSettings();
}

// Navigation
function switchAdminView(viewName) {
  AdminState.currentView = viewName;
  const viewMap = {
    'ux': { id: 'admin-view-ux', btn: 'btn-admin-nav-ux', title: 'UX & Feature Studio' },
    'kb': { id: 'admin-view-kb', btn: 'btn-admin-nav-kb', title: 'Knowledge Base Studio' },
    'tickets': { id: 'admin-view-tickets', btn: 'btn-admin-nav-tickets', title: 'Escalation & Agent Desk' },
    'analytics': { id: 'admin-view-analytics', btn: 'btn-admin-nav-analytics', title: 'Deflection & CSAT Telemetry' },
    'settings': { id: 'admin-view-settings', btn: 'btn-admin-nav-settings', title: 'RAG Pipeline Settings' }
  };

  Object.values(viewMap).forEach(v => {
    const el = document.getElementById(v.id);
    const btn = document.getElementById(v.btn);
    if (el) el.classList.remove('active-view');
    if (btn) btn.classList.remove('active');
  });

  const active = viewMap[viewName] || viewMap['ux'];
  const activeEl = document.getElementById(active.id);
  const activeBtn = document.getElementById(active.btn);
  const titleEl = document.getElementById('admin-current-view-title');

  if (activeEl) activeEl.classList.add('active-view');
  if (activeBtn) activeBtn.classList.add('active');
  if (titleEl) titleEl.textContent = active.title;

  if (viewName === 'tickets') loadAdminTickets();
  if (viewName === 'analytics') loadAnalyticsData();
  if (viewName === 'kb') loadKnowledgeBaseChunks();

  if (window.innerWidth <= 768) {
    const sidebar = document.getElementById('app-sidebar');
    if (sidebar) sidebar.classList.remove('mobile-open');
  }
}

function toggleAppSidebar() {
  const sidebar = document.getElementById('app-sidebar');
  if (sidebar) sidebar.classList.toggle('mobile-open');
}

// Health Check
async function checkBackendHealth() {
  const dot = document.getElementById('sidebar-status-dot');
  const txt = document.getElementById('sidebar-status-text');
  try {
    const res = await fetch(`${AdminState.backendUrl}/health`);
    if (res.ok) {
      if (dot) dot.style.backgroundColor = 'var(--accent-emerald)';
      if (txt) txt.textContent = 'Admin Connected';
    }
  } catch (e) {
    if (dot) dot.style.backgroundColor = 'var(--accent-amber)';
    if (txt) txt.textContent = 'Backend Offline';
  }
}

// ==============================================================================
// 1. UX & FEATURE CONFIGURATION ENGINE
// ==============================================================================
async function loadFeatureSettings() {
  try {
    const res = await fetch(`${AdminState.backendUrl}/api/features`);
    if (res.ok) {
      const f = await res.json();
      document.getElementById('feat-enable-streaming').checked = Boolean(f.enable_streaming);
      document.getElementById('feat-enable-vision').checked = Boolean(f.enable_vision_upload);
      document.getElementById('feat-enable-language').checked = Boolean(f.enable_multi_language);
      document.getElementById('feat-enable-faq-chips').checked = Boolean(f.enable_faq_chips);
      document.getElementById('feat-enable-csat').checked = Boolean(f.enable_csat_popup);
      document.getElementById('feat-enable-ticket-lookup').checked = Boolean(f.enable_ticket_lookup);
      document.getElementById('feat-enable-announcement').checked = Boolean(f.enable_announcement_banner);
      document.getElementById('feat-auto-escalate-vip').checked = Boolean(f.auto_escalate_vip);

      if (f.announcement_banner_text) {
        document.getElementById('feat-announcement-text').value = f.announcement_banner_text;
      }
      if (f.welcome_greeting) {
        document.getElementById('feat-welcome-greeting').value = f.welcome_greeting;
      }
      if (f.theme_mode) {
        document.getElementById('feat-theme-mode').value = f.theme_mode;
      }
    }
  } catch (e) {
    console.warn('Could not load features from backend:', e);
  }
}

async function saveFeatureSettings() {
  const payload = {
    enable_streaming: document.getElementById('feat-enable-streaming').checked,
    enable_vision_upload: document.getElementById('feat-enable-vision').checked,
    enable_multi_language: document.getElementById('feat-enable-language').checked,
    enable_faq_chips: document.getElementById('feat-enable-faq-chips').checked,
    enable_csat_popup: document.getElementById('feat-enable-csat').checked,
    enable_ticket_lookup: document.getElementById('feat-enable-ticket-lookup').checked,
    enable_announcement_banner: document.getElementById('feat-enable-announcement').checked,
    auto_escalate_vip: document.getElementById('feat-auto-escalate-vip').checked,
    announcement_banner_text: document.getElementById('feat-announcement-text').value.trim(),
    welcome_greeting: document.getElementById('feat-welcome-greeting').value.trim(),
    theme_mode: document.getElementById('feat-theme-mode').value
  };

  try {
    const res = await fetch(`${AdminState.backendUrl}/api/features`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': AdminState.apiKey
      },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      alert('🎉 UX & Feature configuration updated successfully! Customer portal will reflect these changes immediately.');
    } else {
      const err = await res.json();
      alert(`Error updating features: ${err.detail || 'Unauthorized'}`);
    }
  } catch (e) {
    alert('Failed to save feature configuration. Please check backend connection.');
  }
}

// ==============================================================================
// 2. KNOWLEDGE BASE STUDIO (ChromaDB Vector Management)
// ==============================================================================
async function loadKnowledgeBaseChunks() {
  try {
    const res = await fetch(`${AdminState.backendUrl}/api/kb/chunks`);
    if (res.ok) {
      const data = await res.json();
      AdminState.kbChunks = data.chunks || [];
      document.getElementById('kb-total-chunks-count').textContent = data.total || AdminState.kbChunks.length;
      renderKbChunksGrid();
    }
  } catch (e) {
    console.warn('Could not load KB chunks:', e);
  }
}

function renderKbChunksGrid() {
  const grid = document.getElementById('kb-chunks-grid');
  if (!grid) return;

  grid.innerHTML = AdminState.kbChunks.map(c => `
    <div class="kb-chunk-card">
      <div class="chunk-card-header">
        <span class="badge badge-glow-primary badge-font-sm">${c.id}</span>
        <button type="button" class="btn-icon btn-sm kb-card-delete-btn" onclick="deletePolicyChunk('${c.id}')" title="Delete chunk from ChromaDB" aria-label="Delete chunk from ChromaDB">
          <i class="fa-solid fa-trash-can"></i>
        </button>
      </div>
      <h4 class="chunk-card-title">${c.title}</h4>
      <p class="chunk-card-content">${c.content}</p>
      <div class="chunk-card-meta">
        <span><i class="fa-solid fa-file-lines"></i> ${c.source || 'company_faq.txt'}</span>
        <span><i class="fa-solid fa-layer-group"></i> ${c.tokens || 60} tokens</span>
      </div>
    </div>
  `).join('');
}

function openAddPolicyModal() {
  const modal = document.getElementById('add-policy-modal');
  if (modal) {
    modal.classList.remove('is-hidden');
    modal.classList.add('open');
  }
}
function closeAddPolicyModal() {
  const modal = document.getElementById('add-policy-modal');
  if (modal) {
    modal.classList.add('is-hidden');
    modal.classList.remove('open');
  }
}

async function handleAddPolicySubmit(event) {
  event.preventDefault();
  const title = document.getElementById('new-policy-title').value.trim();
  const content = document.getElementById('new-policy-content').value.trim();

  try {
    const res = await fetch(`${AdminState.backendUrl}/api/kb/add`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': AdminState.apiKey
      },
      body: JSON.stringify({ title: title, content: content, source: 'custom_policy.txt' })
    });

    if (res.ok) {
      closeAddPolicyModal();
      document.getElementById('new-policy-title').value = '';
      document.getElementById('new-policy-content').value = '';
      alert(`Clause "${title}" successfully vectorized and indexed into ChromaDB!`);
      await loadKnowledgeBaseChunks();
    } else {
      alert('Failed to vectorize policy. Check Admin API key.');
    }
  } catch (e) {
    alert('Error connecting to backend.');
  }
}

async function deletePolicyChunk(chunkId) {
  if (!confirm(`Are you sure you want to remove chunk ${chunkId} from the vector store?`)) return;

  try {
    const res = await fetch(`${AdminState.backendUrl}/api/kb/chunks/${chunkId}`, {
      method: 'DELETE',
      headers: { 'X-API-Key': AdminState.apiKey }
    });

    if (res.ok) {
      await loadKnowledgeBaseChunks();
    } else {
      alert('Delete failed. Please check Admin API key.');
    }
  } catch (e) {
    alert('Backend connection error.');
  }
}

async function resetDefaultKnowledgeBase() {
  if (!confirm('Re-index knowledge base from default documentation files?')) return;
  try {
    const res = await fetch(`${AdminState.backendUrl}/api/kb/reset`, {
      method: 'POST',
      headers: { 'X-API-Key': AdminState.apiKey }
    });
    if (res.ok) {
      alert('Knowledge base re-indexed successfully into ChromaDB!');
      await loadKnowledgeBaseChunks();
    }
  } catch (e) {
    alert('Re-index failed.');
  }
}

function exportKnowledgeBaseJson() {
  window.open(`${AdminState.backendUrl}/api/kb/export`, '_blank');
}

// ==============================================================================
// 3. ESCALATION & AGENT DESK
// ==============================================================================
async function loadAdminTickets() {
  try {
    const res = await fetch(`${AdminState.backendUrl}/api/tickets`);
    if (res.ok) {
      const data = await res.json();
      AdminState.tickets = data.tickets || [];
      const badge = document.getElementById('admin-ticket-badge');
      const openCount = AdminState.tickets.filter(t => t.status === 'Open').length;
      if (badge) badge.textContent = openCount;
      renderAdminTicketsList();
    }
  } catch (e) {
    console.warn('Could not load tickets:', e);
  }
}

function filterAdminTickets(status, btnEl) {
  AdminState.activeTicketFilter = status;
  document.querySelectorAll('.tickets-filter-bar .filter-chip').forEach(b => b.classList.remove('active'));
  if (btnEl) btnEl.classList.add('active');
  renderAdminTicketsList();
}

function renderAdminTicketsList() {
  const container = document.getElementById('admin-tickets-container');
  if (!container) return;

  const filtered = AdminState.tickets.filter(t => {
    if (AdminState.activeTicketFilter === 'all') return true;
    return t.status === AdminState.activeTicketFilter;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state-card">
        <i class="fa-solid fa-ticket empty-state-icon"></i>
        <p>No tickets found in category "${AdminState.activeTicketFilter}".</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(t => {
    const isVip = t.customer_tier && t.customer_tier.includes('VIP');
    const sla = t.sla_details || { label: 'SLA Active', badge_status: 'normal' };
    const messages = t.messages || [];

    return `
      <div class="ticket-card ${isVip ? 'vip-ticket-glow' : ''}" id="card-${t.id}">
        <div class="ticket-top-row">
          <div class="ticket-id-tag">
            <strong>${t.id}</strong>
            <span class="customer-tag">${t.customer_name} (${t.customer_tier || 'Standard Retail'})</span>
          </div>
          <div class="ticket-status-pill-wrap">
            <span class="badge ${sla.badge_status === 'breached' ? 'badge-glow-rose' : 'badge-glow-amber'}">
              <i class="fa-solid fa-stopwatch"></i> ${sla.label}
            </span>
            <span class="status-badge ${t.status.toLowerCase().replace(' ', '-')}">${t.status}</span>
          </div>
        </div>

        <h4 class="ticket-subject-title">${t.subject}</h4>
        <p class="ticket-query-text">${t.query}</p>

        <!-- Message Thread -->
        <div class="ticket-thread-box">
          ${messages.map(m => `
            <div class="thread-msg-item ${m.is_internal_note ? 'internal-staff-note' : (m.sender === t.customer_name ? 'customer-msg' : 'agent-msg')}">
              <div class="thread-msg-meta">
                <span>${m.is_internal_note ? '🔒 Staff Note (' + m.sender + ')' : m.sender}</span>
                <span>${m.timestamp}</span>
              </div>
              <div class="thread-msg-text">${m.text}</div>
            </div>
          `).join('')}
        </div>

        <!-- Copilot & Agent Actions Area -->
        <div class="agent-actions-panel">
          <div class="copilot-btn-group">
            <button type="button" class="btn btn-secondary btn-sm" onclick="suggestCopilotReply('${t.id}')">
              <i class="fa-solid fa-wand-magic-sparkles text-primary"></i> Suggest AI Copilot Draft
            </button>
            <div class="macro-dropdown-wrap">
              <select onchange="applyMacro('${t.id}', this.value); this.value='';" class="form-select btn-sm macro-select-control" title="Apply 1-click response macro" aria-label="Apply 1-click response macro">
                <option value="">⚡ Apply 1-Click Macro...</option>
                <option value="macro_return_rma">📦 30-Day Return RMA</option>
                <option value="macro_warranty_claim">🛡️ 1-Year Warranty Intake</option>
                <option value="macro_price_match">💳 Price Match Credit</option>
                <option value="macro_intl_ddp">✈️ International DHL Details</option>
              </select>
            </div>
          </div>

          <!-- Suggested Draft Box -->
          <div id="copilot-draft-${t.id}" class="copilot-draft-box is-hidden">
            <div class="copilot-draft-header">
              <span><i class="fa-solid fa-robot text-cyan"></i> AI Copilot Grounded Suggestion:</span>
              <button type="button" class="btn-text-link" onclick="insertDraftIntoReply('${t.id}')">Insert into Reply</button>
            </div>
            <p id="copilot-draft-text-${t.id}" class="copilot-draft-content"></p>
          </div>

          <!-- Reply Composer -->
          <div class="agent-reply-composer">
            <textarea id="agent-reply-text-${t.id}" class="form-textarea" rows="2" placeholder="Type reply to customer or internal staff note..." title="Type agent reply" aria-label="Type agent reply"></textarea>
            <div class="agent-reply-controls">
              <label for="is-note-${t.id}" class="agent-note-checkbox-label">
                <input type="checkbox" id="is-note-${t.id}" title="Toggle confidential staff note" aria-label="Toggle confidential staff note">
                <span>🔒 Confidential Staff Note</span>
              </label>
              <div class="btn-group-sm">
                <button type="button" class="btn btn-outline btn-sm" onclick="updateTicketStatus('${t.id}', 'Resolved')">
                  <i class="fa-solid fa-check"></i> Mark Resolved
                </button>
                <button type="button" class="btn btn-primary btn-sm" onclick="sendAgentMessage('${t.id}')">
                  <i class="fa-solid fa-paper-plane"></i> Send
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

async function suggestCopilotReply(ticketId) {
  const box = document.getElementById(`copilot-draft-${ticketId}`);
  const txt = document.getElementById(`copilot-draft-text-${ticketId}`);
  if (box && txt) {
    box.classList.remove('is-hidden');
    txt.innerHTML = '<span class="typing-cursor">Synthesizing grounded response with verified citations...</span>';
  }

  try {
    const res = await fetch(`${AdminState.backendUrl}/api/tickets/${ticketId}/suggest-reply`, { method: 'POST' });
    if (res.ok) {
      const data = await res.json();
      txt.textContent = data.suggested_reply;
    }
  } catch (e) {
    txt.textContent = "Could not generate copilot suggestion. Please check Gemini API key.";
  }
}

function insertDraftIntoReply(ticketId) {
  const draftTxt = document.getElementById(`copilot-draft-text-${ticketId}`)?.textContent || '';
  const replyInput = document.getElementById(`agent-reply-text-${ticketId}`);
  if (replyInput) replyInput.value = draftTxt;
}

async function applyMacro(ticketId, macroId) {
  if (!macroId) return;
  try {
    const res = await fetch(`${AdminState.backendUrl}/api/tickets/${ticketId}/apply-macro`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ macro_id: macroId, sender: 'Support Specialist' })
    });
    if (res.ok) {
      await loadAdminTickets();
    }
  } catch (e) {
    alert('Failed to apply macro.');
  }
}

async function sendAgentMessage(ticketId) {
  const textInput = document.getElementById(`agent-reply-text-${ticketId}`);
  const isNoteInput = document.getElementById(`is-note-${ticketId}`);
  const text = textInput.value.trim();
  const isNote = Boolean(isNoteInput?.checked);
  if (!text) return;

  try {
    const res = await fetch(`${AdminState.backendUrl}/api/tickets/${ticketId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sender: isNote ? 'Staff Specialist' : 'OmniDesk Agent',
        text: text,
        is_internal_note: isNote
      })
    });

    if (res.ok) {
      textInput.value = '';
      if (isNoteInput) isNoteInput.checked = false;
      await loadAdminTickets();
    }
  } catch (e) {
    alert('Failed to send message.');
  }
}

async function updateTicketStatus(ticketId, status) {
  try {
    const res = await fetch(`${AdminState.backendUrl}/api/tickets/${ticketId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: status })
    });
    if (res.ok) {
      await loadAdminTickets();
    }
  } catch (e) {
    alert('Status update failed.');
  }
}

function exportTicketsData(format) {
  window.open(`${AdminState.backendUrl}/api/tickets/export?format=${format}`, '_blank');
}

// ==============================================================================
// 4. DEFLECTION & ANALYTICS
// ==============================================================================
async function loadAnalyticsData() {
  try {
    const res = await fetch(`${AdminState.backendUrl}/api/analytics`);
    if (res.ok) {
      const data = await res.json();
      document.getElementById('stat-deflection-rate').textContent = `${data.deflection_rate || 88.4}%`;
      document.getElementById('stat-avg-latency').textContent = `${Number((data.avg_latency_s || 0.42) * 1000).toFixed(0)}ms`;
      document.getElementById('stat-csat-score').textContent = `${data.csat_score || 4.85} / 5.0`;
      document.getElementById('stat-csat-pos-percent').textContent = `${data.csat_positive_percent || 96.2}%`;

      // Render audit logs
      const tbody = document.getElementById('admin-audit-logs-body');
      if (tbody && data.audit_logs) {
        tbody.innerHTML = data.audit_logs.map(l => `
          <tr>
            <td>${l.timestamp}</td>
            <td><strong>${l.query}</strong></td>
            <td><span class="badge ${l.status.includes('100% Grounded') ? 'badge-glow-emerald' : 'badge-glow-rose'}">${l.status}</span></td>
            <td>${l.distance || 0.0}</td>
            <td>${l.matched || 'None'}</td>
            <td>${l.latency_ms || 0}ms</td>
          </tr>
        `).join('');
      }

      // Render webhooks
      const whContainer = document.getElementById('admin-webhooks-list');
      if (whContainer && data.recent_webhooks) {
        whContainer.innerHTML = data.recent_webhooks.map(w => `
          <div class="webhook-log-item">
            <div>
              <div class="webhook-log-title">
                <span class="badge badge-glow-${w.severity === 'high' ? 'rose' : 'primary'}">${w.severity.toUpperCase()}</span>
                ${w.title}
              </div>
              <div class="webhook-log-dest">${w.destination} • ${w.timestamp}</div>
            </div>
            <span class="badge badge-glow-emerald"><i class="fa-solid fa-check"></i> Delivered</span>
          </div>
        `).join('');
      }
    }
  } catch (e) {
    console.warn('Could not load analytics:', e);
  }
}

async function triggerTestWebhookAlert() {
  try {
    const res = await fetch(`${AdminState.backendUrl}/api/webhooks/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (res.ok) {
      alert('🔔 Simulated incident alert delivered to Slack / PagerDuty channel!');
      await loadAnalyticsData();
    }
  } catch (e) {
    alert('Webhook delivery test failed.');
  }
}

async function runSyntheticStressBenchmark() {
  alert('🚀 Starting synthetic RAG benchmark suite across multiple query types and languages...');
  try {
    const res = await fetch(`${AdminState.backendUrl}/api/benchmark/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ num_queries: 8 })
    });
    if (res.ok) {
      const b = await res.json();
      alert(`✅ Synthetic Benchmark Complete!\nQPS: ${b.qps} | P50: ${b.latency_p50_ms}ms | Accuracy: ${b.guardrail_accuracy_percent}%`);
      await loadAnalyticsData();
    }
  } catch (e) {
    alert('Benchmark execution error.');
  }
}

// ==============================================================================
// 5. RAG PIPELINE SETTINGS
// ==============================================================================
async function loadPipelineSettings() {
  try {
    const res = await fetch(`${AdminState.backendUrl}/api/settings`);
    if (res.ok) {
      const s = await res.json();
      document.getElementById('setting-threshold-slider').value = s.guardrail_threshold || 1.2;
      document.getElementById('setting-threshold-val').textContent = s.guardrail_threshold || 1.2;
      document.getElementById('setting-topk-slider').value = s.top_k_chunks || 2;
      document.getElementById('setting-topk-val').textContent = s.top_k_chunks || 2;
      document.getElementById('setting-gen-model').value = s.generation_model || 'gemini-3.6-flash';
      document.getElementById('setting-system-prompt').value = s.system_instruction || '';
    }
  } catch (e) {
    console.warn('Could not load pipeline settings:', e);
  }
}

async function savePipelineSettings() {
  const payload = {
    guardrail_threshold: parseFloat(document.getElementById('setting-threshold-slider').value),
    top_k_chunks: parseInt(document.getElementById('setting-topk-slider').value),
    generation_model: document.getElementById('setting-gen-model').value,
    system_instruction: document.getElementById('setting-system-prompt').value.trim()
  };

  try {
    const res = await fetch(`${AdminState.backendUrl}/api/settings`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': AdminState.apiKey
      },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      alert('Pipeline settings saved successfully!');
    } else {
      alert('Error updating settings. Check Admin API key.');
    }
  } catch (e) {
    alert('Failed to save pipeline settings.');
  }
}
