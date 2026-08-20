// ═══════════════════════════════════════════════════════════════════════════════
// CareerCopilot AI — Main Script
// ═══════════════════════════════════════════════════════════════════════════════

const API_BASE = '/api';

let currentUser = null;
let resumeData = null;
let jobsData = [];
let careerPlan = null;
let interviewQuestions = [];
let clHistory = [];

// ── Utility ─────────────────────────────────────────────────────────────────
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i> ${message}`;
    container.appendChild(toast);
    setTimeout(() => { toast.style.animation = 'toastIn 0.3s ease reverse forwards'; setTimeout(() => toast.remove(), 300); }, 3500);
}

function showLoading(text = 'Loading...') {
    let overlay = document.querySelector('.loading-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = '<div class="loader"><div class="loader-spinner"></div><p></p></div>';
        document.body.appendChild(overlay);
    }
    overlay.querySelector('p').textContent = text;
    overlay.style.display = 'flex';
}

function hideLoading() {
    const overlay = document.querySelector('.loading-overlay');
    if (overlay) overlay.style.display = 'none';
}

function showAuthModal(message) {
    const modal = document.getElementById('auth-modal');
    modal.classList.add('active');
    if (message) {
        const err = document.getElementById('auth-error');
        err.textContent = message;
        err.classList.remove('hidden');
        setTimeout(() => err.classList.add('hidden'), 5000);
    }
}

function hideAuthModal() {
    document.getElementById('auth-modal').classList.remove('active');
}

function skipAuth() {
    localStorage.setItem('token', 'demo-token');
    currentUser = { name: 'Guest' };
    hideAuthModal();
    showToast('Continuing as guest', 'info');
}

function handleAuthSuccess(data) {
    localStorage.setItem('token', data.access_token);
    currentUser = data.user || { name: 'User', email: data.email };
    if (currentUser.name) localStorage.setItem('userName', currentUser.name);
    if (currentUser.email) localStorage.setItem('userEmail', currentUser.email);
    hideAuthModal();
    updateUserUI();
    loadSettingsProfile();
    showToast('Welcome back!', 'success');
}

function showAuthError(msg) {
    const err = document.getElementById('auth-error');
    err.textContent = msg;
    err.classList.remove('hidden');
    setTimeout(() => err.classList.add('hidden'), 5000);
}

// ── Navigation ──────────────────────────────────────────────────────────────
function navigateTo(section) {
    const isLoggedIn = !!localStorage.getItem('token') && localStorage.getItem('token') !== 'demo-token';
    const hasApiKey = !!localStorage.getItem('aiApiKey');

    // Block all sections except dashboard and settings if not logged in or no API key
    if (section !== 'dashboard' && section !== 'settings') {
        if (!isLoggedIn) {
            showAuthModal('Please login to access this feature');
            return;
        }
        if (!hasApiKey) {
            showToast('Please set your API key in Settings first', 'error');
            navigateTo('settings');
            return;
        }
    }

    // Settings only accessible when logged in
    if (section === 'settings' && !isLoggedIn) {
        showAuthModal('Please login to access Settings');
        return;
    }

    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    const target = document.getElementById(`section-${section}`);
    if (target) target.classList.add('active');
    const navLink = document.querySelector(`.nav-link[data-section="${section}"]`);
    if (navLink) navLink.classList.add('active');
    window.scrollTo({ top: 0, behavior: 'smooth' });
    const navCenter = document.querySelector('.nav-center');
    if (navCenter) navCenter.classList.remove('open');
    const hamburger = document.getElementById('hamburger-btn');
    if (hamburger) hamburger.classList.remove('active');
}

// ── Auth ────────────────────────────────────────────────────────────────────
function initAuth() {
    // Eye toggle for password fields
    document.querySelectorAll('.auth-pw-toggle').forEach(btn => {
        btn.addEventListener('click', () => {
            const target = document.getElementById(btn.dataset.target);
            if (target.type === 'password') {
                target.type = 'text';
                btn.innerHTML = '<i class="fas fa-eye-slash"></i>';
            } else {
                target.type = 'password';
                btn.innerHTML = '<i class="fas fa-eye"></i>';
            }
        });
    });

    // Add has-toggle class to password inputs
    document.querySelectorAll('.auth-pw-toggle').forEach(btn => {
        const target = document.getElementById(btn.dataset.target);
        if (target) target.classList.add('has-toggle');
    });

    // Password strength and requirements validation
    const regPassword = document.getElementById('reg-password');
    const confirmPw = document.getElementById('reg-confirm-password');
    const strengthFill = document.getElementById('pw-strength-fill');
    const strengthText = document.getElementById('pw-strength-text');
    const pwMatch = document.getElementById('pw-match');

    regPassword.addEventListener('input', () => {
        const val = regPassword.value;
        let strength = 0;
        const reqs = {
            length: val.length >= 8,
            upper: /[A-Z]/.test(val),
            number: /[0-9]/.test(val),
            symbol: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(val)
        };

        // Update requirement indicators
        Object.keys(reqs).forEach(key => {
            const el = document.getElementById(`pw-req-${key}`);
            if (el) {
                if (reqs[key]) {
                    el.classList.add('met');
                    el.innerHTML = '<i class="fas fa-check-circle"></i> ' + el.textContent.replace(/[^\w\s+]/g, '').trim();
                } else {
                    el.classList.remove('met');
                    el.innerHTML = '<i class="fas fa-circle"></i> ' + el.textContent.replace(/[^\w\s+]/g, '').trim();
                }
            }
        });

        // Calculate strength
        if (reqs.length) strength++;
        if (reqs.upper) strength++;
        if (reqs.number) strength++;
        if (reqs.symbol) strength++;

        // Update strength bar
        const colors = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3ecf8e'];
        const labels = ['Weak', 'Fair', 'Good', 'Strong', 'Very Strong'];
        strengthFill.style.width = (strength * 25) + '%';
        strengthFill.style.background = colors[strength] || colors[0];
        strengthText.textContent = strength > 0 ? labels[strength - 1] : '';
        strengthText.style.color = colors[strength] || 'var(--text-muted)';
    });

    // Confirm password match
    confirmPw.addEventListener('input', () => {
        if (confirmPw.value === regPassword.value && confirmPw.value.length > 0) {
            pwMatch.textContent = '✓ Passwords match';
            pwMatch.style.color = 'var(--accent-primary)';
        } else if (confirmPw.value.length > 0) {
            pwMatch.textContent = '✗ Passwords do not match';
            pwMatch.style.color = '#ef4444';
        } else {
            pwMatch.textContent = '';
        }
    });

    // Gmail validation
    const regEmail = document.getElementById('reg-email');
    regEmail.addEventListener('input', () => {
        const email = regEmail.value;
        if (email && !email.endsWith('@gmail.com')) {
            regEmail.setCustomValidity('Only Gmail addresses are accepted');
        } else {
            regEmail.setCustomValidity('');
        }
    });

    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            const form = tab.dataset.tab;
            document.getElementById('login-form').classList.toggle('hidden', form !== 'login');
            document.getElementById('register-form').classList.toggle('hidden', form !== 'register');
        });
    });

    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        try {
            const data = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            }).then(r => r.json());
            if (data.access_token) {
                handleAuthSuccess(data);
            } else {
                showAuthError(data.detail || 'Login failed');
            }
        } catch (err) {
            showAuthError(err.message);
        }
    });

    document.getElementById('register-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('reg-name').value;
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;
        try {
            const data = await fetch(`${API_BASE}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, name }),
            }).then(r => r.json());
            if (data.access_token) {
                handleAuthSuccess(data);
            } else {
                showAuthError(data.detail || 'Registration failed');
            }
        } catch (err) {
            showAuthError(err.message);
        }
    });
}

