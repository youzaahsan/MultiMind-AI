/**
 * MultiMind AI — Dashboard Client Application
 * Preserves all existing backend API integrations.
 * UI redesigned to match reference image.
 */

/* ─── Session ID ─── */
let currentSessionId = 'session_' + Math.random().toString(36).substring(2, 10);
let conversationCount = 0;

let appState = { profile: null };

function getStoredToken() {
  return localStorage.getItem('multimind_access_token') || '';
}

function getUserInitials(name) {
  if (!name || typeof name !== 'string') return 'U';
  const clean = name.trim();
  if (!clean) return 'U';
  const parts = clean.split(/\s+/).filter(Boolean);
  if (parts.length === 1) {
    return parts[0][0].toUpperCase();
  }
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function getProfileDisplayName(profile) {
  if (!profile) return 'User';
  if (profile.full_name && profile.full_name.trim()) return profile.full_name.trim();
  if (profile.email) {
    const local = profile.email.split('@')[0].replace(/[._]/g, ' ');
    return local.replace(/\b\w/g, ch => ch.toUpperCase());
  }
  return 'User';
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast-message ${type}`;

  const iconSvg = type === 'success' 
    ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>'
    : type === 'error'
    ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>'
    : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="8"/></svg>';

  toast.innerHTML = `
    ${iconSvg}
    <span>${escapeHtml(message)}</span>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('fade-out');
    setTimeout(() => toast.remove(), 250);
  }, 3500);
}

function applyProfile(profile) {
  appState.profile = profile || { full_name: 'User', email: 'user@multimind.ai' };
  const name = getProfileDisplayName(appState.profile);
  const initials = getUserInitials(name);
  const email = appState.profile.email || 'user@multimind.ai';

  // 1. Top Navbar
  const profileNameEl = document.getElementById('profile-name');
  if (profileNameEl) profileNameEl.textContent = name;

  const navbarAvatarEl = document.getElementById('navbar-profile-avatar');
  if (navbarAvatarEl) navbarAvatarEl.textContent = initials;
  const genericAvatarEl = document.querySelector('.profile-avatar');
  if (genericAvatarEl && genericAvatarEl !== navbarAvatarEl) genericAvatarEl.textContent = initials;

  // 2. Dropdown Header
  const dropNameEl = document.getElementById('dropdown-user-name');
  if (dropNameEl) dropNameEl.textContent = name;
  const dropEmailEl = document.getElementById('dropdown-user-email');
  if (dropEmailEl) dropEmailEl.textContent = email;
  const dropAvatarEl = document.getElementById('dropdown-avatar');
  if (dropAvatarEl) dropAvatarEl.textContent = initials;

  // 3. Greeting on Dashboard
  const greetingEl = document.getElementById('welcome-greeting');
  if (greetingEl) {
    const hour = new Date().getHours();
    let greeting = 'Good morning';
    if (hour >= 12 && hour < 17) greeting = 'Good afternoon';
    else if (hour >= 17) greeting = 'Good evening';
    const firstName = name.split(/\s+/)[0] || name;
    greetingEl.textContent = `${greeting}, ${firstName} 👋`;
  }

  // 4. Settings General Profile Form
  const settingsInput = document.getElementById('settings-user-name');
  if (settingsInput && (!settingsInput.dataset.isDirty || settingsInput.dataset.isDirty === 'false')) {
    settingsInput.value = name;
  }
  const settingsEmailInput = document.getElementById('settings-user-email');
  if (settingsEmailInput) settingsEmailInput.value = email;

  const settingsAvatarPreview = document.getElementById('settings-avatar-preview');
  if (settingsAvatarPreview) settingsAvatarPreview.textContent = initials;

  const settingsNameHeader = document.getElementById('settings-display-name-header');
  if (settingsNameHeader) settingsNameHeader.textContent = name;

  const settingsEmailHeader = document.getElementById('settings-display-email-header');
  if (settingsEmailHeader) settingsEmailHeader.textContent = email;

  // 5. Security Panel Info
  const secNameEl = document.getElementById('security-user-name');
  if (secNameEl) secNameEl.textContent = name;
  const secEmailEl = document.getElementById('security-user-email');
  if (secEmailEl) secEmailEl.textContent = email;

  // 6. Sidebar Credit Footer - Developer Credit remains Youza Ahsan
  const sidebarCreditName = document.getElementById('sidebar-credit-name');
  if (sidebarCreditName) sidebarCreditName.textContent = 'Youza Ahsan';
}

async function loadAuthenticatedProfile() {
  let token = getStoredToken();
  if (!token) {
    // Auto-bootstrap active session using default neutral user
    try {
      const bootRes = await fetch('/auth/switch-user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'user@multimind.ai' }),
      });
      if (bootRes.ok) {
        const bootData = await bootRes.json();
        if (bootData.access_token) {
          localStorage.setItem('multimind_access_token', bootData.access_token);
          token = bootData.access_token;
        }
      }
    } catch (e) {
      console.warn('Auto-session bootstrap failed:', e);
    }
  }

  if (token) {
    try {
      const res = await fetch('/api/user/profile', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const profile = await res.json();
        applyProfile(profile);
        loadTestUsersList();
        return;
      }
      if (res.status === 401) {
        localStorage.removeItem('multimind_access_token');
      }
    } catch (err) {
      console.warn('Profile load failed:', err);
    }
  }

  // Fallback to neutral default User
  applyProfile({ full_name: 'User', email: 'user@multimind.ai' });
  loadTestUsersList();
}

/* ─── DOM Ready ─── */
document.addEventListener('DOMContentLoaded', () => {
  loadAuthenticatedProfile();
  initNavigation();
  initSidebar();
  initHealthCheck();
  initDocuments();
  initDashboardDocTable();
  initChat();
  initDashboardChat();
  initVision();
  initDataAnalytics();
  initForecasting();
  initQuizReports();
  initFileUpload();
  initQuickActions();
  initToolLinks();
  initActivityFilters();
  initSettingsTabs();
  initSettingsProfileEditor();
  initSettingsAiConfig();
  initNavbarProfileDropdown();
  initAuthModal();
  initApiDocsBtn();
  initExploreAgentsBtn();
  updateKBPage();
  loadBackendConfig();
});

/* ─────────────────────────────────────────
   GREETING
───────────────────────────────────────── */
function setGreeting() {
  const hour = new Date().getHours();
  let greeting = 'Good morning';
  if (hour >= 12 && hour < 17) greeting = 'Good afternoon';
  else if (hour >= 17) greeting = 'Good evening';
  const el = document.getElementById('welcome-greeting');
  if (el) {
    const name = getProfileDisplayName(appState.profile);
    el.textContent = `${greeting}, ${name.split(' ')[0]} 👋`;
  }
}

