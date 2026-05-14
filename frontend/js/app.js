const API_BASE = 'http://localhost:8000/api';

// ── State ──────────────────────────────────────────────
let sessionId       = null;
let isLoading       = false;
let lastStory       = null; // refined_story mais recente, não exibido até o usuário pedir

// ── DOM refs ───────────────────────────────────────────
const welcomeScreen = document.getElementById('welcomeScreen');
const messagesList  = document.getElementById('messagesList');
const messageInput  = document.getElementById('messageInput');
const sendButton    = document.getElementById('sendButton');
const statusDot     = document.getElementById('statusDot');
const statusLabel   = document.getElementById('statusLabel');

// ── Status indicator ───────────────────────────────────
function setStatus(state) {
  statusDot.className = 'status-dot ' + (state === 'online' ? 'online' : state === 'error' ? 'error' : '');
  statusLabel.textContent =
    state === 'online'  ? 'Online' :
    state === 'error'   ? 'Erro de conexão' :
    state === 'loading' ? 'Aguardando…' : 'Conectando…';
}

async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    setStatus(res.ok ? 'online' : 'error');
  } catch {
    setStatus('error');
  }
}

// ── Auto-resize textarea ───────────────────────────────
function resizeTextarea() {
  messageInput.style.height = 'auto';
  messageInput.style.height = Math.min(messageInput.scrollHeight, 160) + 'px';
}

messageInput.addEventListener('input', resizeTextarea);

messageInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
});

sendButton.addEventListener('click', handleSend);

// ── Example cards ──────────────────────────────────────
document.querySelectorAll('.example-card').forEach((card) => {
  card.addEventListener('click', () => {
    startSession(card.dataset.title, card.dataset.description);
  });
});

// ── Message rendering ──────────────────────────────────
function appendUserMessage(text) {
  hideWelcome();
  const el = document.createElement('div');
  el.className = 'message user';
  el.innerHTML = `
    <span class="message-label">Você</span>
    <div class="message-bubble">${escapeHtml(text)}</div>
  `;
  messagesList.appendChild(el);
  scrollToBottom();
}

function appendAgentMessage(text, story) {
  // Remove botão anterior de "Gerar artefato" se existir
  const prev = document.getElementById('artifact-trigger');
  if (prev) prev.remove();

  const el = document.createElement('div');
  el.className = 'message agent';
  el.innerHTML = `
    <span class="message-label">PM Agent</span>
    <div class="message-bubble">${escapeHtml(text)}</div>
  `;
  messagesList.appendChild(el);

  // Botão para revelar o artefato, se tiver story
  if (story) {
    const trigger = document.createElement('div');
    trigger.id = 'artifact-trigger';
    trigger.className = 'artifact-trigger-row';
    trigger.innerHTML = `
      <button class="btn btn-artifact" id="artifactBtn">
        <span class="btn-icon">◈</span> Gerar artefato
      </button>
    `;
    messagesList.appendChild(trigger);

    document.getElementById('artifactBtn').addEventListener('click', () => {
      trigger.remove();
      renderStoryCard(story, sessionId + '-' + Date.now());
    });
  }

  scrollToBottom();
}

function appendInterviewMessage(question, suggestion) {
  const prev = document.getElementById('artifact-trigger');
  if (prev) prev.remove();

  const el = document.createElement('div');
  el.className = 'message agent';
  el.innerHTML = `
    <span class="message-label">PM Agent</span>
    <div class="message-bubble">
      ${escapeHtml(question)}
      ${suggestion ? `<div class="interview-suggestion">${escapeHtml(suggestion)}</div>` : ''}
    </div>
  `;
  messagesList.appendChild(el);
  scrollToBottom();
}