// ── Settings ────────────────────────────────────────────────────────────────
function loadSettingsProfile() {
    const name = localStorage.getItem('userName') || '';
    const email = localStorage.getItem('userEmail') || '';
    const nameInput = document.getElementById('settings-name');
    const emailInput = document.getElementById('settings-email');
    if (nameInput) nameInput.value = name;
    if (emailInput) emailInput.value = email;
    const initial = document.getElementById('settings-initial');
    if (initial && name) initial.textContent = name.charAt(0).toUpperCase();
}

function initSettings() {
    loadSettingsProfile();

    // Theme toggle
    document.querySelectorAll('.settings-theme-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.settings-theme-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            if (btn.dataset.theme === 'light') {
                document.body.classList.add('light-theme');
            } else {
                document.body.classList.remove('light-theme');
            }
            localStorage.setItem('theme', btn.dataset.theme);
        });
    });

    // Load saved theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
        document.getElementById('theme-light').classList.add('active');
        document.getElementById('theme-dark').classList.remove('active');
    }

    // Profile save
    document.getElementById('settings-save-profile').addEventListener('click', () => {
        const name = document.getElementById('settings-name').value;
        if (name) {
            localStorage.setItem('userName', name);
            updateUserUI();
            showToast('Profile saved', 'success');
        }
    });

    // Avatar upload
    const avatarWrap = document.getElementById('settings-avatar-wrap');
    const avatarInput = document.getElementById('settings-avatar-input');
    avatarWrap.addEventListener('click', () => avatarInput.click());
    avatarInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (ev) => {
                avatarWrap.innerHTML = `<img src="${ev.target.result}" style="width:100%;height:100%;object-fit:cover;border-radius:50%"><div class="settings-avatar-lg-overlay"><i class="fas fa-camera"></i></div>`;
                localStorage.setItem('userAvatar', ev.target.result);
            };
            reader.readAsDataURL(file);
        }
    });

    // Model save
    document.getElementById('settings-save-model').addEventListener('click', () => {
        const provider = document.getElementById('settings-provider').value;
        const model = document.getElementById('settings-model').value;
        const apiKey = document.getElementById('settings-api-key').value;
        localStorage.setItem('aiProvider', provider);
        localStorage.setItem('aiModel', model);
        if (apiKey) localStorage.setItem('aiApiKey', apiKey);
        showToast('Model settings saved', 'success');
    });

    // Logout
    document.getElementById('settings-logout').addEventListener('click', () => {
        localStorage.removeItem('token');
        currentUser = null;
        showAuthModal();
        showToast('Signed out', 'info');
    });

    // Load saved avatar
    const savedAvatar = localStorage.getItem('userAvatar');
    if (savedAvatar) {
        document.getElementById('settings-avatar-wrap').innerHTML = `<img src="${savedAvatar}" style="width:100%;height:100%;object-fit:cover;border-radius:50%"><div class="settings-avatar-lg-overlay"><i class="fas fa-camera"></i></div>`;
    }

    // Load saved model
    const savedProvider = localStorage.getItem('aiProvider');
    if (savedProvider) document.getElementById('settings-provider').value = savedProvider;
    const savedModel = localStorage.getItem('aiModel');
    if (savedModel) document.getElementById('settings-model').value = savedModel;
    const savedApiKey = localStorage.getItem('aiApiKey');
    if (savedApiKey) document.getElementById('settings-api-key').value = savedApiKey;

    // Provider change updates models
    document.getElementById('settings-provider').addEventListener('change', (e) => {
        const models = {
            gemini: [['gemini/gemini-2.5-flash', 'Gemini 2.5 Flash'], ['gemini/gemini-2.5-flash-lite', 'Gemini 2.5 Flash Lite']],
            openai: [['openai/gpt-4o-mini', 'GPT-4o Mini'], ['openai/gpt-4o', 'GPT-4o']],
            groq: [['groq/llama-3.3-70b-versatile', 'Llama 3.3 70B']],
            deepseek: [['deepseek/deepseek-chat', 'DeepSeek V3']],
            qwen: [['qwen/qwen-turbo', 'Qwen Turbo']],
        };
        const modelSelect = document.getElementById('settings-model');
        modelSelect.innerHTML = (models[e.target.value] || []).map(([v, l]) => `<option value="${v}">${l}</option>`).join('');
    });
}