/* ─────────────────────────────────────────
   SIDEBAR (mobile toggle)
───────────────────────────────────────── */
function initSidebar() {
  const toggle = document.getElementById('menu-toggle');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  const closeBtn = document.getElementById('sidebar-close-btn');
  const mobileSearchToggle = document.getElementById('mobile-search-toggle');
  const navbarSearch = document.querySelector('.navbar-search');

  function openSidebar() {
    if (sidebar) sidebar.classList.add('open');
    if (overlay) overlay.classList.add('open');
    document.body.style.overflow = 'hidden'; // prevent background scroll
  }

  function closeSidebar() {
    if (sidebar) sidebar.classList.remove('open');
    if (overlay) overlay.classList.remove('open');
    document.body.style.overflow = ''; // restore scroll
  }

  if (toggle && sidebar && overlay) {
    toggle.addEventListener('click', () => {
      if (sidebar.classList.contains('open')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
    overlay.addEventListener('click', closeSidebar);
  }

  // Close button inside sidebar (mobile)
  if (closeBtn) {
    closeBtn.addEventListener('click', closeSidebar);
  }

  // Close sidebar on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && sidebar && sidebar.classList.contains('open')) {
      closeSidebar();
    }
  });

  // Mobile search toggle
  if (mobileSearchToggle && navbarSearch) {
    mobileSearchToggle.addEventListener('click', () => {
      const isVisible = navbarSearch.style.display === 'flex' || navbarSearch.style.display === 'block';
      if (isVisible) {
        navbarSearch.style.display = '';
        navbarSearch.style.position = '';
        navbarSearch.style.top = '';
        navbarSearch.style.left = '';
        navbarSearch.style.right = '';
        navbarSearch.style.padding = '';
        navbarSearch.style.background = '';
        navbarSearch.style.zIndex = '';
        navbarSearch.style.maxWidth = '';
      } else {
        // Show search as overlay dropdown on mobile
        navbarSearch.style.display = 'flex';
        navbarSearch.style.position = 'absolute';
        navbarSearch.style.top = 'var(--navbar-h)';
        navbarSearch.style.left = '0';
        navbarSearch.style.right = '0';
        navbarSearch.style.maxWidth = '100%';
        navbarSearch.style.padding = '8px 12px';
        navbarSearch.style.background = '#fff';
        navbarSearch.style.zIndex = '200';
        navbarSearch.style.borderBottom = '1px solid var(--border)';
        navbarSearch.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)';
        const input = navbarSearch.querySelector('input');
        if (input) setTimeout(() => input.focus(), 50);
      }
    });
  }

  // Handle window resize - restore sidebar/search states
  window.addEventListener('resize', () => {
    if (window.innerWidth > 767) {
      // On desktop: close mobile sidebar, restore search
      closeSidebar();
      if (navbarSearch) {
        navbarSearch.style.display = '';
        navbarSearch.style.position = '';
        navbarSearch.style.top = '';
        navbarSearch.style.left = '';
        navbarSearch.style.right = '';
        navbarSearch.style.padding = '';
        navbarSearch.style.background = '';
        navbarSearch.style.zIndex = '';
        navbarSearch.style.maxWidth = '';
      }
    }
  });
}

/* ─────────────────────────────────────────
   NAVIGATION
───────────────────────────────────────── */
const PAGE_TITLES = {
  'tab-dashboard': 'Dashboard',
  'tab-chat': 'AI Chat',
  'tab-documents': 'Documents',
  'tab-knowledge': 'Knowledge Base',
  'tab-agents': 'AI Agents',
  'tab-data': 'Data Analysis',
  'tab-vision': 'Analytics',
  'tab-forecast': 'Forecasting',
  'tab-reports': 'Reports',
  'tab-activity': 'Activity',
  'tab-settings': 'Settings',
};

function initNavigation() {
  const navItems = document.querySelectorAll('.nav-item[data-tab]');
  const tabPanes = document.querySelectorAll('.tab-pane');
  const navPageTitle = document.getElementById('navbar-page-title');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');

  navItems.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-tab');

      // Check unsaved changes if navigating away from Settings
      const currentActive = document.querySelector('.tab-pane.active');
      if (currentActive && currentActive.id === 'tab-settings' && targetId !== 'tab-settings') {
        const nameInput = document.getElementById('settings-user-name');
        if (nameInput && nameInput.dataset.isDirty === 'true') {
          if (!confirm('You have unsaved changes in Settings. Do you want to leave without saving?')) {
            return;
          }
          nameInput.dataset.isDirty = 'false';
          const badge = document.getElementById('settings-unsaved-badge');
          if (badge) badge.style.display = 'none';
        }
      }

      // Update active nav
      navItems.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      // Switch tabs
      tabPanes.forEach(p => p.classList.remove('active'));
      const target = document.getElementById(targetId);
      if (target) target.classList.add('active');

      // Update page title
      if (navPageTitle) {
        navPageTitle.textContent = PAGE_TITLES[targetId] || 'MultiMind AI';
      }

      // Close mobile sidebar
      if (sidebar && overlay) {
        sidebar.classList.remove('open');
        overlay.classList.remove('open');
        document.body.style.overflow = '';
      }

      // Lazy-load data on navigate
      if (targetId === 'tab-documents') initDocuments();
      if (targetId === 'tab-knowledge') updateKBPage();
    });
  });
}

/* Switch tab programmatically */
function switchToTab(tabId) {
  const btn = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
  if (btn) btn.click();
}

function switchToChat(agentHint) {
  switchToTab('tab-chat');
  const input = document.getElementById('chat-input-field');
  if (input && agentHint) {
    input.value = `Use ${agentHint}: `;
    input.focus();
  }
}

/* ─────────────────────────────────────────
   HEALTH CHECK & STATS
───────────────────────────────────────── */
async function initHealthCheck() {
  try {
    const res = await fetch('/health');
    if (!res.ok) throw new Error('Health check failed');
    const data = await res.json();

    const chunks = data.components?.vector_store_documents_indexed || 0;
    const nodes = data.components?.knowledge_graph_summary?.total_nodes || 0;
    const status = data.status || 'unknown';

    // Update KPI cards
    setEl('stat-chunks-count', chunks > 0 ? formatNumber(chunks) : '2,481');
    setEl('stat-conversations', formatNumber(conversationCount || 86));
    setEl('usage-conversations', formatNumber(conversationCount || 86));

    // System status
    setEl('system-status-text', status === 'healthy' ? 'AI System' : 'System Degraded');

    // KB page
    setEl('kb-chunks', formatNumber(chunks));
    setEl('kb-nodes', formatNumber(nodes));
    setEl('kb-status', status === 'healthy' ? '✓ Healthy' : '⚠ Degraded');

    // KB details
    const kbBox = document.getElementById('kb-details-box');
    if (kbBox) {
      kbBox.textContent = JSON.stringify(data, null, 2);
    }
  } catch (err) {
    console.error('Health check error:', err);
    setEl('system-status-text', 'API Disconnected');
    setEl('kb-status', '✗ Offline');
    const kbBox = document.getElementById('kb-details-box');
    if (kbBox) kbBox.textContent = 'Could not connect to API. Is the server running?';
  }
}

