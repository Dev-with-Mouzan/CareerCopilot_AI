<div align="center">

<img src="https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge&logo=vercel" alt="Active"/>
<img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
<img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
<img src="https://img.shields.io/badge/LangGraph-Workflows-FF6B6B?style=for-the-badge" alt="LangGraph"/>

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

**CareerCopilot AI** is a multi-workflow AI system that automates every stage of the modern job search. Built on **LangGraph**, it deploys six specialized workflows — **Resume Parser**, **Job Matcher**, **ATS Analyzer**, **Career Strategist**, **Interview Coach**, and **Chat Assistant** — that work together through shared state to find your dream roles, optimize your resume, and build a personalized career roadmap.

> **No more spray-and-pray applications. Just targeted, data-driven career moves.**

---

## ✨ Features

| Feature | Description |
|---|---|
| 📝 **Resume Parsing** | Deterministic PDF/DOCX extraction into structured profiles with skill detection across 300+ technologies |
| 🔍 **Multi-Source Job Discovery** | Aggregates listings from LinkedIn, Remotive, Jobicy, and custom scrapers with deduplication |
| 🎯 **Skill-Based Job Matching** | Multi-factor scoring: skill overlap, experience level, seniority, location, salary, and semantic similarity |
| 📊 **ATS Compatibility Scoring** | Keyword coverage, skill gaps, experience alignment, and LLM-powered improvement recommendations |
| 💡 **Strategic Career Planning** | Skill gap analysis, market intelligence, learning roadmaps, and 30-60-90 day action plans |
| 🤖 **Interview Preparation** | Targeted question generation with answer evaluation across technical, behavioral, and system design categories |
| 💬 **AI Chat Assistant** | Context-aware coaching with conversation history and tool usage tracking |
| ⚙️ **Model Settings** | Choose your AI provider and model from the UI — Gemini, OpenAI, DeepSeek, Qwen — with per-user API key support |
| 🔐 **JWT + API Key Auth** | Secure authentication with bcrypt password hashing and token-based access |
| 📈 **Observability** | Request tracing, LLM token tracking, cost estimation, and structured logging |
| 💎 **Premium UI** | Glassmorphism design with dynamic particles, micro-animations, and dark-mode aesthetic |

---

## 🛠️ Tech Stack

