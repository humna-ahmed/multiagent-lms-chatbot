def fmt(x):
    return f"{x:.2f}"

import streamlit as st
import sqlite3
import pandas as pd

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Student LMS",
    layout="wide"
)

# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------
st.sidebar.title("📘 LMS Navigation")

page = st.sidebar.radio(
    "Go to",
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
DB_PATH = "backend/database/lms.db"

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

selected_courses = st.multiselect(
    "📚 Select course(s):",
    options=list(course_map.keys()),
    default=list(course_map.keys())[:1]
)

# ==================================================
# PAGE 1: PERSONAL INFO
# ==================================================
if page == "Personal Info":

    st.title("👤 Personal Information")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Name", student_name)
        st.metric("Registration No", registration_no)

    with col2:
        st.metric("Semester", semester)
        st.metric("Student ID", student_id)

    st.markdown("---")
    st.subheader("📚 Enrolled Courses")

    for course in course_map.keys():
        st.write(f"• {course}")

# ==================================================
# PAGE 2: DASHBOARD
# ==================================================
elif page == "Dashboard":

    st.title("📊 Academic Overview")

    for course_name in selected_courses:
        course_id = course_map[course_name]
        st.markdown("---")
        st.subheader(course_name)

        # Attendance
        cur.execute("""
            SELECT classes_attended, total_classes
            FROM attendance
            WHERE student_id = ? AND course_id = ?
        """, (student_id, course_id))
        att = cur.fetchone()
        attendance_pct = round((att[0] / att[1]) * 100, 1) if att else 0

        # Marks
        cur.execute("""
            SELECT quiz1, quiz2, quiz3, quiz4,
                   assignment1, assignment2, assignment3, assignment4,
                   midterm
            FROM marks
            WHERE student_id = ? AND course_id = ?
        """, (student_id, course_id))
        marks = cur.fetchone()

        quizzes = sum(marks[:4])
        assignments = sum(marks[4:8])
        midterm = marks[8]

        col1, col2, col3 = st.columns(3)
        col1.metric("Attendance", f"{attendance_pct}%")
        col2.metric("Quiz Total", quizzes)
        col3.metric("Assignment Total", assignments)

        chart_df = pd.DataFrame({
            "Assessment": ["Quizzes", "Assignments", "Midterm"],
            "Score": [quizzes, assignments, midterm]
        })

        st.bar_chart(chart_df.set_index("Assessment"))

# ==================================================
# PAGE 3: QUIZZES
# ==================================================
elif page == "Quizzes":

    st.title("📝 Quizzes")

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
            "Marks": q
        })

        st.table(df)

# ==================================================
# PAGE 4: ASSIGNMENTS
# ==================================================
elif page == "Assignments":

    st.title("📂 Assignments")

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
            "Assignment": ["Assignment 1", "Assignment 2", "Assignment 3", "Assignment 4"],
            "Marks": a
        })

        st.table(df)

# ==================================================
# PAGE 5: ATTENDANCE
# ==================================================
elif page == "Attendance":

    st.title("📅 Attendance")

    for course_name in selected_courses:
        course_id = course_map[course_name]
        st.subheader(course_name)

        cur.execute("""
            SELECT classes_attended, total_classes
            FROM attendance
            WHERE student_id = ? AND course_id = ?
        """, (student_id, course_id))

        att = cur.fetchone()
        attendance_pct = round((att[0] / att[1]) * 100, 1) if att else 0

        st.metric("Attendance", f"{attendance_pct}%")
        st.progress(int(attendance_pct))

# ==================================================
# PAGE 6: CHATBOT
# ==================================================
elif page == "Chatbot":

    st.title("🤖 LMS Assistant")

    st.info("Ask questions about your courses, quizzes, attendance, and performance.")

    # IMPORTANT: Replace port if your Chainlit runs on a different one
    chainlit_url = "http://localhost:8000"

    st.components.v1.iframe(
        src=chainlit_url,
        height=650,
        scrolling=True
    )

    st.markdown(
        f"[🔗 Open chatbot in new tab]({chainlit_url})",
        unsafe_allow_html=True
    )

# --------------------------------------------------
# CLOSE DB
# --------------------------------------------------
conn.close()
