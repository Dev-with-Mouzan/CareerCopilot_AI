// CareerCopilot AI - Enhanced Frontend JavaScript
// API Base URL - adjust for production
const API_BASE = 'https://careercopolitai-production.up.railway.app';

// State
let currentJobId = null;
let isUploading = false;
let resumeUploaded = false;
let agentStatusInterval = null;

// ============================================
// Particle Background Effect
// ============================================
function createParticles() {
    const container = document.getElementById('particles-container');
    if (!container) return;

    const particleCount = 30;

    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';

        const size = Math.random() * 4 + 2;
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.animationDelay = `${Math.random() * 20}s`;
        particle.style.animationDuration = `${15 + Math.random() * 20}s`;

        // Random gradient colors
        const colors = [
            'radial-gradient(circle, #6366f1 0%, transparent 70%)',
            'radial-gradient(circle, #22d3ee 0%, transparent 70%)',
            'radial-gradient(circle, #a855f7 0%, transparent 70%)'
        ];
        particle.style.background = colors[Math.floor(Math.random() * colors.length)];

        container.appendChild(particle);
    }
}

// ============================================
// Toast Notifications - Enhanced
// ============================================
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = {
        success: '✓',
        error: '✕',
        info: 'ℹ'
    };

    toast.innerHTML = `
        <span class="text-xl">${icons[type]}</span>
        <span class="text-sm font-medium">${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'toastSlideOut 0.4s ease forwards';
        setTimeout(() => toast.remove(), 400);
    }, 4000);
}

// ============================================
// Agent Status Updates
// ============================================
function updateAgentStatus(phase) {
    const cards = document.querySelectorAll('.agent-card');
    const statuses = {
        0: ['Active', 'Waiting', 'Waiting', 'Waiting'],
        1: ['Done', 'Active', 'Waiting', 'Waiting'],
        2: ['Done', 'Done', 'Active', 'Waiting'],
        3: ['Done', 'Done', 'Done', 'Active']
    };

    const colors = {
        'Active': 'text-secondary',
        'Done': 'text-green-400',
        'Waiting': 'text-gray-500'
    };

    const currentStatuses = statuses[phase] || statuses[0];

    cards.forEach((card, index) => {
        const statusEl = card.querySelector('.agent-status');
        if (statusEl) {
            statusEl.textContent = currentStatuses[index];
            statusEl.className = `agent-status mt-1 text-xs ${colors[currentStatuses[index]]}`;
        }

        if (currentStatuses[index] === 'Active') {
            card.classList.add('active');
            card.style.borderColor = 'var(--primary)';
        } else {
            card.classList.remove('active');
            card.style.borderColor = '';
        }
    });
}

// ============================================
// File Upload Handling
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    createParticles();

    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');

    // Click to upload
    dropZone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) handleFile(file);
    });

    // Drag and drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
    });
});

function handleFile(file) {
    if (!file.type.includes('pdf')) {
        showToast('Please upload a PDF file', 'error');
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        showToast('File size must be less than 10MB', 'error');
        return;
    }

    // Show file info with animation
    document.getElementById('file-name').textContent = file.name;
    const fileInfo = document.getElementById('file-info');
    fileInfo.classList.remove('hidden');
    fileInfo.style.animation = 'messageIn 0.4s ease-out';

    // Upload the file
    uploadResume(file);
}

async function uploadResume(file) {
    isUploading = true;
    showToast('Uploading resume...', 'info');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE}/api/upload-resume`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            resumeUploaded = true;
            showToast('Resume uploaded successfully!', 'success');

            // Show preview with formatting
            document.getElementById('resume-preview').innerHTML = `
                <div class="space-y-3 animate-messageIn">
                    <div class="flex items-center gap-3 pb-3 border-b border-white/10">
                        <div class="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
                            <svg class="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                            </svg>
                        </div>
                        <div>
                            <p class="text-white font-medium">${escapeHtml(file.name)}</p>
                            <p class="text-xs text-gray-500">${(file.size / 1024).toFixed(2)} KB</p>
                        </div>
                    </div>
                    <div>
                        <p class="text-xs text-gray-500 mb-2 uppercase tracking-wide">Preview</p>
                        <p class="text-gray-300 text-sm leading-relaxed">${data.preview || 'Preview not available'}</p>
                    </div>
                </div>
            `;

            // Enable generate button with visual feedback
            const btn = document.getElementById('generate-btn');
            btn.disabled = false;
            btn.classList.add('ring-2', 'ring-primary/50');
        } else {
            showToast(data.detail || 'Upload failed', 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showToast('Failed to upload resume. Is the server running?', 'error');
    } finally {
        isUploading = false;
    }
}

