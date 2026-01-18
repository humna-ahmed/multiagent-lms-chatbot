# dashboard/dashboard.py
import streamlit as st
import sqlite3
import pandas as pd
import sys
import os
import asyncio
# --------------------------------------------------
# ADD PARENT DIRECTORY TO PYTHON PATH (for agents)
# --------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from agents import Agent  # if you need Agent class
from backend.agents.triage_agent import triage_agent
# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Student LMS",
    layout="wide"
)

# --------------------------------------------------
# HELPER FUNCTION
# --------------------------------------------------
def fmt(x):
    return f"{float(x):.2f}"

# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------
st.sidebar.title("📘 LMS Navigation")

page = st.sidebar.radio(
    "Navigate",
    [
        "Personal Info",
        "Dashboard",
        "Quizzes",
        "Assignments",
        "Attendance",
        "Chatbot"
    ]
)

# --------------------------------------------------
# DATABASE PATH
# --------------------------------------------------
DB_PATH = os.path.join(PROJECT_ROOT, "backend", "database", "lms.db")

 
# --------------------------------------------------
# AUTH CHECK
# --------------------------------------------------
student_id = st.query_params.get("student_id")

if not student_id:
    st.error("❌ Unauthorized access. Please login first.")
    st.stop()

# --------------------------------------------------
# CONNECT TO DATABASE
# --------------------------------------------------
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# --------------------------------------------------
# FETCH STUDENT INFO
# --------------------------------------------------
cur.execute("""
    SELECT name, registration_no, semester
    FROM students
    WHERE student_id = ?
""", (student_id,))
student = cur.fetchone()

if not student:
    st.error("Student not found.")
    st.stop()

student_name, registration_no, semester = student

# --------------------------------------------------
# FETCH COURSES
# --------------------------------------------------
cur.execute("""
    SELECT DISTINCT c.course_id, c.course_name
    FROM courses c
    JOIN marks m ON m.course_id = c.course_id
    WHERE m.student_id = ?
""", (student_id,))
courses = cur.fetchall()
course_map = {name: cid for cid, name in courses}
course_names = list(course_map.keys())

# --------------------------------------------------
# HELPER: PAGE-SCOPED COURSE SELECTOR
# --------------------------------------------------
def course_selector(page_key):
    selector_key = f"courses_{page_key}"
    options = ["Select All Courses"] + course_names

    selected = st.multiselect(
        "📚 Select course(s) to view",
        options=options,
        key=selector_key
    )

    if "Select All Courses" in selected:
        return course_names

    return selected

# ==================================================
# PAGE: PERSONAL INFO
# ==================================================
if page == "Personal Info":
    st.title("👤 Personal Information")
    col1, col2 = st.columns(2)
    col1.metric("Name", student_name)
    col1.metric("Registration No", registration_no)
    col2.metric("Semester", semester)
    col2.metric("Student ID", student_id)

    st.markdown("---")
    st.subheader("📚 Enrolled Courses")
    for course in course_names:
        st.write(f"• {course}")

# ==================================================
# PAGE: DASHBOARD
# ==================================================
elif page == "Dashboard":
    st.title("📊 Academic Overview")
    selected_courses = course_selector("dashboard")

    if not selected_courses:
        st.info("ℹ️ Please select one or more courses to view academic overview.")
    else:
        for course_name in selected_courses:
            course_id = course_map[course_name]
            st.markdown("---")
            st.subheader(course_name)

            cur.execute("""
                SELECT classes_attended, total_classes
                FROM attendance
                WHERE student_id = ? AND course_id = ?
            """, (student_id, course_id))
            att = cur.fetchone()
            attendance_pct = round((att[0] / att[1]) * 100, 2) if att else 0

            cur.execute("""
                SELECT quiz1, quiz2, quiz3, quiz4,
                       assignment1, assignment2, assignment3, assignment4,
                       midterm
                FROM marks
                WHERE student_id = ? AND course_id = ?
            """, (student_id, course_id))
            m = cur.fetchone()

            quiz_total = round(sum(m[:4]), 2)
            assignment_total = round(sum(m[4:8]), 2)
            midterm = round(m[8], 2)

            col1, col2, col3 = st.columns(3)
            col1.metric("Attendance %", f"{fmt(attendance_pct)}%")
            col2.metric("Quiz Total", fmt(quiz_total))
            col3.metric("Assignment Total", fmt(assignment_total))

            chart_df = pd.DataFrame({
                "Assessment": ["Quizzes", "Assignments", "Midterm"],
                "Score": [quiz_total, assignment_total, midterm]
            })
            st.bar_chart(chart_df.set_index("Assessment"))

