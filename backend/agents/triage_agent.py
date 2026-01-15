from backend.agents.lms_agent import lms_agent
from backend.agents.predictive_agent import predictive_agent
from backend.agents.planner_agent import planner_agent

def triage(query, student_id):
    q = query.lower()
    if "attendance" in q or "marks" in q:
        return lms_agent(student_id)
    if "predict" in q:
        return predictive_agent(student_id)
    if "plan" in q:
        return planner_agent(student_id)
    return "I could not understand your request."
