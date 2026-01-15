import streamlit as st
import sqlite3
import pandas as pd

# --- Page Config ---
st.set_page_config(page_title="Student LMS Dashboard", layout="wide")

# --- Database Path ---
DB_PATH = "backend/database/lms.db"

# --- Connect to DB ---
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# --- Sidebar: Enter Registration No ---
st.sidebar.title("Student Login")
registration_no = st.sidebar.text_input("Enter Registration No:")

if registration_no:
    # Fetch student info
    cur.execute("SELECT student_id, name FROM students WHERE registration_no = ?", (registration_no,))
    student_row = cur.fetchone()
    
    if student_row:
        student_id, student_name = student_row
        st.title(f"Welcome, {student_name} 🎓")
        
        # Fetch all courses for student
        cur.execute("""
            SELECT c.course_id, c.course_name
            FROM courses c
            JOIN marks m ON m.course_id = c.course_id
            WHERE m.student_id = ?
        """, (student_id,))
        courses = cur.fetchall()
        
        if courses:
            course_options = {name: cid for cid, name in courses}
            
            # Multi-select dropdown
            selected_courses = st.multiselect(
                "Select courses to view:",
                options=list(course_options.keys())
            )
            
            for course_name in selected_courses:
                course_id = course_options[course_name]
                
                st.markdown("---")
                st.subheader(f"Course: {course_name}")
                
                # --- Fetch attendance ---
                cur.execute("SELECT classes_attended, total_classes FROM attendance WHERE student_id=? AND course_id=?",
                            (student_id, course_id))
                att_row = cur.fetchone()
                if att_row:
                    classes_attended, total_classes = att_row
                    attendance_pct = round((classes_attended / total_classes) * 100, 1)
                else:
                    attendance_pct = 0

                # --- Fetch marks ---
                cur.execute("""
                    SELECT quiz1, quiz2, quiz3, quiz4,
                           assignment1, assignment2, assignment3, assignment4,
                           midterm
                    FROM marks
                    WHERE student_id=? AND course_id=?
                """, (student_id, course_id))
                marks_row = cur.fetchone()
                if marks_row:
                    marks = list(marks_row)
                    quiz_marks = {f"Quiz {i+1}": round(m,2) for i, m in enumerate(marks[:4])}
                    assignment_marks = {f"Assignment {i+1}": round(m,2) for i, m in enumerate(marks[4:8])}
                    midterm = round(marks[8],2)
                    total_quiz = round(sum(quiz_marks.values()),2)
                    total_assignment = round(sum(assignment_marks.values()),2)
                    
                    # Predicted final (simple sum scaled to 50)
                    predicted_final = round(50 * ((total_quiz + total_assignment + midterm)/50), 2)
                else:
                    quiz_marks, assignment_marks = {}, {}
                    midterm = predicted_final = 0
                    total_quiz = total_assignment = 0
                
                # --- Columns for layout ---
                col1, col2 = st.columns([1,1])
                
                with col1:
                    st.metric("Attendance %", f"{attendance_pct}%")
                    
                    with st.expander("Quizzes Details"):
                        st.table(pd.DataFrame.from_dict(quiz_marks, orient="index", columns=["Marks"]))
                        st.write(f"**Total Quizzes:** {total_quiz:.2f}/10")
                        
                    with st.expander("Assignments Details"):
                        st.table(pd.DataFrame.from_dict(assignment_marks, orient="index", columns=["Marks"]))
                        st.write(f"**Total Assignments:** {total_assignment:.2f}/20")
                    
                    st.metric("Midterm", f"{midterm:.2f}/20")
                    st.metric("Predicted Final", f"{predicted_final:.2f}/50")
                    
                    # Attendance progress bar
                    st.progress(int(attendance_pct))
                    
                with col2:
                    # Bar chart for visual comparison
                    chart_data = pd.DataFrame({
                        "Assessment": list(quiz_marks.keys()) + list(assignment_marks.keys()) + ["Midterm", "Final (Predicted)"],
                        "Score": list(quiz_marks.values()) + list(assignment_marks.values()) + [midterm, predicted_final]
                    })
                    st.bar_chart(chart_data.set_index("Assessment"))
        else:
            st.warning("No courses found for this student.")
                
    else:
        st.warning("Student not found. Please check your registration number.")

conn.close()
