
const PROTRUDING_SNIPPETS = {
  'quickstart': [
    { prompt: '$', text: 'git clone https://github.com/MaxMasAI/agentic-web.git' },
    { prompt: '$', text: 'cd agentic-web && run.bat' }
  ],
  'install_source': [
    { prompt: '$', text: 'git clone https://github.com/MaxMasAI/agentic-web.git' },
    { prompt: '$', text: 'cd agentic-web' },
    { prompt: '$', text: 'install.bat' }
  ],
  'auto_reload': [
    { prompt: '$', text: 'dev.bat' }
  ],
  'unix': [
    { prompt: '$', text: 'git clone https://github.com/MaxMasAI/agentic-web.git' },
    { prompt: '$', text: 'cd agentic-web && python3 -m venv .venv && source .venv/bin/activate' },
    { prompt: '$', text: 'pip install -r requirements.txt && python3 app.py' }
  ],
  'docker': [
    { prompt: '$', text: 'docker compose up --build' }
  ]
};

let activeProtrudingKey = 'quickstart';

function switchProtrudingTab(tabKey, btn) {
  activeProtrudingKey = tabKey;
  document.querySelectorAll('.protruding-tab-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');

  const body = document.getElementById('protrudingCodeBody');
  if (!body) return;

  const lines = PROTRUDING_SNIPPETS[tabKey] || PROTRUDING_SNIPPETS['quickstart'];
  body.innerHTML = lines.map(l => `
        <div class="cmd-line">
          <span class="cmd-prompt">${l.prompt || '$'}</span>
          <span class="cmd-text">${l.text}</span>
        </div>
      `).join('');
}

function copyProtrudingSnippet() {
  const lines = PROTRUDING_SNIPPETS[activeProtrudingKey] || PROTRUDING_SNIPPETS['quickstart'];
  const textToCopy = lines.map(l => l.text).join('\n');
  navigator.clipboard.writeText(textToCopy).then(() => {
    const btn = document.getElementById('protrudingCopyBtn');
    const text = document.getElementById('protrudingCopyText');
    if (btn && text) {
      btn.classList.add('copied');
      text.innerText = 'Copied!';
      setTimeout(() => {
        btn.classList.remove('copied');
        text.innerText = 'Copy';
      }, 2000);
    }
  });
}

const CODE_SNIPPETS = {
  'tab-win': `# Clone and run on Windows:\ngit clone https://github.com/MaxMasAI/agentic-web.git\ncd agentic-web\n\n# Automatic 1-Click Setup:\ninstall.bat\n\n# Launch Full Suite (Voice Server + Desktop GUI):\nrun.bat`,
  'tab-dev': `# ⚡ Live Auto-Reload Dev Engine (Restarts on Ctrl+S):\ndev.bat\n\n# Or launch with custom debounce settling delay:\npython dev.py --delay 1.5`,
  'tab-unix': `# Clone and run on macOS / Linux:\ngit clone https://github.com/MaxMasAI/agentic-web.git\ncd agentic-web\n\n# Create isolated virtual environment:\npython3 -m venv .venv\nsource .venv/bin/activate\npip install -r requirements.txt\n\n# Launch Desktop GUI:\npython3 app.py`,
  'tab-docker': `# Run containerized execution sandbox via Docker:\ndocker compose up --build`,
  'tab-exe': `# Build single-file standalone Windows .exe without Python dependencies:\npython STD_EXE.py\n\n# Binary output saved to:\n# dist/agentic-web/agentic-web.exe`
};