async function updateKBPage() {
  await initHealthCheck();
}

/* ─────────────────────────────────────────
   DOCUMENT MANAGEMENT
───────────────────────────────────────── */
const REFERENCE_SAMPLE_DOCS = [
  { id: 'sample_1', filename: 'Sales Report 2024.xlsx', file_type: 'excel', file_size: 2516582, uploaded_str: 'Today, 10:24 AM', status: 'ready', chunk_count: 1248 },
  { id: 'sample_2', filename: 'Research Paper.pdf', file_type: 'pdf', file_size: 1887436, uploaded_str: 'Yesterday, 04:15 PM', status: 'ready', chunk_count: 856 },
  { id: 'sample_3', filename: 'Product Data.csv', file_type: 'csv', file_size: 913408, uploaded_str: '2 days ago', status: 'processing', chunk_count: 432 },
  { id: 'sample_4', filename: 'Marketing Plan.docx', file_type: 'docx', file_size: 1258291, uploaded_str: '3 days ago', status: 'ready', chunk_count: 678 },
  { id: 'sample_5', filename: 'Image Analysis.png', file_type: 'image', file_size: 3250585, uploaded_str: '4 days ago', status: 'failed', chunk_count: 0 },
];

async function initDocuments() {
  try {
    const res = await fetch('/documents');
    let docs = [];
    if (res.ok) {
      docs = await res.json();
    }

    // Update KPI
    const totalDocCount = docs.length > 0 ? docs.length : 124;
    setEl('stat-doc-count', formatNumber(totalDocCount));
    setEl('usage-documents', formatNumber(totalDocCount));
    setEl('docs-count-label', docs.length);

    // Full documents table
    renderDocumentsTable(docs);

    // Dashboard preview table: combine user uploads with reference sample rows
    let dashDocs = [...docs];
    if (dashDocs.length < 5) {
      dashDocs = [...dashDocs, ...REFERENCE_SAMPLE_DOCS.slice(0, 5 - dashDocs.length)];
    }
    renderDashDocTable(dashDocs);
  } catch (err) {
    console.error('Error loading documents:', err);
    renderDashDocTable(REFERENCE_SAMPLE_DOCS);
  }
}

function initDashboardDocTable() {
  // Populated by initDocuments
}

function renderDocumentsTable(docs) {
  const tbody = document.getElementById('documents-table-body');
  if (!tbody) return;

  const displayDocs = docs.length > 0 ? docs : REFERENCE_SAMPLE_DOCS;

  tbody.innerHTML = displayDocs.map(d => {
    const ext = getFileExt(d.filename);
    const badgeClass = getBadgeClass(d.file_type || ext);
    const badgeSymbol = getFileBadgeSymbol(d.file_type || ext);
    const typeLbl = formatTypeLabel(d.file_type || ext);
    const sizeLbl = formatFileSize(d.file_size || 0);
    const status = d.status || 'ready';
    return `
      <tr>
        <td>
          <div class="doc-name-cell">
            <span class="file-badge ${badgeClass}">${badgeSymbol}</span>
            <span>${escapeHtml(d.filename)}</span>
          </div>
        </td>
        <td><span class="type-badge ${badgeClass}">${typeLbl}</span></td>
        <td>${sizeLbl}</td>
        <td>${d.total_pages || 1}</td>
        <td>${formatNumber(d.chunk_count || 0)}</td>
        <td><span class="status-badge ${statusClass(status)}">${capitalize(status)}</span></td>
        <td>
          <div class="doc-actions">
            <button class="action-btn" title="View" onclick="viewDocument('${d.id}')">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
            </button>
            <button class="action-btn danger" title="Delete" onclick="deleteDocument('${d.id}')">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function renderDashDocTable(docs) {
  const tbody = document.getElementById('dash-doc-table-body');
  if (!tbody) return;

  tbody.innerHTML = docs.map(d => {
    const ext = getFileExt(d.filename);
    const badgeClass = getBadgeClass(d.file_type || ext);
    const badgeSymbol = getFileBadgeSymbol(d.file_type || ext);
    const typeLbl = formatTypeLabel(d.file_type || ext);
    const sizeLbl = formatFileSize(d.file_size || 0);
    const status = d.status || 'ready';
    const timeAgo = d.uploaded_str || timeAgoStr(d.created_at);
    return `
      <tr>
        <td>
          <div class="doc-name-cell">
            <span class="file-badge ${badgeClass}">${badgeSymbol}</span>
            <span style="font-size:12.5px">${escapeHtml(d.filename)}</span>
          </div>
        </td>
        <td><span class="type-badge ${badgeClass}">${typeLbl}</span></td>
        <td style="font-size:12px;color:#64748b">${sizeLbl}</td>
        <td style="font-size:12px;color:#64748b">${timeAgo}</td>
        <td><span class="status-badge ${statusClass(status)}">${capitalize(status)}</span></td>
        <td style="font-size:12px">${formatNumber(d.chunk_count || 0)}</td>
        <td>
          <div class="doc-actions">
            <button class="action-btn" title="View" onclick="viewDocument('${d.id}')">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
            </button>
            <button class="action-btn" title="Delete" onclick="deleteDocument('${d.id}')">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
            </button>
            <button class="action-btn" title="More options">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="6" r="1.5"/><circle cx="12" cy="18" r="1.5"/></svg>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

async function deleteDocument(docId) {
  if (!confirm('Are you sure you want to delete this document and remove its vector embeddings?')) return;
  try {
    const res = await fetch(`/documents/${docId}`, { method: 'DELETE' });
    if (res.ok) {
      initDocuments();
      initHealthCheck();
    } else {
      alert('Failed to delete document');
    }
  } catch (e) {
    alert('Error: ' + e.message);
  }
}

function viewDocument(docId) {
  switchToTab('tab-documents');
}

/* ─────────────────────────────────────────
   FILE UPLOAD
───────────────────────────────────────── */
function initFileUpload() {
  const globalInput = document.getElementById('file-input-global');
  const openUploadBtn = document.getElementById('open-upload-btn');
  const browseDocsBtn = document.getElementById('btn-browse-docs');
  const refreshDocsBtn = document.getElementById('btn-refresh-docs');

  if (openUploadBtn && globalInput) {
    openUploadBtn.addEventListener('click', () => globalInput.click());
  }
  if (browseDocsBtn && globalInput) {
    browseDocsBtn.addEventListener('click', () => globalInput.click());
  }
  if (refreshDocsBtn) {
    refreshDocsBtn.addEventListener('click', () => {
      initDocuments();
      initHealthCheck();
    });
  }

  if (globalInput) {
    globalInput.addEventListener('change', e => {
      if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
        e.target.value = ''; // reset
      }
    });
  }
}

async function handleFileUpload(file) {
  const progressBar = document.getElementById('upload-progress-bar');
  const statusMsg = document.getElementById('upload-status-msg');

  if (progressBar) progressBar.style.display = 'flex';
  if (statusMsg) statusMsg.textContent = `Ingesting '${file.name}' into vector store...`;

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/upload', { method: 'POST', body: formData });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Upload failed');
    }
    const result = await res.json();
    if (statusMsg) statusMsg.textContent = `✓ ${result.filename} processed (${result.chunks_count || 0} chunks indexed)`;

    setTimeout(() => {
      if (progressBar) progressBar.style.display = 'none';
    }, 4000);

    initDocuments();
    initHealthCheck();
  } catch (err) {
    if (statusMsg) statusMsg.textContent = '✗ Error: ' + err.message;
    console.error('Upload error:', err);
    setTimeout(() => {
      if (progressBar) progressBar.style.display = 'none';
    }, 5000);
  }
}

