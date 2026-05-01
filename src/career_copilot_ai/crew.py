from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from career_copilot_ai.tools.custom_tool import TopJobsScraperTool, VectorDBQueryTool, LinkedInJobsScraperTool, RemotiveAPITool, JobicyAPITool
from pydantic import BaseModel, Field
from typing import List
import os

# ---------------------------------------------------------------------------
# LLM Configuration
#   • job_scraper  → Groq  (fast, good at tool-calling & web scraping tasks)
#   • ats_scorer   → Gemini (strong analytical reasoning for scoring)
#   • career_coach → Gemini (natural, conversational guidance)
# ---------------------------------------------------------------------------
_GROQ_LLM = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=os.environ.get("GROQ_API_KEY"),
    temperature=0.3,       # Lower = more consistent tool calls
)

_GEMINI_LLM = LLM(
    model="gemini/gemini-2.5-flash-lite",
    api_key=os.environ.get("GOOGLE_API_KEY"),
    temperature=0.5,
)

class ScoredJob(BaseModel):
    job_title: str = Field(description="The title of the job.")
    company: str = Field(description="The company offering the job.")
    link: str = Field(description="URL link to the job posting.")
    ats_score: int = Field(description="The ATS match score out of 100.")
    missing_keywords: List[str] = Field(description="Keywords missing from the resume.")
    match_reasoning: str = Field(description="Short explanation of why this job matches the resume.")

class JobReport(BaseModel):
    top_jobs: List[ScoredJob] = Field(description="List of top scored jobs.")

@CrewBase
class CareerCopilotAi():
    """CareerCopilotAi crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def job_scraper(self) -> Agent:
        return Agent(
            config=self.agents_config['job_scraper'], # type: ignore[index]
            llm=_GROQ_LLM,                           # Groq: fast tool calls
            tools=[TopJobsScraperTool(), LinkedInJobsScraperTool(), RemotiveAPITool(), JobicyAPITool()],
            verbose=True
        )

    @agent
    def ats_scorer(self) -> Agent:
        return Agent(
            config=self.agents_config['ats_scorer'], # type: ignore[index]
            llm=_GEMINI_LLM,                         # Gemini: deep analysis
            verbose=True
        )

    @agent
    def career_coach(self) -> Agent:
        return Agent(
            config=self.agents_config['career_coach'], # type: ignore[index]
            llm=_GEMINI_LLM,                           # Gemini: natural chat
            tools=[VectorDBQueryTool()],               # Can query saved job chunks
            verbose=True,
            memory=False
        )

    @task
    def scrape_jobs_task(self) -> Task:
        return Task(
            config=self.tasks_config['scrape_jobs_task'], # type: ignore[index]
        )

    @task
    def ats_scoring_task(self) -> Task:
        return Task(
            config=self.tasks_config['ats_scoring_task'], # type: ignore[index]
            output_pydantic=JobReport
        )

    @task
    def career_coaching_task(self) -> Task:
        return Task(
            config=self.tasks_config['career_coaching_task'], # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the CareerCopilotAi crew"""
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks,   # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            memory=False,
        )