// ============================================
// Generate Career Plan - Enhanced
// ============================================
async function generateCareerPlan() {
    if (!resumeUploaded) {
        showToast('Please upload a resume first', 'error');
        return;
    }

    const btn = document.getElementById('generate-btn');
    const loadingState = document.getElementById('loading-state');
    const resultsContainer = document.getElementById('results-container');
    const loadingText = document.getElementById('loading-text');
    const loadingBar = document.getElementById('loading-bar');
    const loadingPercent = document.getElementById('loading-percent');
    const agentsStatus = document.getElementById('agents-status');

    btn.disabled = true;
    loadingState.classList.remove('hidden');
    resultsContainer.classList.add('hidden');
    agentsStatus.classList.remove('hidden');

    const loadingMessages = [
        'Analyzing your resume...',
        'Scraping job listings from multiple sources...',
        'Running ATS compatibility analysis...',
        'Generating personalized career plan...',
        'Finalizing recommendations...'
    ];

    let messageIndex = 0;
    let percent = 0;

    const messageInterval = setInterval(() => {
        if (messageIndex < loadingMessages.length) {
            loadingText.textContent = loadingMessages[messageIndex];
            percent = Math.round(((messageIndex + 1) / loadingMessages.length) * 100);
            loadingBar.style.width = `${percent}%`;
            loadingPercent.textContent = `${percent}%`;

            // Update agent status based on phase
            updateAgentStatus(messageIndex);

            messageIndex++;
        }
    }, 1500);

    try {
        const response = await fetch(`${API_BASE}/api/run-crew`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_query: 'What are the best job matches for me based on my resume?',
                websites: 'https://www.workingnamads.com/jobs\nhttps://www.flexjobs.com/remote-jobs#remote-jobs-list'
            })
        });

        const data = await response.json();

        if (response.ok) {
            currentJobId = data.job_id;
            showToast('Career plan generation started!', 'success');

            // Poll for status
            pollStatus(currentJobId);
        } else {
            showToast(data.detail || 'Failed to start generation', 'error');
            loadingState.classList.add('hidden');
            agentsStatus.classList.add('hidden');
            btn.disabled = false;
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to connect to server', 'error');
        loadingState.classList.add('hidden');
        agentsStatus.classList.add('hidden');
        btn.disabled = false;
    } finally {
        clearInterval(messageInterval);
    }
}

