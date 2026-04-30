from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from career_copilot_ai.tools.custom_tool import TopJobsScraperTool, VectorDBQueryTool
from pydantic import BaseModel, Field
from typing import List

class ScoredJob(BaseModel):
    job_title: str = Field(description="The title of the job.")
    company: str = Field(description="The company offering the job.")
    link: str = Field(description="URL link to the job posting.")
    ats_score: int = Field(description="The ATS match score out of 100.")
    missing_keywords: List[str] = Field(description="Keywords missing from the resume.")
    match_reasoning: str = Field(description="Short explanation of why this job matches the resume.")

class JobReport(BaseModel):
    top_jobs: List[ScoredJob] = Field(description="List of top scored jobs.")

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class CareerCopilotAi():
    """CareerCopilotAi crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def job_scraper(self) -> Agent:
        return Agent(
            config=self.agents_config['job_scraper'], # type: ignore[index]
            tools=[TopJobsScraperTool()],
            verbose=True
        )

    @agent
    def ats_scorer(self) -> Agent:
        return Agent(
            config=self.agents_config['ats_scorer'], # type: ignore[index]
            verbose=True
        )

    @agent
    def career_coach(self) -> Agent:
        return Agent(
            config=self.agents_config['career_coach'], # type: ignore[index]
            verbose=True,
            memory=False
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
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
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            memory=False,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