function updateUserUI() {
    const name = localStorage.getItem('userName') || 'User';
    const initial = name.charAt(0).toUpperCase();
    const initial2 = name.split(' ').length > 1 ? name.split(' ')[1].charAt(0).toUpperCase() : name.charAt(1).toUpperCase() || '';
    const initials = initial + initial2;
    const avatar = localStorage.getItem('userAvatar');
    const isLoggedIn = !!localStorage.getItem('token') && localStorage.getItem('token') !== 'demo-token';
    const hasApiKey = !!localStorage.getItem('aiApiKey');

    // Update nav user display
    const navGuest = document.getElementById('nav-guest');
    const navUser = document.getElementById('nav-user');
    if (isLoggedIn) {
        navGuest.classList.add('hidden');
        navUser.classList.remove('hidden');
        if (avatar) {
            document.getElementById('nav-avatar').innerHTML = `<img src="${avatar}" style="width:100%;height:100%;object-fit:cover;border-radius:50%">`;
        } else {
            document.getElementById('nav-avatar').innerHTML = `<span>${initials}</span>`;
        }
    } else {
        navGuest.classList.remove('hidden');
        navUser.classList.add('hidden');
    }

    // Update settings page elements
    const settingsInitial = document.getElementById('settings-initial');
    const settingsName = document.getElementById('settings-name');
    if (settingsInitial) settingsInitial.textContent = initials;
    if (settingsName) settingsName.value = name;

    // If no API key and logged in, show warning toast
    if (isLoggedIn && !hasApiKey) {
        // Don't spam toast, only on specific actions
    }
}

