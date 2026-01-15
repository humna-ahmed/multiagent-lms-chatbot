import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "lms.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Add courses
courses = ["Calculus", "Functional English", "Physics", "Programming"]
for c in courses:
    cur.execute("INSERT OR IGNORE INTO courses (course_name) VALUES (?)", (c,))

# Get student_id
cur.execute("SELECT student_id FROM students WHERE registration_no = ?", ("2021-CS-001",))
student_id = cur.fetchone()[0]

# Add marks for this student
cur.execute("""
INSERT OR REPLACE INTO marks (
    student_id, course_id, quiz1, quiz2, quiz3, quiz4,
    assignment1, assignment2, assignment3, assignment4, midterm
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    student_id, 1, 2, 2.5, 2, 2.5, 4, 5, 4, 5, 15
))
conn.commit()
conn.close()

print("✅ Test courses and marks added")