async function pollStatus(jobId) {
    const loadingText = document.getElementById('loading-text');

    const poll = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/status/${jobId}`);
            const data = await response.json();

            if (data.status === 'done') {
                document.getElementById('loading-state').classList.add('hidden');
                document.getElementById('agents-status').classList.add('hidden');
                document.getElementById('results-container').classList.remove('hidden');
                document.getElementById('generate-btn').disabled = false;
                showToast('Career plan generated successfully!', 'success');

                // Display results with Markdown rendering
                displayResults(data.result);

                // Auto-fetch jobs
                setTimeout(fetchJobs, 500);
            } else if (data.status === 'failed') {
                document.getElementById('loading-state').classList.add('hidden');
                document.getElementById('agents-status').classList.add('hidden');
                document.getElementById('generate-btn').disabled = false;
                showToast(`Generation failed: ${data.error}`, 'error');
            } else {
                loadingText.textContent = 'Still processing... This may take a few minutes';
                setTimeout(poll, 3000);
            }
        } catch (error) {
            console.error('Poll error:', error);
            setTimeout(poll, 3000);
        }
    };

    poll();
}

function displayResults(result) {
    const careerPlanOutput = document.getElementById('career-plan-output');
    const resumeOptOutput = document.getElementById('resume-optimization-output');

    const rawMarkdown = result && result.raw ? result.raw : (typeof result === 'string' ? result : '');

    if (rawMarkdown) {
        if (typeof marked !== 'undefined') {
            careerPlanOutput.innerHTML = `<div class="markdown-body">${marked.parse(rawMarkdown)}</div>`;
            // Hide the second redundant column to keep it clean
            if (resumeOptOutput && resumeOptOutput.parentElement) {
                resumeOptOutput.parentElement.classList.add('hidden');
            }
            careerPlanOutput.parentElement.classList.replace('lg:grid-cols-2', 'lg:grid-cols-1');
        } else {
            careerPlanOutput.textContent = rawMarkdown;
        }
    } else {
        careerPlanOutput.innerHTML = `
            <div class="flex items-center gap-3 text-gray-500">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
                Results available in raw format
            </div>
        `;
    }
}

// ============================================
// Fetch Jobs - Enhanced
// ============================================
async function fetchJobs() {
    const btn = document.getElementById('fetch-jobs-btn');
    const container = document.getElementById('jobs-container');
    const emptyState = document.getElementById('jobs-empty');

    btn.disabled = true;
    btn.innerHTML = '<span class="flex items-center gap-2"><span class="spinner"></span> Fetching...</span>';

    try {
        const response = await fetch(`${API_BASE}/api/jobs`);
        const data = await response.json();

        if (response.ok) {
            emptyState.classList.add('hidden');
            container.classList.remove('hidden');

            // 1. Try to get jobs from the structured 'jobs' object
            let jobsList = [];
            if (data.jobs) {
                const source = data.jobs.top_jobs || (Array.isArray(data.jobs) ? data.jobs : []);
                jobsList = source.map(j => ({
                    title: j.job_title || j.title || 'Job Position',
                    company: j.company || 'Company',
                    link: j.link || '#',
                    ats_score: j.ats_score || 0,
                    reasoning: j.match_reasoning || j.reasoning || '',
                    location: j.location || 'Remote'
                }));
            }

            // 2. If no structured jobs, try parsing from markdown
            if (jobsList.length === 0 && data.raw_markdown) {
                jobsList = parseJobsFromMarkdown(data.raw_markdown);
            }

            // 3. Display the results
            if (jobsList.length > 0) {
                displayJobs(jobsList, container);
                showToast(`Found ${jobsList.length} job matches!`, 'success');
            } else {
                container.innerHTML = `
                    <div class="col-span-full text-center py-12">
                        <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-primary/10 flex items-center justify-center">
                            <span class="text-2xl">📭</span>
                        </div>
                        <p class="text-gray-400">No jobs found. Try running the career plan again.</p>
                    </div>
                `;
                showToast('Found 0 job matches', 'info');
            }
        } else {
            showToast(data.detail || 'Failed to fetch jobs', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to fetch jobs', 'error');
        container.innerHTML = `
            <div class="col-span-full text-center py-12">
                <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-red-500/10 flex items-center justify-center">
                    <span class="text-2xl">⚠️</span>
                </div>
                <p class="text-gray-400">Failed to connect to server</p>
            </div>
        `;
    } finally {
        btn.disabled = false;
        btn.innerHTML = `
            <span class="flex items-center gap-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                </svg>
                Fetch Jobs
            </span>
        `;
    }
}

function parseJobsFromMarkdown(markdown) {
    const jobs = [];
    if (!markdown) return jobs;
    
    const lines = markdown.split('\n');
    let currentJob = null;

    for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;

        // Pattern 1: **Title** at Company
        // Pattern 2: **Title (Company)**:
        // Pattern 3: **Title** - Company
        const patterns = [
            /\*\*(.+?)\*\*\s+at\s+(.+)/,
            /\d+\.\s+\*\*(.+?)\s+\((.+?)\)\*\*/,
            /\*\*(.+?)\*\*\s+-\s+(.+)/,
            /\d+\.\s+\*\*(.+?)\*\*:\s+(.+)/
        ];

        let match = null;
        for (const regex of patterns) {
            match = trimmed.match(regex);
            if (match) break;
        }

        if (match) {
            if (currentJob) jobs.push(currentJob);
            currentJob = {
                title: match[1].trim(),
                company: match[2].replace(':', '').trim(),
                link: '#',
                location: 'Remote'
            };
        } else if (currentJob) {
            if (trimmed.toLowerCase().includes('link:') || trimmed.toLowerCase().includes('url:')) {
                currentJob.link = trimmed.split(':')[1]?.trim() || '#';
            } else if (trimmed.toLowerCase().includes('reasoning:')) {
                currentJob.reasoning = trimmed.split(':')[1]?.trim();
            }
        }
    }

    if (currentJob) jobs.push(currentJob);
    return jobs.filter(j => j.title).slice(0, 10);
}

function displayJobs(jobs, container) {
    if (jobs.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-12">
                <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-primary/10 flex items-center justify-center">
                    <span class="text-2xl">🔍</span>
                </div>
                <p class="text-gray-400">No jobs found in the response</p>
            </div>
        `;
        return;
    }

    container.innerHTML = jobs.map((job, index) => {
        const matchScore = job.ats_score || (95 - index * 5);
        const matchColor = matchScore >= 85 ? 'text-green-400 bg-green-400/10' :
            matchScore >= 70 ? 'text-yellow-400 bg-yellow-400/10' :
                'text-orange-400 bg-orange-400/10';

        return `
            <div class="job-card group p-5 rounded-xl bg-card border border-white/5 hover:border-primary/50 cursor-pointer relative overflow-hidden" title="${escapeHtml(job.reasoning || '')}">
                <div class="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-primary/10 to-transparent rounded-bl-full pointer-events-none"></div>

                <div class="relative z-10">
                    <div class="flex items-start justify-between mb-3">
                        <div class="flex-1">
                            <h4 class="font-semibold text-white group-hover:text-primary transition-colors">${escapeHtml(job.title) || 'Job Position'}</h4>
                            <p class="text-sm text-gray-400">${escapeHtml(job.company) || 'Company'}</p>
                        </div>
                        <span class="px-2.5 py-1 text-xs font-semibold rounded-full ${matchColor} match-badge">
                            ${matchScore}% Match
                        </span>
                    </div>

                    ${job.location ? `
                        <p class="text-xs text-gray-500 mb-3 flex items-center gap-1">
                            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
                            </svg>
                            ${escapeHtml(job.location)}
                        </p>
                    ` : ''}

                    <a href="${job.link || '#'}" target="_blank" class="inline-flex items-center gap-1.5 text-sm text-primary hover:text-secondary transition-colors font-medium">
                        Apply Now
                        <svg class="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
                        </svg>
                    </a>
                </div>
            </div>
        `;
    }).join('');
}

