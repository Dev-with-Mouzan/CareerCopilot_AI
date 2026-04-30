# CareerCopilot AI Crew

Welcome to the CareerCopilot AI Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

## Project Structure

```text
CareerCopilot-AI/
├── api/                  # Backend API (FastAPI) for resume parsing and job matching
│   └── main.py           # API endpoints and logic
├── frontend/             # Premium web interface
│   ├── assets/           # UI assets (images, icons)
│   ├── index.html        # Main entry point
│   ├── script.js         # Frontend logic and API integration
│   └── style.css         # Custom premium styling
├── src/career_copilot_ai/ # Core Multi-Agent System (CrewAI)
│   ├── config/           # Configuration files
│   │   ├── agents.yaml   # Agent roles and goals
│   │   └── tasks.yaml    # Task definitions
│   ├── tools/            # Custom agent tools
│   │   └── custom_tool.py
│   ├── crew.py           # Crew orchestration logic
│   ├── main.py           # Entry point for the AI system
│   └── utils.py          # Helper functions
├── knowledge/            # Domain-specific knowledge base for agents
├── tests/                # Automated testing suite
├── AGENTS.md             # CrewAI reference guide
├── pyproject.toml        # Project dependencies and configuration (uv)
└── vercel.json           # Vercel deployment configuration
```


## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```
### Customizing

**Add your `OPENAI_API_KEY` into the `.env` file**

- Modify `src/career_copilot_ai/config/agents.yaml` to define your agents
- Modify `src/career_copilot_ai/config/tasks.yaml` to define your tasks
- Modify `src/career_copilot_ai/crew.py` to add your own logic, tools and specific args
- Modify `src/career_copilot_ai/main.py` to add custom inputs for your agents and tasks

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
$ crewai run
```

This command initializes the CareerCopilot AI Crew, assembling the agents and assigning them tasks as defined in your configuration.

This example, unmodified, will run the create a `report.md` file with the output of a research on LLMs in the root folder.

## Understanding Your Crew

The CareerCopilot AI Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

## Support

For support, questions, or feedback regarding the CareerCopilot AI Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.
