#!/usr/bin/env python
import sys
import warnings
import os

from datetime import datetime

from career_copilot_ai.crew import CareerCopilotAi
from career_copilot_ai.utils import extract_text_from_pdf

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    resume_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'resume.pdf')
    resume_text = extract_text_from_pdf(resume_path)

    inputs = {
        'resume': resume_text,
        'websites': 'https://www.workingnomads.com/jobs\nhttps://remote.co/\nhttps://remotive.com/\nhttps://www.linkedin.com/jobs/remote-jobs/?f_W=2%2C4&originalSubdomain=pk\nhttps://www.flexjobs.com/remote-jobs#remote-jobs-list'
    }

    try:
        CareerCopilotAi().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")

def chat():
    """
    Run an interactive chat session with the Career Coach agent.
    """
    resume_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'resume.pdf')
    resume_text = extract_text_from_pdf(resume_path)
    
    print("\n" + "="*50)
    print("Welcome to CareerCopilot-AI Coach Chat!")
    print("Type 'exit' or 'quit' to end the session.")
    print("="*50 + "\n")
    
    crew_instance = CareerCopilotAi()
    coach_agent = crew_instance.career_coach()
    
    while True:
        try:
            user_query = input("\nYou: ")
            if user_query.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
                
            print("\nCareerCoach is thinking...")
            prompt = f"The user asks: '{user_query}'\nUse the Vector DB to find relevant info from previously scraped jobs if applicable. The user's resume text is: {resume_text}"
            result = coach_agent.kickoff(prompt)
            print(f"\nCareerCoach: {result.raw}")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nError communicating with CareerCoach: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        CareerCopilotAi().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        CareerCopilotAi().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    try:
        CareerCopilotAi().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "topic": "",
        "current_year": ""
    }

    try:
        result = CareerCopilotAi().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