### Backend — AI & Logic
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **AI Orchestration**: [LangGraph](https://langchain-ai.github.io/langgraph/) — stateful graph workflows
- **LLM Routing**: [LiteLLM](https://docs.litellm.ai/) — unified interface for Gemini, Groq, OpenAI, DeepSeek, Qwen, Anthropic
- **Database**: [PostgreSQL](https://www.postgresql.org/) + [pgvector](https://github.com/pgvector/pgvector) (async via SQLAlchemy 2.0)
- **Cache**: [Redis](https://redis.io/) — multi-layer caching (in-memory + Redis)
- **Auth**: JWT (PyJWT) + API key headers
- **Resume Parsing**: PyMuPDF (primary), PyPDF2 (fallback), python-docx
- **Scraping**: HTTPX, BeautifulSoup4

### Frontend — UI/UX
- **Styling**: [Tailwind CSS](https://tailwindcss.com/) + custom glassmorphism design system
- **Logic**: Vanilla JavaScript (Async/Await API integration)
- **Aesthetics**: Glassmorphism, micro-animations, backdrop filters, particle effects
- **Typography**: Inter (Google Fonts)

### DevOps & Infrastructure
- **Backend Hosting**: [AWS](https://aws.amazon.com/) — persistent server for AI workloads
- **Frontend Hosting**: [Vercel](https://vercel.com/) — global CDN, instant static delivery
- **Dependency Management**: [UV](https://docs.astral.sh/uv/)

---

## 🏗️ Project Architecture

```
CareerCopilot_AI/
│
├── backend/                     # FastAPI + LangGraph Backend
│   ├── main.py                  # App entrypoint, middleware, lifespan
│   ├── core/
│   │   ├── config.py            # Pydantic settings (env-driven)
│   │   ├── models.py            # SQLAlchemy ORM models (14 tables)
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   └── state.py             # LangGraph TypedDict state definitions
│   │
│   ├── graphs/                  # LangGraph workflow definitions
│   │   ├── orchestrator.py      # Pipeline registry & full-pipeline coordinator
│   │   ├── resume_graph.py      # Resume parsing workflow
│   │   ├── job_graph.py         # Job discovery & matching workflow
│   │   ├── ats_graph.py         # ATS scoring workflow
│   │   ├── career_graph.py      # Career planning workflow
│   │   ├── interview_graph.py   # Interview prep workflow
│   │   └── chat_graph.py        # Conversational AI workflow
│   │
│   ├── services/                # Deterministic & LLM-powered services
│   │   ├── resume_parser.py     # PDF/DOCX → structured profile
│   │   ├── job_normalizer.py    # Raw job data normalization
│   │   ├── job_deduplicator.py  # Cross-source deduplication
│   │   ├── skill_matcher.py     # Multi-factor skill matching
│   │   ├── skill_gap_engine.py  # Gap analysis & learning paths
│   │   ├── ats_engine.py        # Deterministic ATS scoring
│   │   ├── market_analyzer.py   # Market intelligence aggregation
│   │   ├── embeddings.py        # Vector embedding service (pgvector)
│   │   ├── cache.py             # Multi-layer cache (memory + Redis)
│   │   ├── llm_service.py       # Model router, fallback, cost tracking
│   │   └── job_sources/         # Job board integrations
│   │       ├── base.py          # Abstract source interface
│   │       ├── linkedin.py      # LinkedIn Guest API
│   │       ├── remotive.py      # Remotive Public API
│   │       ├── jobicy.py        # Jobicy Public API
│   │       ├── generic_scraper.py
│   │       └── manager.py       # Source orchestrator
│   │
│   ├── api/                     # FastAPI route handlers
│   │   ├── router.py            # Central router (aggregates sub-routers)
│   │   ├── resume.py            # Resume upload & parsing endpoints
│   │   ├── jobs.py              # Job search & match endpoints
│   │   ├── ats.py               # ATS scoring endpoints
│   │   ├── career.py            # Career planning endpoints
│   │   ├── interview.py         # Interview prep endpoints
│   │   ├── chat.py              # Chat assistant endpoints
│   │   ├── applications.py      # Application tracking endpoints
│   │   └── admin.py             # Admin & health check endpoints
│   │
│   ├── security/                # Auth & rate limiting
│   │   ├── auth.py              # JWT + API key authentication
│   │   ├── rate_limit.py        # Per-IP rate limiting
│   │   └── sanitization.py      # Input sanitization
│   │
│   ├── observability/           # Monitoring & tracing
│   │   ├── tracing.py           # Request tracing middleware
│   │   └── metrics.py           # In-memory metrics collector
│   │
│   └── db/                      # Database layer
│       ├── session.py           # Async session management
│       └── migrations.py        # Alembic migration helpers
│
├── frontend/                    # Web Interface
│   ├── index.html               # Glassmorphic UI shell
│   ├── script.js                # API integration & state management
│   └── style.css                # Custom animations, variables & theme
│
├── tests/                       # Test suite
│   ├── unit/
│   ├── integration/
│   ├── graph/
│   ├── security/
│   └── evaluation/
│
├── api/                         # Legacy CrewAI backend (deprecated)
├── .env.example                 # Environment variable template
├── pyproject.toml               # Project metadata & tool config
├── requirements.txt             # Python dependencies
└── README.md
```

---

## 🤖 Meet the AI Workflows

<table>
<tr>
<td width="33%" align="center">
<h3>📝 Resume Parser</h3>
<p>Deterministic extraction from PDF/DOCX into structured profiles. Detects 300+ skills, parses experience, education, projects, and certifications with content-hash caching.</p>
</td>
<td width="33%" align="center">
<h3>🔍 Job Matcher</h3>
<p>Aggregates from LinkedIn, Remotive, and Jobicy. Normalizes schemas, deduplicates across sources, and scores matches using skill overlap, experience alignment, seniority, location, and salary.</p>
</td>
<td width="33%" align="center">
<h3>📊 ATS Analyzer</h3>
<p>Deterministic keyword/skill/education scoring plus LLM-powered explanation. Generates actionable recommendations and improved resume sections.</p>
</td>
</tr>
<tr>
<td width="33%" align="center">
<h3>💡 Career Strategist</h3>
<p>Identifies skill gaps against market demand, analyzes salary distributions, and builds personalized 30-60-90 day action plans with learning roadmaps.</p>
</td>
<td width="33%" align="center">
<h3>🤖 Interview Coach</h3>
<p>Generates targeted questions (technical, behavioral, system design) based on your resume and target role. Evaluates answers with detailed feedback.</p>
</td>
<td width="33%" align="center">
<h3>💬 Chat Assistant</h3>
<p>Context-aware career coaching with conversation history. Leverages resume profile and job data for personalized guidance.</p>
</td>
</tr>
</table>

---

## 🚀 Getting Started

### Prerequisites
- Python **3.10+**
- **PostgreSQL** (with pgvector extension for semantic search)
- **Redis** (for caching layer)
- [UV](https://docs.astral.sh/uv/) *(recommended)*

### 1 — Clone the Repository
```bash
git clone https://github.com/Dev-with-Mouzan/CareerCopilot_AI.git
cd CareerCopilot_AI
```

### 2 — Configure Environment Variables
Copy the example and fill in your keys:
```bash
cp .env.example .env
```

### 3 — Install Dependencies
```bash
uv sync
uv pip install -r requirements.txt
```

### 4 — Set Up the Database
```bash
# Create the database
createdb careercopilot

# Tables are created automatically on first startup
# For production, use Alembic migrations
```

### 5 — Run the Application

**Start the backend server:**
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Launch the frontend:**
Open `frontend/index.html` in your browser, or start a local live server.

**API docs available at:** `http://localhost:8000/docs`

---

## 🔧 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `CC_POSTGRES_URL` | Yes | `postgresql+asyncpg://postgres:postgres@localhost:5432/careercopilot` | Async PostgreSQL connection string |
| `CC_REDIS_URL` | No | `redis://localhost:6379/0` | Redis URL for caching (empty = no cache) |
| `CC_JWT_SECRET` | Yes | `change-me-in-production` | Secret key for JWT signing |
| `CC_GEMINI_API_KEY` | Yes* | | Google Gemini API key |
| `CC_GROQ_API_KEY` | No | | Groq API key (fallback provider) |
| `CC_OPENAI_API_KEY` | No | | OpenAI API key (fallback provider) |
| `CC_DEEPSEEK_API_KEY` | No | | DeepSeek API key (V3 / R1 models) |
| `CC_QWEN_API_KEY` | No | | Alibaba Qwen API key (DashScope) |
| `CC_LLM_PROVIDER` | No | `gemini` | Primary LLM provider |
| `CC_FAST_MODEL` | No | `gemini/gemini-2.5-flash-lite` | Fast model for extraction tasks |
| `CC_STRONG_MODEL` | No | `gemini/gemini-2.5-flash` | Strong model for analysis tasks |
| `CC_EMBEDDING_MODEL` | No | `text-embedding-004` | Embedding model for semantic search |
| `CC_DEBUG` | No | `false` | Enable debug logging |
| `CC_ENVIRONMENT` | No | `development` | `development` / `staging` / `production` |

> **Note:** All env vars use the `CC_` prefix (configurable in `backend/core/config.py`).

---

## 🌐 API Overview

All endpoints are prefixed with `/api`. Authentication via `Authorization: Bearer <token>` or `X-API-Key` header.

| Tag | Endpoints | Description |
|---|---|---|
| **Resumes** | `POST /api/resumes/upload`, `GET /api/resumes/{id}` | Upload and parse resumes |
| **Jobs** | `POST /api/jobs/search`, `GET /api/jobs/{id}` | Search, match, and retrieve jobs |
| **ATS** | `POST /api/ats/analyze`, `GET /api/ats/{id}` | ATS compatibility scoring |
| **Career** | `POST /api/career/plan`, `GET /api/career/{id}` | Career planning and skill gaps |
| **Interviews** | `POST /api/interviews/start`, `POST /api/interviews/answer` | Interview prep sessions |
| **Chat** | `POST /api/chat`, `GET /api/chat/{conversation_id}` | Conversational AI assistant |
| **Applications** | `POST /api/applications`, `GET /api/applications` | Application tracking |
| **Admin** | `GET /api/health`, `GET /api/metrics` | Health checks and metrics |

---

## 🌐 Deployment

| Layer | Platform | Purpose |
|---|---|---|
| **Frontend** | [Vercel](https://career-copilot-ai-five.vercel.app) | Global CDN, instant static delivery |
| **Backend** | AWS | Persistent server for AI workloads |

**🔗 Live Application: [https://career-copilot-ai-five.vercel.app/](https://career-copilot-ai-five.vercel.app/)**

---

## 🗺️ Roadmap

- [x] Resume parsing with skill detection
- [x] Multi-source job aggregation (LinkedIn, Remotive, Jobicy)
- [x] Skill-based job matching with scoring
- [x] ATS compatibility analysis
- [x] Career planning with skill gap analysis
- [x] Interview preparation with answer evaluation
- [x] Conversational AI chat assistant
- [x] JWT + API key authentication
- [x] Request tracing and LLM cost tracking
- [ ] Alembic database migrations
- [ ] WebSocket real-time job alerts
- [ ] Browser extension for live JD analysis
- [ ] Resume version diff and A/B testing
- [ ] Salary negotiation coaching module
- [ ] Multi-language resume support

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

Built with ❤️ by **Mouzan Raza**

*If CareerCopilot helped you land a role, consider giving this repo a ⭐ — it means the world!*

[![Live Demo](https://img.shields.io/badge/Try%20It%20Now-career--copilot--ai--five.vercel.app-6366F1?style=for-the-badge)](https://career-copilot-ai-five.vercel.app/)

</div>
