/* ==========================================================================
   OMNIDESK AI - LANDING PAGE INTERACTIVE ENGINE
   ========================================================================== */

// Toast Helper
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
  }, 4000);
}

// 1. Navbar Sticky & Scroll Effects
window.addEventListener('scroll', () => {
  const navbar = document.getElementById('navbar');
  if (!navbar) return;
  if (window.scrollY > 40) {
    navbar.classList.add('scrolled');
  } else {
    navbar.classList.remove('scrolled');
  }
});

// Mobile menu toggle
const mobileToggleBtn = document.getElementById('mobile-toggle-btn');
const navMenu = document.getElementById('nav-menu');
if (mobileToggleBtn && navMenu) {
  mobileToggleBtn.addEventListener('click', () => {
    const isVisible = navMenu.style.display === 'flex';
    navMenu.style.display = isVisible ? 'none' : 'flex';
    navMenu.style.flexDirection = 'column';
    navMenu.style.position = 'absolute';
    navMenu.style.top = '100%';
    navMenu.style.left = '0';
    navMenu.style.width = '100%';
    navMenu.style.background = 'rgba(11, 15, 25, 0.98)';
    navMenu.style.padding = '1.5rem';
    navMenu.style.borderBottom = '1px solid rgba(255,255,255,0.1)';
  });
}

// 2. Animated RAG Pipeline Node Cycling
let currentStep = 0;
const pipelineNodes = ['node-ingest', 'node-embed', 'node-retrieve', 'node-synthesis'];
function cyclePipelineHighlight() {
  pipelineNodes.forEach((nodeId, idx) => {
    const el = document.getElementById(nodeId);
    if (el) {
      if (idx === currentStep) {
        el.classList.add('active-step');
      } else {
        el.classList.remove('active-step');
      }
    }
  });
  currentStep = (currentStep + 1) % pipelineNodes.length;
}
setInterval(cyclePipelineHighlight, 2400);

// 3. Interactive ROI Calculator Logic
function updateRoiCalc() {
  const ticketsSlider = document.getElementById('slider-tickets');
  const costSlider = document.getElementById('slider-cost');
  const deflectionSlider = document.getElementById('slider-deflection');

  if (!ticketsSlider || !costSlider || !deflectionSlider) return;

  const tickets = parseInt(ticketsSlider.value, 10);
  const costPerTicket = parseFloat(costSlider.value);
  const deflectionRate = parseInt(deflectionSlider.value, 10) / 100;

  // Update slider labels
  document.getElementById('val-tickets').textContent = tickets.toLocaleString() + ' / mo';
  document.getElementById('val-cost').textContent = '$' + costPerTicket.toFixed(2);
  document.getElementById('val-deflection').textContent = Math.round(deflectionRate * 100) + '%';

  // Calculations
  const deflectedTickets = Math.round(tickets * deflectionRate);
  const monthlySavings = deflectedTickets * costPerTicket;
  const annualSavings = Math.round(monthlySavings * 12);
  const agentHoursSaved = Math.round((deflectedTickets * 10) / 60); // 10 mins per ticket avg

  // Render animated or formatted values
  document.getElementById('roi-annual-savings').textContent = '$' + annualSavings.toLocaleString();
  document.getElementById('roi-monthly-tickets-saved').textContent = deflectedTickets.toLocaleString();
  document.getElementById('roi-agent-hours-saved').textContent = agentHoursSaved.toLocaleString() + ' hrs';
}

// Initialize ROI calc
updateRoiCalc();

// 4. Pricing Cycle Toggle (Monthly vs Annual with 20% discount)
function togglePricingCycle() {
  const isAnnual = document.getElementById('pricing-toggle').checked;
  const labelMonthly = document.getElementById('label-monthly');
  const labelAnnual = document.getElementById('label-annual');

  const priceStarter = document.getElementById('price-starter');
  const priceGrowth = document.getElementById('price-growth');
  const priceEnterprise = document.getElementById('price-enterprise');

  const periodStarter = document.getElementById('period-starter');
  const periodGrowth = document.getElementById('period-growth');
  const periodEnterprise = document.getElementById('period-enterprise');

  if (isAnnual) {
    labelMonthly.style.color = 'var(--text-muted)';
    labelAnnual.style.color = 'var(--text-main)';
    // 20% discount applied
    priceStarter.textContent = '39';
    priceGrowth.textContent = '159';
    priceEnterprise.textContent = '479';
    periodStarter.textContent = '/mo (billed annually)';
    periodGrowth.textContent = '/mo (billed annually)';
    periodEnterprise.textContent = '/mo (billed annually)';
  } else {
    labelMonthly.style.color = 'var(--text-main)';
    labelAnnual.style.color = 'var(--text-muted)';
    priceStarter.textContent = '49';
    priceGrowth.textContent = '199';
    priceEnterprise.textContent = '599';
    periodStarter.textContent = '/month';
    periodGrowth.textContent = '/month';
    periodEnterprise.textContent = '/month';
  }
}

// 5. FAQ Accordion Interaction
document.querySelectorAll('.faq-question').forEach((button) => {
  button.addEventListener('click', () => {
    const parentItem = button.parentElement;
    const isActive = parentItem.classList.contains('active');

    // Close all other items
    document.querySelectorAll('.faq-item').forEach((item) => {
      item.classList.remove('active');
    });

    if (!isActive) {
      parentItem.classList.add('active');
    }
  });
});