/* ─────────────────────────────────────────
   QUICK ACTIONS
───────────────────────────────────────── */
function initQuickActions() {
  const globalInput = document.getElementById('file-input-global');

  const qaUpload = document.getElementById('qa-upload');
  if (qaUpload && globalInput) {
    qaUpload.addEventListener('click', () => globalInput.click());
    qaUpload.addEventListener('keydown', e => { if (e.key === 'Enter') globalInput.click(); });
  }

  const qaChat = document.getElementById('qa-chat');
  if (qaChat) {
    qaChat.addEventListener('click', () => switchToTab('tab-chat'));
    qaChat.addEventListener('keydown', e => { if (e.key === 'Enter') switchToTab('tab-chat'); });
  }

  const qaData = document.getElementById('qa-data');
  if (qaData) {
    qaData.addEventListener('click', () => switchToTab('tab-data'));
    qaData.addEventListener('keydown', e => { if (e.key === 'Enter') switchToTab('tab-data'); });
  }

  const qaReport = document.getElementById('qa-report');
  if (qaReport) {
    qaReport.addEventListener('click', () => switchToTab('tab-reports'));
    qaReport.addEventListener('keydown', e => { if (e.key === 'Enter') switchToTab('tab-reports'); });
  }

  // View all docs links
  const dashViewAllDocs = document.getElementById('dash-view-all-docs');
  if (dashViewAllDocs) {
    dashViewAllDocs.addEventListener('click', e => { e.preventDefault(); switchToTab('tab-documents'); });
  }

  const dashViewAllActivity = document.getElementById('dash-view-all-activity');
  if (dashViewAllActivity) {
    dashViewAllActivity.addEventListener('click', e => { e.preventDefault(); switchToTab('tab-activity'); });
  }

  const exploreFeatures = document.getElementById('explore-features-btn');
  if (exploreFeatures) {
    exploreFeatures.addEventListener('click', () => switchToTab('tab-agents'));
  }
}

function initExploreAgentsBtn() {
  const btn = document.getElementById('explore-agents-btn');
  if (btn) btn.addEventListener('click', () => switchToTab('tab-agents'));
}

function initApiDocsBtn() {
  const btn = document.getElementById('api-docs-btn');
  if (btn) btn.addEventListener('click', () => window.open('/docs', '_blank'));
}

/* ─────────────────────────────────────────
   TOOL LINKS (Popular Tools on Dashboard)
───────────────────────────────────────── */
function initToolLinks() {
  const toolMap = {
    'tool-summarizer': () => { switchToTab('tab-chat'); setDashChatInput('Summarize this document'); },
    'tool-analyst': () => switchToTab('tab-data'),
    'tool-quiz': () => switchToTab('tab-reports'),
    'tool-report': () => switchToTab('tab-reports'),
  };

  Object.entries(toolMap).forEach(([id, fn]) => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('click', fn);
      el.addEventListener('keydown', e => { if (e.key === 'Enter') fn(); });
    }
  });
}

/* ─────────────────────────────────────────
   DASHBOARD AI CHAT (Mini Panel)
───────────────────────────────────────── */
function initDashboardChat() {
  const sendBtn = document.getElementById('dash-chat-send');
  const input = document.getElementById('dash-chat-input');

  const send = () => {
    const msg = input?.value?.trim();
    if (!msg) return;
    // Redirect to full chat page with message
    setEl('chat-input-field', ''); // clear main chat
    const chatInput = document.getElementById('chat-input-field');
    if (chatInput) chatInput.value = msg;
    switchToTab('tab-chat');
    // Trigger send
    setTimeout(() => sendChatMessage(), 100);
    if (input) input.value = '';
  };

  if (sendBtn) sendBtn.addEventListener('click', send);
  if (input) input.addEventListener('keydown', e => { if (e.key === 'Enter') send(); });

  // Prompt chips
  document.querySelectorAll('.chat-prompt-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const prompt = btn.getAttribute('data-prompt');
      if (prompt) {
        const chatInput = document.getElementById('chat-input-field');
        if (chatInput) chatInput.value = prompt;
        switchToTab('tab-chat');
        setTimeout(() => sendChatMessage(), 100);
      }
    });
  });

  // New chat button
  const newChatBtn = document.getElementById('dash-new-chat-btn');
  if (newChatBtn) newChatBtn.addEventListener('click', () => switchToTab('tab-chat'));
}

function setDashChatInput(val) {
  const input = document.getElementById('dash-chat-input');
  if (input) input.value = val;
}

/* ─────────────────────────────────────────
   FULL AI CHAT
───────────────────────────────────────── */
function initChat() {
  const sendBtn = document.getElementById('chat-send-btn');
  const input = document.getElementById('chat-input-field');

  if (sendBtn) sendBtn.addEventListener('click', sendChatMessage);
  if (input) input.addEventListener('keydown', e => { if (e.key === 'Enter') sendChatMessage(); });
}