function switchCodeTab(tabKey) {
  document.querySelectorAll('.code-tab-btn').forEach(btn => btn.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('codeBlock').innerText = CODE_SNIPPETS[tabKey];
}

function copySnippet() {
  const code = document.getElementById('codeBlock').innerText;
  navigator.clipboard.writeText(code).then(() => {
    const btn = document.querySelector('.btn-copy');
    btn.innerText = '✅ Copied!';
    setTimeout(() => { btn.innerText = '📋 Copy'; }, 2000);
  });
}

function validateLiveSchema() {
  const val = document.getElementById('schemaInput').value.trim();
  const feedback = document.getElementById('schemaFeedback');
  try {
    const parsed = JSON.parse(val);
    if (!parsed.id || !parsed.name || !parsed.role) {
      feedback.innerText = "⚠️ Missing required fields: 'id', 'name', or 'role'.";
      feedback.style.color = "#fbbf24";
    } else {
      feedback.innerText = `✅ Valid Schema: ${parsed.name} (${parsed.id}) · ${parsed.is_leader ? '👑 Master Leader' : '🤖 Specialist'}`;
      feedback.style.color = "#34d399";
    }
  } catch (e) {
    feedback.innerText = "❌ JSON Syntax Error: " + e.message;
    feedback.style.color = "#ef4444";
  }
}

/* ── Base URL & Asset Helper Configuration ── */
const IMAGE_BASE_URL = '../images/';

function getAssetPath(filename) {
  if (!filename) return '';
  if (filename.startsWith('http://') || filename.startsWith('https://')) return filename;
  const clean = filename.replace(/^(\.\.\/images\/|images\/)/, '');
  return `${IMAGE_BASE_URL}${clean}`;
}

/* ── Gallery & Lightbox Screen Viewer Logic ── */
const GALLERY_ITEMS = [
  { src: `${IMAGE_BASE_URL}000_web_agent.gif`, title: 'Live Web Agent Execution', tag: '#000 Live Demo', desc: 'Real-time animated Chrome DevTools Protocol (CDP) autonomous browser task automation stream.' },
  { src: `${IMAGE_BASE_URL}000_web_agent.png`, title: 'Autonomous Web Agent HUD', tag: '#000 Web Agent', desc: 'Browser automation HUD overlay with synchronized live agent cursors and step execution.' },
  { src: `${IMAGE_BASE_URL}00_Agentic_Web_Full_Overview.png`, title: 'Full Platform Overview', tag: '#00 Overview', desc: 'Unified multi-agent operating interface with active leader telemetry and system status.' },
  { src: `${IMAGE_BASE_URL}01_Mission_Control_Dashboard.png`, title: 'Mission Control Dashboard', tag: '#01 Mission Control', desc: 'Real-time AI squad orchestration, agent state grid, and parallel task execution monitoring.' },
  { src: `${IMAGE_BASE_URL}02_Task_Dispatch_Console.png`, title: 'Task Dispatch Console', tag: '#02 Task Dispatch', desc: 'Prompt input, agent assignment, automated task routing, and asynchronous worker execution.' },
  { src: `${IMAGE_BASE_URL}03_Multi_Agent_Squads.png`, title: 'Multi-Agent Squad Matrix', tag: '#03 Squads', desc: 'Parallel specialist agent assignment with role definitions and real-time activity indicators.' },
  { src: `${IMAGE_BASE_URL}04_Mission_History_Archives.png`, title: 'Mission History Archives', tag: '#04 Archives', desc: 'Persisted execution logs, prompt-response history, and token usage audit trails in SQLite WAL.' },
  { src: `${IMAGE_BASE_URL}05_Multi_Model_AI_Chat.png`, title: 'Multi-Model AI Chat', tag: '#05 Chat', desc: 'Synchronized conversational workspace allowing side-by-side model query benchmarking.' },
  { src: `${IMAGE_BASE_URL}06_Document_Knowledge_Chat.png`, title: 'Document Knowledge Chat', tag: '#06 Knowledge', desc: 'Vector semantic document retrieval and localized context-augmented generation.' },
  { src: `${IMAGE_BASE_URL}07_Deep_Research_Studio.png`, title: 'Deep Research Studio', tag: '#07 Research', desc: 'Autonomous recursive web search, source citation verification, and report synthesis studio.' },
  { src: `${IMAGE_BASE_URL}08_Media_Studio.png`, title: 'Media & Asset Studio', tag: '#08 Media', desc: 'Visual asset generation, image synthesis, and multi-modal creative workspace.' },
  { src: `${IMAGE_BASE_URL}09_Inbuilt_VS_Code_Monaco_Studio.png`, title: 'Inbuilt Monaco Studio', tag: '#09 Monaco IDE', desc: 'Native VS Code Monaco editor with syntax highlighting, IntelliSense, and live preview rendering.' },
  { src: `${IMAGE_BASE_URL}10_Infinite_Agent_Canvas_IDE.png`, title: 'Infinite Agent Canvas IDE', tag: '#10 Canvas DAG', desc: 'Visual node graph canvas with custom wires, dependency routing, and parallel task DAGs.' },
  { src: `${IMAGE_BASE_URL}11_Agent_Playground_Arena.png`, title: 'Agent Playground Arena', tag: '#11 Playground', desc: 'Interactive testing arena for prompt engineering, schema verification, and latency benchmarks.' },
  { src: `${IMAGE_BASE_URL}12_Custom_Agent_Builder.png`, title: 'Custom Agent Builder', tag: '#12 Builder', desc: 'Modal dialog for custom models, Ollama endpoints, and Master Leader promotion.' },
  { src: `${IMAGE_BASE_URL}13_AI_Painter_Studio.png`, title: 'AI Painter Studio', tag: '#13 Painter', desc: 'Canvas sketching and generative AI artwork synthesis environment.' },
  { src: `${IMAGE_BASE_URL}14_Scratchpad_Notepad.png`, title: 'Scratchpad Notepad', tag: '#14 Scratchpad', desc: 'Persistent floating note-taking drawer and live scratch text editor.' },
  { src: `${IMAGE_BASE_URL}15_Automated_Job_Scheduler.png`, title: 'Automated Job Scheduler', tag: '#15 Scheduler', desc: 'Background cron task manager and recurring multi-agent workflow automation.' },
  { src: `${IMAGE_BASE_URL}16_MCP_Server_Hub.png`, title: 'MCP Server Hub', tag: '#16 MCP Tools', desc: 'Model Context Protocol tool registry with Senior Engineering Addy Osmani skills.' },
  { src: `${IMAGE_BASE_URL}17_Semantic_Neural_Memory.png`, title: 'Semantic Neural Memory', tag: '#17 Vector Memory', desc: 'Long-term memory store with sqlite-vec embeddings and session recall.' },
  { src: `${IMAGE_BASE_URL}18_Project_File_Explorer.png`, title: 'Project File Explorer', tag: '#18 Explorer', desc: 'Workspace directory tree navigation, code inspection, and file editing.' },
  { src: `${IMAGE_BASE_URL}19_System_Settings.png`, title: 'System Settings & Keys', tag: '#19 Settings', desc: 'API key configuration, model endpoint management, and UI theme preferences.' },
  { src: `${IMAGE_BASE_URL}20_Multi_Agent_Browser_HUD_Controls.png`, title: 'Browser HUD Controls', tag: '#20 Browser HUD', desc: 'Live in-browser CDP control overlay with agent cursor tracking and action chips.' },
  { src: `${IMAGE_BASE_URL}21_Live_Agent_Pool_Browser_Monitor.png`, title: 'Agent Pool Browser Monitor', tag: '#21 Pool Monitor', desc: 'Visual worker pool monitoring with live Chrome CDP remote debugging on port 9222.' },
  { src: `${IMAGE_BASE_URL}22_Browser_Automation_Control_Center.png`, title: 'Browser Automation Center', tag: '#22 Automation', desc: 'Playwright headless/headful automation dashboard with DOM tree inspector.' },
  { src: `${IMAGE_BASE_URL}23_web_agent.png`, title: 'Multi-Agent Web Operations HUD', tag: '#23 Web Agent', desc: 'Multi-agent browser automation console with real-time DOM element targeting and task tracing.' },
  { src: `${IMAGE_BASE_URL}24_tokens.png`, title: 'Token Telemetry & Analytics', tag: '#24 1B+ Tokens', desc: 'Real-time token manager with 1.019B+ daily pool tracker and rate limiter dashboard.' }
];

let currentLightboxIndex = 0;

function openLightbox(index) {
  currentLightboxIndex = index;
  const item = GALLERY_ITEMS[index];
  if (!item) return;
  const modal = document.getElementById('imageModal');
  const img = document.getElementById('lightboxImage');
  img.src = item.src;
  document.getElementById('lightboxTitleText').innerText = item.title;
  document.getElementById('lightboxTagText').innerText = item.tag;
  document.getElementById('lightboxDescText').innerText = item.desc;
  document.getElementById('lightboxCounterText').innerText = `${index + 1} / ${GALLERY_ITEMS.length}`;
  modal.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeLightbox() {
  const modal = document.getElementById('imageModal');
  if (modal) modal.classList.remove('active');
  document.body.style.overflow = '';
}

function navLightbox(direction) {
  currentLightboxIndex = (currentLightboxIndex + direction + GALLERY_ITEMS.length) % GALLERY_ITEMS.length;
  openLightbox(currentLightboxIndex);
}

function handleModalBackdropClick(e) {
  if (e.target.id === 'imageModal') {
    closeLightbox();
  }
}

function filterGallery(category, btn) {
  document.querySelectorAll('.gallery-filter-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  document.querySelectorAll('.gallery-card').forEach(card => {
    if (category === 'all' || card.getAttribute('data-category') === category) {
      card.style.display = 'flex';
      // Trigger smooth reveal for newly visible filtered cards
      requestAnimationFrame(() => {
        card.classList.add('in-view');
        const img = card.querySelector('img.gallery-img');
        if (img && (img.complete && img.naturalWidth > 0)) {
          img.classList.add('loaded');
        }
      });
    } else {
      card.style.display = 'none';
      card.classList.remove('in-view');
    }
  });
}

/* ── Viewport Progressive Slow Loading Engine ── */
function initViewportLazyLoading() {
  const observerOptions = {
    root: null,
    rootMargin: '80px 0px 80px 0px',
    threshold: 0.05
  };

  const cardObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const card = entry.target;
        card.classList.add('in-view');
        const img = card.querySelector('img.gallery-img');
        if (img) {
          const targetSrc = img.getAttribute('data-src') || img.src;
          if (targetSrc && img.src !== targetSrc) {
            img.src = targetSrc;
          }
          if (img.complete && img.naturalWidth > 0) {
            setTimeout(() => img.classList.add('loaded'), 80);
          } else {
            img.addEventListener('load', () => {
              setTimeout(() => img.classList.add('loaded'), 80);
            }, { once: true });
          }
        }
        observer.unobserve(card);
      }
    });
  }, observerOptions);

  document.querySelectorAll('.gallery-card').forEach((card, idx) => {
    card.style.transitionDelay = `${(idx % 3) * 0.08}s`;
    cardObserver.observe(card);
  });

  // Hero demo showcase slow viewport progressive load
  const heroImg = document.querySelector('.hero-demo-img');
  if (heroImg) {
    const heroObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          if (heroImg.complete && heroImg.naturalWidth > 0) {
            setTimeout(() => heroImg.classList.add('loaded'), 100);
          } else {
            heroImg.addEventListener('load', () => {
              setTimeout(() => heroImg.classList.add('loaded'), 100);
            }, { once: true });
          }
          observer.unobserve(heroImg);
        }
      });
    }, observerOptions);
    heroObserver.observe(heroImg);
  }
}