function renderStoryCard(story, cardId) {
  const spLabel  = story.story_points != null ? `${story.story_points} pts` : '—';
  const frItems  = listItems(story.functional_requirements);
  const brItems  = listItems(story.business_rules);
  const acItems  = listItems(story.acceptance_criteria);
  const depItems = story.dependencies && story.dependencies.length
    ? listItems(story.dependencies)
    : '<li>Nenhuma dependência identificada.</li>';

  const el = document.createElement('div');
  el.className = 'message agent';
  el.innerHTML = `
    <span class="message-label">PM Agent · Artefato</span>
    <div class="story-card" id="card-${cardId}">
      <div class="story-card-header">
        <span class="story-card-title">${escapeHtml(story.title)}</span>
        <span class="story-points-badge">✦ ${spLabel}</span>
      </div>
      <div class="story-card-body">
        <div class="story-section">
          <span class="story-section-label">User Story</span>
          <p class="story-section-text">${escapeHtml(story.user_story)}</p>
        </div>
        <div class="story-section">
          <span class="story-section-label">Requisitos Funcionais</span>
          <ul class="story-list">${frItems}</ul>
        </div>
        <div class="story-section">
          <span class="story-section-label">Regras de Negócio</span>
          <ul class="story-list">${brItems}</ul>
        </div>
        <div class="story-section">
          <span class="story-section-label">Critérios de Aceite</span>
          <ul class="story-list">${acItems}</ul>
        </div>
        <div class="story-section">
          <span class="story-section-label">Dependências</span>
          <ul class="story-list">${depItems}</ul>
        </div>
      </div>
      <div class="story-card-footer" id="footer-${cardId}">
        <button class="btn btn-primary" id="confirm-${cardId}">
          <span class="btn-icon">⬆</span> Criar no Jira
        </button>
        <button class="btn btn-ghost" id="discard-${cardId}">
          <span class="btn-icon">✕</span> Descartar
        </button>
      </div>
    </div>
  `;

  messagesList.appendChild(el);
  scrollToBottom();

  document.getElementById(`confirm-${cardId}`).addEventListener('click', () => confirmSession(cardId));
  document.getElementById(`discard-${cardId}`).addEventListener('click', () => discardSession(cardId));
}

function showTyping() {
  const el = document.createElement('div');
  el.className = 'message agent';
  el.id = 'typing-indicator';
  el.innerHTML = `
    <span class="message-label">PM Agent</span>
    <div class="typing-indicator">
      <div class="typing-dots">
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
      </div>
      <span class="typing-text">Refinando história…</span>
    </div>
  `;
  messagesList.appendChild(el);
  scrollToBottom();
}

function removeTyping() {
  const el = document.getElementById('typing-indicator');
  if (el) el.remove();
}

function appendError(text) {
  const el = document.createElement('div');
  el.className = 'message agent';
  el.innerHTML = `
    <span class="message-label">PM Agent</span>
    <div class="message-bubble" style="color: var(--danger); border-color: rgba(239,68,68,0.2);">${escapeHtml(text)}</div>
  `;
  messagesList.appendChild(el);
  scrollToBottom();
}

// ── API calls ──────────────────────────────────────────
async function startSession(title, description) {
  if (isLoading) return;
  setLoading(true);
  hideWelcome();
  appendUserMessage(`${title}\n\n${description}`);
  showTyping();

  try {
    const res = await fetch(`${API_BASE}/stories/session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, description }),
    });

    if (!res.ok) throw new Error(`Erro ${res.status}: ${await res.text()}`);
    const data = await res.json();

    removeTyping();
    sessionId = data.session_id;

    if (data.phase === 'interviewing') {
      lastStory = null;
      appendInterviewMessage(data.question, data.suggestion);
    } else {
      lastStory = data.refined_story || null;
      appendAgentMessage(data.message, lastStory);
    }
    setStatus('online');
  } catch (err) {
    removeTyping();
    appendError(`Não foi possível iniciar a sessão. ${err.message}`);
    setStatus('error');
    showWelcome();
    sessionId = null;
    lastStory = null;
  } finally {
    setLoading(false);
  }
}

async function continueSession(message) {
  if (!sessionId || isLoading) return;
  setLoading(true);
  appendUserMessage(message);

  // Remove botão de artefato anterior enquanto processa
  const prev = document.getElementById('artifact-trigger');
  if (prev) prev.remove();

  showTyping();

  try {
    const res = await fetch(`${API_BASE}/stories/session/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });

    if (!res.ok) throw new Error(`Erro ${res.status}: ${await res.text()}`);
    const data = await res.json();

    removeTyping();

    if (data.phase === 'interviewing') {
      appendInterviewMessage(data.question, data.suggestion);
    } else {
      lastStory = data.refined_story || lastStory;
      appendAgentMessage(data.message, lastStory);
    }
    setStatus('online');
  } catch (err) {
    removeTyping();
    appendError(`Erro na conversa. ${err.message}`);
    setStatus('error');
  } finally {
    setLoading(false);
  }
}

