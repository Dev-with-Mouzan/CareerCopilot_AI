from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from career_copilot_ai.tools.custom_tool import TopJobsScraperTool, VectorDBQueryTool
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
    def job_hunter(self) -> Agent:
        return Agent(
            config=self.agents_config['job_hunter'], # type: ignore[index]
            tools=[TopJobsScraperTool()],
            verbose=True
        )

    @agent
    def ats_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['ats_analyst'], # type: ignore[index]
            verbose=True
        )

    @agent
    def career_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config['career_strategist'], # type: ignore[index]
            tools=[VectorDBQueryTool()],
            verbose=True,
            memory=True
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def scrape_jobs_listings_task(self) -> Task:
        return Task(
            config=self.tasks_config['scrape_jobs_listings_task'], # type: ignore[index]
        )

    @task
    def analyze_job_matches_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_job_matches_task'], # type: ignore[index]
        )

    @task
    def identify_skill_gaps_task(self) -> Task:
        return Task(
            config=self.tasks_config['identify_skill_gaps_task'], # type: ignore[index]
        )

    @task
    def optimize_resume_task(self) -> Task:
        return Task(
            config=self.tasks_config['optimize_resume_task'], # type: ignore[index]
        )

    @task
    def provide_strategic_guidance_task(self) -> Task:
        return Task(
            config=self.tasks_config['provide_strategic_guidance_task'], # type: ignore[index]
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
            memory=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