// ── Navigation Links ────────────────────────────────────────────────────────
function initNavigation() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => navigateTo(link.dataset.section));
    });

    const hamburger = document.getElementById('hamburger-btn');
    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        document.querySelector('.nav-center').classList.toggle('open');
    });
}

// ── Resume ──────────────────────────────────────────────────────────────────
function initResume() {
    const zone = document.getElementById('upload-zone');
    const input = document.getElementById('resume-file-input');
    const btn = document.getElementById('upload-btn');

    btn.addEventListener('click', (e) => { e.stopPropagation(); input.click(); });
    zone.addEventListener('click', () => input.click());

    zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('drag-over'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        if (e.dataTransfer.files.length) uploadResume(e.dataTransfer.files[0]);
    });

    input.addEventListener('change', (e) => {
        if (e.target.files.length) uploadResume(e.target.files[0]);
    });

    document.getElementById('analyze-ats-btn').addEventListener('click', analyzeATS);
    document.getElementById('delete-resume-btn').addEventListener('click', deleteResume);
}

async function uploadResume(file) {
    if (file.type !== 'application/pdf') {
        showToast('Please upload a PDF file', 'error');
        return;
    }
    showLoading('Uploading resume...');
    try {
        const formData = new FormData();
        formData.append('file', file);
        const data = await fetch(`${API_BASE}/resumes`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
            body: formData,
        }).then(r => r.json());
        hideLoading();
        if (data.error) {
            showToast(data.error, 'error');
            return;
        }
        resumeData = data;
        document.getElementById('upload-zone').classList.add('hidden');
        document.getElementById('resume-card').classList.remove('hidden');
        document.getElementById('resume-filename').textContent = file.name;
        document.getElementById('resume-words').textContent = data.word_count || '—';
        document.getElementById('resume-sections').textContent = data.sections_found || '—';
        document.getElementById('resume-ats-score').textContent = data.ats_score ? `${data.ats_score}%` : '—';
        document.getElementById('resume-profile').textContent = data.summary || '';
        showToast('Resume uploaded successfully', 'success');
        updateDashboardProgress();
    } catch (err) {
        hideLoading();
        showToast('Upload failed: ' + err.message, 'error');
    }
}

async function analyzeATS() {
    if (!resumeData) return showToast('Upload a resume first', 'error');
    showLoading('Analyzing ATS score...');
    try {
        // ATS analysis requires a job_id — disabled until job matching is wired up
        showToast('Select a job first to run ATS analysis', 'info');
        hideLoading();
        return;
    } catch (err) {
        hideLoading();
        showToast('Analysis failed', 'error');
    }
}

function deleteResume() {
    resumeData = null;
    document.getElementById('upload-zone').classList.remove('hidden');
    document.getElementById('resume-card').classList.add('hidden');
    showToast('Resume removed', 'info');
}

// ── Jobs ────────────────────────────────────────────────────────────────────
function initJobs() {
    document.getElementById('search-jobs-btn').addEventListener('click', searchJobs);
}

