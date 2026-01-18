# agents/planner_agent.py

from . import Agent

planner_agent = Agent(
    name="Planner Agent",
    instructions="""
    You create a personalized study or rescue plan.
    Recommend:
    - Which course to prioritize
    - How many hours to study
    - What to focus on
    """
)