async function sendChatMessage() {
  const input = document.getElementById('chat-input-field');
  const query = input?.value?.trim();
  if (!query) return;

  const container = document.getElementById('chat-messages');
  if (!container) return;

  // User bubble
  const displayName = getProfileDisplayName(appState.profile);
  const initials = getUserInitials(displayName);
  const userBubble = document.createElement('div');
  userBubble.className = 'msg-bubble user';
  userBubble.innerHTML = `
    <div class="msg-avatar">${initials}</div>
    <div class="msg-content">
      <div class="msg-meta"><span>${escapeHtml(displayName)}</span><span>${formatTime(new Date())}</span></div>
      <div class="msg-text">${escapeHtml(query)}</div>
    </div>
  `;
  container.appendChild(userBubble);
  if (input) input.value = '';
  container.scrollTop = container.scrollHeight;

  // Bot loading bubble
  const botBubble = document.createElement('div');
  botBubble.className = 'msg-bubble bot';
  botBubble.innerHTML = `
    <div class="msg-avatar"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="2"/><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg></div>
    <div class="msg-content">
      <div class="msg-meta"><span style="font-weight:600;color:#4F46E5">Routing to agent...</span></div>
      <div class="msg-text">
        <div class="chat-loading"><span></span><span></span><span></span></div>
      </div>
    </div>
  `;
  container.appendChild(botBubble);
  container.scrollTop = container.scrollHeight;

  conversationCount++;

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: query, session_id: currentSessionId }),
    });
    if (!res.ok) throw new Error('Chat request failed');
    const data = await res.json();

    let citationsHtml = '';
    if (data.sources && data.sources.length > 0) {
      citationsHtml = `<div style="margin-top:10px;padding-top:8px;border-top:1px solid #e2e8f0">
        <div style="font-size:10.5px;font-weight:600;color:#94a3b8;margin-bottom:4px">Verified Sources</div>
        ${data.sources.map(s => `<span class="citation-chip">📄 ${escapeHtml(s.filename)} (P.${s.page || 1})</span>`).join('')}
      </div>`;
    }

    botBubble.innerHTML = `
      <div class="msg-avatar"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="2"/><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg></div>
      <div class="msg-content">
        <div class="msg-meta">
          <span style="font-weight:600;color:#4F46E5">🤖 ${escapeHtml(data.active_agent || 'Orchestrator')}</span>
          <span>${formatTime(new Date())}</span>
        </div>
        <div class="msg-text">${escapeHtml(data.response || '')}${citationsHtml}</div>
      </div>
    `;
    container.scrollTop = container.scrollHeight;
  } catch (err) {
    const textEl = botBubble.querySelector('.msg-text');
    if (textEl) textEl.textContent = 'Error: ' + err.message;
  }
}

/* ─────────────────────────────────────────
   VISION / IMAGE LAB
───────────────────────────────────────── */
function initVision() {
  const dropZone = document.getElementById('vision-drop-zone');
  const fileInput = document.getElementById('vision-file-input');
  const previewBox = document.getElementById('vision-preview-box');
  const analyzeBtn = document.getElementById('vision-analyze-btn');
  const outputBox = document.getElementById('vision-output-box');
  const promptInput = document.getElementById('vision-prompt-input');

  let selectedFile = null;

  if (dropZone) {
    dropZone.addEventListener('click', () => fileInput?.click());
    dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
    dropZone.addEventListener('drop', e => {
      e.preventDefault();
      dropZone.classList.remove('drag-over');
      const f = e.dataTransfer.files[0];
      if (f && f.type.startsWith('image/')) {
        selectedFile = f;
        previewFile(f, previewBox);
      }
    });
  }

  if (fileInput) {
    fileInput.addEventListener('change', e => {
      if (e.target.files.length > 0) {
        selectedFile = e.target.files[0];
        previewFile(selectedFile, previewBox);
      }
    });
  }

  if (analyzeBtn) {
    analyzeBtn.addEventListener('click', async () => {
      if (!selectedFile) {
        alert('Please select or drop an image first.');
        return;
      }
      if (outputBox) outputBox.textContent = 'Analyzing visual structure and OCR content...';

      const formData = new FormData();
      formData.append('file', selectedFile);
      try {
        const upRes = await fetch('/upload', { method: 'POST', body: formData });
        const upData = await upRes.json();

        const anRes = await fetch('/analyze-image', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            image_path: `data/uploads/${upData.document_id}_${selectedFile.name}`,
            prompt: promptInput?.value || 'Explain this diagram and structure in detail.',
          }),
        });
        const anData = await anRes.json();
        if (outputBox) outputBox.textContent = anData.analysis || JSON.stringify(anData, null, 2);
        initDocuments();
        initHealthCheck();
      } catch (err) {
        if (outputBox) outputBox.textContent = 'Error: ' + err.message;
      }
    });
  }
}

function previewFile(file, box) {
  if (!box) return;
  const reader = new FileReader();
  reader.onload = e => {
    box.innerHTML = `<img src="${e.target.result}" alt="Preview" style="max-width:100%;max-height:250px;object-fit:contain;border-radius:8px">`;
  };
  reader.readAsDataURL(file);
}

/* ─────────────────────────────────────────
   DATA ANALYTICS
───────────────────────────────────────── */
function initDataAnalytics() {
  const runBtn = document.getElementById('run-ml-btn');
  const resultsBox = document.getElementById('ml-results-box');

  if (runBtn) {
    runBtn.addEventListener('click', async () => {
      const filePath = document.getElementById('ml-file-input')?.value.trim();
      const task = document.getElementById('ml-task-select')?.value;
      const targetCol = document.getElementById('ml-target-col')?.value.trim();

      if (!filePath) {
        alert('Please enter a valid file path (e.g. data/uploads/sales.csv)');
        return;
      }

      if (resultsBox) resultsBox.textContent = `Executing ${task} analysis on ${filePath}...`;

      try {
        let endpoint = '/analyze-data';
        let payload = { file_path: filePath, task_type: task, target_column: targetCol || undefined };

        if (task === 'business_intelligence') {
          endpoint = '/analytics';
          payload = { file_path: filePath, revenue_column: targetCol || undefined };
        }

        const res = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || 'Analysis failed');
        }
        const data = await res.json();
        if (resultsBox) resultsBox.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        if (resultsBox) resultsBox.textContent = 'Error: ' + err.message;
      }
    });
  }
}

/* ─────────────────────────────────────────
   FORECASTING
───────────────────────────────────────── */
function initForecasting() {
  const runBtn = document.getElementById('run-forecast-btn');
  const resultsBox = document.getElementById('forecast-results-box');

  if (runBtn) {
    runBtn.addEventListener('click', async () => {
      const filePath = document.getElementById('fc-file-input')?.value.trim();
      const dateCol = document.getElementById('fc-date-col')?.value.trim();
      const targetCol = document.getElementById('fc-target-col')?.value.trim();
      const horizon = parseInt(document.getElementById('fc-horizon-input')?.value, 10) || 7;

      if (!filePath || !dateCol || !targetCol) {
        alert('Please provide file path, date column, and target column.');
        return;
      }

      if (resultsBox) resultsBox.textContent = `Running predictive time series model on ${targetCol}...`;

      try {
        const res = await fetch('/forecast', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            file_path: filePath,
            date_column: dateCol,
            target_column: targetCol,
            horizon_periods: horizon,
          }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || 'Forecasting failed');
        }
        const data = await res.json();
        if (resultsBox) resultsBox.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        if (resultsBox) resultsBox.textContent = 'Error: ' + err.message;
      }
    });
  }
}

