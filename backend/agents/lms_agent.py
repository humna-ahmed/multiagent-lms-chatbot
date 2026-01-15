import sqlite3

def lms_agent(student_id):
    conn = sqlite3.connect("backend/database/lms.db")
    cur = conn.cursor()
    cur.execute("SELECT AVG(marks) FROM quizzes WHERE student_id=?", (student_id,))
    quiz_avg = cur.fetchone()[0] or 0
    return f"Your average quiz score is {quiz_avg}/2.5"