async function searchJobs() {
    const keywords = document.getElementById('job-keywords').value;
    const location = document.getElementById('job-location').value;
    showLoading('Searching jobs...');
    try {
        const params = new URLSearchParams();
        if (keywords) params.set('keywords', keywords);
        if (location) params.set('location', location);
        const data = await fetch(`${API_BASE}/jobs/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('token')}` },
            body: JSON.stringify({ target_role: keywords || 'Software Engineer', keywords }),
        }).then(r => r.json());
        hideLoading();
        jobsData = data.jobs || data || [];
        renderJobs();
        showToast(`Found ${jobsData.length} jobs`, 'success');
    } catch (err) {
        hideLoading();
        showToast('Search failed', 'error');
    }
}

function quickJobSearch(term) {
    document.getElementById('job-keywords').value = term;
    searchJobs();
}

function renderJobs() {
    const list = document.getElementById('jobs-list');
    const empty = document.getElementById('jobs-empty');
    if (!jobsData.length) {
        list.innerHTML = '';
        empty.classList.remove('hidden');
        return;
    }
    empty.classList.add('hidden');
    list.innerHTML = jobsData.map((job, i) => `
        <div class="job-card glass-card">
            <div class="job-icon"><i class="fas fa-briefcase"></i></div>
            <div class="job-body">
                <div class="job-title">${job.title || 'Untitled'}</div>
                <div class="job-company">${job.company || 'Unknown'}</div>
                <div class="job-meta">
                    ${job.location ? `<span><i class="fas fa-map-marker-alt"></i> ${job.location}</span>` : ''}
                    ${job.type ? `<span><i class="fas fa-clock"></i> ${job.type}</span>` : ''}
                </div>
            </div>
            <div class="job-actions">
                <button class="btn btn-primary btn-sm" onclick="analyzeJob(${i})"><i class="fas fa-clipboard-check"></i> ATS</button>
                <button class="btn btn-ghost btn-sm" onclick="trackJob(${i})"><i class="fas fa-plus"></i> Track</button>
            </div>
        </div>
    `).join('');
}

async function analyzeJob(index) {
    showToast('Analyzing job match...', 'info');
}

function trackJob(index) {
    showToast('Job added to tracker', 'success');
}

// ── Career Plan ─────────────────────────────────────────────────────────────
function initCareer() {
    document.getElementById('generate-plan-btn').addEventListener('click', generateCareerPlan);
    document.getElementById('export-plan-btn').addEventListener('click', exportPlan);
}

async function generateCareerPlan() {
    if (!resumeData) return showToast('Upload a resume first', 'error');
    showLoading('Generating career plan...');
    try {
        const data = await fetch(`${API_BASE}/career/plan`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('token')}` },
            body: JSON.stringify({ resume_id: resumeData.resume_id }),
        }).then(r => r.json());
        hideLoading();
        careerPlan = data;
        const result = document.getElementById('career-plan-result');
        result.classList.remove('hidden');
        result.innerHTML = `
            <div class="glass-card">
                <h3 style="margin-bottom:16px"><i class="fas fa-route" style="color:var(--accent-primary)"></i> Your Career Plan</h3>
                <div style="white-space:pre-wrap;line-height:1.8;color:var(--text-secondary);font-size:0.9rem">${data.plan || data.content || JSON.stringify(data, null, 2)}</div>
            </div>
        `;
        document.getElementById('export-plan-btn').style.display = 'inline-flex';
        showToast('Career plan generated', 'success');
        updateDashboardProgress();
    } catch (err) {
        hideLoading();
        showToast('Generation failed', 'error');
    }
}

function exportPlan() {
    if (!careerPlan) return;
    const text = careerPlan.plan || careerPlan.content || JSON.stringify(careerPlan, null, 2);
    const blob = new Blob([text], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'career-plan.txt';
    a.click();
    showToast('Plan exported', 'success');
}

// ── Interview ───────────────────────────────────────────────────────────────
function initInterview() {
    document.getElementById('start-interview-btn').addEventListener('click', startInterview);
}

async function startInterview() {
    showLoading('Preparing questions...');
    try {
        const resumeId = resumeData?.resume_id || resumeData?.version_id || '';
        const data = await fetch(`${API_BASE}/interviews?resume_id=${resumeId}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
        }).then(r => r.json());
        hideLoading();
        interviewQuestions = data.questions || data || [];
        renderInterview();
        showToast('Interview ready', 'success');
    } catch (err) {
        hideLoading();
        showToast('Failed to start interview', 'error');
    }
}