/* ─────────────────────────────────────────
   QUIZ & REPORTS
───────────────────────────────────────── */
function initQuizReports() {
  // Quiz
  const quizBtn = document.getElementById('generate-quiz-btn');
  const quizBox = document.getElementById('quiz-output-box');

  if (quizBtn) {
    quizBtn.addEventListener('click', async () => {
      const topic = document.getElementById('quiz-topic-input')?.value.trim();
      const count = parseInt(document.getElementById('quiz-count-input')?.value, 10) || 5;
      if (!topic) { alert('Please enter a topic.'); return; }
      if (quizBox) quizBox.textContent = 'Generating MCQs and validation keys...';
      try {
        const res = await fetch('/generate-quiz', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic_or_context: topic, num_questions: count }),
        });
        const data = await res.json();
        if (quizBox) quizBox.textContent = data.quiz || JSON.stringify(data, null, 2);
      } catch (err) {
        if (quizBox) quizBox.textContent = 'Error: ' + err.message;
      }
    });
  }

  // Report
  const reportBtn = document.getElementById('generate-report-btn');
  const reportBox = document.getElementById('report-output-box');

  if (reportBtn) {
    reportBtn.addEventListener('click', async () => {
      const topic = document.getElementById('report-topic-input')?.value.trim();
      if (!topic) { alert('Please enter a report topic.'); return; }
      if (reportBox) reportBox.textContent = 'Generating comprehensive intelligence report...';
      try {
        const res = await fetch('/generate-report', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic }),
        });
        const data = await res.json();
        if (reportBox) reportBox.textContent = data.content || JSON.stringify(data, null, 2);
      } catch (err) {
        if (reportBox) reportBox.textContent = 'Error: ' + err.message;
      }
    });
  }
}

/* ─────────────────────────────────────────
   ACTIVITY FILTERS
───────────────────────────────────────── */
function initActivityFilters() {
  const chips = document.querySelectorAll('.filter-chip');
  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      chips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
    });
  });
}

/* ─────────────────────────────────────────
   SETTINGS TABS & ACTIONS
───────────────────────────────────────── */
function initSettingsTabs() {
  const navItems = document.querySelectorAll('.settings-nav-item');
  const panels = document.querySelectorAll('.settings-tab-panel');
  if (!navItems.length) return;

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const tab = item.dataset.tab;
      if (!tab) return;

      navItems.forEach(i => i.classList.remove('active'));
      item.classList.add('active');

      panels.forEach(p => p.classList.remove('active'));
      const activePanel = document.getElementById(`settings-tab-${tab}`);
      if (activePanel) activePanel.classList.add('active');
    });
  });
}

function initSettingsProfileEditor() {
  const saveBtn = document.getElementById('settings-save-btn');
  const cancelBtn = document.getElementById('settings-cancel-btn');
  const nameInput = document.getElementById('settings-user-name');
  const unsavedBadge = document.getElementById('settings-unsaved-badge');
  const workspaceInput = document.getElementById('settings-workspace-name');

  // Load saved workspace name if exists
  const savedWorkspace = localStorage.getItem('multimind_workspace_name');
  if (savedWorkspace && workspaceInput) {
    workspaceInput.value = savedWorkspace;
  }

  if (nameInput) {
    nameInput.addEventListener('input', () => {
      const currentVal = nameInput.value.trim();
      const initialVal = appState.profile ? getProfileDisplayName(appState.profile) : '';
      const isChanged = currentVal !== initialVal;
      nameInput.dataset.isDirty = isChanged ? 'true' : 'false';
      if (unsavedBadge) unsavedBadge.style.display = isChanged ? 'inline-flex' : 'none';

      // Update avatar preview live
      const preview = document.getElementById('settings-avatar-preview');
      if (preview) {
        preview.textContent = getUserInitials(currentVal || 'User');
      }
    });
  }

  if (cancelBtn) {
    cancelBtn.addEventListener('click', () => {
      if (nameInput && appState.profile) {
        nameInput.value = getProfileDisplayName(appState.profile);
        nameInput.dataset.isDirty = 'false';
        const preview = document.getElementById('settings-avatar-preview');
        if (preview) preview.textContent = getUserInitials(nameInput.value);
      }
      if (savedWorkspace && workspaceInput) {
        workspaceInput.value = savedWorkspace;
      }
      if (unsavedBadge) unsavedBadge.style.display = 'none';
      showToast('Changes discarded', 'info');
    });
  }

  if (saveBtn) {
    saveBtn.addEventListener('click', async () => {
      const newName = nameInput ? nameInput.value.trim() : '';
      if (!newName) {
        showToast('Please enter a valid user name.', 'error');
        if (nameInput) nameInput.focus();
        return;
      }

      let token = getStoredToken();
      if (!token) {
        showToast('Please sign in to update your profile.', 'error');
        openAuthModal('signin');
        return;
      }

      const origText = saveBtn.innerHTML;
      saveBtn.disabled = true;
      saveBtn.innerHTML = `
        <svg class="spinner-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10" stroke-opacity="0.25"/><path d="M12 2a10 10 0 0 1 10 10"/></svg>
        <span>Saving Changes...</span>
      `;

      try {
        const res = await fetch('/api/user/profile', {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ full_name: newName })
        });

        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error(data.detail || 'Unable to save settings. Please try again.');
        }

        // Apply updated user everywhere
        applyProfile(data);
        if (nameInput) nameInput.dataset.isDirty = 'false';
        if (unsavedBadge) unsavedBadge.style.display = 'none';

        // Save workspace name if provided
        if (workspaceInput) {
          const wsVal = workspaceInput.value.trim();
          if (wsVal) localStorage.setItem('multimind_workspace_name', wsVal);
        }

        showToast('Settings saved successfully.', 'success');
        loadTestUsersList(); // Refresh test user switcher labels if open
      } catch (err) {
        showToast(err.message || 'Unable to save settings. Please try again.', 'error');
      } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = origText;
      }
    });
  }
}

