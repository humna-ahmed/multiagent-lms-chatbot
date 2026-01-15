import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "lms.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    registration_no TEXT UNIQUE,
    name TEXT,
    password_hash BLOB,
    semester INTEGER,
    department TEXT
)
""")
# Courses table
cur.execute("""
CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_name TEXT UNIQUE
)
""")

# Marks table
cur.execute("""
CREATE TABLE IF NOT EXISTS marks (
    mark_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    course_id INTEGER,
    quiz1 REAL,
    quiz2 REAL,
    quiz3 REAL,
    quiz4 REAL,
    assignment1 REAL,
    assignment2 REAL,
    assignment3 REAL,
    assignment4 REAL,
    midterm REAL,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(course_id) REFERENCES courses(course_id)
)
""")
# Attendance table
cur.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    course_id INTEGER,
    classes_attended INTEGER,
    total_classes INTEGER,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(course_id) REFERENCES courses(course_id)
)
""")

conn.commit()
conn.close()

print("Database initialized at:", DB_PATH)
