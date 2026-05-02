from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from career_copilot_ai.tools.custom_tool import TopJobsScraperTool, VectorDBQueryTool, LinkedInJobsScraperTool, RemotiveAPITool, JobicyAPITool
from pydantic import BaseModel, Field
from typing import List
import os

# ---------------------------------------------------------------------------
# LLM Configuration
#   • job_hunter         → Groq (Fast tool-calling & web searching)
#   • ats_analyst        → Gemini (Deep analytical reasoning)
#   • career_strategist  → Gemini (Strategic planning)
# ---------------------------------------------------------------------------
_GROQ_LLM = LLM(
    model="groq/llama-3.1-8b-instant",
    api_key=os.environ.get("GROQ_API_KEY"),
    temperature=0.1,       # Lower temperature for precise tool calling
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
    def job_hunter(self) -> Agent:
        return Agent(
            config=self.agents_config['job_hunter'], # type: ignore[index]
            llm=_GROQ_LLM,                           # Groq: ultra-fast tool calls
            tools=[TopJobsScraperTool(), LinkedInJobsScraperTool(), RemotiveAPITool(), JobicyAPITool()],
            verbose=True
        )

    @agent
    def ats_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['ats_analyst'], # type: ignore[index]
            llm=_GEMINI_LLM,                         # Gemini: deep analysis
            verbose=True
        )

    @agent
    def career_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config['career_strategist'], # type: ignore[index]
            llm=_GEMINI_LLM,                           # Gemini: strategic planning
            tools=[VectorDBQueryTool()],               # Can query saved job chunks
            verbose=True,
            memory=False
        )

    @task
    def identify_skill_gaps_task(self) -> Task:
        return Task(
            config=self.tasks_config['identify_skill_gaps_task'], # type: ignore[index]
        )

    @task
    def ats_scoring_task(self) -> Task:
        return Task(
            config=self.tasks_config['ats_scoring_task'], # type: ignore[index]
            output_pydantic=JobReport
        )

    @task
    def provide_strategic_guidance_task(self) -> Task:
        return Task(
            config=self.tasks_config['provide_strategic_guidance_task'], # type: ignore[index]
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
