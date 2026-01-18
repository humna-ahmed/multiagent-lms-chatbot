from backend.agents import Agent
from backend.agents.lms_agent import lms_agent
from backend.agents.predictive_agent import predictive_agent
from backend.agents.planner_agent import planner_agent

triage_agent = Agent(
    name="Academic AI Companion",
    instructions="""
You are the student's Academic AI Companion.

You can:
1) Retrieve information from the LMS (quizzes, assignments, attendance)
2) Predict final exam marks
3) Create a personalized rescue or study plan

You NEVER say you are a planner, predictor, or LMS agent.
You speak directly to the student in a friendly academic tone.
""",
    handoffs=[lms_agent, predictive_agent, planner_agent]
)
