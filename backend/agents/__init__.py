# backend/agents/__init__.py

import re

class Agent:
    def __init__(self, name, instructions, handoffs=None):
        self.name = name
        self.instructions = instructions
        self.handoffs = handoffs or []

    async def handle_query(self, user_query, student_id, db_connection, llm_model=None):
        """
        Triage agent entry point.
        Routes queries to sub-agents when needed.
        Only the triage agent ever talks to the user.
        """

        query_lower = user_query.lower()
        cursor = db_connection.cursor()

        # ==================================================
        # 0. Greetings / Small talk (ABSOLUTE EXIT)
        # ==================================================
        if re.fullmatch(r"(hi|hello|hey|good morning|good evening)", query_lower.strip()):
            return (
                "👋 Hi! I’m your Academic AI Companion.\n\n"
                "You can ask me things like:\n"
                "• What are my quiz marks in Calculus?\n"
                "• Predict my final exam score\n"
                "• Make a study or rescue plan for finals\n\n"
                "How can I help you today?"
            )


        # ==================================================
        # 1. Intent-based routing (NO default to planner)
        # ==================================================
        agent = None

        if re.search(r"\b(quiz|assignment|attendance)\b", query_lower):
            agent = self.handoffs[0]  # LMS

        elif re.search(r"\b(predict|prediction|final score|marks)\b", query_lower):
            agent = self.handoffs[1]  # Prediction

        elif re.search(r"\b(plan|study|rescue|focus)\b", query_lower):
            agent = self.handoffs[2]  # Planner

        # ==================================================
        # 1.5 Triage fallback (NO agent selected)
        # ==================================================
        if agent is None:
            return (
                "I can help you with:\n"
                "• Quiz, assignment, or attendance queries\n"
                "• Final exam predictions\n"
                "• Study or rescue plans\n\n"
                "What would you like to do?"
            )

        # ==================================================
        # Helper: Detect course name (for LMS / Planner)
        # ==================================================
        cursor.execute("SELECT course_name FROM courses")
        courses = [row[0] for row in cursor.fetchall()]

        course_name = None
        for course in courses:
            if re.search(rf"\b{re.escape(course.lower())}\b", query_lower):
                course_name = course
                break

        # ==================================================
        # 2. LMS Agent (silent worker)
        # ==================================================
        if agent.name == "LMS Agent":

            if not course_name:
                return "Please specify the course name."

            # Attendance
            if "attendance" in query_lower:
                cursor.execute("""
                    SELECT classes_attended, total_classes
                    FROM attendance a
                    JOIN courses c ON c.course_id = a.course_id
                    WHERE a.student_id=? AND c.course_name=?
                """, (student_id, course_name))

                row = cursor.fetchone()
                if not row:
                    return f"No attendance data found for {course_name}."

                attended, total = row
                percentage = round((attended / total) * 100, 2)
                return f"Your attendance in {course_name} is {attended}/{total} ({percentage}%)."

            # Quizzes / Assignments
            cursor.execute("""
                SELECT quiz1, quiz2, quiz3, quiz4,
                       assignment1, assignment2, assignment3, assignment4
                FROM marks m
                JOIN courses c ON c.course_id = m.course_id
                WHERE m.student_id=? AND c.course_name=?
            """, (student_id, course_name))

            row = cursor.fetchone()
            if not row:
                return f"No marks data found for {course_name}."

            quizzes = row[:4]
            assignments = row[4:]

            return (
                f"📘 **{course_name} Marks**\n\n"
                f"Quizzes: {quizzes}\n"
                f"Assignments: {assignments}"
            )

        # ==================================================
        # 3. Predictive Agent (silent worker)
        # ==================================================
        elif agent.name == "Prediction Agent":

            cursor.execute("""
                SELECT quiz1, quiz2, quiz3, quiz4,
                       assignment1, assignment2, assignment3, assignment4,
                       midterm
                FROM marks
                WHERE student_id=?
            """, (student_id,))

            row = cursor.fetchone()
            if not row:
                return "No marks data available to predict your final score."

            quiz_total = sum(x for x in row[:4] if x is not None)
            assignment_total = sum(x for x in row[4:8] if x is not None)
            midterm = row[8] or 0

            predicted_final = round((quiz_total + assignment_total + midterm), 2)
            predicted_final = min(predicted_final, 50)

            return f"📈 Based on your performance so far, your predicted final score is **{predicted_final}/50**."

        # ==================================================
        # 4. Planner Agent (silent worker)
        # ==================================================
        elif agent.name == "Planner Agent":

            cursor.execute("""
                SELECT c.course_name,
                       a.classes_attended, a.total_classes,
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

                if attended and total and (attended / total) < 0.75:
                    suggestions.append(f"📌 Attend more classes in **{cname}**")

                quiz_marks = marks[:4]
                assignment_marks = marks[4:8]

                if quiz_marks and sum(x for x in quiz_marks if x) / 4 < 8:
                    suggestions.append(f"📌 Improve quiz preparation for **{cname}**")

                if assignment_marks and sum(x for x in assignment_marks if x) / 4 < 8:
                    suggestions.append(f"📌 Focus on assignments in **{cname}**")

            if not suggestions:
                suggestions.append("✅ You’re doing great! All courses are on track.")

            return "📝 **Study Plan Recommendations**\n\n" + "\n".join(suggestions)