# ==================================================
# PAGE: QUIZZES
# ==================================================
elif page == "Quizzes":
    st.title("📝 Quizzes")
    selected_courses = course_selector("quizzes")

    if not selected_courses:
        st.info("ℹ️ Please select a course to view quizzes.")
    else:
        for course_name in selected_courses:
            course_id = course_map[course_name]
            st.subheader(course_name)

            cur.execute("""
                SELECT quiz1, quiz2, quiz3, quiz4
                FROM marks
                WHERE student_id = ? AND course_id = ?
            """, (student_id, course_id))
            q = cur.fetchone()

            df = pd.DataFrame({
                "Quiz": ["Quiz 1", "Quiz 2", "Quiz 3", "Quiz 4"],
                "Marks": [fmt(x) for x in q]
            })
            st.table(df)

# ==================================================
# PAGE: ASSIGNMENTS
# ==================================================
elif page == "Assignments":
    st.title("📂 Assignments")
    selected_courses = course_selector("assignments")

    if not selected_courses:
        st.info("ℹ️ Please select a course to view assignments.")
    else:
        for course_name in selected_courses:
            course_id = course_map[course_name]
            st.subheader(course_name)

            cur.execute("""
                SELECT assignment1, assignment2, assignment3, assignment4
                FROM marks
                WHERE student_id = ? AND course_id = ?
            """, (student_id, course_id))
            a = cur.fetchone()

            df = pd.DataFrame({
                "Assignment": [
                    "Assignment 1",
                    "Assignment 2",
                    "Assignment 3",
                    "Assignment 4"
                ],
                "Marks": [fmt(x) for x in a]
            })
            st.table(df)

# ==================================================
# PAGE: ATTENDANCE
# ==================================================
elif page == "Attendance":
    st.title("📅 Attendance")
    selected_courses = course_selector("attendance")

    if not selected_courses:
        st.info("ℹ️ Please select a course to view attendance.")
    else:
        for course_name in selected_courses:
            course_id = course_map[course_name]
            st.subheader(course_name)

            cur.execute("""
                SELECT classes_attended, total_classes
                FROM attendance
                WHERE student_id = ? AND course_id = ?
            """, (student_id, course_id))
            att = cur.fetchone()

            attendance_pct = round((att[0] / att[1]) * 100, 2) if att else 0
            st.metric("Attendance %", f"{fmt(attendance_pct)}%")
            st.progress(int(attendance_pct))
# ==================================================
# PAGE: CHATBOT (STREAMLIT + TRIAGE AGENT)
# ==================================================
elif page == "Chatbot":

    st.title("🤖 LMS Assistant")
    st.caption("Ask questions about your academics, attendance, or performance.")

    # ----------------------------------
    # Initialize session state
    # ----------------------------------
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "welcome_shown" not in st.session_state:
        welcome_msg = (
            "👋 Hello! I’m your **Academic AI Companion**.\n\n"
            "I can help you:\n\n"
            "1️⃣ Retrieve information from your LMS\n\n"
            "2️⃣ Predict your final exam grades\n\n"
            "3️⃣ Create a rescue or study plan\n\n\n"
            "Ask me anything about your academics!"
        )
        st.session_state.messages.append(
            {"role": "assistant", "content": welcome_msg}
        )
        st.session_state.welcome_shown = True

    # ----------------------------------
    # Display chat history
    # ----------------------------------
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ----------------------------------
    # User input
    # ----------------------------------
    prompt = st.chat_input("Ask me something...")

    if prompt:
        # Show user message
        st.session_state.messages.append(
            {"role": "user", "content": prompt}
        )
        with st.chat_message("user"):
            st.markdown(prompt)

        # ----------------------------------
        # AI response
        # ----------------------------------
        try:
            import asyncio
            from backend.agents.triage_agent import triage_agent
            from backend.agents.llm import GeminiLLM

            llm_model = GeminiLLM()

            bot_reply = asyncio.run(
                triage_agent.handle_query(
                    user_query=prompt,
                    student_id=student_id,
                    db_connection=conn,
                    llm_model=llm_model
                )
            )

        except Exception as e:
            bot_reply = (
                f"⚠️ Error: {e}\n\n"
                "Currently unable to fetch answer.\n"
                f"Hi {student_name}! 👋 I'm your LMS assistant demo."
            )

        # Store and display assistant reply
        st.session_state.messages.append(
            {"role": "assistant", "content": bot_reply}
        )
        with st.chat_message("assistant"):
            st.markdown(bot_reply)


# --------------------------------------------------
# CLOSE DB
# --------------------------------------------------
conn.close()