async function confirmSession(cardId) {
  const confirmBtn = document.getElementById(`confirm-${cardId}`);
  const discardBtn = document.getElementById(`discard-${cardId}`);
  if (!confirmBtn || confirmBtn.disabled) return;

  confirmBtn.disabled = true;
  discardBtn.disabled = true;
  confirmBtn.innerHTML = '<span class="btn-icon">⟳</span> Criando…';

  try {
    const res = await fetch(`${API_BASE}/stories/session/${sessionId}/confirm`, {
      method: 'POST',
    });

    if (!res.ok) throw new Error(`Erro ${res.status}: ${await res.text()}`);
    const data = await res.json();

    const footer = document.getElementById(`footer-${cardId}`);
    if (footer) {
      const ticket = data.jira_ticket;
      const isMock = ticket.url === 'http://mock/browse/MOCK-0';
      footer.innerHTML = `
        <span class="btn btn-success">
          <span class="btn-icon">✓</span> Criado: ${escapeHtml(ticket.ticket_key)}
        </span>
        ${!isMock
          ? `<a href="${ticket.url}" target="_blank" class="btn btn-ghost" style="text-decoration:none;">Abrir no Jira ↗</a>`
          : '<span class="btn btn-ghost" style="cursor:default;opacity:0.5;">Jira desabilitado</span>'
        }
      `;
    }

    appendAgentMessage('Ticket criado com sucesso! Podemos refinar outra história?', null);
    sessionId = null;
    lastStory = null;
  } catch (err) {
    appendError(`Falha ao criar ticket. ${err.message}`);
    if (confirmBtn) {
      confirmBtn.disabled = false;
      confirmBtn.innerHTML = '<span class="btn-icon">⬆</span> Criar no Jira';
    }
    if (discardBtn) discardBtn.disabled = false;
  }
}

async function discardSession(cardId) {
  const confirmBtn = document.getElementById(`confirm-${cardId}`);
  const discardBtn = document.getElementById(`discard-${cardId}`);
  if (!discardBtn || discardBtn.disabled) return;

  confirmBtn.disabled = true;
  discardBtn.disabled = true;

  try {
    await fetch(`${API_BASE}/stories/session/${sessionId}`, { method: 'DELETE' });
  } catch {
    // best effort
  }

  const footer = document.getElementById(`footer-${cardId}`);
  if (footer) {
    footer.innerHTML = `<span class="btn btn-ghost" style="cursor:default;opacity:0.5;">✕ Descartado</span>`;
  }

  appendAgentMessage('Sessão descartada. Podemos começar uma nova história?', null);
  sessionId = null;
  lastStory = null;
}

// ── Send handler ───────────────────────────────────────
function handleSend() {
  const text = messageInput.value.trim();
  if (!text || isLoading) return;

  messageInput.value = '';
  resizeTextarea();

  if (!sessionId) {
    const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
    const title       = lines[0];
    const description = lines.slice(1).join('\n') || title;
    startSession(title, description);
  } else {
    continueSession(text);
  }
}

// ── Helpers ────────────────────────────────────────────
function hideWelcome() {
  if (welcomeScreen) welcomeScreen.style.display = 'none';
}

function showWelcome() {
  if (welcomeScreen && messagesList.children.length === 0) {
    welcomeScreen.style.display = 'flex';
  }
}

function setLoading(state) {
  isLoading = state;
  sendButton.disabled = state;
  messageInput.disabled = state;
  setStatus(state ? 'loading' : 'online');
}

function scrollToBottom() {
  const container = document.getElementById('chatContainer');
  requestAnimationFrame(() => { container.scrollTop = container.scrollHeight; });
}

function listItems(arr) {
  if (!arr || arr.length === 0) return '<li>—</li>';
  return arr.map(item => `<li>${escapeHtml(item)}</li>`).join('');
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
    .replace(/\n/g, '<br>');
}

// ── Init ───────────────────────────────────────────────
checkHealth();
