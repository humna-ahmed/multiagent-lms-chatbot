def fmt(x):
    return f"{x:.2f}"
import streamlit as st
import sqlite3
import pandas as pd

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Student LMS Dashboard",
    layout="wide"
)

# --------------------------------------------------
# DATABASE PATH
# --------------------------------------------------
DB_PATH = "backend/database/lms.db"

# --------------------------------------------------
# AUTH CHECK (VERY IMPORTANT)
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
cur.execute(
    "SELECT name, registration_no FROM students WHERE student_id = ?",
    (student_id,)
)
student = cur.fetchone()

if not student:
    st.error("Student not found.")
    st.stop()

student_name, registration_no = student

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.title("🎓 Student LMS Dashboard")
st.markdown(f"### Welcome, **{student_name}** ({registration_no})")

# --------------------------------------------------
# FETCH COURSES FOR STUDENT
# --------------------------------------------------
cur.execute("""
    SELECT DISTINCT c.course_id, c.course_name
    FROM courses c
    JOIN marks m ON m.course_id = c.course_id
    WHERE m.student_id = ?
""", (student_id,))

courses = cur.fetchall()

if not courses:
    st.warning("No courses found for this student.")
    conn.close()
    st.stop()

course_map = {name: cid for cid, name in courses}

# --------------------------------------------------
# COURSE MULTI-SELECT (TICK DROPDOWN)
# --------------------------------------------------
selected_courses = st.multiselect(
    "📚 Select course(s) to view:",
    options=list(course_map.keys()),
    default=[list(course_map.keys())[0]]
)

# --------------------------------------------------
# LOOP THROUGH SELECTED COURSES
# --------------------------------------------------
for course_name in selected_courses:
    course_id = course_map[course_name]

    st.markdown("---")
    st.subheader(f"📘 {course_name}")

    # -----------------------------
    # ATTENDANCE
    # -----------------------------
    cur.execute("""
        SELECT classes_attended, total_classes
        FROM attendance
        WHERE student_id = ? AND course_id = ?
    """, (student_id, course_id))

    att = cur.fetchone()
    attendance_pct = round((att[0] / att[1]) * 100, 1) if att else 0

    # -----------------------------
    # MARKS
    # -----------------------------
    cur.execute("""
        SELECT quiz1, quiz2, quiz3, quiz4,
               assignment1, assignment2, assignment3, assignment4,
               midterm
        FROM marks
        WHERE student_id = ? AND course_id = ?
    """, (student_id, course_id))

    marks = cur.fetchone()

    if marks:
        quizzes = {f"Quiz {i+1}": fmt(m) for i, m in enumerate(marks[:4])}
        assignments = {f"Assignment {i+1}": fmt(m) for i, m in enumerate(marks[4:8])}
        midterm = fmt(marks[8])

        total_quiz = fmt(sum(float(v) for v in quizzes.values()))
        total_assignment = fmt(sum(float(v) for v in assignments.values()))

        # Simple predicted final (out of 50)
        predicted_final = fmt(
    50 * ((float(total_quiz) + float(total_assignment) + float(midterm)) / 50)
)
    else:
        quizzes, assignments = {}, {}
        midterm = total_quiz = total_assignment = predicted_final = 0

    # --------------------------------------------------
    # UI LAYOUT
    # --------------------------------------------------
    col1, col2 = st.columns([1.1, 1])

    with col1:
        st.metric("📊 Attendance", f"{attendance_pct}%")
        st.progress(int(attendance_pct))

        with st.expander("📝 Quiz Details"):
            st.table(pd.DataFrame.from_dict(quizzes, orient="index", columns=["Marks"]))
            st.write(f"**Total:** {total_quiz} / 10")

        with st.expander("📂 Assignment Details"):
            st.table(pd.DataFrame.from_dict(assignments, orient="index", columns=["Marks"]))
            st.write(f"**Total:** {total_assignment} / 20")

        st.metric("🧠 Midterm", f"{midterm} / 20")
        st.metric("🔮 Predicted Final", f"{predicted_final} / 50")

    with col2:
        chart_df = pd.DataFrame({
            "Assessment": (
                list(quizzes.keys())
                + list(assignments.keys())
                + ["Midterm", "Final (Predicted)"]
            ),
            "Score": (
    [float(v) for v in quizzes.values()]
    + [float(v) for v in assignments.values()]
    + [float(midterm), float(predicted_final)]
)

        })

        st.bar_chart(chart_df.set_index("Assessment"))

# --------------------------------------------------
# CLOSE DB
# --------------------------------------------------
conn.close()
