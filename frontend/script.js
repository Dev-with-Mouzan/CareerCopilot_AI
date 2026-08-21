// ═══════════════════════════════════════════════════════════════════════════════
// CareerCopilot AI — Main Script
// ═══════════════════════════════════════════════════════════════════════════════

const API_BASE = '/api';

async function apiFetch(url, options = {}) {
    const headers = { ...(options.headers || {}) };
    const apiKey = localStorage.getItem('aiApiKey');
    if (apiKey) headers['X-API-Key'] = apiKey;
    const model = localStorage.getItem('aiModel');
    if (model) headers['X-Model'] = model;
    const res = await fetch(url, { ...options, headers });
    if (!res.ok) {
        let msg = `Request failed (${res.status})`;
        try {
            const body = await res.json();
            msg = body.detail || body.error || msg;
        } catch (_) { /* non-JSON error */ }
        throw new Error(msg);
    }
    return res;
}

let resumeData = null;
let jobsData = [];
let careerPlan = null;

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

// ── Navigation ──────────────────────────────────────────────────────────────
function navigateTo(section) {
    if (section !== 'settings' && !isApiKeyConfigured()) {
        showToast('Please set your API key and model in Settings first', 'error');
        section = 'settings';
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

// ── Settings ────────────────────────────────────────────────────────────────
function isApiKeyConfigured() {
    return !!(localStorage.getItem('aiApiKey') && localStorage.getItem('aiModel'));
}

function checkApiKeyRequired() {
    const overlay = document.getElementById('api-key-overlay');
    if (!overlay) return;
    if (isApiKeyConfigured()) {
        overlay.classList.add('hidden');
    } else {
        overlay.classList.remove('hidden');
    }
}
function getSelectedModel() {
    const select = document.getElementById('settings-model');
    if (select.value === '__custom__') {
        return document.getElementById('settings-custom-model').value.trim() || '';
    }
    return select.value;
}

function syncCustomModelInput() {
    const select = document.getElementById('settings-model');
    const isCustom = select.value === '__custom__';
    document.getElementById('settings-custom-model-group').classList.toggle('hidden', !isCustom);
    if (isCustom) document.getElementById('settings-custom-model').focus();
}

function initSettings() {
    // Model save
    document.getElementById('settings-save-model').addEventListener('click', () => {
        const provider = document.getElementById('settings-provider').value;
        const model = getSelectedModel();
        const apiKey = document.getElementById('settings-api-key').value;
        if (!model) return showToast('Please enter a model name', 'error');
        localStorage.setItem('aiProvider', provider);
        localStorage.setItem('aiModel', model);
        if (apiKey) localStorage.setItem('aiApiKey', apiKey);
        showToast('Model settings saved', 'success');
        checkApiKeyRequired();
    });

    // Load saved model
    const savedProvider = localStorage.getItem('aiProvider');
    if (savedProvider) document.getElementById('settings-provider').value = savedProvider;
    const savedApiKey = localStorage.getItem('aiApiKey');
    if (savedApiKey) document.getElementById('settings-api-key').value = savedApiKey;
    const savedModel = localStorage.getItem('aiModel');
    const modelSelect = document.getElementById('settings-model');
    if (savedModel) {
        const isKnown = Array.from(modelSelect.options).some(o => o.value === savedModel);
        if (isKnown) {
            modelSelect.value = savedModel;
        } else {
            modelSelect.value = '__custom__';
            document.getElementById('settings-custom-model').value = savedModel;
            document.getElementById('settings-custom-model-group').classList.remove('hidden');
        }
    }

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
        modelSelect.innerHTML = (models[e.target.value] || []).map(([v, l]) => `<option value="${v}">${l}</option>`).join('') + '<option value="__custom__">Custom (type exact model name)</option>';
        document.getElementById('settings-custom-model-group').classList.add('hidden');
    });

    // Custom model toggle
    document.getElementById('settings-model').addEventListener('change', syncCustomModelInput);
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
        const data = await apiFetch(`${API_BASE}/resumes`, {
            method: 'POST',
            body: formData,
        }).then(r => r.json());
        hideLoading();
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
let jobsMode = 'manual';

function initJobs() {
    document.getElementById('search-jobs-btn').addEventListener('click', () => {
        if (jobsMode === 'resume') searchResumeJobs();
        else searchJobs();
    });
    document.getElementById('jobs-mode-manual').addEventListener('click', () => setJobsMode('manual'));
    document.getElementById('jobs-mode-resume').addEventListener('click', () => setJobsMode('resume'));
}

function setJobsMode(mode) {
    jobsMode = mode;
    document.querySelectorAll('#section-jobs .cl-mode-btn').forEach(b => b.classList.toggle('active', b.dataset.mode === mode));
    document.getElementById('jobs-manual-form').classList.toggle('hidden', mode !== 'manual');
    document.getElementById('jobs-resume-hint').classList.toggle('hidden', mode !== 'resume');
    if (mode === 'resume') {
        const status = document.getElementById('jobs-resume-status');
        if (resumeData?.resume_id) {
            status.textContent = 'Your resume is ready to use.';
            status.style.color = 'var(--accent-primary)';
        } else {
            status.textContent = 'Upload a resume first, or use Manual Search mode.';
            status.style.color = '#ef4444';
        }
    }
}

async function searchJobs() {
    const keywords = document.getElementById('job-keywords').value;
    const location = document.getElementById('job-location').value;
    if (!keywords.trim()) return showToast('Enter a job title or keywords', 'error');
    showLoading('Searching jobs...');
    try {
        const data = await apiFetch(`${API_BASE}/jobs/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_role: keywords.trim(), location }),
        }).then(r => r.json());
        hideLoading();
        jobsData = (data.jobs || []).slice(0, 15);
        renderJobs();
        showToast(`Found ${jobsData.length} jobs`, jobsData.length ? 'success' : 'info');
    } catch (err) {
        hideLoading();
        showToast(err.message || 'Search failed', 'error');
    }
}

async function searchResumeJobs() {
    if (!resumeData?.resume_id) return showToast('Upload a resume first', 'error');
    showLoading('Matching jobs to your resume...');
    try {
        const data = await apiFetch(`${API_BASE}/jobs/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ resume_id: resumeData.resume_id }),
        }).then(r => r.json());
        hideLoading();
        jobsData = (data.jobs || []).slice(0, 15);
        renderJobs();
        showToast(`Found ${jobsData.length} matched jobs`, jobsData.length ? 'success' : 'info');
    } catch (err) {
        hideLoading();
        showToast(err.message || 'Matching failed', 'error');
    }
}

