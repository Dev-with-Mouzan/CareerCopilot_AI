<div align="center">

<img src="https://img.shields.io/badge/Status-Live-brightgreen?style=for-the-badge&logo=vercel" alt="Live"/>
<img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
<img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
<img src="https://img.shields.io/badge/CrewAI-Powered-FF6B6B?style=for-the-badge" alt="CrewAI"/>

<br/>
<br/>

```
  ██████╗ █████╗ ██████╗ ███████╗███████╗██████╗      ██████╗ ██████╗ ██████╗ ██╗██╗      ██████╗ ████████╗
 ██╔════╝██╔══██╗██╔══██╗██╔════╝██╔════╝██╔══██╗    ██╔════╝██╔═══██╗██╔══██╗██║██║     ██╔═══██╗╚══██╔══╝
 ██║     ███████║██████╔╝█████╗  █████╗  ██████╔╝    ██║     ██║   ██║██████╔╝██║██║     ██║   ██║   ██║   
 ██║     ██╔══██║██╔══██╗██╔══╝  ██╔══╝  ██╔══██╗    ██║     ██║   ██║██╔═══╝ ██║██║     ██║   ██║   ██║   
 ╚██████╗██║  ██║██║  ██║███████╗███████╗██║  ██║    ╚██████╗╚██████╔╝██║     ██║███████╗╚██████╔╝   ██║   
  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝    ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝ ╚═════╝    ╚═╝   
```

### 🚀 Your Agentic Job Matcher & Career Strategist

*Stop applying blindly. Start landing interviews.*

<br/>

[![🌐 Live Demo](https://img.shields.io/badge/🌐%20Live%20Demo-career--copilot--ai--five.vercel.app-6366F1?style=for-the-badge)](https://career-copilot-ai-five.vercel.app/)

</div>

---

## 📖 Overview

**CareerCopilot AI** is a premium, multi-agent AI system that automates every stage of the modern job search. Powered by **CrewAI**, it deploys a coordinated team of specialized AI agents — a **Job Hunter**, an **ATS Analyst**, and a **Career Strategist** — working in parallel to find your dream remote roles, rewrite your resume for maximum ATS impact, and chart a long-term career roadmap tailored to you.

> **No more spray-and-pray applications. Just targeted, data-driven career moves.**

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Multi-Source Job Scouting** | Real-time scraping and analysis of listings from LinkedIn, Remotive, Jobicy, and more |
| 📊 **Smart ATS Scoring** | Deep resume-to-JD compatibility analysis with an exact keyword match percentage |
| 📝 **AI Resume Optimization** | High-impact rewrites, targeted keyword injection, and bullet-point enhancements |
| 💡 **Strategic Career Coaching** | Personalized 30-60-90 day action plans with skill-building and networking roadmaps |
| 🤖 **Persistent AI Chat Coach** | Gemini 2.0-powered coach that retains context across your resume and full session history |
| 💎 **Premium UI** | Glassmorphism design with dynamic particles, micro-animations, and a dark-mode aesthetic |

---

## 🛠️ Tech Stack

### Backend — AI & Logic
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Agent Orchestration**: [CrewAI](https://crewai.com/)
- **LLMs**:
  - **Llama 3.3 via Groq** — High-speed web scraping and tool-calling
  - **Gemini 2.0 Flash via Google** — Deep analytical reasoning and coaching
- **Resume Parsing**: PyPDF2
- **Web Scraping**: BeautifulSoup4, Requests

### Frontend — UI/UX
- **Styling**: Vanilla CSS3 (Custom Design System) + [Tailwind CSS](https://tailwindcss.com/)
- **Logic**: Vanilla JavaScript (Async/Await API Integration)
- **Aesthetics**: Glassmorphism, Micro-animations, Backdrop Filters
- **Typography**: Inter (Google Fonts)

### DevOps & Infrastructure
- **Backend Hosting**: [Railway](https://railway.app/) — Persistent background task processing
- **Frontend Hosting**: [Vercel](https://vercel.com/) — Lightning-fast static delivery
- **Dependency Management**: [UV](https://docs.astral.sh/uv/)

---

## 🏗️ Project Architecture

```
MatchForge-AI/
│
├── api/                        # FastAPI Backend
│   └── main.py                 # Endpoints, session logic & middleware
│
├── frontend/                   # Web Interface
│   ├── index.html              # Glassmorphic UI shell
│   ├── script.js               # API integration & state management
│   └── style.css               # Custom animations, variables & theme
│
├── src/career_copilot_ai/      # Core AI Engine (CrewAI)
│   ├── config/                 # YAML configs for Agents & Tasks
│   │   ├── agents.yaml
│   │   └── tasks.yaml
│   ├── tools/                  # Custom scraping & search tools
│   ├── crew.py                 # Multi-agent orchestration logic
│   └── main.py                 # AI crew entry point
│
├── requirements.txt
└── README.md
```

---

## 🤖 Meet the AI Crew

<table>
<tr>
<td width="33%" align="center">
<h3>🔍 Lead Job Hunter</h3>
<p>Scours LinkedIn and top remote job boards to surface the highest-quality matches aligned with your exact skill set, experience level, and role preferences.</p>
</td>
<td width="33%" align="center">
<h3>📊 ATS Analyst</h3>
<p>An expert in Applicant Tracking Systems. Analyzes job descriptions to find keyword gaps, scores your existing resume, and rewrites it for maximum ATS pass-through.</p>
</td>
<td width="33%" align="center">
<h3>💡 Career Strategist</h3>
<p>Synthesizes all data into a cohesive career plan — ensuring you aren't just landing a job, but intentionally building the career you want.</p>
</td>
</tr>
</table>

---

## 🚀 Getting Started

### Prerequisites
- Python **3.10+**
- [UV](https://docs.astral.sh/uv/) *(recommended for fast dependency management)*

### 1 — Clone the Repository
```bash
git clone https://github.com/your-username/career-copilot-ai.git
cd career-copilot-ai
```

### 2 — Configure Environment Variables
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key
GOOGLE_API_KEY=your_google_api_key
```

### 3 — Install Dependencies
```bash
uv pip install -r requirements.txt
```

### 4 — Run the Application

**Start the backend server:**
```bash
uv run uvicorn api.main:app --reload
```

**Launch the frontend:**
Open `frontend/index.html` in your browser, or start a local live server.

---

## 🌐 Deployment

| Layer | Platform | Purpose |
|---|---|---|
| **Frontend** | [Vercel](https://vercel.com/) | Global CDN, instant static delivery |
| **Backend** | [Railway](https://railway.app/) | Persistent server for long-running AI tasks |

**🔗 Live Application: [https://career-copilot-ai-five.vercel.app/](https://career-copilot-ai-five.vercel.app/)**

---

## 🗺️ Roadmap

- [ ] LinkedIn OAuth integration for one-click profile import
- [ ] Automated job application submission
- [ ] Interview preparation agent with mock Q&A
- [ ] Salary benchmarking and negotiation coaching
- [ ] Browser extension for real-time JD analysis

---

## 🤝 Contributing

Contributions are welcome! Please open an issue first to discuss what you'd like to change, then submit a pull request.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add your feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---



<div align="center">

Built with ❤️ by **Agentic Lab**

*If CareerCopilot helped you land a role, consider giving this repo a ⭐ — it means the world!*

[![Live Demo](https://img.shields.io/badge/Try%20It%20Now-career--copilot--ai--five.vercel.app-6366F1?style=for-the-badge)](https://career-copilot-ai-five.vercel.app/)

</div>