// ============================================
// Chat Functionality - Enhanced
// ============================================
async function sendMessage(event) {
    event.preventDefault();

    const input = document.getElementById('chat-input');
    const messagesContainer = document.getElementById('chat-messages');
    const message = input.value.trim();

    if (!message) return;

    // Add user message
    addChatMessage(message, 'user');
    input.value = '';

    // Show typing indicator
    const typingId = showTypingIndicator();

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });

        const data = await response.json();

        // Remove typing indicator
        removeTypingIndicator(typingId);

        if (response.ok) {
            addChatMessage(data.reply, 'assistant');
        } else {
            showToast(data.detail || 'Failed to get response', 'error');
            // Add error message to chat
            addChatMessage("Sorry, I encountered an error. Please try again.", 'assistant', true);
        }
    } catch (error) {
        console.error('Chat error:', error);
        removeTypingIndicator(typingId);
        showToast('Failed to connect to chat server', 'error');
        addChatMessage("I'm having trouble connecting. Please check if the server is running.", 'assistant', true);
    }
}

function addChatMessage(content, role, isError = false) {
    const container = document.getElementById('chat-messages');
    const isUser = role === 'user';

    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message flex items-start gap-3';

    messageDiv.innerHTML = `
        <div class="w-10 h-10 rounded-xl ${isUser ? 'bg-gray-600' : 'bg-gradient-to-br from-primary to-secondary'} flex items-center justify-center flex-shrink-0 shadow-lg ${isUser ? '' : 'shadow-primary/25'}">
            <span class="text-lg">${isUser ? '👤' : '🤖'}</span>
        </div>
        <div class="flex-1 overflow-hidden">
            <div class="${isUser ? 'bg-gradient-to-br from-primary/20 to-primary/10 rounded-tr-none' : isError ? 'bg-red-500/10 border-red-500/20' : 'bg-gradient-to-br from-white/5 to-white/10 border-white/5'} rounded-2xl ${isUser ? 'rounded-tl-none' : 'rounded-tl-none'} p-4 max-w-[95%] backdrop-blur-sm border ${isUser ? '' : 'border-white/5'}">
                <div class="markdown-body text-sm leading-relaxed ${isError ? 'text-red-300' : ''}">
                    ${isUser ? `<p>${escapeHtml(content)}</p>` : marked.parse(content)}
                </div>
            </div>
        </div>
    `;

    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

function showTypingIndicator() {
    const container = document.getElementById('chat-messages');
    const id = 'typing-' + Date.now();

    const typingDiv = document.createElement('div');
    typingDiv.id = id;
    typingDiv.className = 'chat-message flex items-start gap-3';
    typingDiv.innerHTML = `
        <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center flex-shrink-0 shadow-lg shadow-primary/25">
            <span class="text-lg">🤖</span>
        </div>
        <div class="bg-white/5 rounded-2xl rounded-tl-none p-4 backdrop-blur-sm border border-white/5">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;

    container.appendChild(typingDiv);
    container.scrollTop = container.scrollHeight;

    return id;
}

function removeTypingIndicator(id) {
    const element = document.getElementById(id);
    if (element) {
        element.style.opacity = '0';
        element.style.transform = 'translateY(10px)';
        setTimeout(() => element.remove(), 200);
    }
}

// ============================================
// Clear Session
// ============================================
async function clearSession() {
    if (!confirm('Are you sure you want to clear all data and start fresh?')) return;

    try {
        const response = await fetch(`${API_BASE}/api/session`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showToast('Session cleared', 'success');

            // Reset UI with animations
            document.getElementById('file-info').classList.add('hidden');
            document.getElementById('resume-preview').innerHTML = '<p class="text-center text-gray-500">Upload a resume to see preview...</p>';
            document.getElementById('results-container').classList.add('hidden');
            document.getElementById('jobs-container').innerHTML = '';
            document.getElementById('jobs-empty').classList.remove('hidden');
            document.getElementById('generate-btn').disabled = true;
            document.getElementById('agents-status').classList.add('hidden');

            // Reset chat
            const chatContainer = document.getElementById('chat-messages');
            chatContainer.innerHTML = `
                <div class="flex items-start gap-3">
                    <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center flex-shrink-0 shadow-lg shadow-primary/25">
                        <span class="text-lg">🤖</span>
                    </div>
                    <div class="flex-1">
                        <div class="bg-gradient-to-br from-white/5 to-white/10 rounded-2xl rounded-tl-none p-4 max-w-[85%] backdrop-blur-sm border border-white/5">
                            <p class="text-sm leading-relaxed">Hi! I'm your AI career coach. I've analyzed your resume and can help you with:</p>
                            <ul class="text-sm mt-2 space-y-1 text-gray-300">
                                <li class="flex items-center gap-2"><span class="text-primary">✓</span> Job search strategies</li>
                                <li class="flex items-center gap-2"><span class="text-primary">✓</span> Resume optimization tips</li>
                                <li class="flex items-center gap-2"><span class="text-primary">✓</span> Interview preparation</li>
                                <li class="flex items-center gap-2"><span class="text-primary">✓</span> Career guidance</li>
                            </ul>
                            <p class="text-sm mt-3 text-gray-400">What would you like to know?</p>
                        </div>
                    </div>
                </div>
            `;

            resumeUploaded = false;
            currentJobId = null;
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to clear session', 'error');
    }
}

// ============================================
// Utility Functions
// ============================================
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function parseMarkdown(text) {
    if (!text) return '';
    return text
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
        .replace(/\*(.*)\*/gim, '<em>$1</em>')
        .replace(/^- (.*$)/gim, '<li>$1</li>')
        .replace(/\n/gim, '<br>');
}

// Health check on load
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/api/health`);
        const data = await response.json();

        if (response.ok && data.status === 'ok') {
            console.log('✓ API Health:', data);
            if (data.resume_loaded) {
                resumeUploaded = true;
                document.getElementById('generate-btn').disabled = false;
                showToast('Welcome back! Resume already loaded.', 'success');
            } else {
                showToast('Connected to CareerCopilot AI', 'success');
            }
        }
    } catch (error) {
        console.log('⚠ API not available - start the backend server');
        showToast('Backend server not running. Start with: uv run uvicorn main:app', 'error');
    }
}

// Smooth scroll for navigation
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Initialize
createParticles();
checkHealth();