function quickJobSearch(term) {
    if (jobsMode !== 'manual') setJobsMode('manual');
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
    list.innerHTML = jobsData.map((job, i) => {
        const match = job.match || {};
        const score = match.overall_score;
        const scorePct = score != null ? Math.round(score * 100) : null;
        const missing = (match.missing_skills || []).slice(0, 4);
        const source = job.source || '';
        const desc = job.description || '';
        const showMeta = (job.location || job.employment_type || job.remote || job.salary_max);
        return `
        <div class="job-card glass-card">
            <div class="job-card-head">
                <div class="job-icon"><i class="fas fa-briefcase"></i></div>
                <div class="job-body">
                    <div class="job-title-row">
                        <div class="job-title">${job.title || 'Untitled'}</div>
                        ${source ? `<span class="job-source">${source}</span>` : ''}
                    </div>
                    <div class="job-company"><i class="fas fa-building"></i> ${job.company || 'Unknown'}</div>
                </div>
                ${scorePct != null ? `
                <div class="job-score-badge ${scorePct >= 60 ? 'high' : scorePct >= 30 ? 'mid' : 'low'}">
                    <div class="job-score-num">${scorePct}%</div>
                    <div class="job-score-label">match</div>
                </div>` : ''}
            </div>
            ${showMeta ? `
            <div class="job-meta">
                ${job.location ? `<span class="job-meta-pill"><i class="fas fa-map-marker-alt"></i> ${job.location}</span>` : ''}
                ${job.employment_type ? `<span class="job-meta-pill"><i class="fas fa-clock"></i> ${job.employment_type}</span>` : ''}
                ${job.remote ? '<span class="job-meta-pill"><i class="fas fa-globe"></i> Remote</span>' : ''}
                ${job.salary_max ? `<span class="job-meta-pill"><i class="fas fa-dollar-sign"></i> ${job.salary_min ? '$' + job.salary_min + ' - ' : ''}$${job.salary_max}</span>` : ''}
            </div>` : ''}
            ${scorePct != null && scorePct >= 0 ? `
            <div class="job-match-bar">
                <div class="job-match-track"><div class="job-match-fill ${scorePct >= 60 ? 'high' : scorePct >= 30 ? 'mid' : 'low'}" style="width:${scorePct}%"></div></div>
                <span class="job-match-label ${scorePct >= 60 ? 'high' : scorePct >= 30 ? 'mid' : 'low'}">${scorePct}% match</span>
            </div>` : ''}
            ${missing.length ? `
            <div class="job-missing">
                <span class="job-missing-label">Missing skills:</span>
                ${missing.map(s => `<span class="job-missing-chip">${s}</span>`).join('')}
            </div>` : ''}
            ${desc ? `<div class="job-desc">${desc.slice(0, 200)}${desc.length > 200 ? '...' : ''}</div>` : ''}
            <div class="job-actions">
                <button class="btn btn-primary btn-sm" onclick="analyzeJob(${i})"><i class="fas fa-clipboard-check"></i> ATS</button>
                ${job.source_url ? `<a class="btn btn-ghost btn-sm job-apply-link" href="${job.source_url}" target="_blank" rel="noopener"><i class="fas fa-external-link-alt"></i> Apply Now</a>` : ''}
            </div>
        </div>
    `;
    }).join('');
}