/* ── Auto-Hide Sidebar Helpers ── */
function closeSidebarOnNav() {
  const sb = document.getElementById('sidebar');
  if (sb) {
    sb.classList.remove('is-open');
    if (document.activeElement) document.activeElement.blur();
  }
}

function toggleSidebarPin() {
  const sb = document.getElementById('sidebar');
  if (sb) sb.classList.toggle('is-open');
}

function clearSearch() {
  const input = document.getElementById('docSearch');
  input.value = '';
  document.getElementById('searchClearBtn').style.display = 'none';
  filterDocs();
}

function filterDocs() {
  const input = document.getElementById('docSearch');
  const q = input.value.toLowerCase().trim();
  const clearBtn = document.getElementById('searchClearBtn');
  if (clearBtn) clearBtn.style.display = q ? 'block' : 'none';

  // If user is searching, expand sidebar so results are clearly visible
  const sb = document.getElementById('sidebar');
  if (sb && q) sb.classList.add('is-open');

  // Filter main document sections & cards
  document.querySelectorAll('.doc-section, .agent-card, .skill-card, .tier-card, .gallery-card').forEach(el => {
    const txt = el.innerText.toLowerCase();
    el.style.display = txt.includes(q) ? '' : 'none';
  });

  // Filter sidebar TOC links
  document.querySelectorAll('.toc-links li').forEach(li => {
    const txt = li.innerText.toLowerCase();
    li.style.display = txt.includes(q) ? '' : 'none';
  });
}

