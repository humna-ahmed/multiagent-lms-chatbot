# agent.py
import asyncio
import sqlite3
from typing import Dict, Any, Optional

from agents import (
    Agent,
    Runner,
    RunConfig,
    OpenAIChatCompletionsModel,
    function_tool
)
from openai import AsyncOpenAI


# =========================================================
# MODEL SETUP
# =========================================================

external_client = AsyncOpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key="AIzaSyCXwq_BDPbEs52lYw1HhbsaETIqpbaDOAw"
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.5-flash",
    openai_client=external_client
)

config = RunConfig(model=model)


# =========================================================
# ASYNC DB LOGIC (WRAPS SQLITE – SAFE)
# =========================================================

async def _get_course_data_async(
    course_name: str,
    student_id: int,
    db: sqlite3.Connection
) -> Dict[str, Any]:

    cursor = db.cursor()

    cursor.execute(
        "SELECT course_id FROM courses WHERE course_name = ?",
        (course_name,)
    )
    course = cursor.fetchone()

    if not course:
        return {"error": f"Course '{course_name}' not found"}

    course_id = course[0]

    data = {
        "course_name": course_name,
        "quizzes": [],
        "assignments": [],
        "attendance": None,
        "midterm": None
    }

    # Quizzes
    cursor.execute("""
        SELECT quiz_name, marks_obtained, max_marks
        FROM quizzes
        WHERE student_id=? AND course_id=?
    """, (student_id, course_id))

    for name, obtained, maxm in cursor.fetchall():
        data["quizzes"].append({
            "name": name,
            "obtained": obtained,
            "max": maxm,
            "percentage": round((obtained / maxm) * 100, 2) if maxm else 0
        })

    # Assignments
    cursor.execute("""
        SELECT assignment_name, marks_obtained, max_marks
        FROM assignments
        WHERE student_id=? AND course_id=?
    """, (student_id, course_id))

    for name, obtained, maxm in cursor.fetchall():
        data["assignments"].append({
            "name": name,
            "obtained": obtained,
            "max": maxm,
            "percentage": round((obtained / maxm) * 100, 2) if maxm else 0
        })

    # Attendance
    cursor.execute("""
        SELECT classes_attended, total_classes
        FROM attendance
        WHERE student_id=? AND course_id=?
    """, (student_id, course_id))

    att = cursor.fetchone()
    if att:
        attended, total = att
        data["attendance"] = round((attended / total) * 100, 2) if total else 0

    # Midterm
    cursor.execute("""
        SELECT midterm FROM marks
        WHERE student_id=? AND course_id=?
    """, (student_id, course_id))

    mid = cursor.fetchone()
    if mid and mid[0] is not None:
        data["midterm"] = {
            "marks": mid[0],
            "percentage": round((mid[0] / 20) * 100, 2)
        }

    return data


async def _get_performance_data_async(
    course_name: str,
    student_id: int,
    db: sqlite3.Connection
) -> Dict[str, Any]:

    cursor = db.cursor()

    cursor.execute(
        "SELECT course_id FROM courses WHERE course_name=?",
        (course_name,)
    )
    course = cursor.fetchone()

    if not course:
        return {"error": "Course not found"}

    course_id = course[0]

    scores = []

    cursor.execute("""
        SELECT marks_obtained, max_marks
        FROM quizzes
        WHERE student_id=? AND course_id=?
    """, (student_id, course_id))

    for o, m in cursor.fetchall():
        if m:
            scores.append((o / m) * 100)

    avg = round(sum(scores) / len(scores), 2) if scores else 0

    return {
        "quiz_average": avg,
        "consistency": round(100 - (max(scores) - min(scores)), 2) if scores else 0
    }


async def _get_course_analysis_async(
    course_name: Optional[str],
    student_id: int,
    db: sqlite3.Connection
) -> Dict[str, Any]:

    cursor = db.cursor()

    if course_name:
        cursor.execute(
            "SELECT course_id FROM courses WHERE course_name=?",
            (course_name,)
        )
        course = cursor.fetchone()

        if not course:
            return {"error": "Course not found"}

        course_ids = [(course[0], course_name)]
    else:
        cursor.execute("SELECT course_id, course_name FROM courses")
        course_ids = cursor.fetchall()

    analysis = []

    for cid, cname in course_ids:
        cursor.execute("""
            SELECT classes_attended, total_classes
            FROM attendance
            WHERE student_id=? AND course_id=?
        """, (student_id, cid))

        att = cursor.fetchone()
        pct = round((att[0] / att[1]) * 100, 2) if att and att[1] else 0

        analysis.append({
            "course": cname,
            "attendance": pct,
            "risk": "high" if pct < 75 else "low"
        })

    return {"analysis": analysis}


# =========================================================
# TOOL BUILDER (SYNC ONLY – SAFE)
# =========================================================

def build_tools(student_id: int, db: sqlite3.Connection):

    loop = asyncio.get_event_loop()

    @function_tool
    def get_course_data(course_name: str):
        return loop.run_until_complete(
            _get_course_data_async(course_name, student_id, db)
        )

    @function_tool
    def get_performance_data(course_name: str):
        return loop.run_until_complete(
            _get_performance_data_async(course_name, student_id, db)
        )

    @function_tool
    def get_course_analysis(course_name: Optional[str] = None):
        return loop.run_until_complete(
            _get_course_analysis_async(course_name, student_id, db)
        )

    return [get_course_data, get_performance_data, get_course_analysis]


# =========================================================
# AGENT SETUP
# =========================================================

def build_agents(student_id: int, db):

    tools = build_tools(student_id, db)

    lms_agent = Agent(
        name="LMS Agent",
        model=model,
        tools=tools,
        instructions="Retrieve academic data and format clearly."
    )

    predictive_agent = Agent(
        name="Prediction Agent",
        model=model,
        tools=[tools[1], tools[2]],
        instructions="Predict academic outcomes."
    )

    planner_agent = Agent(
        name="Planner Agent",
        model=model,
        tools=[tools[0], tools[2]],
        instructions="Create study plans."
    )

    triage_agent = Agent(
        name="Academic AI Companion",
        model=model,
        handoffs=[lms_agent, predictive_agent, planner_agent],
        instructions="Route queries to the correct specialist."
    )

    return triage_agent


# =========================================================
# MAIN
# =========================================================

async def main():

    db = sqlite3.connect("lms.db")  # 🔴 your real DB
    student_id = 1

    triage_agent = build_agents(student_id, db)

    result = await Runner.run(
        starting_agent=triage_agent,
        input="Show my quiz performance in Calculus",
        run_config=config
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
