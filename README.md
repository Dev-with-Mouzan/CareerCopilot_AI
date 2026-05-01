# CareerCopilot AI 🚀
### *Your Agentic Job Matcher & Career Strategist*

CareerCopilot AI is a premium, multi-agent AI system designed to automate the modern job search. Powered by **CrewAI**, it orchestrates a team of specialized agents—a **Job Hunter**, an **ATS Analyst**, and a **Career Strategist**—to help users find their dream remote jobs, optimize their resumes, and build a long-term career roadmap.

---

## ✨ Key Features

- 🔍 **Automated Multi-Source Scouting**: Scrapes and analyzes job listings from LinkedIn, Remotive, Jobicy, and more in real-time.
- 📊 **Smart ATS Scoring**: Performs deep analysis of resume compatibility with target job descriptions, providing an exact match percentage.
- 📝 **AI-Driven Resume Optimization**: Generates high-impact rewrites, keyword suggestions, and bullet-point enhancements.
- 💡 **Strategic Career Coaching**: Provides a 30-60-90 day action plan, including skill-building roadmaps and networking strategies.
- 🤖 **Interactive AI Chat**: A persistent career coach (powered by Gemini 2.0) that remembers your resume and previous conversations.
- 💎 **Premium UI**: A stunning, modern web interface featuring glassmorphism, dynamic particles, and a seamless "dark mode" aesthetic.

---

## 🛠️ Tech Stack

### **Backend (AI & Logic)**
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Agent Orchestration**: [CrewAI](https://crewai.com/)
- **LLMs**: 
  - **Llama 3.3 (Groq)**: For high-speed web scraping and tool-calling.
  - **Gemini 2.0 Flash (Google)**: For deep analytical reasoning and coaching.
- **Parsing**: PyPDF2 (Resume extraction)
- **Scraping**: BeautifulSoup4, Requests

### **Frontend (UI/UX)**
- **Styling**: Vanilla CSS3 (Custom Design System) + [Tailwind CSS](https://tailwindcss.com/)
- **Logic**: Vanilla JavaScript (Async/Await API Integration)
- **Aesthetics**: Glassmorphism, Micro-animations, Backdrop Filters
- **Typography**: Inter (Google Fonts)

### **DevOps & Infrastructure**
- **Backend Hosting**: [Railway](https://railway.app/)
- **Frontend Hosting**: [Vercel](https://vercel.com/)
- **Dependency Management**: [UV](https://docs.astral.sh/uv/)

---

## 🏗️ Project Architecture

```text
MatchForge-AI/
├── api/                  # FastAPI Backend API
│   └── main.py           # API endpoints & session logic
├── frontend/             # Modern Web Interface
│   ├── index.html        # Glassmorphic UI
│   ├── script.js         # API Integration & UI logic
│   └── style.css         # Custom animations & theme
├── src/career_copilot_ai/ # Core AI Logic (CrewAI)
│   ├── config/           # YAML configs for Agents & Tasks
│   ├── tools/            # Custom Job Scraping & Search Tools
│   ├── crew.py           # Multi-agent orchestration
│   └── main.py           # Entry point for the AI crew
├── requirements.txt      # Project dependencies
└── README.md             # Project documentation
```

---

## 🚀 Getting Started

### **1. Prerequisites**
- Python 3.10 or higher
- [UV](https://docs.astral.sh/uv/) (Recommended for fast dependency management)

### **2. Environment Setup**
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_key
GOOGLE_API_KEY=your_google_key
```

### **3. Installation**
```bash
# Install dependencies
uv pip install -r requirements.txt
```

### **4. Running the Project**

**Start the Backend:**
```bash
uv run uvicorn api.main:app --reload
```

**Launch the Frontend:**
Simply open `frontend/index.html` in your browser or use a local live server.

---

## 🤖 Meet the AI Crew

- **Lead Job Hunter**: Scours LinkedIn and remote job boards to find the highest-quality matches for your specific skill set.
- **ATS Analyst**: Expert in Applicant Tracking Systems. Analyzes job descriptions to find keyword gaps and rewrites your resume for maximum impact.
- **Career Strategist**: Synthesizes all data into a cohesive career plan, ensuring you aren't just getting a job, but building a career.

---

## 🌐 Deployment

- **Backend**: Deployed on **Railway** for persistent background task processing.
- **Frontend**: Deployed on **Vercel** for lightning-fast static delivery.

---

Built with ❤️ by **Agentic Lab**