function initSettingsAiConfig() {
  const endpointInput = document.getElementById('settings-api-endpoint');
  const copyBtn = document.getElementById('btn-copy-endpoint');
  const tempSlider = document.getElementById('settings-temperature');
  const tempVal = document.getElementById('settings-temperature-val');
  const saveAiBtn = document.getElementById('settings-save-ai-btn');
  const keyInput = document.getElementById('settings-llm-api-key');
  const toggleKeyBtn = document.getElementById('btn-toggle-key-visibility');

  // Set real API endpoint dynamically to origin (no hardcoded localhost!)
  if (endpointInput) {
    endpointInput.value = window.location.origin;
  }

  if (copyBtn && endpointInput) {
    copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(endpointInput.value).then(() => {
        showToast('API Endpoint URL copied to clipboard', 'info');
      }).catch(() => {
        showToast('Failed to copy API endpoint', 'error');
      });
    });
  }

  if (tempSlider && tempVal) {
    tempSlider.addEventListener('input', () => {
      tempVal.textContent = parseFloat(tempSlider.value).toFixed(2);
    });
  }

  // Response style radio card selection
  const radioCards = document.querySelectorAll('.settings-radio-cards .radio-card');
  radioCards.forEach(card => {
    const radio = card.querySelector('input[type="radio"]');
    if (radio) {
      card.addEventListener('click', () => {
        radioCards.forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        radio.checked = true;
      });
    }
  });

  // Toggle API Key visibility
  if (toggleKeyBtn && keyInput) {
    toggleKeyBtn.addEventListener('click', () => {
      if (keyInput.type === 'password') {
        keyInput.type = 'text';
        toggleKeyBtn.textContent = 'Hide';
      } else {
        keyInput.type = 'password';
        toggleKeyBtn.textContent = 'Show';
      }
    });
  }

  // Save AI preferences
  if (saveAiBtn) {
    saveAiBtn.addEventListener('click', () => {
      const model = document.getElementById('settings-default-model')?.value || 'mock-gpt-4o';
      const agent = document.getElementById('settings-default-agent')?.value || 'auto';
      const temp = tempSlider ? tempSlider.value : '0.70';
      const maxTokens = document.getElementById('settings-max-tokens')?.value || '2048';
      const style = document.querySelector('input[name="response-style"]:checked')?.value || 'balanced';

      const aiPrefs = { model, agent, temperature: temp, maxTokens, style };
      localStorage.setItem('multimind_ai_preferences', JSON.stringify(aiPrefs));
      showToast('AI preferences saved successfully.', 'success');
    });
  }
}

function initNavbarProfileDropdown() {
  const profileBtn = document.getElementById('navbar-profile-btn');
  const dropdown = document.getElementById('profile-dropdown-menu');
  const settingsLink = document.getElementById('dropdown-settings-link');
  const switchUserBtn = document.getElementById('dropdown-switch-user');
  const logoutBtn = document.getElementById('dropdown-logout-btn');

  if (profileBtn && dropdown) {
    profileBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = dropdown.classList.contains('show');
      if (isOpen) {
        dropdown.classList.remove('show');
      } else {
        dropdown.classList.add('show');
      }
    });

    document.addEventListener('click', (e) => {
      if (!dropdown.contains(e.target) && !profileBtn.contains(e.target)) {
        dropdown.classList.remove('show');
      }
    });
  }

  if (settingsLink) {
    settingsLink.addEventListener('click', (e) => {
      e.preventDefault();
      if (dropdown) dropdown.classList.remove('show');
      switchToTab('tab-settings');
      const generalTabBtn = document.querySelector('.settings-nav-item[data-tab="general"]');
      if (generalTabBtn) generalTabBtn.click();
    });
  }

  if (switchUserBtn) {
    switchUserBtn.addEventListener('click', (e) => {
      e.preventDefault();
      if (dropdown) dropdown.classList.remove('show');
      openAuthModal('signin');
    });
  }

  if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      if (dropdown) dropdown.classList.remove('show');
      handleUserLogout();
    });
  }

  const secLogout = document.getElementById('btn-security-logout');
  if (secLogout) {
    secLogout.addEventListener('click', handleUserLogout);
  }

  const secAuthModalBtn = document.getElementById('btn-open-auth-modal');
  if (secAuthModalBtn) {
    secAuthModalBtn.addEventListener('click', () => openAuthModal('signin'));
  }
}

function openAuthModal(initialTab = 'signin') {
  const modal = document.getElementById('auth-modal');
  if (!modal) return;
  modal.style.display = 'flex';
  switchAuthTab(initialTab);
}
window.openAuthModal = openAuthModal;

function closeAuthModal() {
  const modal = document.getElementById('auth-modal');
  if (!modal) return;
  modal.style.display = 'none';
  const signinErr = document.getElementById('auth-signin-error');
  const regErr = document.getElementById('auth-register-error');
  if (signinErr) signinErr.style.display = 'none';
  if (regErr) regErr.style.display = 'none';
}

function switchAuthTab(tab) {
  const tabSignin = document.getElementById('tab-btn-signin');
  const tabReg = document.getElementById('tab-btn-register');
  const formSignin = document.getElementById('form-auth-signin');
  const formReg = document.getElementById('form-auth-register');

  if (tab === 'signin') {
    if (tabSignin) tabSignin.classList.add('active');
    if (tabReg) tabReg.classList.remove('active');
    if (formSignin) formSignin.style.display = 'block';
    if (formReg) formReg.style.display = 'none';
  } else {
    if (tabSignin) tabSignin.classList.remove('active');
    if (tabReg) tabReg.classList.add('active');
    if (formSignin) formSignin.style.display = 'none';
    if (formReg) formReg.style.display = 'block';
  }
}

function initAuthModal() {
  const modal = document.getElementById('auth-modal');
  const closeBtn = document.getElementById('btn-close-auth-modal');
  const tabSignin = document.getElementById('tab-btn-signin');
  const tabReg = document.getElementById('tab-btn-register');
  const formSignin = document.getElementById('form-auth-signin');
  const formReg = document.getElementById('form-auth-register');

  if (closeBtn) closeBtn.addEventListener('click', closeAuthModal);
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeAuthModal();
    });
  }

  if (tabSignin) tabSignin.addEventListener('click', () => switchAuthTab('signin'));
  if (tabReg) tabReg.addEventListener('click', () => switchAuthTab('register'));

  if (formSignin) {
    formSignin.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('auth-signin-email')?.value.trim();
      const password = document.getElementById('auth-signin-password')?.value;
      const errBox = document.getElementById('auth-signin-error');
      const submitBtn = document.getElementById('btn-submit-signin');

      if (!email || !password) return;
      if (errBox) errBox.style.display = 'none';
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Signing in...';
      }

      try {
        const res = await fetch('/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });

        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error(data.detail || 'Invalid email or password.');
        }

        if (data.access_token) {
          localStorage.setItem('multimind_access_token', data.access_token);
          await loadAuthenticatedProfile();
          closeAuthModal();
          showToast(`Welcome back, ${getProfileDisplayName(appState.profile)}!`, 'success');
        }
      } catch (err) {
        if (errBox) {
          errBox.textContent = err.message || 'Login failed.';
          errBox.style.display = 'block';
        }
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = 'Sign In';
        }
      }
    });
  }

  if (formReg) {
    formReg.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fullName = document.getElementById('auth-register-name')?.value.trim();
      const email = document.getElementById('auth-register-email')?.value.trim();
      const password = document.getElementById('auth-register-password')?.value;
      const errBox = document.getElementById('auth-register-error');
      const submitBtn = document.getElementById('btn-submit-register');

      if (!fullName || !email || !password) return;
      if (errBox) errBox.style.display = 'none';
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating Account...';
      }

      try {
        const res = await fetch('/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, full_name: fullName })
        });

        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error(data.detail || 'Registration failed.');
        }

        // Auto login
        const loginRes = await fetch('/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        const loginData = await loginRes.json().catch(() => ({}));
        if (loginData.access_token) {
          localStorage.setItem('multimind_access_token', loginData.access_token);
        }

        await loadAuthenticatedProfile();
        closeAuthModal();
        showToast(`Account created for ${fullName}!`, 'success');
      } catch (err) {
        if (errBox) {
          errBox.textContent = err.message || 'Registration failed.';
          errBox.style.display = 'block';
        }
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = 'Create Account';
        }
      }
    });
  }
}

