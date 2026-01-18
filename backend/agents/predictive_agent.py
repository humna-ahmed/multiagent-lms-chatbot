# agents/predictive_agent.py

from . import Agent

predictive_agent = Agent(
    name="Prediction Agent",
    instructions="""
    You predict final exam marks (out of 50) based on:
    quizzes, assignments, and midterm performance.
    Explain the prediction briefly.
    """
)