// 6. Interactive Demo Chat Simulator
const demoKnowledgeFallback = [
  {
    keywords: ['return', 'refund', '30-day', 'exchange', 'restocking'],
    answer: "You can return eligible items within 30 calendar days of delivery for a full refund. Items must be unused and in original packaging. Open-box electronics carry a 15% restocking fee. Standard return shipping is free in the USA and Canada.",
    source: "Section 1: Return and Exchange Policy (company_faq.txt)"
  },
  {
    keywords: ['ship', 'international', 'duties', 'canada', 'dhl', 'delivery', 'overnight'],
    answer: "We ship domestically (Standard 3-5 days is free over $50, Expedited 2-Day is $14.99) and internationally to 85+ countries via DHL Express (7-14 days). All international orders are shipped DDP (Delivered Duty Paid) with all taxes and customs collected at checkout.",
    source: "Section 2: Shipping and Delivery Policy (company_faq.txt)"
  },
  {
    keywords: ['warranty', 'defect', 'repair', 'broken', 'care'],
    answer: "All hardware products include a 1-Year Limited Manufacturer Warranty covering defects in materials and craftsmanship. Standard warranty does not cover accidental drops or water damage. To submit a claim, provide your serial number and photos via support@company.com.",
    source: "Section 4: Warranty and Repair Coverage (company_faq.txt)"
  },
  {
    keywords: ['cancel', 'modify', 'change address', 'order'],
    answer: "Orders can be cancelled or modified within a strict 60-minute window after placement. After 60 minutes, orders enter warehouse picking and can only be returned upon delivery.",
    source: "Section 3: Order Modification & Cancellation (company_faq.txt)"
  }
];

function sendDemoQuery(text) {
  const input = document.getElementById('demo-user-input');
  if (input) input.value = text;
  handleDemoSubmit();
}

function handleDemoKeyPress(e) {
  if (e.key === 'Enter') {
    handleDemoSubmit();
  }
}

async function handleDemoSubmit() {
  const input = document.getElementById('demo-user-input');
  const chatMessages = document.getElementById('demo-chat-messages');
  if (!input || !chatMessages) return;

  const userText = input.value.trim();
  if (!userText) return;

  // Add User Message
  const userBubble = document.createElement('div');
  userBubble.className = 'chat-bubble user';
  userBubble.textContent = userText;
  chatMessages.appendChild(userBubble);
  input.value = '';
  chatMessages.scrollTop = chatMessages.scrollHeight;

  // Add Loading Bubble
  const loadingBubble = document.createElement('div');
  loadingBubble.className = 'chat-bubble bot';
  loadingBubble.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Checking verified store policies in ChromaDB...`;
  chatMessages.appendChild(loadingBubble);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  // Try live backend first
  let answered = false;
  try {
    const res = await fetch('http://localhost:8000/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: userText }),
      signal: AbortSignal.timeout(3000)
    });

    if (res.ok) {
      const data = await res.json();
      renderBotDemoResponse(loadingBubble, data.answer, data.sources && data.sources.length > 0 ? data.sources[0] : null);
      answered = true;
    }
  } catch (err) {
    // Backend offline or timeout -> proceed to smart grounded fallback
  }

  if (!answered) {
    setTimeout(() => {
      let matched = null;
      const lowerQuery = userText.toLowerCase();

      for (const item of demoKnowledgeFallback) {
        if (item.keywords.some(k => lowerQuery.includes(k))) {
          matched = item;
          break;
        }
      }

      if (matched) {
        renderBotDemoResponse(loadingBubble, matched.answer, matched.source);
      } else {
        renderBotDemoResponse(
          loadingBubble,
          "I am sorry, but our verified documentation does not cover that specific inquiry. Please contact our human support team at support@company.com.",
          null
        );
      }
    }, 450);
  }
}

function renderBotDemoResponse(bubbleEl, answerText, source) {
  let sourceHtml = '';
  if (source) {
    sourceHtml = `
      <div class="verified-source-tag">
        <i class="fa-solid fa-shield-check"></i>
        <span><strong>Verified Source:</strong> ${source.length > 90 ? source.substring(0, 90) + '...' : source}</span>
      </div>
    `;
  }

  bubbleEl.innerHTML = `
    <div>${answerText}</div>
    ${sourceHtml}
  `;

  const chatMessages = document.getElementById('demo-chat-messages');
  if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 7. Modal Control
function openDemoModal(tier = '') {
  const modal = document.getElementById('demo-modal');
  const title = document.getElementById('modal-title');
  if (tier && title) {
    title.textContent = `Get Started with ${tier}`;
  }
  if (modal) modal.classList.add('open');
}

function closeDemoModal() {
  const modal = document.getElementById('demo-modal');
  if (modal) modal.classList.remove('open');
}

function handleLeadSubmit(e) {
  e.preventDefault();
  const name = document.getElementById('lead-name').value;
  closeDemoModal();
  showToast(`Thank you, ${name}! Your sandbox credentials have been generated.`, 'success');
  e.target.reset();
}