function renderInterview() {
    const container = document.getElementById('interview-questions');
    container.classList.remove('hidden');
    container.innerHTML = interviewQuestions.map((q, i) => `
        <div class="interview-question glass-card">
            <h3>Question ${i + 1}</h3>
            <div class="interview-q-text">${q.question || q}</div>
            <textarea class="interview-textarea" id="interview-answer-${i}" placeholder="Type your answer..."></textarea>
            <button class="btn btn-primary btn-sm" onclick="submitAnswer(${i})"><i class="fas fa-check"></i> Submit</button>
            <div class="interview-feedback hidden" id="feedback-${i}"></div>
        </div>
    `).join('');
}

async function submitAnswer(index) {
    const answer = document.getElementById(`interview-answer-${index}`).value;
    if (!answer.trim()) return showToast('Type an answer first', 'error');
    showLoading('Getting feedback...');
    try {
        const data = await fetch(`${API_BASE}/interview/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('token')}` },
            body: JSON.stringify({ question: interviewQuestions[index]?.question || interviewQuestions[index], answer }),
        }).then(r => r.json());
        hideLoading();
        const fb = document.getElementById(`feedback-${index}`);
        fb.classList.remove('hidden');
        fb.textContent = data.feedback || data.feedback_text || 'Good answer!';
        showToast('Feedback received', 'success');
    } catch (err) {
        hideLoading();
        showToast('Feedback failed', 'error');
    }
}

// ── Cover Letter ────────────────────────────────────────────────────────────
function initCoverLetter() {
    document.querySelectorAll('.cl-tone-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.cl-tone-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });

    document.getElementById('cl-generate-btn').addEventListener('click', generateCoverLetter);
    document.getElementById('cl-copy-btn').addEventListener('click', copyCoverLetter);
}

async function generateCoverLetter() {
    const company = document.getElementById('cl-company').value;
    const role = document.getElementById('cl-role').value;
    const tone = document.querySelector('.cl-tone-btn.active')?.dataset.tone || 'professional';

    if (!company || !role) return showToast('Fill in company and role', 'error');
    showLoading('Generating cover letter...');
    try {
        const resumeId = resumeData?.resume_id || resumeData?.version_id || '';
        const data = await fetch(`${API_BASE}/cover-letters`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('token')}` },
            body: JSON.stringify({ resume_id: resumeId, company_name: company, job_title: role, tone }),
        }).then(r => r.json());
        hideLoading();
        const content = data.cover_letter || data.content || data.text || '';
        document.getElementById('cl-result').classList.remove('hidden');
        document.getElementById('cl-result-content').textContent = content;
        document.getElementById('cl-result-meta').textContent = `${company} — ${role} — ${tone}`;
        clHistory.unshift({ company, role, tone, content, date: new Date() });
        renderCLHistory();
        showToast('Cover letter generated', 'success');
    } catch (err) {
        hideLoading();
        showToast('Generation failed', 'error');
    }
}

function copyCoverLetter() {
    const text = document.getElementById('cl-result-content').textContent;
    navigator.clipboard.writeText(text).then(() => showToast('Copied to clipboard', 'success'));
}

function renderCLHistory() {
    const list = document.getElementById('cl-history-list');
    list.innerHTML = clHistory.map((item, i) => `
        <div class="cl-history-card glass-card" onclick="showCLHistory(${i})">
            <div class="cl-history-icon"><i class="fas fa-pen-fancy"></i></div>
            <div class="cl-history-body">
                <div class="cl-history-name">${item.company} — ${item.role}</div>
                <div class="cl-history-detail">${item.tone} • ${item.date.toLocaleDateString()}</div>
            </div>
            <i class="fas fa-chevron-right cl-history-arrow"></i>
        </div>
    `).join('');
}

function showCLHistory(index) {
    const item = clHistory[index];
    if (!item) return;
    document.getElementById('cl-result').classList.remove('hidden');
    document.getElementById('cl-result-content').textContent = item.content;
    document.getElementById('cl-result-meta').textContent = `${item.company} — ${item.role} — ${item.tone}`;
}

// ── Chat ────────────────────────────────────────────────────────────────────
function initChat() {
    const fab = document.getElementById('chat-fab');
    const widget = document.getElementById('chat-widget');
    const closeBtn = document.getElementById('chat-widget-close');
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-chat-btn');

    fab.addEventListener('click', () => {
        fab.classList.toggle('active');
        widget.classList.toggle('open');
    });

    closeBtn.addEventListener('click', () => {
        fab.classList.remove('active');
        widget.classList.remove('open');
    });

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });

    input.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 80) + 'px';
    });
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;

    const messagesDiv = document.getElementById('chat-messages');
    const welcome = messagesDiv.querySelector('.chat-welcome');
    if (welcome) welcome.remove();

    messagesDiv.innerHTML += `
        <div class="chat-msg user">
            <div class="chat-msg-avatar human"><i class="fas fa-user"></i></div>
            <div class="chat-msg-bubble">${msg}</div>
        </div>
    `;

    input.value = '';
    input.style.height = 'auto';

    const meta = document.getElementById('chat-meta');
    meta.innerHTML = '<div class="typing-indicator"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>';

    try {
        const data = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('token')}` },
            body: JSON.stringify({ message: msg }),
        }).then(r => r.json());
        meta.innerHTML = '';
        const reply = data.reply || data.response || data.message || 'I could not process that request.';
        messagesDiv.innerHTML += `
            <div class="chat-msg assistant">
                <div class="chat-msg-avatar ai"><i class="fas fa-robot"></i></div>
                <div class="chat-msg-bubble">${reply}</div>
            </div>
        `;
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    } catch (err) {
        meta.innerHTML = '';
        messagesDiv.innerHTML += `
            <div class="chat-msg assistant">
                <div class="chat-msg-avatar ai"><i class="fas fa-robot"></i></div>
                <div class="chat-msg-bubble" style="color:#ef4444">Connection error. Please try again.</div>
            </div>
        `;
    }
}