async function analyzeJob(index) {
    const job = jobsData[index];
    if (!job) return;
    if (!resumeData?.resume_id) return showToast('Upload a resume first to run ATS analysis', 'error');
    showLoading('Analyzing job match...');
    try {
        const res = await apiFetch(`${API_BASE}/jobs/${job.id || job.job_id}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ resume_id: resumeData.resume_id }),
        });
        const data = await res.json();
        hideLoading();
        if (!res.ok) return showToast(data.error || 'Analysis failed', 'error');
        showToast('ATS analysis complete', 'success');
        const report = data.report || {};
        const existing = jobsData[index];
        existing.match = {
            ...(existing.match || {}),
            overall_score: report.overall_score != null ? report.overall_score / 100 : existing.match?.overall_score,
            missing_skills: report.missing_skills || existing.match?.missing_skills || [],
        };
        renderJobs();
        renderAtsModal(job, report);
    } catch (err) {
        hideLoading();
        showToast('Analysis failed', 'error');
    }
}

function renderAtsModal(job, report) {
    const modal = document.getElementById('ats-modal');
    const body = document.getElementById('ats-modal-body');
    const scores = [
        ['Overall Match', report.overall_score],
        ['Keywords', report.keyword_score],
        ['Skills', report.skill_score],
        ['Experience', report.experience_score],
        ['Semantic', report.semantic_score],
        ['Education', report.education_score],
    ].filter(([, v]) => v != null);
    const pct = v => Math.round((v || 0) * 100);

    let html = `
        <div class="ats-job-info">
            <div class="ats-job-title">${job.title || 'Untitled'}</div>
            <div class="ats-job-company">${job.company || 'Unknown'}</div>
        </div>
        <div class="ats-score-grid">`;
    scores.forEach(([label, val]) => {
        const p = pct(val);
        const cls = p >= 60 ? 'high' : p >= 30 ? 'mid' : 'low';
        html += `
        <div class="ats-score-item">
            <div class="ats-score-label">${label}</div>
            <div class="ats-score-ring ${cls}"><span>${p}%</span></div>
            <div class="ats-score-bar"><div class="ats-score-fill ${cls}" style="width:${p}%"></div></div>
        </div>`;
    });
    html += `</div>`;

    if (report.missing_keywords && report.missing_keywords.length) {
        html += `<div class="ats-section"><h4>Missing Keywords</h4><div class="ats-chips">${report.missing_keywords.slice(0, 15).map(k => `<span class="ats-chip">${k}</span>`).join('')}</div></div>`;
    }
    if (report.missing_skills && report.missing_skills.length) {
        html += `<div class="ats-section"><h4>Missing Skills</h4><div class="ats-chips">${report.missing_skills.slice(0, 15).map(k => `<span class="ats-chip">${k}</span>`).join('')}</div></div>`;
    }
    if (report.recommendations && report.recommendations.length) {
        html += `<div class="ats-section"><h4>Recommendations</h4><ul class="ats-recs">${report.recommendations.map(r => `<li>${window.marked ? marked.parseInline(r) : r}</li>`).join('')}</ul></div>`;
    }

    body.innerHTML = html;
    modal.classList.add('show');
}

function closeAtsModal() {
    document.getElementById('ats-modal').classList.remove('show');
}

// ── Career Plan ─────────────────────────────────────────────────────────────
let careerMode = 'field';

function initCareer() {
    document.getElementById('generate-plan-btn').addEventListener('click', generateCareerPlan);
    document.getElementById('export-plan-btn').addEventListener('click', exportPlan);
    document.getElementById('career-mode-field').addEventListener('click', () => setCareerMode('field'));
    document.getElementById('career-mode-resume').addEventListener('click', () => setCareerMode('resume'));
}

function setCareerMode(mode) {
    careerMode = mode;
    document.querySelectorAll('.career-mode-btn').forEach(b => b.classList.toggle('active', b.dataset.mode === mode));
    document.getElementById('career-field-form').classList.toggle('hidden', mode !== 'field');
    document.getElementById('career-resume-hint').classList.toggle('hidden', mode !== 'resume');
    if (mode === 'resume') {
        const status = document.getElementById('career-resume-status');
        if (resumeData?.resume_id) {
            status.textContent = 'Your resume is ready to use.';
            status.style.color = 'var(--accent-primary)';
        } else {
            status.textContent = 'Upload a resume first, or use Describe Your Field mode.';
            status.style.color = '#ef4444';
        }
    }
}

async function generateCareerPlan() {
    const targetField = document.getElementById('career-target-field').value.trim();
    const payload = {};
    if (careerMode === 'resume') {
        if (!resumeData?.resume_id) return showToast('Upload a resume first, or switch to Describe Your Field', 'error');
        payload.resume_id = resumeData.resume_id;
        payload.target_role = targetField || '';
    } else {
        if (!targetField) return showToast('Describe your target career field', 'error');
        payload.target_role = targetField;
    }
    showLoading('Generating career plan...');
    try {
        const data = await apiFetch(`${API_BASE}/career/plan`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        }).then(r => r.json());
        hideLoading();
        careerPlan = data;
        const result = document.getElementById('career-plan-result');
        result.classList.remove('hidden');
        result.innerHTML = renderCareerPlan(data);
        document.getElementById('export-plan-btn').style.display = 'inline-flex';
        showToast('Career plan generated', 'success');
        updateDashboardProgress();
    } catch (err) {
        hideLoading();
        showToast(err.message || 'Generation failed', 'error');
    }
}

function renderCareerPlan(data) {
    const plan = data.plan || {};
    const target = data.target_role || '';
    const skillGaps = plan.skill_gaps || data.skill_gaps || [];
    const learning = plan.learning_priorities || [];
    const timeline = plan.timeline || {};
    const strategy = plan.application_strategy || plan.strategy || '';
    const current = plan.current_state || '';
    const targetState = plan.target_state || `Transition to ${target}`;

    let html = `<div class="career-plan-result-card glass-card">
        <h3 style="margin-bottom:16px"><i class="fas fa-route" style="color:var(--accent-primary)"></i> Your Career Plan</h3>`;

    if (target) html += `<div class="career-plan-section"><strong>Target:</strong> ${target}</div>`;
    if (current) html += `<div class="career-plan-section"><strong>Current:</strong> ${current}</div>`;
    if (targetState) html += `<div class="career-plan-section"><strong>Goal:</strong> ${targetState}</div>`;

    if (skillGaps.length) {
        html += `<div class="career-plan-section"><h4>Skill Gaps</h4><ul>`;
        skillGaps.slice(0, 8).forEach(g => {
            const gObj = typeof g === 'string' ? { skill: g } : g;
            html += `<li><strong>${gObj.skill || 'Skill'}</strong> ${gObj.priority ? `(priority ${gObj.priority})` : ''} — ${gObj.market_demand || ''}</li>`;
        });
        html += `</ul></div>`;
    }

    if (learning.length) {
        html += `<div class="career-plan-section"><h4>Learning Priorities</h4><ul>`;
        learning.forEach(l => {
            const text = typeof l === 'string' ? l : (l.text || l.title || JSON.stringify(l));
            html += `<li>${text}</li>`;
        });
        html += `</ul></div>`;
    }

    if (Object.keys(timeline).length) {
        html += `<div class="career-plan-section"><h4>Timeline</h4><ul>`;
        Object.entries(timeline).forEach(([k, v]) => {
            if (k === 'total_estimated_months') return;
            html += `<li><strong>${k.replace(/_/g, ' ')}:</strong> ${v}</li>`;
        });
        if (timeline.total_estimated_months) html += `<li><strong>Estimated total:</strong> ${timeline.total_estimated_months} months</li>`;
        html += `</ul></div>`;
    }

    if (strategy) html += `<div class="career-plan-section"><h4>Application Strategy</h4><div class="career-plan-text">${window.marked ? marked.parse(strategy) : strategy}</div></div>`;

    html += `</div>`;
    return html;
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
let interviewSession = null;
let currentQuestionIndex = 0;

function initInterview() {
    document.getElementById('start-interview-btn').addEventListener('click', startInterview);
    document.querySelectorAll('#interview-type-selector .cl-tone-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('#interview-type-selector .cl-tone-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });
}

async function startInterview() {
    const role = document.getElementById('interview-job-role').value.trim();
    const jobDesc = document.getElementById('interview-job-desc').value.trim();
    const type = document.querySelector('#interview-type-selector .cl-tone-btn.active')?.dataset.type || 'mixed';
    if (!role) return showToast('Enter a job role to prepare for', 'error');

    showLoading('Preparing 15 interview questions...');
    try {
        const data = await apiFetch(`${API_BASE}/interviews`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                job_role: role,
                job_description: jobDesc,
                interview_type: type,
                resume_id: resumeData?.resume_id || null,
            }),
        }).then(r => r.json());
        hideLoading();
        interviewSession = data;
        currentQuestionIndex = 0;
        document.getElementById('interview-setup-card').classList.add('hidden');
        const container = document.getElementById('interview-questions');
        container.classList.remove('hidden');
        renderInterviewQuestion(0);
        showToast(`${data.total_questions} questions ready`, 'success');
    } catch (err) {
        hideLoading();
        showToast(err.message || 'Failed to start interview', 'error');
    }
}

function renderInterviewQuestion(index) {
    const container = document.getElementById('interview-questions');
    const q = interviewSession.questions[index];
    if (!q) return;
    const total = interviewSession.total_questions || interviewSession.questions.length;
    const progress = Math.round((index / total) * 100);
    container.innerHTML = `
        <div class="interview-progress">
            <div class="interview-progress-track"><div class="interview-progress-fill" style="width:${progress}%"></div></div>
            <span class="interview-progress-label">Question ${index + 1} of ${total}</span>
        </div>
        <div class="interview-question glass-card" id="interview-current-q">
            <div class="interview-q-meta">
                <span class="interview-q-cat">${q.category || 'technical'}</span>
                <span class="interview-q-diff">${q.difficulty || 'medium'}</span>
            </div>
            <h3>Question ${index + 1}</h3>
            <div class="interview-q-text">${q.question || q}</div>
            <textarea class="interview-textarea" id="interview-answer" placeholder="Type your answer... (be specific, use examples, and structure your response)"></textarea>
            <button class="btn btn-primary btn-sm" id="interview-submit-btn" onclick="submitInterviewAnswer()">
                <i class="fas fa-check"></i> Submit Answer
            </button>
            <div class="interview-feedback hidden" id="interview-feedback"></div>
        </div>
    `;
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function submitInterviewAnswer() {
    const answer = document.getElementById('interview-answer').value;
    if (!answer.trim()) return showToast('Type an answer first', 'error');
    const submitBtn = document.getElementById('interview-submit-btn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Evaluating...';
    try {
        const data = await apiFetch(`${API_BASE}/interviews/${interviewSession.session_id}/answer`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question_index: currentQuestionIndex, answer: answer.trim() }),
        }).then(r => r.json());
        renderInterviewFeedback(data);
    } catch (err) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-check"></i> Submit Answer';
        showToast(err.message || 'Feedback failed', 'error');
    }
}

function renderInterviewFeedback(data) {
    const container = document.getElementById('interview-current-q');
    const feedbackDiv = document.getElementById('interview-feedback');
    feedbackDiv.classList.remove('hidden');
    const score = data.score ?? 0;
    const scoreColor = score >= 7 ? 'var(--accent-primary)' : score >= 4 ? '#eab308' : '#ef4444';
    const strengths = data.strengths || [];
    const improvements = data.improvements || [];
    const modelAnswer = data.model_answer || '';

    let html = `
        <div class="interview-score" style="border-color:${scoreColor}">
            <span class="interview-score-value" style="color:${scoreColor}">${score}/10</span>
            <span class="interview-score-label">Score</span>
        </div>
        <div class="interview-fb-section">
            <h4>Feedback</h4>
            <p>${data.feedback || 'Good answer!'}</p>
        </div>
    `;
    if (strengths.length) {
        html += `<div class="interview-fb-section"><h4>Strengths</h4><ul>${strengths.map(s => `<li>${s}</li>`).join('')}</ul></div>`;
    }
    if (improvements.length) {
        html += `<div class="interview-fb-section"><h4>Areas to Improve</h4><ul>${improvements.map(s => `<li>${s}</li>`).join('')}</ul></div>`;
    }
    if (modelAnswer) {
        html += `<div class="interview-fb-section"><h4>Model Answer</h4><div class="interview-model-answer">${modelAnswer}</div></div>`;
    }

    const total = interviewSession.total_questions || interviewSession.questions.length;
    const isLast = currentQuestionIndex >= total - 1;

    html += `<div class="interview-actions" style="display:flex;gap:12px;justify-content:center;margin-top:20px;flex-wrap:wrap">`;
    if (isLast) {
        html += `<button class="btn btn-primary" id="interview-finish-btn" onclick="finishInterview()"><i class="fas fa-flag-checkered"></i> Finish & See Results</button>`;
    } else {
        html += `<button class="btn btn-primary" onclick="renderInterviewQuestion(currentQuestionIndex + 1)"><i class="fas fa-arrow-right"></i> Next Question</button>`;
    }
    html += `</div>`;

    feedbackDiv.innerHTML = html;
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function finishInterview() {
    showLoading('Calculating your score...');
    try {
        const data = await apiFetch(`${API_BASE}/interviews/${interviewSession.session_id}`, {
            method: 'GET',
        }).then(r => r.json());
        hideLoading();
        if (data.completed) markInterviewCompleted();
        renderInterviewResults(data);
    } catch (err) {
        hideLoading();
        showToast(err.message || 'Failed to load results', 'error');
    }
}

function renderInterviewResults(data) {
    const container = document.getElementById('interview-questions');
    const scores = (data.scores || []).filter(s => s !== null);
    const total = data.total_questions || scores.length || 0;
    const overall = data.overall_score ?? 0;
    const correct = scores.filter(s => s >= 7).length;
    const needsWork = scores.filter(s => s >= 4 && s < 7).length;
    const retry = scores.filter(s => s < 4).length;

    const pct = Math.round((correct / (scores.length || 1)) * 100);
    const grade = overall >= 8 ? 'Excellent' : overall >= 6 ? 'Good' : overall >= 4 ? 'Fair' : 'Needs Improvement';
    const gradeColor = overall >= 7 ? 'var(--accent-primary)' : overall >= 4 ? '#eab308' : '#ef4444';

    container.innerHTML = `
        <div class="interview-results glass-card">
            <h3><i class="fas fa-trophy" style="color:var(--accent-primary)"></i> Interview Complete!</h3>
            <div class="interview-results-score">
                <div class="interview-results-big" style="color:${gradeColor}">${overall}/10</div>
                <div class="interview-results-grade">${grade}</div>
                <div class="interview-results-bar-track"><div class="interview-results-bar-fill" style="width:${pct}%"></div></div>
            </div>
            <div class="interview-results-stats">
                <div class="interview-result-stat">
                    <div class="interview-result-num" style="color:var(--accent-primary)">${correct}</div>
                    <div class="interview-result-label">Strong</div>
                </div>
                <div class="interview-result-stat">
                    <div class="interview-result-num" style="color:#eab308">${needsWork}</div>
                    <div class="interview-result-label">Good</div>
                </div>
                <div class="interview-result-stat">
                    <div class="interview-result-num" style="color:#ef4444">${retry}</div>
                    <div class="interview-result-label">Needs Work</div>
                </div>
                <div class="interview-result-stat">
                    <div class="interview-result-num">${total}</div>
                    <div class="interview-result-label">Total</div>
                </div>
            </div>
            <div class="interview-results-actions" style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-top:20px">
                <button class="btn btn-primary" onclick="retryWeakQuestions()"><i class="fas fa-redo"></i> Retry Weak Questions</button>
                <button class="btn btn-ghost" onclick="resetInterview()"><i class="fas fa-rotate-left"></i> New Interview</button>
            </div>
        </div>
    `;
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function retryWeakQuestions() {
    const container = document.getElementById('interview-questions');
    const scores = interviewSession.scores || [];
    const weakIndices = scores.map((s, i) => s !== null && s < 7 ? i : null).filter(i => i !== null);
    if (!weakIndices.length) {
        showToast('No weak questions to retry. Great job!', 'success');
        return;
    }
    const q = interviewSession.questions[weakIndices[0]];
    currentQuestionIndex = weakIndices[0];
    const total = interviewSession.questions.length;
    container.innerHTML = `
        <div class="interview-progress">
            <div class="interview-progress-track"><div class="interview-progress-fill" style="width:${Math.round((currentQuestionIndex / total) * 100)}%"></div></div>
            <span class="interview-progress-label">Retrying Question ${currentQuestionIndex + 1} of ${total}</span>
        </div>
        <div class="interview-question glass-card" id="interview-current-q">
            <div class="interview-q-meta">
                <span class="interview-q-cat">${q.category}</span>
                <span class="interview-q-diff">${q.difficulty}</span>
            </div>
            <h3>Retry Question ${currentQuestionIndex + 1}</h3>
            <div class="interview-q-text">${q.question}</div>
            <textarea class="interview-textarea" id="interview-answer" placeholder="Try again with a more detailed answer..."></textarea>
            <button class="btn btn-primary btn-sm" id="interview-submit-btn" onclick="submitInterviewAnswer()">
                <i class="fas fa-check"></i> Submit Answer
            </button>
            <div class="interview-feedback hidden" id="interview-feedback"></div>
        </div>
    `;
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function resetInterview() {
    interviewSession = null;
    interviewCompleted = false;
    currentQuestionIndex = 0;
    document.getElementById('interview-questions').classList.add('hidden');
    document.getElementById('interview-setup-card').classList.remove('hidden');
    document.getElementById('interview-job-desc').value = '';
    document.getElementById('interview-job-role').value = '';
    updateDashboardProgress();
}

// ── Cover Letter ────────────────────────────────────────────────────────────
let clMode = 'form';

function initCoverLetter() {
    document.querySelectorAll('.cl-tone-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.cl-tone-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });

    document.getElementById('cl-generate-btn').addEventListener('click', generateCoverLetter);
    document.getElementById('cl-copy-btn').addEventListener('click', copyCoverLetter);
    document.getElementById('cl-mode-form').addEventListener('click', () => setClMode('form'));
    document.getElementById('cl-mode-resume').addEventListener('click', () => setClMode('resume'));
}

function setClMode(mode) {
    clMode = mode;
    document.querySelectorAll('.cl-mode-btn').forEach(b => b.classList.toggle('active', b.dataset.mode === mode));
    document.getElementById('cl-form-fields').classList.toggle('hidden', mode !== 'form');
    document.getElementById('cl-resume-hint').classList.toggle('hidden', mode !== 'resume');
    if (mode === 'resume') {
        const status = document.getElementById('cl-resume-status');
        if (resumeData?.resume_id) {
            status.textContent = 'Your resume is ready to use.';
            status.style.color = 'var(--accent-primary)';
        } else {
            status.textContent = 'Upload a resume first, or use Fill Details mode.';
            status.style.color = '#ef4444';
        }
    }
}

async function generateCoverLetter() {
    const company = document.getElementById('cl-company').value.trim();
    const role = document.getElementById('cl-role').value.trim();
    const jobDesc = document.getElementById('cl-job-desc').value.trim();
    const tone = document.querySelector('.cl-tone-btn.active')?.dataset.tone || 'professional';

    const payload = { tone };
    if (clMode === 'resume') {
        if (!resumeData?.resume_id) return showToast('Upload a resume first, or switch to Fill Details', 'error');
        payload.resume_id = resumeData.resume_id;
        if (company) payload.company_name = company;
        if (role) payload.job_title = role;
    } else {
        if (!company || !role) return showToast('Fill in company and role', 'error');
        payload.company_name = company;
        payload.job_title = role;
    }
    if (jobDesc) payload.job_description = jobDesc;

    showLoading('Generating cover letter...');
    try {
        const data = await apiFetch(`${API_BASE}/cover-letters`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        }).then(r => r.json());
        hideLoading();
        const content = data.content || data.cover_letter || data.text || '';
        document.getElementById('cl-result').classList.remove('hidden');
        document.getElementById('cl-result-content').textContent = content;
        const companyDisp = data.company_name || company || '';
        const roleDisp = data.job_title || role || '';
        document.getElementById('cl-result-meta').textContent = `${companyDisp}${companyDisp && roleDisp ? ' — ' : ''}${roleDisp}${tone ? ' — ' + tone : ''}`;
        clHistory.unshift({ company: companyDisp, role: roleDisp, tone, content, date: new Date() });
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

// ── Reviews ────────────────────────────────────────────────────────────────
function initReviews() {
    const submitBtn = document.getElementById('review-submit-btn');
    if (submitBtn) {
        submitBtn.addEventListener('click', submitReview);
    }
    loadReviews();
    loadHomeTestimonials();
}

async function submitReview() {
    const name = document.getElementById('review-name').value.trim();
    const email = document.getElementById('review-email').value.trim();
    const profession = document.getElementById('review-profession').value.trim();
    const review = document.getElementById('review-text').value.trim();

    if (!name) return showToast('Please enter your name', 'error');
    if (!email || !email.includes('@')) return showToast('Please enter a valid email', 'error');
    if (!review) return showToast('Please write your review', 'error');

    const btn = document.getElementById('review-submit-btn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
    try {
        await apiFetch(`${API_BASE}/reviews`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, review, profession }),
        });
        document.getElementById('review-name').value = '';
        document.getElementById('review-email').value = '';
        document.getElementById('review-profession').value = '';
        document.getElementById('review-text').value = '';
        showToast('Thank you for your review!', 'success');
        await Promise.all([loadReviews(), loadHomeTestimonials()]);
    } catch (err) {
        showToast(err.message || 'Failed to submit review', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit Review';
    }
}

function reviewAvatar(name) {
    const parts = (name || 'U').trim().split(/\s+/);
    return (parts[0][0] + (parts[1] ? parts[1][0] : '')).toUpperCase();
}

const _avatarColors = ['#3ecf8e', '#8b5cf6', '#f59e0b', '#3b82f6', '#ec4899', '#14b8a6'];
function avatarColor(name) {
    let hash = 0;
    for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) >>> 0;
    return _avatarColors[hash % _avatarColors.length];
}

function formatReviewDate(iso) {
    try {
        const d = new Date(iso);
        return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
    } catch (e) {
        return '';
    }
}

async function loadReviews() {
    try {
        const data = await apiFetch(`${API_BASE}/reviews`).then(r => r.json());
        const list = document.getElementById('reviews-list');
        const reviews = data.reviews || [];
        if (!reviews.length) {
            list.innerHTML = `<div class="reviews-empty glass-card"><i class="fas fa-star"></i> No reviews yet — be the first to leave one!</div>`;
            return;
        }
        list.innerHTML = reviews.map(r => `
            <div class="review-card glass-card">
                <div class="review-card-head">
                    <div class="review-avatar" style="background:${avatarColor(r.name || 'U')}">${reviewAvatar(r.name)}</div>
                    <div>
                        <div class="review-name">${r.name || 'Anonymous'}${r.profession ? `<span class="review-profession"><i class="fas fa-briefcase"></i> ${r.profession}</span>` : ''}</div>
                        <div class="review-date">${formatReviewDate(r.created_at)}</div>
                    </div>
                    <div class="review-stars"><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i></div>
                </div>
                <p class="review-text">${r.review || ''}</p>
            </div>
        `).join('');
    } catch (err) {
        document.getElementById('reviews-list').innerHTML = `<div class="reviews-empty glass-card"><i class="fas fa-exclamation-circle"></i> Could not load reviews.</div>`;
    }
}

async function loadHomeTestimonials() {
    const container = document.getElementById('home-testimonials');
    if (!container) return;
    try {
        const data = await apiFetch(`${API_BASE}/reviews`).then(r => r.json());
        const reviews = data.reviews || [];
        if (!reviews.length) return; // keep the default static testimonials
        const shuffled = [...reviews].sort(() => 0.5 - Math.random()).slice(0, 3);
        container.innerHTML = shuffled.map(r => `
            <div class="cf-testimonial glass-card">
                <div class="cf-testi-quote"><i class="fas fa-quote-left"></i></div>
                <p class="cf-testi-text">${r.review || ''}</p>
                <div class="cf-testi-author">
                    <div class="cf-testi-avatar" style="background:${avatarColor(r.name || 'U')}">${reviewAvatar(r.name)}</div>
                    <div>
                        <div class="cf-testi-name">${r.name || 'Anonymous'}</div>
                        <div class="cf-testi-role">${r.profession || r.email || ''}</div>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (err) {
        // keep the default static testimonials on error
    }
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
        const data = await apiFetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
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
                <div class="chat-msg-bubble" style="color:#ef4444">Error: ${err.message || 'Connection failed. Please try again.'}</div>
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
let interviewCompleted = false;

function markInterviewCompleted() {
    interviewCompleted = true;
    updateDashboardProgress();
}

function updateDashboardProgress() {
    const steps = [
        { key: 'resume', done: !!resumeData },
        { key: 'jobs', done: jobsData.length > 0 },
        { key: 'career', done: !!careerPlan },
        { key: 'interview', done: interviewCompleted },
    ];
    const doneCount = steps.filter(s => s.done).length;
    const pct = Math.round((doneCount / steps.length) * 100);
    document.getElementById('dash-progress-pct').textContent = `${pct}%`;
    document.getElementById('dash-progress-fill').style.width = `${pct}%`;
    document.querySelectorAll('.cf-journey-step').forEach(el => {
        const step = steps.find(s => s.key === el.dataset.jstep);
        el.classList.toggle('done', !!(step && step.done));
    });
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
    initSettings();
    checkApiKeyRequired();
    initResume();
    initJobs();
    initCareer();
    initInterview();
    initCoverLetter();
    initChat();
    initReviews();
    initFAQ();

    // Settings toggle icon
    const settingsToggle = document.getElementById('settings-toggle');
    if (settingsToggle) {
        settingsToggle.addEventListener('click', () => navigateTo('settings'));
    }
});