// Keyboard shortcuts: Lightbox navigation (Arrows, Esc), Search focus (Ctrl+K, '/')
document.addEventListener('keydown', (e) => {
  const modal = document.getElementById('imageModal');
  const isModalActive = modal && modal.classList.contains('active');

  if (isModalActive) {
    if (e.key === 'Escape') {
      closeLightbox();
    } else if (e.key === 'ArrowLeft') {
      navLightbox(-1);
    } else if (e.key === 'ArrowRight') {
      navLightbox(1);
    }
    return;
  }

  if ((e.ctrlKey && e.key.toLowerCase() === 'k') || (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA')) {
    e.preventDefault();
    const searchInput = document.getElementById('docSearch');
    if (searchInput) searchInput.focus();
  } else if (e.key === 'Escape') {
    const searchInput = document.getElementById('docSearch');
    if (document.activeElement === searchInput) {
      if (searchInput.value) {
        clearSearch();
      } else {
        searchInput.blur();
      }
    }
  }
});

// Dynamic Terminal Feed Simulation
const feed = [
  '<span class="t-meta">🌐 [Specialist] Meta AI:</span> Analyzing engagement metrics and viral keywords...',
  '<span class="t-perplexity">🔍 [Specialist] Perplexity AI:</span> Verified real-time API latency benchmarks across 4 clouds.',
  '<span class="t-nvidia">⚡ [Specialist] Nvidia NIM:</span> GPU tensor compute speed benchmarked at 142 tok/s.',
  '<span class="t-leader">👑 [Master Leader] Gemini 2.0:</span> Quality audit passed. Aggregating final deployment package.'
];

let feedIndex = 0;
setInterval(() => {
  if (feedIndex < feed.length) {
    const div = document.createElement('div');
    div.innerHTML = `<span class="t-dim">[${new Date().toTimeString().split(' ')[0]}]</span> ${feed[feedIndex]}`;
    const terminal = document.getElementById('liveTerminal');
    if (terminal) {
      terminal.appendChild(div);
      terminal.scrollTop = terminal.scrollHeight;
    }
    feedIndex++;
  }
}, 3500);

/* ── Live Autonomous Multi-Agent Moving Cursors Engine ── */
const ACTIVE_AGENT_CURSORS = [
  {
    id: 'gemini',
    name: '👑 Google Gemini 2.0',
    role: 'Master Leader',
    color: '#8b5cf6',
    gradient: 'linear-gradient(135deg, #7c3aed, #4c1d95)',
    dotColor: '#c084fc',
    actions: ['👑 Master Squad Leader', '⚡ Dispatching Subtasks', '✨ Reviewing Quality', '🎯 Architecture Planning', '🛡️ Validating Spec'],
    currentX: 180,
    currentY: 340,
    targetX: 180,
    targetY: 340,
    speed: 0.038
  },
  {
    id: 'deepseek',
    name: '🔬 DeepSeek-V3 / R1',
    role: 'Reasoning Specialist',
    color: '#2563eb',
    gradient: 'linear-gradient(135deg, #2563eb, #1e3a8a)',
    dotColor: '#60a5fa',
    actions: ['🔬 Deep Reasoning', '🧪 Writing Unit Tests', '📐 Synthesizing CSS Grid', '⚡ Optimizing Latency', '🧠 Logic Decomposition'],
    currentX: 450,
    currentY: 420,
    targetX: 450,
    targetY: 420,
    speed: 0.044
  },
  {
    id: 'claude',
    name: '🎭 Claude 3.5 Sonnet',
    role: 'Security & Editorial',
    color: '#d97706',
    gradient: 'linear-gradient(135deg, #d97706, #78350f)',
    dotColor: '#fbbf24',
    actions: ['🛡️ Security Audit 0-Day', '🎭 Editorial Refinement', '♿ A11y Compliance', '🧹 Code Simplification', '📦 Modular Design Review'],
    currentX: 720,
    currentY: 600,
    targetX: 720,
    targetY: 600,
    speed: 0.04
  },
  {
    id: 'chatgpt',
    name: '✍️ ChatGPT-4o',
    role: 'Documentation & Copy',
    color: '#059669',
    gradient: 'linear-gradient(135deg, #059669, #064e3b)',
    dotColor: '#34d399',
    actions: ['✍️ Drafting Release Notes', '📄 Packaging Deliverables', '📊 Formatting Markdown', '🎨 Style Consistency', '🌐 API Documentation'],
    currentX: 300,
    currentY: 850,
    targetX: 300,
    targetY: 850,
    speed: 0.042
  },
  {
    id: 'web_agent',
    name: '🖥️ Web-Agent (CDP)',
    role: 'Browser Automation',
    color: '#06b6d4',
    gradient: 'linear-gradient(135deg, #06b6d4, #164e63)',
    dotColor: '#22d3ee',
    actions: ['🖥️ Chrome CDP Port 9222', '🖱️ Inspecting DOM Tree', '📸 Capturing Viewport', '⚡ Executing Playwright', '🔍 Target Element #000'],
    currentX: 850,
    currentY: 350,
    targetX: 850,
    targetY: 350,
    speed: 0.048
  },
  {
    id: 'groq',
    name: '⚡ Groq Llama-3.3',
    role: 'Ultra-Fast Inference',
    color: '#e11d48',
    gradient: 'linear-gradient(135deg, #e11d48, #881337)',
    dotColor: '#fb7185',
    actions: ['⚡ 142 tok/s Inference', '⏱️ Zero Latency Buffer', '🚀 Streaming Response', '📊 Rate Limit Token Check', '🔥 High-Throughput Batch'],
    currentX: 520,
    currentY: 920,
    targetX: 520,
    targetY: 920,
    speed: 0.052
  }
];

let cursorsEnabled = true;
const cursorElements = [];

const LANDMARK_ACTIONS = {
  '#hero': ['👑 Telemetry Stream', '⚡ 1.019B Daily Pool', '🚀 Orchestrating AI Squad', '✨ Live Mission Dispatch'],
  '#kpi': ['📊 1.019B+ Token Audit', '⏱️ 00:00 UTC Reset Check', '📈 10+ Models Synchronized', '🎯 Senior Skills: 24'],
  '#architecture': ['🏗️ 5-Tier Architecture', '🛡️ Tier-3 Sandbox Inspection', '💾 SQLite WAL Store', '🔒 OS Security Guard'],
  '#screens': ['🖼️ Reviewing Screen #000 GIF', '🔍 Zooming Monaco IDE #09', '🎨 Inspecting Canvas DAG #10', '⚡ Browser HUD #20'],
  '#models': ['👑 Dynamic Leader Swap', '🔬 DeepSeek-V3 Reasoning', '🎭 Claude Security Audit', '⚡ Groq 142 tok/s'],
  '#tokens': ['📊 Auditing 1,019,100,000 Quota', '⏱️ Syncing UTC 00:00 Reset', '🛡️ Checking Rate Limiter', '💳 Free Daily Quota Matrix'],
  '#skills': ['🛠️ Executing Addy Osmani Skill', '📜 MCP 9-Field Schema', '🧹 Clean Architecture Audit', '⚡ Refactoring Performance'],
  '#voice': ['🎙️ Streaming Gemini 2.0 Voice', '🔊 WebSocket Bridge 8000', '⚡ Sub-100ms Voice Telemetry', '🎤 Audio In/Out Sync'],
  '#fancyzones': ['📐 Tiling Window Layout', '🪟 Docking PySide6 Canvas', '🖥️ Multi-Monitor Snapping', '📐 4-Zone Matrix'],
  '#canvas': ['🎨 Connecting DAG Node', '⚡ Live Monaco Syntax Check', '📦 Persisting Node State', '🔗 Edge Dependency Link'],
  '#quickstart': ['🚀 Validating pip install -e .', '⚙️ Verifying PySide6 UI', '✨ Running agentic-web', '📋 Testing Setup Spec']
};

function initAgentCursors() {
  let container = document.getElementById('agentCursorsContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'agentCursorsContainer';
    document.body.appendChild(container);
  }

  // Floating Toggle Pill
  const toggleBtn = document.createElement('div');
  toggleBtn.className = 'cursor-toggle-float';
  toggleBtn.id = 'cursorToggleBtn';
  toggleBtn.innerHTML = `<span class="pulse-dot" style="background:#34d399;box-shadow:0 0 10px #34d399;"></span> 🤖 <span id="cursorToggleLabel">6 Live Agents Active</span>`;
  toggleBtn.onclick = toggleAgentCursors;
  document.body.appendChild(toggleBtn);

  // Build DOM elements for each agent
  ACTIVE_AGENT_CURSORS.forEach((agent) => {
    const el = document.createElement('div');
    el.className = 'agent-live-cursor';
    el.id = `agent-cursor-${agent.id}`;

    el.innerHTML = `
          <svg class="agent-cursor-pointer" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M4 2L20 10.5L12.5 13L9 21L4 2Z" fill="${agent.color}" stroke="#ffffff" stroke-width="1.6" stroke-linejoin="round"/>
          </svg>
          <div class="agent-cursor-badge" style="background: ${agent.gradient}; border-color: ${agent.dotColor};">
            <span class="agent-cursor-dot" style="background: ${agent.dotColor}; box-shadow: 0 0 10px ${agent.dotColor};"></span>
            <span>${agent.name}</span>
            <span class="agent-cursor-action" id="action-${agent.id}">${agent.actions[0]}</span>
          </div>
        `;
    container.appendChild(el);
    cursorElements.push({ agent, el });
  });

  // Initial targets & loop
  assignNewAgentTargets();
  requestAnimationFrame(updateAgentCursors);
  setInterval(assignNewAgentTargets, 3200);
}

function toggleAgentCursors() {
  cursorsEnabled = !cursorsEnabled;
  const container = document.getElementById('agentCursorsContainer');
  const label = document.getElementById('cursorToggleLabel');
  if (container) container.style.display = cursorsEnabled ? 'block' : 'none';
  if (label) label.innerText = cursorsEnabled ? '6 Live Agents Active' : 'Agent Cursors Paused';
}

function assignNewAgentTargets() {
  if (!cursorsEnabled) return;

  const docHeight = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
  const docWidth = window.innerWidth;
  const scrollY = window.pageYOffset || document.documentElement.scrollTop;
  const viewHeight = window.innerHeight;

  const landmarkKeys = Object.keys(LANDMARK_ACTIONS);

  ACTIVE_AGENT_CURSORS.forEach((agent, idx) => {
    // 50% of agents prioritize wandering in the current user viewport, 50% explore the whole website
    const targetViewport = idx % 2 === 0;

    if (targetViewport && Math.random() < 0.8) {
      // Wander within or near visible screen area
      agent.targetX = Math.random() * (docWidth - 320) + 40;
      agent.targetY = Math.max(80, Math.min(docHeight - 120, scrollY + Math.random() * (viewHeight * 0.85) + 40));

      const actEl = document.getElementById(`action-${agent.id}`);
      if (actEl) {
        actEl.innerText = agent.actions[Math.floor(Math.random() * agent.actions.length)];
      }
    } else {
      // Wander across whole website sections
      const randKey = landmarkKeys[Math.floor(Math.random() * landmarkKeys.length)];
      const targetEl = document.querySelector(randKey);

      if (targetEl) {
        const rect = targetEl.getBoundingClientRect();
        const elTop = rect.top + scrollY;
        agent.targetX = Math.max(30, Math.min(docWidth - 300, rect.left + Math.random() * Math.max(100, rect.width * 0.8)));
        agent.targetY = Math.max(80, Math.min(docHeight - 120, elTop + Math.random() * Math.max(80, rect.height * 0.8)));

        const actEl = document.getElementById(`action-${agent.id}`);
        if (actEl) {
          const actionsList = LANDMARK_ACTIONS[randKey] || agent.actions;
          actEl.innerText = actionsList[Math.floor(Math.random() * actionsList.length)];
        }
      } else {
        agent.targetX = Math.random() * (docWidth - 320) + 40;
        agent.targetY = Math.random() * (docHeight - 240) + 120;
      }
    }

    // Periodic click ripples on arrival
    if (Math.random() < 0.5) {
      setTimeout(() => {
        if (cursorsEnabled) spawnCursorRipple(agent.currentX, agent.currentY, agent.dotColor);
      }, Math.random() * 1200 + 400);
    }
  });
}

function spawnCursorRipple(x, y, color) {
  const rip = document.createElement('div');
  rip.className = 'agent-click-ripple';
  rip.style.left = `${x}px`;
  rip.style.top = `${y}px`;
  rip.style.borderColor = color;
  rip.style.boxShadow = `0 0 16px ${color}, inset 0 0 8px ${color}`;
  document.body.appendChild(rip);
  setTimeout(() => rip.remove(), 650);
}

function updateAgentCursors() {
  if (cursorsEnabled) {
    cursorElements.forEach(({ agent, el }) => {
      agent.currentX += (agent.targetX - agent.currentX) * agent.speed;
      agent.currentY += (agent.targetY - agent.currentY) * agent.speed;

      el.style.transform = `translate3d(${agent.currentX}px, ${agent.currentY}px, 0)`;
    });
  }
  requestAnimationFrame(updateAgentCursors);
}

// Launch engines on document ready
function initApp() {
  initAgentCursors();
  initViewportLazyLoading();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}