// ── FAQ ─────────────────────────────────────────────────────────────────────
function initFAQ() {
    document.querySelectorAll('.cf-faq-question').forEach(btn => {
        btn.addEventListener('click', () => {
            const item = btn.closest('.cf-faq-item');
            item.classList.toggle('open');
        });
    });
}

// ── Dashboard Progress ──────────────────────────────────────────────────────
function updateDashboardProgress() {
    let progress = 0;
    if (currentUser) progress += 25;
    if (resumeData) progress += 25;
    if (jobsData.length) progress += 25;
    if (careerPlan) progress += 25;
    document.getElementById('dash-progress-pct').textContent = `${progress}%`;
    document.getElementById('dash-progress-fill').style.width = `${progress}%`;
}

// ── Page Loader ─────────────────────────────────────────────────────────────
function initLoader() {
    const loader = document.getElementById('page-loader');
    setTimeout(() => loader.classList.add('hidden'), 1400);
}

// ── Init ────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initLoader();
    initNavigation();
    initAuth();
    initSettings();
    initResume();
    initJobs();
    initCareer();
    initInterview();
    initCoverLetter();
    initChat();
    initFAQ();
    updateUserUI();

    // Login button in nav
    const navLoginBtn = document.getElementById('nav-login-btn');
    if (navLoginBtn) {
        navLoginBtn.addEventListener('click', () => showAuthModal());
    }

    // Settings toggle icon
    const settingsToggle = document.getElementById('settings-toggle');
    if (settingsToggle) {
        settingsToggle.addEventListener('click', () => {
            const isLoggedIn = !!localStorage.getItem('token') && localStorage.getItem('token') !== 'demo-token';
            if (!isLoggedIn) {
                showAuthModal('Please login to access Settings');
                return;
            }
            navigateTo('settings');
        });
    }

    const token = localStorage.getItem('token');
    if (token) {
        currentUser = true;
        updateUserUI();
    } else {
        showAuthModal();
    }
});
