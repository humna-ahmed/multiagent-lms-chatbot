import sqlite3, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "lms.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Fetch all students
cur.execute("SELECT student_id, registration_no FROM students")
students = cur.fetchall()

# Fetch all courses
cur.execute("SELECT course_id FROM courses")
courses = [c[0] for c in cur.fetchall()]

# Assign random marks for each student in each course
import random

for student_id, reg_no in students:
    for course_id in courses:
        cur.execute("""
        INSERT OR REPLACE INTO marks (
            student_id, course_id, quiz1, quiz2, quiz3, quiz4,
            assignment1, assignment2, assignment3, assignment4, midterm
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student_id, course_id,
            random.uniform(2, 2.5), random.uniform(2, 2.5), random.uniform(2, 2.5), random.uniform(2, 2.5),  # quizzes
            random.uniform(4,5), random.uniform(4,5), random.uniform(4,5), random.uniform(4,5),              # assignments
            random.uniform(12, 20)  # midterm
        ))

conn.commit()
conn.close()
print("✅ Added marks for all students")