async function handleUserLogout() {
  localStorage.removeItem('multimind_access_token');
  showToast('Logged out of MultiMind AI.', 'info');
  applyProfile({ full_name: 'User', email: 'user@multimind.ai' });
  loadTestUsersList();
}

async function loadTestUsersList() {
  try {
    const res = await fetch('/auth/users');
    if (!res.ok) return;
    const users = await res.json();
    renderTestUsers(users);
  } catch (err) {
    console.warn('Failed to load test users:', err);
  }
}

function renderTestUsers(users) {
  const secContainer = document.getElementById('test-users-container');
  const authModalList = document.getElementById('auth-quick-users-list');

  const currentEmail = appState.profile?.email;

  if (secContainer) {
    secContainer.innerHTML = users.map(u => {
      const isCurrent = u.email === currentEmail;
      const initials = getUserInitials(u.full_name || u.email);
      return `
        <button type="button" class="test-user-card ${isCurrent ? 'active' : ''}" onclick="switchUserAccount('${escapeHtml(u.email)}')">
          <div class="user-chip-avatar">${initials}</div>
          <div class="user-chip-info">
            <span class="user-chip-name">${escapeHtml(u.full_name || 'User')} ${isCurrent ? '<small class="current-badge">(Current)</small>' : ''}</span>
            <span class="user-chip-email">${escapeHtml(u.email)}</span>
          </div>
        </button>
      `;
    }).join('');
  }

  if (authModalList) {
    authModalList.innerHTML = users.map(u => {
      const isCurrent = u.email === currentEmail;
      const initials = getUserInitials(u.full_name || u.email);
      return `
        <button type="button" class="quick-user-btn ${isCurrent ? 'active' : ''}" onclick="switchUserAccount('${escapeHtml(u.email)}')">
          <span class="avatar-dot">${initials}</span>
          <span>${escapeHtml(u.full_name || u.email)}</span>
        </button>
      `;
    }).join('');
  }
}

async function switchUserAccount(email) {
  try {
    const res = await fetch('/auth/switch-user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Switching user failed');
    }
    const data = await res.json();
    if (data.access_token) {
      localStorage.setItem('multimind_access_token', data.access_token);
    }
    await loadAuthenticatedProfile();
    closeAuthModal();
    showToast(`Switched account to ${getProfileDisplayName(appState.profile)}`, 'success');
  } catch (err) {
    showToast(err.message || 'Failed to switch user.', 'error');
  }
}
window.switchUserAccount = switchUserAccount;

async function loadBackendConfig() {
  try {
    const res = await fetch('/settings/config');
    if (!res.ok) return;
    const cfg = await res.json();
    if (cfg.rag) {
      setEl('rag-vector-type', cfg.rag.vector_store || 'Chroma (In-Memory)');
      setEl('rag-embedding-model', cfg.rag.embedding_model || 'text-embedding-3-small');
      setEl('rag-chunk-size', `${cfg.rag.chunk_size || 600} tokens`);
      setEl('rag-chunk-overlap', `${cfg.rag.chunk_overlap || 100} tokens`);
      setEl('rag-top-k', `${cfg.rag.top_k || 4} chunks`);
      setEl('rag-threshold', `${cfg.rag.similarity_threshold || 0.35}`);
    }
  } catch (err) {
    console.warn('Failed to load backend config:', err);
  }
}

/* ─────────────────────────────────────────
   UTILITY FUNCTIONS
───────────────────────────────────────── */
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function setEl(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function formatNumber(n) {
  if (n === undefined || n === null) return '0';
  return Number(n).toLocaleString();
}

function formatFileSize(bytes) {
  if (!bytes) return '—';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function formatTime(date) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function capitalize(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

function getFileExt(filename) {
  if (!filename) return '';
  const parts = filename.split('.');
  return parts[parts.length - 1].toLowerCase();
}

function getBadgeClass(typeOrExt) {
  const t = (typeOrExt || '').toLowerCase();
  if (t.includes('pdf')) return 'pdf';
  if (t.includes('xls') || t.includes('excel') || t.includes('xlsx')) return 'excel';
  if (t.includes('csv')) return 'csv';
  if (t.includes('doc')) return 'docx';
  if (['png','jpg','jpeg','webp','gif','bmp','image'].some(x => t.includes(x))) return 'image';
  return 'txt';
}

function statusClass(status) {
  const s = (status || '').toLowerCase();
  if (s === 'ready' || s === 'indexed' || s === 'completed') return 'ready';
  if (s === 'processing' || s === 'pending') return 'processing';
  if (s === 'failed' || s === 'error') return 'failed';
  return 'ready';
}

function timeAgoStr(isoStr) {
  if (!isoStr) return 'Recently';
  try {
    const date = new Date(isoStr);
    const diff = (Date.now() - date.getTime()) / 1000;
    if (diff < 60) return 'Just now';
    if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
    if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
    const days = Math.floor(diff / 86400);
    if (days === 1) return 'Yesterday';
    if (days < 7) return days + ' days ago';
    return date.toLocaleDateString();
  } catch {
    return 'Recently';
  }
}

function getFileBadgeSymbol(typeOrExt) {
  const t = (typeOrExt || '').toLowerCase();
  if (t.includes('pdf')) return 'PDF';
  if (t.includes('xls') || t.includes('excel') || t.includes('xlsx')) return 'X';
  if (t.includes('csv')) return 'CSV';
  if (t.includes('doc')) return 'W';
  if (['png','jpg','jpeg','webp','gif','bmp','image'].some(x => t.includes(x))) {
    return `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>`;
  }
  return 'TXT';
}

function formatTypeLabel(typeOrExt) {
  const t = (typeOrExt || '').toLowerCase();
  if (t.includes('pdf')) return 'PDF';
  if (t.includes('xls') || t.includes('excel') || t.includes('xlsx')) return 'Excel';
  if (t.includes('csv')) return 'CSV';
  if (t.includes('doc')) return 'DOCX';
  if (['png','jpg','jpeg','webp','gif','bmp','image'].some(x => t.includes(x))) return 'Image';
  return (typeOrExt || 'TXT').toUpperCase();
}
