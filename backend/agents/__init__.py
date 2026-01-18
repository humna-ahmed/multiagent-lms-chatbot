# backend/agents/__init__.py

import sqlite3
import re

class Agent:
    def __init__(self, name, instructions, handoffs=None):
        self.name = name
        self.instructions = instructions
        self.handoffs = handoffs or []

    async def handle_query(self, user_query, student_id, db_connection, llm_model=None):
        """
        Routes the query to the correct agent, fetches real data from DB,
        and returns a response. LLM is optional (used for natural phrasing only).
        """

        query_lower = user_query.lower()
        cursor = db_connection.cursor()

        # ----------------------------
        # 1. Route to correct agent
        # ----------------------------
        if "quiz" in query_lower or "assignment" in query_lower or "attendance" in query_lower:
            agent = self.handoffs[0]  # LMS Agent
        elif "predict" in query_lower or "marks" in query_lower or "score" in query_lower:
            agent = self.handoffs[1]  # Prediction Agent
        else:
            agent = self.handoffs[2]  # Planner Agent

        # ----------------------------
        # Helper: find course mentioned in query
        # ----------------------------
        cursor.execute("SELECT course_name FROM courses")
        courses = [row[0] for row in cursor.fetchall()]
        course_name = None
        for course in courses:
            if re.search(r'\b' + re.escape(course.lower()) + r'\b', query_lower):
                course_name = course
                break

        # ----------------------------
        # 2. LMS Agent
        # ----------------------------
        if agent.name == "LMS Agent":
            if not course_name:
                return "Please specify the course you want to check."

            # Attendance query
            if "attendance" in query_lower:
                cursor.execute("""
                    SELECT classes_attended, total_classes
                    FROM attendance a
                    JOIN courses c ON c.course_id = a.course_id
                    WHERE a.student_id=? AND c.course_name=?
                """, (student_id, course_name))
                row = cursor.fetchone()
                if row:
                    attended, total = row
                    return f"Your attendance in {course_name} is {attended}/{total} classes ({round(attended/total*100,2)}%)."
                else:
                    return f"No attendance data found for {course_name}."

            # Quiz / assignment query
            elif "quiz" in query_lower or "assignment" in query_lower:
                cursor.execute("""
                    SELECT quiz1, quiz2, quiz3, quiz4,
                           assignment1, assignment2, assignment3, assignment4
                    FROM marks m
                    JOIN courses c ON c.course_id = m.course_id
                    WHERE m.student_id=? AND c.course_name=?
                """, (student_id, course_name))
                row = cursor.fetchone()
                if row:
                    quizzes = row[:4]
                    assignments = row[4:]
                    return (
                        f"{course_name}:\n"
                        f"  Quizzes: {quizzes}\n"
                        f"  Assignments: {assignments}"
                    )
                else:
                    return f"No marks data found for {course_name}."

            return "I could not understand your LMS query."

        # ----------------------------
        # 3. Predictive Agent
        # ----------------------------
        elif agent.name == "Prediction Agent":
            cursor.execute("""
                SELECT quiz1, quiz2, quiz3, quiz4,
                       assignment1, assignment2, assignment3, assignment4,
                       midterm
                FROM marks
                WHERE student_id=?
            """, (student_id,))
            row = cursor.fetchone()
            if row:
                quiz_total = sum([x for x in row[:4] if x is not None])
                assignment_total = sum([x for x in row[4:8] if x is not None])
                midterm = row[8] if row[8] is not None else 0
                predicted_final = round((quiz_total + assignment_total + midterm) / 50 * 50, 2)  # simple formula
                return f"Based on your marks so far, your predicted final score is {predicted_final}/50."
            else:
                return "No marks data available to predict final grade."

        # ----------------------------
        # 4. Planner Agent
        # ----------------------------
        elif agent.name == "Planner Agent":
            # optional: fetch courses & marks for smarter suggestions
            cursor.execute("""
                SELECT c.course_name, a.classes_attended, a.total_classes,
                       m.quiz1, m.quiz2, m.quiz3, m.quiz4,
                       m.assignment1, m.assignment2, m.assignment3, m.assignment4,
                       m.midterm
                FROM courses c
                LEFT JOIN attendance a ON a.course_id = c.course_id AND a.student_id=?
                LEFT JOIN marks m ON m.course_id = c.course_id AND m.student_id=?
            """, (student_id, student_id))
            rows = cursor.fetchall()
            suggestions = []
            for row in rows:
                cname, attended, total, *marks = row
                if attended is not None and total is not None and attended/total < 0.75:
                    suggestions.append(f"- Attend more classes in {cname}")
                quiz_avg = sum([x for x in marks[:4] if x is not None])/4 if any(marks[:4]) else None
                assignment_avg = sum([x for x in marks[4:8] if x is not None])/4 if any(marks[4:8]) else None
                if quiz_avg is not None and quiz_avg < 8:
                    suggestions.append(f"- Improve quiz scores in {cname}")
                if assignment_avg is not None and assignment_avg < 8:
                    suggestions.append(f"- Improve assignment scores in {cname}")

            if not suggestions:
                suggestions.append("- Keep up the good work! All courses are on track.")

            return "Study Plan Recommendations:\n" + "\n".join(suggestions)

        # ----------------------------
        # 5. Optional: fallback to LLM
        # ----------------------------
        if llm_model:
            prompt = f"""
You are the Academic AI Companion.
Student ID: {student_id}
User query: {user_query}
Answer clearly and concisely.
"""
            return await llm_model.complete(prompt)

        return "Sorry, I could not process your query."
