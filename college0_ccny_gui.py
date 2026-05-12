
# College0 local Tkinter application.
# Run with: python college0_ccny_gui.py

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

DB_NAME = "college0.db"


class College0DB:
    def __init__(self, db_name=DB_NAME):
        self.conn = sqlite3.connect(db_name)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        self.seed_data()

    def create_tables(self):
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT NOT NULL,
            must_change_password INTEGER DEFAULT 0,
            warnings INTEGER DEFAULT 0,
            suspended INTEGER DEFAULT 0
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS student_profiles (
            user_id INTEGER PRIMARY KEY,
            gpa REAL DEFAULT 0.0,
            overall_gpa REAL DEFAULT 0.0,
            honor_roll INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS instructor_profiles (
            user_id INTEGER PRIMARY KEY,
            avg_rating REAL DEFAULT 0.0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            role_applied TEXT NOT NULL,
            gpa REAL DEFAULT 0.0,
            status TEXT DEFAULT 'Pending',
            justification TEXT DEFAULT ''
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            required INTEGER DEFAULT 0
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            instructor_id INTEGER,
            semester TEXT NOT NULL,
            period_state TEXT NOT NULL,
            meeting_time TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            cancelled INTEGER DEFAULT 0,
            FOREIGN KEY(course_id) REFERENCES courses(id),
            FOREIGN KEY(instructor_id) REFERENCES users(id)
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            grade TEXT DEFAULT '',
            UNIQUE(class_id, student_id),
            FOREIGN KEY(class_id) REFERENCES classes(id),
            FOREIGN KEY(student_id) REFERENCES users(id)
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS waitlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(class_id, student_id)
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            stars INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            visible_text TEXT NOT NULL,
            hidden INTEGER DEFAULT 0,
            UNIQUE(class_id, student_id)
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filed_by INTEGER NOT NULL,
            against_user INTEGER NOT NULL,
            detail TEXT NOT NULL,
            status TEXT DEFAULT 'Open'
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS graduation_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            status TEXT DEFAULT 'Pending',
            decision_note TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY(student_id) REFERENCES users(id)
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS taboo_words (
            word TEXT PRIMARY KEY
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS system_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS rule_events (
            user_id INTEGER NOT NULL,
            event_key TEXT NOT NULL,
            PRIMARY KEY(user_id, event_key)
        )
        """)
        self.conn.commit()

    def seed_data(self):
        cur = self.conn.cursor()

        def ensure_user(username, password, role, full_name, must_change=0):
            cur.execute("SELECT id FROM users WHERE username = ?", (username,))
            row = cur.fetchone()
            if row:
                return row["id"]
            cur.execute("""
                INSERT INTO users(username, password, role, full_name, must_change_password)
                VALUES (?, ?, ?, ?, ?)
            """, (username, password, role, full_name, must_change))
            return cur.lastrowid

        ensure_user("registrar", "admin123", "Registrar", "Main Registrar")
        student1 = ensure_user(
            "s1001", "temp123", "Student", "Alice Rivera", 1)
        student2 = ensure_user("s1002", "temp123", "Student", "Brian Chen", 1)
        student3 = ensure_user(
            "s1003", "temp123", "Student", "Camila Torres", 1)
        student4 = ensure_user("s1004", "temp123", "Student", "Daniel Park", 1)
        instructor1 = ensure_user(
            "i2001", "teach123", "Instructor", "Prof. Diaz")
        instructor2 = ensure_user(
            "i2002", "teach123", "Instructor", "Prof. Kim")
        instructor3 = ensure_user(
            "i2003", "teach123", "Instructor", "Prof. Shah")

        for sid, gpa in [(student1, 3.8), (student2, 2.9), (student3, 3.4), (student4, 2.3)]:
            cur.execute(
                "INSERT OR IGNORE INTO student_profiles(user_id, gpa, overall_gpa) VALUES (?, ?, ?)", (sid, gpa, gpa))
        for iid in [instructor1, instructor2, instructor3]:
            cur.execute(
                "INSERT OR IGNORE INTO instructor_profiles(user_id, avg_rating) VALUES (?, 0.0)", (iid,))

        courses = [
            ("CS101", "Intro to Programming", 1),
            ("CS102", "Data Structures", 1),
            ("CS201", "Software Engineering", 0),
            ("CS205", "Database Systems", 0),
            ("MATH101", "Discrete Math", 1),
            ("ENG101", "Academic Writing", 1),
        ]
        for code, title, req in courses:
            cur.execute(
                "INSERT OR IGNORE INTO courses(code, title, required) VALUES (?, ?, ?)", (code, title, req))

        cur.execute("SELECT COUNT(*) AS cnt FROM classes")
        if cur.fetchone()["cnt"] == 0:
            class_specs = [
                ("CS101", instructor1, "Mon 10:00-12:00", 3),
                ("CS201", instructor2, "Wed 14:00-16:00", 2),
                ("CS205", instructor3, "Tue 09:00-11:00", 2),
                ("MATH101", instructor2, "Thu 12:00-14:00", 3),
            ]
            for course_code, inst, meeting, cap in class_specs:
                cur.execute("SELECT id FROM courses WHERE code=?",
                            (course_code,))
                course_id = cur.fetchone()["id"]
                cur.execute("""
                    INSERT INTO classes(course_id, instructor_id, semester, period_state, meeting_time, capacity)
                    VALUES (?, ?, 'Spring 2026', 'Registration', ?, ?)
                """, (course_id, inst, meeting, cap))

        for word in ["stupid", "idiot", "trash"]:
            cur.execute(
                "INSERT OR IGNORE INTO taboo_words(word) VALUES (?)", (word,))
        cur.execute(
            "INSERT OR IGNORE INTO system_state(key, value) VALUES ('current_period', 'Registration')")
        cur.execute(
            "INSERT OR IGNORE INTO system_state(key, value) VALUES ('student_quota', '6')")
        self.conn.commit()

    def authenticate(self, username, password):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE username=? AND password=?", (username, password))
        return cur.fetchone()

    def change_password(self, user_id, new_password):
        self.conn.execute(
            "UPDATE users SET password=?, must_change_password=0 WHERE id=?", (new_password, user_id))
        self.conn.commit()

    def get_setting(self, key, default=""):
        cur = self.conn.cursor()
        cur.execute("SELECT value FROM system_state WHERE key=?", (key,))
        row = cur.fetchone()
        return row["value"] if row else default

    def set_setting(self, key, value):
        self.conn.execute(
            "INSERT INTO system_state(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, str(value)),
        )
        self.conn.commit()

    def get_current_period(self):
        return self.get_setting("current_period", "Registration")

    def has_rule_event(self, user_id, event_key):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT 1 FROM rule_events WHERE user_id=? AND event_key=?", (user_id, event_key))
        return cur.fetchone() is not None

    def add_rule_event(self, user_id, event_key):
        self.conn.execute(
            "INSERT OR IGNORE INTO rule_events(user_id, event_key) VALUES (?, ?)", (user_id, event_key))

    def refresh_user_status(self, user_id):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT role, warnings, suspended FROM users WHERE id=?", (user_id,))
        row = cur.fetchone()
        if not row:
            return
        suspended = row["suspended"]
        if row["warnings"] >= 3:
            suspended = 1
        self.conn.execute(
            "UPDATE users SET suspended=? WHERE id=?", (suspended, user_id))

    def issue_warning(self, user_id, event_key, count=1):
        if event_key and self.has_rule_event(user_id, event_key):
            return False
        self.conn.execute(
            "UPDATE users SET warnings = warnings + ? WHERE id=?", (count, user_id))
        if event_key:
            self.add_rule_event(user_id, event_key)
        self.refresh_user_status(user_id)
        self.conn.commit()
        return True

    def get_student_quota(self):
        try:
            return int(self.get_setting("student_quota", "6"))
        except ValueError:
            return 6

    def get_active_student_count(self):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM users WHERE role='Student' AND suspended=0")
        return cur.fetchone()["cnt"]

    def evaluate_application_rule(self, app):
        if app["role_applied"] != "Student":
            return "Approve", "Instructor applications may be approved directly by the registrar."
        quota = self.get_student_quota()
        active_students = self.get_active_student_count()
        if app["gpa"] > 3.0 and active_students < quota:
            return "Approve", f"Student GPA is above 3.0 and the active student count {active_students}/{quota} is within quota."
        if app["gpa"] <= 3.0:
            return "Reject", "Student GPA must be above 3.0 for normal admission."
        return "Reject", f"Student quota reached: {active_students}/{quota} active students."

    def set_current_period(self, new_period):
        old_period = self.get_current_period()
        message_parts = []
        requested_period = new_period
        if new_period == "Running":
            affected = self.run_running_period_audit()
            if affected:
                requested_period = "Special Registration"
                message_parts.append(
                    "Classes with fewer than 3 students were canceled, so the system moved into Special Registration.")
        elif old_period == "Grading" and new_period != "Grading":
            audit_message = self.run_grading_period_audit()
            if audit_message:
                message_parts.append(audit_message)
        self.set_setting("current_period", requested_period)
        self.conn.execute(
            "UPDATE classes SET period_state=? WHERE cancelled=0", (requested_period,))
        self.conn.commit()
        if not message_parts:
            message_parts.append(
                f"Semester period changed from {old_period} to {requested_period}.")
        return " ".join(message_parts)

    def public_rankings(self):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT u.full_name, sp.overall_gpa
        FROM student_profiles sp
        JOIN users u ON u.id = sp.user_id
        ORDER BY sp.overall_gpa DESC
        LIMIT 5
        """)
        top_students = cur.fetchall()
        cur.execute("""
        SELECT c.code, c.title, ROUND(AVG(r.stars), 2) AS avg_stars
        FROM reviews r
        JOIN classes cl ON cl.id = r.class_id
        JOIN courses c ON c.id = cl.course_id
        WHERE r.hidden = 0
        GROUP BY c.code, c.title
        ORDER BY avg_stars DESC
        LIMIT 5
        """)
        top_classes = cur.fetchall()
        cur.execute("""
        SELECT c.code, c.title, ROUND(AVG(r.stars), 2) AS avg_stars
        FROM reviews r
        JOIN classes cl ON cl.id = r.class_id
        JOIN courses c ON c.id = cl.course_id
        WHERE r.hidden = 0
        GROUP BY c.code, c.title
        ORDER BY avg_stars ASC
        LIMIT 5
        """)
        low_classes = cur.fetchall()
        return top_students, top_classes, low_classes

    def submit_application(self, full_name, role_applied, gpa):
        self.conn.execute(
            "INSERT INTO applications(full_name, role_applied, gpa) VALUES (?, ?, ?)", (full_name, role_applied, gpa))
        self.conn.commit()

    def get_applications(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM applications ORDER BY status, id DESC")
        return cur.fetchall()

    def get_class_setup_rows(self):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT cl.id, c.code, c.title, cl.meeting_time, cl.capacity, cl.instructor_id,
               u.full_name AS instructor
        FROM classes cl
        JOIN courses c ON c.id = cl.course_id
        LEFT JOIN users u ON u.id = cl.instructor_id
        ORDER BY c.code
        """)
        return cur.fetchall()

    def update_class_setup(self, class_id, instructor_id, meeting_time, capacity):
        if self.get_current_period() != "Setup":
            return "Class setup is only editable during the Setup period."
        self.conn.execute(
            "UPDATE classes SET instructor_id=?, meeting_time=?, capacity=?, period_state='Setup' WHERE id=?",
            (instructor_id, meeting_time, capacity, class_id),
        )
        self.conn.commit()
        return "Class setup updated."

    def approve_application(self, app_id, justification=""):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM applications WHERE id=?", (app_id,))
        app = cur.fetchone()
        if not app or app["status"] != "Pending":
            return "Application not found or already processed."
        recommended_action, reason = self.evaluate_application_rule(app)
        if recommended_action != "Approve" and not justification.strip():
            return f"Approval requires a justification. Rule check: {reason}"
        cur.execute(
            "UPDATE applications SET status='Approved', justification=? WHERE id=?", (justification, app_id))
        role = app["role_applied"]
        username = f"{'s' if role == 'Student' else 'i'}{1000 + app_id}"
        password = "temp123" if role == "Student" else "teach123"
        try:
            cur.execute("INSERT INTO users(username, password, role, full_name, must_change_password) VALUES (?, ?, ?, ?, ?)",
                        (username, password, role, app["full_name"], 1 if role == "Student" else 0))
        except sqlite3.IntegrityError:
            return "This application was already converted to a user."
        user_id = cur.lastrowid
        if role == "Student":
            cur.execute("INSERT INTO student_profiles(user_id, gpa, overall_gpa) VALUES (?, ?, ?)",
                        (user_id, app["gpa"], app["gpa"]))
        else:
            cur.execute(
                "INSERT INTO instructor_profiles(user_id, avg_rating) VALUES (?, 0.0)", (user_id,))
        self.conn.commit()
        return f"Approved. Username: {username} | Temporary password: {password} | Rule check: {reason}"

    def reject_application(self, app_id, justification=""):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM applications WHERE id=?", (app_id,))
        app = cur.fetchone()
        if not app or app["status"] != "Pending":
            return "Application not found or already processed."
        recommended_action, reason = self.evaluate_application_rule(app)
        if app["role_applied"] == "Student" and recommended_action != "Reject" and not justification.strip():
            return f"Rejecting this student application requires a justification. Rule check: {reason}"
        self.conn.execute(
            "UPDATE applications SET status='Rejected', justification=? WHERE id=?", (justification, app_id))
        self.conn.commit()
        return f"Rejected. Rule check: {reason}"

    def get_available_classes(self):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT cl.id, c.code, c.title, cl.meeting_time, cl.capacity, cl.period_state,
               u.full_name AS instructor,
               (SELECT COUNT(*) FROM registrations r WHERE r.class_id = cl.id) AS enrolled
        FROM classes cl
        JOIN courses c ON c.id = cl.course_id
        LEFT JOIN users u ON u.id = cl.instructor_id
        WHERE cl.cancelled = 0
        ORDER BY c.code
        """)
        rows = list(cur.fetchall())
        current_period = self.get_current_period()
        return [dict(row) | {"period_state": current_period} for row in rows]

    def get_student_registrations(self, student_id):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT r.id, cl.id AS class_id, c.code, c.title, cl.meeting_time, r.grade
        FROM registrations r
        JOIN classes cl ON cl.id = r.class_id
        JOIN courses c ON c.id = cl.course_id
        WHERE r.student_id = ?
        ORDER BY c.code
        """, (student_id,))
        return cur.fetchall()

    def register_student(self, student_id, class_id):
        cur = self.conn.cursor()
        current_period = self.get_current_period()
        if current_period not in {"Registration", "Special Registration"}:
            return "Registration is only allowed during the Registration or Special Registration period."
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM registrations WHERE student_id=?", (student_id,))
        if cur.fetchone()["cnt"] >= 4:
            return "A student can register for at most 4 courses."
        cur.execute("SELECT suspended FROM users WHERE id=?", (student_id,))
        status_row = cur.fetchone()
        if status_row and status_row["suspended"]:
            return "Suspended students cannot register for classes."
        cur.execute("""
        SELECT cl.meeting_time
        FROM registrations r
        JOIN classes cl ON cl.id = r.class_id
        WHERE r.student_id=?
        """, (student_id,))
        current_times = {row["meeting_time"] for row in cur.fetchall()}
        cur.execute(
            "SELECT meeting_time, capacity, period_state FROM classes WHERE id=?", (class_id,))
        target = cur.fetchone()
        if not target:
            return "Class not found."
        if target["meeting_time"] in current_times:
            return "Time conflict detected."
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM registrations WHERE class_id=?", (class_id,))
        enrolled = cur.fetchone()["cnt"]
        if enrolled >= target["capacity"]:
            try:
                cur.execute("INSERT INTO waitlist(class_id, student_id, created_at) VALUES (?, ?, ?)",
                            (class_id, student_id, datetime.now().isoformat()))
                self.conn.commit()
                return "Class is full. Student added to the wait-list."
            except sqlite3.IntegrityError:
                return "Already registered or already on the wait-list."
        try:
            cur.execute(
                "INSERT INTO registrations(class_id, student_id) VALUES (?, ?)", (class_id, student_id))
            self.conn.commit()
            return "Registration successful."
        except sqlite3.IntegrityError:
            return "Already registered for this class."

    def get_instructor_classes(self, instructor_id):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT cl.id, c.code, c.title, cl.meeting_time
        FROM classes cl
        JOIN courses c ON c.id = cl.course_id
        WHERE cl.instructor_id = ? AND cl.cancelled = 0
        ORDER BY c.code
        """, (instructor_id,))
        return cur.fetchall()

    def get_students_in_class(self, class_id):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT r.id, u.full_name, u.id AS student_id, u.username, u.warnings,
               sp.overall_gpa, sp.honor_roll, r.grade
        FROM registrations r
        JOIN users u ON u.id = r.student_id
        LEFT JOIN student_profiles sp ON sp.user_id = u.id
        WHERE r.class_id = ?
        ORDER BY u.full_name
        """, (class_id,))
        return cur.fetchall()

    def assign_grade(self, registration_id, grade):
        if self.get_current_period() != "Grading":
            return "Grades can only be assigned during the Grading period."
        self.conn.execute(
            "UPDATE registrations SET grade=? WHERE id=?", (grade, registration_id))
        self.conn.commit()
        self.recalculate_gpa()
        return "Grade saved."

    def get_waitlist(self, class_id):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT w.id, u.full_name, u.id AS student_id
        FROM waitlist w
        JOIN users u ON u.id = w.student_id
        WHERE w.class_id = ?
        ORDER BY w.created_at
        """, (class_id,))
        return cur.fetchall()

    def admit_waitlisted_student(self, wait_id, class_id):
        if self.get_current_period() not in {"Registration", "Special Registration"}:
            return "Wait-list admissions are only available during Registration or Special Registration."
        cur = self.conn.cursor()
        cur.execute(
            "SELECT student_id FROM waitlist WHERE id=? AND class_id=?", (wait_id, class_id))
        row = cur.fetchone()
        if not row:
            return "Wait-list record not found."
        cur.execute("SELECT suspended FROM users WHERE id=?",
                    (row["student_id"],))
        student_status = cur.fetchone()
        if student_status and student_status["suspended"]:
            return "Suspended students cannot be admitted from the wait-list."
        cur.execute("SELECT capacity FROM classes WHERE id=?", (class_id,))
        capacity = cur.fetchone()["capacity"]
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM registrations WHERE class_id=?", (class_id,))
        if cur.fetchone()["cnt"] >= capacity:
            return "Class is still full."
        cur.execute("INSERT INTO registrations(class_id, student_id) VALUES (?, ?)",
                    (class_id, row["student_id"]))
        cur.execute("DELETE FROM waitlist WHERE id=?", (wait_id,))
        self.conn.commit()
        return "Wait-listed student admitted."

    def get_taboo_words(self):
        cur = self.conn.cursor()
        cur.execute("SELECT word FROM taboo_words ORDER BY word")
        return [row["word"] for row in cur.fetchall()]

    def add_taboo_word(self, word):
        self.conn.execute(
            "INSERT OR IGNORE INTO taboo_words(word) VALUES (?)", (word.lower().strip(),))
        self.conn.commit()

    def submit_review(self, class_id, student_id, stars, review_text):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT grade FROM registrations WHERE class_id=? AND student_id=?", (class_id, student_id))
        reg = cur.fetchone()
        if not reg:
            return "Only students enrolled in the class can review it."
        if reg["grade"]:
            return "Reviews close after the instructor posts the grade."
        taboo = self.get_taboo_words()
        words = review_text.split()
        hit_count = 0
        visible_words = []
        for w in words:
            clean = w.lower().strip(".,!?")
            if clean in taboo:
                hit_count += 1
                visible_words.append("*" * len(w))
            else:
                visible_words.append(w)
        hidden = 0
        visible_text = " ".join(visible_words)
        warning_count = 0
        warning_key = None
        if hit_count >= 3:
            hidden = 1
            visible_text = "[Hidden due to taboo language]"
            warning_count = 2
            warning_key = f"review_taboo_3_{class_id}"
        elif hit_count in [1, 2]:
            warning_count = 1
            warning_key = f"review_taboo_1_{class_id}"
        try:
            self.conn.execute("""
            INSERT INTO reviews(class_id, student_id, stars, review_text, visible_text, hidden)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (class_id, student_id, stars, review_text, visible_text, hidden))
            self.conn.commit()
            if warning_count:
                self.issue_warning(student_id, warning_key, warning_count)
            self.update_instructor_ratings()
            return "Review submitted."
        except sqlite3.IntegrityError:
            return "You already reviewed this class."

    def get_reviews(self):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT c.code, c.title, u.full_name AS student_name, r.stars, r.visible_text, r.hidden
        FROM reviews r
        JOIN classes cl ON cl.id = r.class_id
        JOIN courses c ON c.id = cl.course_id
        JOIN users u ON u.id = r.student_id
        ORDER BY c.code
        """)
        return cur.fetchall()

    def file_complaint(self, filed_by, against_user, detail):
        self.conn.execute("INSERT INTO complaints(filed_by, against_user, detail) VALUES (?, ?, ?)",
                          (filed_by, against_user, detail))
        self.conn.commit()
    def apply_for_graduation(self, student_id):
        cur = self.conn.cursor()
        
        cur.execute("""
            SELECT COUNT(*) AS cnt
            FROM registrations
            WHERE student_id=? AND grade <> ''
        """, (student_id,))
        completed = cur.fetchone()["cnt"]
        
        cur.execute("""
            SELECT c.code
            FROM courses c
            WHERE c.required = 1
            AND c.code NOT IN (
                SELECT co.code
                FROM registrations r
                JOIN classes cl ON cl.id = r.class_id
                JOIN courses co ON co.id = cl.course_id
                WHERE r.student_id=? AND r.grade NOT IN ('', 'F')
            )
        """, (student_id,))
        missing_required = [row["code"] for row in cur.fetchall()]
        
        if completed < 8 or missing_required:
            self.issue_warning(student_id, "reckless_graduation_application", 1)
            self.conn.execute("""
                INSERT INTO graduation_applications(student_id, status, decision_note, created_at)
                VALUES (?, 'Rejected', ?, ?)
            """, (
                student_id,
                f"Rejected automatically. Completed classes: {completed}/8. Missing required: {', '.join(missing_required) if missing_required else 'None'}. Warning issued.",
                datetime.now().isoformat()
            ))
            self.conn.commit()
            return "Graduation rejected. You need 8 completed classes and all required courses. Warning issued."
        
        self.conn.execute("""
            INSERT INTO graduation_applications(student_id, status, decision_note, created_at)
            VALUES (?, 'Pending', 'Eligible for registrar review.', ?)
        """, (student_id, datetime.now().isoformat()))
        self.conn.commit()
        return "Graduation application submitted for registrar review."
    
    def get_graduation_applications(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT ga.id, ga.status, ga.decision_note, ga.created_at,
                   u.full_name, u.username
            FROM graduation_applications ga
            JOIN users u ON u.id = ga.student_id
            ORDER BY ga.id DESC
        """)
        return cur.fetchall()


    def decide_graduation(self, grad_id, approve=True, note=""):
        cur = self.conn.cursor()
        status = "Approved" if approve else "Rejected"
        final_note = note.strip() or status

        cur.execute("SELECT student_id FROM graduation_applications WHERE id=?", (grad_id,))
        row = cur.fetchone()
        if not row:
            return "Graduation application not found."
        
        self.conn.execute("""
            UPDATE graduation_applications
            SET status=?, decision_note=?
            WHERE id=?
        """, (status, final_note, grad_id))

        if approve:
            self.conn.execute(
                "UPDATE users SET suspended=1 WHERE id=?",
                (row["student_id"],)
            )

        self.conn.commit()
        return f"Graduation application {status.lower()}."

    def get_users_by_role(self, role):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, full_name, username FROM users WHERE role=? ORDER BY full_name", (role,))
        return cur.fetchall()

    def get_complaints(self):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT c.id, uf.full_name AS filed_by, ua.full_name AS against_name, c.detail, c.status
        FROM complaints c
        JOIN users uf ON uf.id = c.filed_by
        JOIN users ua ON ua.id = c.against_user
        ORDER BY c.id DESC
        """)
        return cur.fetchall()

    def resolve_complaint(self, complaint_id, punish_against=True):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM complaints WHERE id=?", (complaint_id,))
        row = cur.fetchone()
        if not row:
            return "Complaint not found."
        if punish_against:
            self.issue_warning(
                row["against_user"], f"complaint_against_{complaint_id}", 1)
            status = "Resolved - warning issued to accused"
        else:
            self.issue_warning(
                row["filed_by"], f"complaint_filer_{complaint_id}", 1)
            status = "Resolved - warning issued to filer"
        self.conn.execute(
            "UPDATE complaints SET status=? WHERE id=?", (status, complaint_id))
        self.conn.commit()
        return status

    def run_running_period_audit(self):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT cl.id, cl.instructor_id,
               (SELECT COUNT(*) FROM registrations r WHERE r.class_id = cl.id) AS enrolled
        FROM classes cl
        WHERE cl.cancelled = 0
        """)
        affected_students = 0
        for row in cur.fetchall():
            if row["enrolled"] < 3:
                cur.execute(
                    "SELECT student_id FROM registrations WHERE class_id=?", (row["id"],))
                student_ids = [item["student_id"] for item in cur.fetchall()]
                affected_students += len(student_ids)
                self.conn.execute(
                    "UPDATE classes SET cancelled=1 WHERE id=?", (row["id"],))
                self.conn.execute(
                    "DELETE FROM registrations WHERE class_id=?", (row["id"],))
                self.conn.execute(
                    "DELETE FROM waitlist WHERE class_id=?", (row["id"],))
                if row["instructor_id"]:
                    self.issue_warning(
                        row["instructor_id"], f"cancelled_class_{row['id']}", 1)

        cur.execute("SELECT id FROM users WHERE role='Student' AND suspended=0")
        period_key = "special_registration" if affected_students else "running"
        for row in cur.fetchall():
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM registrations WHERE student_id=?", (row["id"],))
            if cur.fetchone()["cnt"] < 2:
                self.issue_warning(
                    row["id"], f"{period_key}_underload", 1)

        cur.execute("""
        SELECT u.id,
               COUNT(cl.id) AS total_classes,
               SUM(CASE WHEN cl.cancelled = 1 THEN 1 ELSE 0 END) AS cancelled_classes
        FROM users u
        LEFT JOIN classes cl ON cl.instructor_id = u.id
        WHERE u.role='Instructor'
        GROUP BY u.id
        """)
        for row in cur.fetchall():
            if row["total_classes"] and row["cancelled_classes"] == row["total_classes"]:
                self.conn.execute(
                    "UPDATE users SET suspended=1 WHERE id=?", (row["id"],))
        self.conn.commit()
        return affected_students > 0

    def run_grading_period_audit(self):
        cur = self.conn.cursor()
        messages = []
        cur.execute("""
        SELECT cl.id, cl.instructor_id, c.code
        FROM classes cl
        JOIN courses c ON c.id = cl.course_id
        WHERE cl.cancelled = 0
        """)
        for row in cur.fetchall():
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM registrations WHERE class_id=? AND grade=''", (row["id"],))
            if cur.fetchone()["cnt"] > 0 and row["instructor_id"]:
                self.issue_warning(
                    row["instructor_id"], f"missing_grades_{row['id']}", 1)
                messages.append(f"{row['code']} has missing grades.")
        return " ".join(messages[:4])

    def update_instructor_ratings(self):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT cl.instructor_id, AVG(r.stars) AS avg_rating
        FROM reviews r
        JOIN classes cl ON cl.id = r.class_id
        GROUP BY cl.instructor_id
        """)
        for row in cur.fetchall():
            avg_rating = row["avg_rating"] or 0.0
            self.conn.execute(
                "UPDATE instructor_profiles SET avg_rating=? WHERE user_id=?", (avg_rating, row["instructor_id"]))
            if avg_rating < 2:
                self.issue_warning(
                    row["instructor_id"], f"low_average_rating_{row['instructor_id']}", 1)
        self.conn.commit()

    def recalculate_gpa(self):
        points = {"A": 4.0, "A-": 3.7, "B+": 3.3, "B": 3.0,
                  "B-": 2.7, "C+": 2.3, "C": 2.0, "D": 1.0, "F": 0.0}
        cur = self.conn.cursor()
        for st in self.get_users_by_role("Student"):
            cur.execute(
                "SELECT c.code, r.grade FROM registrations r JOIN classes cl ON cl.id = r.class_id JOIN courses c ON c.id = cl.course_id WHERE r.student_id=? AND r.grade <> ''",
                (st["id"],),
            )
            grade_rows = cur.fetchall()
            grades = [points[g["grade"]]
                      for g in grade_rows if g["grade"] in points]
            gpa = round(sum(grades) / len(grades), 2) if grades else 0.0
            honor_roll = 1 if gpa > 3.75 else 0
            self.conn.execute("UPDATE student_profiles SET gpa=?, overall_gpa=?, honor_roll=? WHERE user_id=?",
                              (gpa, gpa, honor_roll, st["id"]))
            if gpa < 2.0 and grades:
                self.conn.execute(
                    "UPDATE users SET suspended=1 WHERE id=?", (st["id"],))
            elif 2.0 <= gpa <= 2.25:
                self.issue_warning(st["id"], "gpa_interview_band", 1)
            failures = {}
            for row in grade_rows:
                if row["grade"] == "F":
                    failures[row["code"]] = failures.get(row["code"], 0) + 1
            for course_code, count in failures.items():
                if count >= 2:
                    self.conn.execute(
                        "UPDATE users SET suspended=1 WHERE id=?", (st["id"],))
                    self.add_rule_event(
                        st["id"], f"failed_same_course_twice_{course_code}")
            if honor_roll:
                cur.execute(
                    "SELECT warnings FROM users WHERE id=?", (st["id"],))
                warn_row = cur.fetchone()
                if warn_row and warn_row["warnings"] > 0 and not self.has_rule_event(st["id"], "honor_roll_warning_credit"):
                    self.conn.execute(
                        "UPDATE users SET warnings = warnings - 1 WHERE id=?", (st["id"],))
                    self.add_rule_event(st["id"], "honor_roll_warning_credit")
            self.refresh_user_status(st["id"])
        self.conn.commit()

    def get_user_summary(self, user_id):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT u.full_name, u.username, u.role, u.warnings, u.suspended,
               sp.gpa, sp.overall_gpa, sp.honor_roll, ip.avg_rating
        FROM users u
        LEFT JOIN student_profiles sp ON sp.user_id = u.id
        LEFT JOIN instructor_profiles ip ON ip.user_id = u.id
        WHERE u.id = ?
        """, (user_id,))
        return cur.fetchone()

    def build_local_knowledge(self, user=None):
        facts = [
            f"Current semester period: {self.get_current_period()}",
            f"Student quota: {self.get_student_quota()} active students",
            "Students normally need GPA above 3.0 and open quota for admission.",
            "Registration is only open during Registration or Special Registration.",
            "Reviews are only allowed by enrolled students before grades are posted.",
        ]
        top_students, top_classes, low_classes = self.public_rankings()
        for row in top_students[:3]:
            facts.append(
                f"Top GPA student: {row['full_name']} with GPA {row['overall_gpa']}")
        for row in top_classes[:2]:
            facts.append(
                f"Highly rated class: {row['code']} {row['title']} rated {row['avg_stars']}")
        if user and user["role"] == "Student":
            for row in self.get_student_registrations(user["id"]):
                facts.append(
                    f"Student class: {row['code']} {row['title']} at {row['meeting_time']} grade {row['grade'] or 'not posted'}")
        if user and user["role"] == "Instructor":
            for row in self.get_instructor_classes(user["id"]):
                facts.append(
                    f"Instructor teaches {row['code']} {row['title']} at {row['meeting_time']}")
        return facts

    def answer_question(self, question, user=None):
        question_lower = question.lower().strip()
        if not question_lower:
            return "Ask about admissions, registration periods, classes, GPA rules, or your current records."
        facts = self.build_local_knowledge(user)
        scored = []
        tokens = [token for token in question_lower.replace(
            "?", " ").split() if len(token) > 2]
        for fact in facts:
            fact_lower = fact.lower()
            score = sum(1 for token in tokens if token in fact_lower)
            if score:
                scored.append((score, fact))
        scored.sort(reverse=True)
        if scored:
            best = [fact for _, fact in scored[:3]]
            return "Local college info:\n- " + "\n- ".join(best)
        return (
            "No strong match was found in the local college knowledge store. "
            "In the full project this would be the point to send the question to an LLM, with a hallucination warning."
        )


class College0App:
    BG = "#f4f1f7"
    NAV = "#6a4a98"
    NAV_LIGHT = "#7c5aaa"
    NAV_DARK = "#553b81"
    GOLD = "#f0d18d"
    CARD = "#ffffff"
    CARD_ALT = "#faf7fd"
    FEATURE = "#a14567"
    FEATURE_BORDER = "#8f3656"
    BANNER = "#a5a2ae"
    TEXT = "#342952"
    MUTED = "#746b86"
    BORDER = "#ddd4ea"
    SUCCESS = "#2d8c5f"
    DANGER = "#bb4f69"

    def __init__(self, root):
        self.root = root
        self.root.title("College0 - CCNY Style Demo")
        self.root.geometry("1300x820")
        self.root.minsize(1180, 760)
        self.root.configure(bg=self.BG)
        self.db = College0DB()
        self.current_user = None
        self.nav_buttons = {}
        self.pages = {}
        self.public_role_var = None
        self.public_name_entry = None
        self.public_gpa_entry = None
        self.configure_styles()
        self.build_shell()
        self.refresh_header_status()
        self.open_main_dashboard()

    def configure_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TCombobox", padding=6, arrowsize=14)
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", self.CARD)],
            selectbackground=[("readonly", self.CARD)],
            selectforeground=[("readonly", self.TEXT)],
            foreground=[("readonly", self.TEXT)],
        )

    def build_shell(self):
        self.header = tk.Frame(self.root, bg=self.NAV, height=94)
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)
        self.header.grid_columnconfigure(1, weight=1)

        brand = tk.Frame(self.header, bg=self.NAV)
        brand.grid(row=0, column=0, sticky="w", padx=(18, 12), pady=12)
        self.make_ccny_logo(brand).pack()

        title_wrap = tk.Frame(self.header, bg=self.NAV)
        title_wrap.grid(row=0, column=1)
        tk.Label(
            title_wrap,
            text="College0 Management System",
            bg=self.NAV,
            fg="white",
            font=("Segoe UI", 22, "bold"),
        ).pack()
        tk.Label(
            title_wrap,
            text="CCNY-inspired visual theme",
            bg=self.NAV,
            fg="#e7dbff",
            font=("Segoe UI", 10),
        ).pack(pady=(4, 0))

        status_wrap = tk.Frame(self.header, bg=self.NAV)
        status_wrap.grid(row=0, column=2, sticky="e", padx=(12, 20))
        tk.Label(status_wrap, text="Session", bg=self.NAV, fg="#eadfff",
                 font=("Segoe UI", 9, "bold")).pack(anchor="e")
        self.header_status = tk.Label(
            status_wrap, text="Guest mode", bg=self.NAV, fg="white", font=("Segoe UI", 10, "bold"))
        self.header_status.pack(anchor="e")

        body = tk.Frame(self.root, bg=self.BG)
        body.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(body, bg=self.NAV, width=260)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.content = tk.Frame(body, bg=self.BG)
        self.content.pack(side="left", fill="both", expand=True)

        tk.Label(self.sidebar, text="MENU", bg=self.NAV, fg="#f1e9ff", font=(
            "Segoe UI", 11, "bold")).pack(anchor="w", padx=20, pady=(22, 8))

        nav_items = [
            ("Dashboard", self.open_main_dashboard),
            ("Apply as Student", lambda: self.open_public_application("Student")),
            ("Apply as Instructor", lambda: self.open_public_application("Instructor")),
            ("Login", lambda: self.show_page("Login", "Login")),
            ("Submit Review", self.open_review_page),
            ("File Complaint", self.open_complaint_page),
            ("AI Assistant", self.open_ai_page),
            ("Help", self.show_help),
            ("Exit", self.root.destroy),
        ]
        for label, command in nav_items:
            btn = tk.Label(
                self.sidebar,
                text=label,
                anchor="w",
                bg=self.NAV,
                fg="white",
                font=("Segoe UI", 11, "bold"),
                padx=22,
                pady=16,
                cursor="hand2",
            )

            btn.pack(fill="x")

            btn.bind("<Button-1>", lambda e, cmd=command: cmd())
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=self.NAV_LIGHT))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=self.NAV))

            tk.Frame(
                self.sidebar,
                bg="#8065ac",
                height=1
            ).pack(fill="x", padx=14)

            self.nav_buttons[label] = btn


        tk.Label(self.sidebar, text="Demo Access", bg=self.NAV, fg=self.GOLD, font=(
            "Segoe UI", 10, "bold")).pack(anchor="w", padx=20, pady=(18, 4))
        demo_text = "Registrar\nregistrar / admin123\n\nStudent\ns1001 / temp123\n\nInstructor\ni2001 / teach123"
        tk.Label(self.sidebar, text=demo_text, justify="left", bg=self.NAV,
                 fg="#efe8ff", font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(8, 0))

        footer = tk.Frame(self.sidebar, bg=self.NAV)
        footer.pack(side="bottom", fill="x", pady=20)
        tk.Label(
            footer,
            text="One-window local GUI\nSame project logic, updated branding",
            bg=self.NAV,
            fg="#d8c9f4",
            font=("Segoe UI", 9),
            justify="left",
        ).pack(anchor="w", padx=20)

        for page in ["Public", "Login", "Dashboard", "Review", "Complaint", "AI"]:
            self.pages[page] = tk.Frame(self.content, bg=self.BG)

        self.build_public_page()
        self.build_login_page()
        self.build_dashboard_placeholder()

    def make_ccny_logo(self, parent):
        canvas = tk.Canvas(parent, width=164, height=68,
                           bg=self.NAV, highlightthickness=0)
        canvas.create_rectangle(9, 10, 155, 58, outline="white", width=2)
        canvas.create_text(82, 35, text="CCNY", fill="white",
                           font=("Times New Roman", 28, "bold"))
        return canvas

    def show_page(self, page_name, nav_key=None):
        for frame in self.pages.values():
            frame.pack_forget()
        self.set_active_nav(nav_key)
        self.pages[page_name].pack(fill="both", expand=True)

    def set_active_nav(self, nav_key):
        for btn in self.nav_buttons.values():
            btn.configure(bg=self.NAV)
        if nav_key in self.nav_buttons:
            self.nav_buttons[nav_key].configure(bg=self.NAV_LIGHT)

    def open_main_dashboard(self):
        if self.current_user:
            self.build_dashboard()
            self.show_page("Dashboard", "Dashboard")
        else:
            self.show_page("Public", "Dashboard")

    def open_public_application(self, role):
        self.show_page("Public", f"Apply as {role}")
        self.set_public_role(role)
    
    def open_review_page(self):
        if not self.current_user or self.current_user["role"] != "Student":
            messagebox.showerror("Access denied", "Please log in as a student first.")
            return
        self.build_review_page()
        self.show_page("Review", "Submit Review")
    
    def open_complaint_page(self):
        if not self.current_user or self.current_user["role"] != "Student":
            messagebox.showerror("Access denied", "Please log in as a student first.")
            return
        self.build_complaint_page()
        self.show_page("Complaint", "File Complaint")
    def build_complaint_page(self):
        frame = self.pages["Complaint"]
        self.clear_frame(frame)

        wrapper = tk.Frame(frame, bg=self.BG)
        wrapper.pack(fill="both", expand=True, padx=24, pady=24)

        self.section_title(wrapper, "File Complaint", "Report an issue with another user")

        card, body = self.make_card(wrapper, "Complaint Form")
        card.pack(fill="x", pady=20)

        tk.Label(body, text="Select User", bg=self.CARD).pack(anchor="w")

        users = self.db.get_users_by_role("Instructor") + self.db.get_users_by_role("Student")

        user_map = {}
        user_var = tk.StringVar()

        dropdown = ttk.Combobox(body, textvariable=user_var, state="readonly")
        dropdown.pack(fill="x", pady=5)

        values = []
        for u in users:
            label = f"{u['full_name']} ({u['username']})"
            user_map[label] = u["id"]
            values.append(label)

        dropdown["values"] = values

        tk.Label(body, text="Complaint Detail", bg=self.CARD).pack(anchor="w")
        detail_box = tk.Text(body, height=4)
        detail_box.pack(fill="x", pady=5)

        def submit():
            selected = user_var.get()
            if not selected:
                messagebox.showerror("Error", "Select a user")
                return

            detail = detail_box.get("1.0", tk.END).strip()
            if not detail:
                messagebox.showerror("Error", "Enter complaint detail")
                return

            self.db.file_complaint(
                self.current_user["id"],
                user_map[selected],
                detail
            )

            messagebox.showinfo("Success", "Complaint submitted")

        tk.Button(body, text="Submit Complaint",
                command=submit,
                bg=self.NAV, fg="white").pack(pady=10)
    
    def open_ai_page(self):
        self.build_ai_page()
        self.show_page("AI", "AI Assistant")

    def build_review_page(self):
        frame = self.pages["Review"]
        self.clear_frame(frame)

        wrapper = tk.Frame(frame, bg=self.BG)
        wrapper.pack(fill="both", expand=True, padx=24, pady=24)

        self.section_title(wrapper, "Submit Review", "Leave feedback for your classes")

        card, body = self.make_card(wrapper, "Review Form")
        card.pack(fill="x", pady=20)

    
        classes = self.db.get_student_registrations(self.current_user["id"])

        class_map = {}
        class_var = tk.StringVar()

        tk.Label(body, text="Select Class", bg=self.CARD).pack(anchor="w")

        dropdown = ttk.Combobox(body, textvariable=class_var, state="readonly")
        dropdown.pack(fill="x", pady=5)

        values = []
        for c in classes:
            label = f"{c['code']} - {c['title']}"
            class_map[label] = c["class_id"]
            values.append(label)

        dropdown["values"] = values

    
        tk.Label(body, text="Stars (1-5)", bg=self.CARD).pack(anchor="w")
        stars_entry = tk.Entry(body)
        stars_entry.pack(fill="x", pady=5)

    # Review text
        tk.Label(body, text="Review", bg=self.CARD).pack(anchor="w")
        review_box = tk.Text(body, height=4)
        review_box.pack(fill="x", pady=5)

    

        def submit():
            selected = class_var.get()
            if not selected:
                messagebox.showerror("Error", "Select a class")
                return

            try:
                stars = int(stars_entry.get())
                if stars < 1 or stars > 5:
                    raise ValueError
            except:
                messagebox.showerror("Error", "Stars must be 1-5")
                return

            text = review_box.get("1.0", tk.END).strip()
            if not text:
                messagebox.showerror("Error", "Write a review")
                return

            class_id = class_map[selected]

            result = self.db.submit_review(
                class_id,
                self.current_user["id"],
                stars,
                text
            )

            messagebox.showinfo("Result", result)

        tk.Button(body, text="Submit Review",
                command=submit,
                bg=self.NAV, fg="white").pack(pady=10)

    def build_ai_page(self):
        frame = self.pages["AI"]
        self.clear_frame(frame)
        
        wrapper = tk.Frame(frame, bg=self.BG)
        wrapper.pack(fill="both", expand=True, padx=24, pady=24)
        
        self.section_title(
            wrapper,
            "College0 AI Assistant",
            "Ask questions about registrations, GPA, classes, reviews, warnings, and semester rules."
            )
        ai_card = self.build_ai_panel(
            wrapper,
            self.current_user,
            "AI College Assistant"
            )
        
        ai_card.pack(fill="both", expand=True, pady=(20, 0))

    def show_help(self):
        messagebox.showinfo(
            "Help",
            "Use the left menu to view the home page, submit an application, or log in with one of the demo accounts.",
        )

    def set_public_role(self, role):
        if self.public_role_var is not None:
            self.public_role_var.set(role)
        if self.public_gpa_entry is not None:
            self.public_gpa_entry.delete(0, tk.END)
            self.public_gpa_entry.insert(
                0, "3.20" if role == "Student" else "0.00")
        if self.public_name_entry is not None:
            self.public_name_entry.focus_set()

    def clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

    def make_card(self, parent, title, subtitle=None):
        outer = tk.Frame(parent, bg=self.BORDER)
        inner = tk.Frame(outer, bg=self.CARD)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        tk.Label(inner, text=title, bg=self.CARD, fg=self.NAV_DARK, font=(
            "Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=(14, 4))
        if subtitle:
            tk.Label(inner, text=subtitle, bg=self.CARD, fg=self.MUTED, font=(
                "Segoe UI", 9)).pack(anchor="w", padx=16, pady=(0, 8))
        body = tk.Frame(inner, bg=self.CARD)
        body.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        return outer, body

    def styled_listbox(self, parent, height=10):
        return tk.Listbox(parent, height=height, relief="flat", bg=self.CARD_ALT, fg=self.TEXT,
                          highlightthickness=1, highlightbackground=self.BORDER,
                          font=("Segoe UI", 10), selectbackground="#e5daf6",
                          selectforeground=self.TEXT, activestyle="none")

    def section_title(self, parent, title, subtitle=""):
        tk.Label(parent, text=title, bg=self.BG, fg=self.NAV_DARK,
                 font=("Segoe UI", 24, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(parent, text=subtitle, bg=self.BG, fg=self.MUTED,
                     font=("Segoe UI", 11)).pack(anchor="w", pady=(6, 0))

    def build_ai_panel(self, parent, user=None, title="College0 AI Assistant"):
        card, body = self.make_card(
            parent,
            title,
            "Answers come from the local College0 knowledge store first. If nothing matches, the app warns that an external LLM answer could hallucinate.",
        )
        question = tk.Text(body, height=4, relief="solid",
                           bd=1, font=("Segoe UI", 10))
        question.pack(fill="x", pady=(0, 10))
        answer = tk.Text(body, height=8, relief="solid", bd=1,
                         font=("Segoe UI", 10), wrap="word")
        answer.pack(fill="both", expand=True)

        def ask_ai():
            response = self.db.answer_question(
                question.get("1.0", tk.END).strip(), user)
            answer.delete("1.0", tk.END)
            answer.insert("1.0", response)

        tk.Button(body, text="Ask AI", command=ask_ai, relief="flat", bg=self.NAV, fg="white",
                  activebackground=self.NAV_LIGHT, activeforeground="white", font=("Segoe UI", 10, "bold"),
                  padx=16, pady=8, cursor="hand2").pack(anchor="w", pady=(10, 0))
        return card

    def make_feature_card(self, parent, badge, title, items):
        card = tk.Frame(parent, bg=self.FEATURE_BORDER)
        inner = tk.Frame(card, bg=self.FEATURE)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        header = tk.Frame(inner, bg=self.FEATURE)
        header.pack(fill="x", padx=16, pady=(14, 10))
        tk.Label(
            header,
            text=badge,
            bg=self.GOLD,
            fg=self.NAV_DARK,
            font=("Segoe UI", 8, "bold"),
            padx=8,
            pady=4,
        ).pack(anchor="w")
        tk.Label(
            header,
            text=title,
            bg=self.FEATURE,
            fg="white",
            font=("Segoe UI", 11, "bold"),
            justify="left",
            anchor="w",
            wraplength=180,
        ).pack(anchor="w", fill="x", pady=(8, 0))

        tk.Frame(inner, bg="#c78aa0", height=1).pack(fill="x", padx=16)
        body = tk.Frame(inner, bg=self.FEATURE)
        body.pack(fill="both", expand=True, padx=18, pady=12)
        for item in items:
            tk.Label(
                body,
                text=f"* {item}",
                bg=self.FEATURE,
                fg="white",
                wraplength=220,
                justify="left",
                font=("Segoe UI", 10),
            ).pack(anchor="w", pady=4)
        return card

    def build_public_page(self):
        frame = self.pages["Public"]
        self.clear_frame(frame)
        hero = tk.Frame(frame, bg=self.BG)
        hero.pack(fill="x", padx=30, pady=(28, 16))
        tk.Label(hero, text="Welcome to College0", bg=self.BG,
                 fg=self.NAV_DARK, font=("Segoe UI", 30, "bold")).pack()
        tk.Frame(hero, bg=self.BORDER, height=1).pack(
            fill="x", padx=180, pady=14)
        tk.Label(
            hero,
            text="An AI-enabled college management system with a CCNY-inspired campus theme.",
            bg=self.BG,
            fg=self.NAV_DARK,
            font=("Segoe UI", 12, "bold"),
        ).pack()

        ranking_row = tk.Frame(frame, bg=self.BG)
        ranking_row.pack(fill="x", padx=24, pady=(0, 10))
        top_students, top_classes, low_classes = self.db.public_rankings()
        student_items = [f"{r['full_name']} - GPA {r['overall_gpa']}" for r in top_students] or [
            "Amy S. - GPA 3.9",
            "John D. - GPA 3.8",
            "Linda K. - GPA 3.7",
        ]
        top_class_items = [f"{r['code']} {r['title']} ({r['avg_stars']})" for r in top_classes] or [
            "Advanced Python (4.8)",
            "Data Science (4.6)",
            "Creative Writing (4.5)",
        ]
        low_class_items = [f"{r['code']} {r['title']} ({r['avg_stars']})" for r in low_classes] or [
            "Intro to Algebra (2.3)",
            "History 101 (2.5)",
            "Art Appreciation (2.6)",
        ]
        groups = [
            ("TOP", "Top Rated Classes", top_class_items),
            ("LOW", "Lowest Rated Classes", low_class_items),
            ("GPA", "Highest GPA Students", student_items),
            ("CCNY", "College Highlights", [
             "Small college community", "Hands-on learning", "AI-enabled assistance"]),
        ]
        for badge, title, items in groups:
            card = self.make_feature_card(ranking_row, badge, title, items)
            card.pack(side="left", fill="both", expand=True, padx=8)

        banner = tk.Frame(frame, bg=self.BANNER, height=46)
        banner.pack(fill="x", padx=28, pady=(14, 18))
        banner.pack_propagate(False)
        tk.Label(
            banner,
            text="Prospective students and instructors can apply to College0 using the form below.",
            bg=self.BANNER,
            fg="white",
            font=("Segoe UI", 11, "bold"),
        ).pack(expand=True)

        app_card, app_body = self.make_card(
            frame, "Visitor Application", "Apply as a student or instructor while keeping the same project workflow.")
        app_card.pack(fill="x", padx=24, pady=16)
        form = tk.Frame(app_body, bg=self.CARD)
        form.pack(fill="x")
        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(2, weight=1)

        tk.Label(form, text="Full Name", bg=self.CARD, fg=self.TEXT, font=(
            "Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.public_name_entry = tk.Entry(
            form, width=34, relief="solid", bd=1, font=("Segoe UI", 10))
        self.public_name_entry.grid(
            row=1, column=0, padx=6, pady=(0, 10), sticky="we")

        tk.Label(form, text="Apply As", bg=self.CARD, fg=self.TEXT, font=(
            "Segoe UI", 10, "bold")).grid(row=0, column=1, sticky="w", padx=6, pady=6)
        self.public_role_var = tk.StringVar(value="Student")
        tk.Entry(
             form,
             textvariable=self.public_role_var,
             width=20,
             relief="solid",
             bd=1,
             font=("Segoe UI", 10),
             state="readonly",
            readonlybackground=self.CARD,
            fg=self.TEXT,
            ).grid(row=1, column=1, padx=6, pady=(0, 10), sticky="we")
        tk.Label(form, text="GPA", bg=self.CARD, fg=self.TEXT, font=(
            "Segoe UI", 10, "bold")).grid(row=0, column=2, sticky="w", padx=6, pady=6)
        self.public_gpa_entry = tk.Entry(
            form, width=12, relief="solid", bd=1, font=("Segoe UI", 10))
        self.public_gpa_entry.insert(0, "3.20")
        self.public_gpa_entry.grid(
            row=1, column=2, padx=6, pady=(0, 10), sticky="we")

        tk.Label(form, text="Student applications use GPA. Instructor applications can leave GPA at 0.00.", bg=self.CARD,
                 fg=self.MUTED, font=("Segoe UI", 9)).grid(row=2, column=0, columnspan=3, sticky="w", padx=6, pady=(0, 10))

        def submit_app():
            name = self.public_name_entry.get().strip()
            role = self.public_role_var.get()
            try:
                gpa = float(self.public_gpa_entry.get().strip() or 0)
            except ValueError:
                messagebox.showerror("Invalid GPA", "Enter a numeric GPA.")
                return
            if not name:
                messagebox.showerror(
                    "Missing name", "Please enter the applicant's full name.")
                return
            self.db.submit_application(name, role, gpa)
            messagebox.showinfo(
                "Submitted", "Application submitted successfully.")
            self.public_name_entry.delete(0, tk.END)
            self.set_public_role("Student")

        tk.Button(
            form,
            text="Submit Application",
            command=submit_app,
            relief="flat",
            bg=self.GOLD,
            fg=self.NAV,
            activebackground="#d8b96d",
            activeforeground=self.NAV,
            font=("Segoe UI", 10, "bold"),
            padx=18,
            pady=10,
            cursor="hand2",
        ).grid(row=3, column=0, columnspan=3, sticky="w", padx=6, pady=8)
        ai_card = self.build_ai_panel(frame, None, "Visitor AI Assistant")
        ai_card.pack(fill="both", expand=True, padx=24, pady=(0, 18))
        return

        ranking_row = tk.Frame(frame, bg=self.BG)
        ranking_row.pack(fill="both", expand=False, padx=24, pady=8)
        top_students, top_classes, low_classes = self.db.public_rankings()
        groups = [
            ("Highest GPA Students", [
             f"{r['full_name']}  •  GPA {r['overall_gpa']}" for r in top_students]),
            ("Highest Rated Classes", [
             f"{r['code']} {r['title']}  •  {r['avg_stars']}★" for r in top_classes]),
            ("Lowest Rated Classes", [
             f"{r['code']} {r['title']}  •  {r['avg_stars']}★" for r in low_classes]),
        ]
        for title, items in groups:
            card, body = self.make_card(ranking_row, title)
            card.pack(side="left", fill="both", expand=True, padx=8)
            lb = self.styled_listbox(body, height=9)
            lb.pack(fill="both", expand=True)
            if items:
                for item in items:
                    lb.insert(tk.END, item)
            else:
                lb.insert(tk.END, "No data available yet")

        app_card, app_body = self.make_card(
            frame, "Visitor Application", "Apply as a student or instructor using the form below.")
        app_card.pack(fill="x", padx=24, pady=16)
        form = tk.Frame(app_body, bg=self.CARD)
        form.pack(fill="x")

        tk.Label(form, text="Full Name", bg=self.CARD, fg=self.TEXT, font=(
            "Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", padx=6, pady=6)
        name_entry = tk.Entry(form, width=34, relief="solid",
                              bd=1, font=("Segoe UI", 10))
        name_entry.grid(row=1, column=0, padx=6, pady=(0, 10), sticky="w")

        tk.Label(form, text="Apply As", bg=self.CARD, fg=self.TEXT, font=(
            "Segoe UI", 10, "bold")).grid(row=0, column=1, sticky="w", padx=6, pady=6)
        role_var = tk.StringVar(value="Student")
        ttk.Combobox(form, textvariable=role_var, values=["Student", "Instructor"], width=20, state="readonly").grid(
            row=1, column=1, padx=6, pady=(0, 10), sticky="w")

        tk.Label(form, text="GPA", bg=self.CARD, fg=self.TEXT, font=(
            "Segoe UI", 10, "bold")).grid(row=0, column=2, sticky="w", padx=6, pady=6)
        gpa_entry = tk.Entry(form, width=12, relief="solid",
                             bd=1, font=("Segoe UI", 10))
        gpa_entry.insert(0, "3.20")
        gpa_entry.grid(row=1, column=2, padx=6, pady=(0, 10), sticky="w")

        tk.Label(form, text="Student applications use GPA. Instructor applications can leave GPA at 0.00.", bg=self.CARD,
                 fg=self.MUTED, font=("Segoe UI", 9)).grid(row=2, column=0, columnspan=3, sticky="w", padx=6, pady=(0, 10))

        def submit_app():
            name = name_entry.get().strip()
            role = role_var.get()
            try:
                gpa = float(gpa_entry.get().strip() or 0)
            except ValueError:
                messagebox.showerror("Invalid GPA", "Enter a numeric GPA.")
                return
            if not name:
                messagebox.showerror(
                    "Missing name", "Please enter the applicant's full name.")
                return
            self.db.submit_application(name, role, gpa)
            messagebox.showinfo(
                "Submitted", "Application submitted successfully.")
            name_entry.delete(0, tk.END)
            gpa_entry.delete(0, tk.END)
            gpa_entry.insert(0, "3.20")

        tk.Button(form, text="Submit Application", command=submit_app, relief="flat", bg=self.GOLD, fg=self.NAV,
                  activebackground="#c79310", activeforeground=self.NAV, font=("Segoe UI", 10, "bold"),
                  padx=18, pady=10, cursor="hand2").grid(row=3, column=0, columnspan=3, sticky="w", padx=6, pady=8)

    def build_login_page(self):
        frame = self.pages["Login"]
        self.clear_frame(frame)
        wrap = tk.Frame(frame, bg=self.BG)
        wrap.pack(fill="both", expand=True, padx=40, pady=36)
        left = tk.Frame(wrap, bg=self.BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 16))
        right = tk.Frame(wrap, bg=self.BG)
        right.pack(side="left", fill="both", expand=True, padx=(16, 0))
        self.section_title(left, "Login to your portal",
                           "Registrars manage the system, students handle registration and reviews, and instructors manage grades.")

        info_card, info_body = self.make_card(left, "What happens after login")
        info_card.pack(fill="x", pady=(20, 0))
        for line in [
            "Registrar: approve applications, review complaints, add taboo words.",
            "Student: register for classes, submit reviews, file complaints.",
            "Instructor: assign grades and admit students from the wait-list.",
        ]:
            tk.Label(info_body, text="- " + line, bg=self.CARD, fg=self.TEXT, wraplength=440,
                     justify="left", font=("Segoe UI", 10)).pack(anchor="w", pady=4)

        login_card, login_body = self.make_card(
            right, "Account Login", "Enter one of the demo account credentials")
        login_card.pack(fill="x", pady=(56, 0))
        tk.Label(login_body, text="Username", bg=self.CARD, fg=self.TEXT, font=(
            "Segoe UI", 10, "bold")).pack(anchor="w", pady=(4, 6))
        user_entry = tk.Entry(login_body, width=34,
                              relief="solid", bd=1, font=("Segoe UI", 11))
        user_entry.pack(anchor="w", pady=(0, 12), ipady=6)
        tk.Label(login_body, text="Password", bg=self.CARD, fg=self.TEXT, font=(
            "Segoe UI", 10, "bold")).pack(anchor="w", pady=(4, 6))
        pass_entry = tk.Entry(login_body, width=34, show="*",
                              relief="solid", bd=1, font=("Segoe UI", 11))
        pass_entry.pack(anchor="w", pady=(0, 14), ipady=6)
        tk.Label(login_body, text="Example: registrar / admin123", bg=self.CARD,
                 fg=self.MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 14))

        def login():
            user = self.db.authenticate(
                user_entry.get().strip(), pass_entry.get().strip())
            if not user:
                messagebox.showerror(
                    "Login failed", "Invalid username or password.")
                return
            self.current_user = user
            self.refresh_header_status()
            if user["must_change_password"]:
                self.prompt_password_change(user["id"])
            self.build_dashboard()
            self.show_page("Dashboard", "Dashboard")

        tk.Button(login_body, text="Login", command=login, relief="flat", bg=self.NAV, fg="white",
                  activebackground=self.NAV_LIGHT, activeforeground="white", font=("Segoe UI", 10, "bold"),
                  padx=20, pady=10, cursor="hand2").pack(anchor="w")
        pass_entry.bind("<Return>", lambda e: login())

    def build_dashboard_placeholder(self):
        frame = self.pages["Dashboard"]
        self.clear_frame(frame)
        wrap = tk.Frame(frame, bg=self.BG)
        wrap.pack(fill="both", expand=True, padx=30, pady=30)
        self.section_title(wrap, "Dashboard",
                           "Log in first to access role-based tools.")
        card, body = self.make_card(wrap, "No active session")
        card.pack(fill="x", pady=(24, 0))
        tk.Label(body, text="Use the Login page to enter the system.",
                 bg=self.CARD, fg=self.TEXT, font=("Segoe UI", 11)).pack(anchor="w")

    def refresh_header_status(self):
        if self.current_user:
            text = f"{self.current_user['full_name']} | {self.current_user['role']} | {self.db.get_current_period()}"
        else:
            text = f"Guest mode | {self.db.get_current_period()}"
        self.header_status.config(text=text)

    def prompt_password_change(self, user_id):
        top = tk.Toplevel(self.root)
        top.title("Change Password")
        top.geometry("360x190")
        top.configure(bg=self.BG)
        top.transient(self.root)
        top.grab_set()
        card, body = self.make_card(top, "Change temporary password")
        card.pack(fill="both", expand=True, padx=18, pady=18)
        tk.Label(body, text="New Password", bg=self.CARD, fg=self.TEXT,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        entry = tk.Entry(body, show="*", width=28,
                         relief="solid", bd=1, font=("Segoe UI", 11))
        entry.pack(anchor="w", pady=(6, 14), ipady=5)

        def save_pw():
            pw = entry.get().strip()
            if len(pw) < 4:
                messagebox.showerror(
                    "Invalid", "Password must be at least 4 characters.")
                return
            self.db.change_password(user_id, pw)
            top.destroy()
            messagebox.showinfo("Updated", "Password changed successfully.")

        tk.Button(body, text="Save Password", command=save_pw, relief="flat", bg=self.GOLD, fg=self.NAV,
                  activebackground="#c79310", activeforeground=self.NAV, font=("Segoe UI", 10, "bold"),
                  padx=16, pady=8, cursor="hand2").pack(anchor="w")

    def build_dashboard(self):
        frame = self.pages["Dashboard"]
        self.clear_frame(frame)
        user = self.current_user
        self.refresh_header_status()
        summary = self.db.get_user_summary(user["id"])
        top = tk.Frame(frame, bg=self.BG)
        top.pack(fill="x", padx=24, pady=22)
        subtitle = f"{user['full_name']} | Warnings: {summary['warnings']} | Suspended: {'Yes' if summary['suspended'] else 'No'}"
        if user["role"] == "Student":
            subtitle += f" | GPA: {summary['overall_gpa'] or 0.0}"
        elif user["role"] == "Instructor":
            subtitle += f" | Avg Rating: {round(summary['avg_rating'] or 0.0, 2)}"
        self.section_title(top, f"{user['role']} Dashboard", subtitle)

        quick = tk.Frame(frame, bg=self.BG)
        quick.pack(fill="x", padx=24, pady=(0, 12))
        for title, value, color in [
            ("Warnings", str(summary["warnings"]), self.GOLD),
            ("Status", "Suspended" if summary["suspended"] else "Active",
             self.DANGER if summary["suspended"] else self.SUCCESS),
            ("Period", self.db.get_current_period(), self.NAV),
        ]:
            card, body = self.make_card(quick, title)
            card.pack(side="left", fill="both", expand=True, padx=8)
            tk.Label(body, text=value, bg=self.CARD, fg=color,
                     font=("Segoe UI", 20, "bold")).pack(anchor="w")

        if user["role"] == "Registrar":
            self.build_registrar_dashboard(frame)
        elif user["role"] == "Student":
            self.build_student_dashboard(frame)
        elif user["role"] == "Instructor":
            self.build_instructor_dashboard(frame)

    def build_registrar_dashboard(self, frame):
        row = tk.Frame(frame, bg=self.BG)
        row.pack(fill="both", expand=True, padx=24, pady=8)
        left = tk.Frame(row, bg=self.BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right = tk.Frame(row, bg=self.BG)
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))

        app_card, app_body = self.make_card(
            left, "Applications", "Approve or reject visitor applications")
        app_card.pack(fill="both", expand=True, pady=(0, 12))
        applications = self.db.get_applications()
        app_list = self.styled_listbox(app_body, height=10)
        app_list.pack(fill="both", expand=True)
        for a in applications:
            app_list.insert(
                tk.END, f"#{a['id']}  |  {a['full_name']}  |  {a['role_applied']}  |  GPA {a['gpa']}  |  {a['status']}")
        tk.Label(app_body, text="Justification (required when you override the student GPA/quota rule)", bg=self.CARD, fg=self.TEXT, font=(
            "Segoe UI", 9, "bold")).pack(anchor="w", pady=(10, 4))
        app_justification = tk.Text(
            app_body, height=3, relief="solid", bd=1, font=("Segoe UI", 10))
        app_justification.pack(fill="x")
        app_rule_note = tk.Label(
            app_body, text="", bg=self.CARD, fg=self.MUTED, justify="left", wraplength=420, font=("Segoe UI", 9))
        app_rule_note.pack(anchor="w", pady=(8, 0))
        btn_row = tk.Frame(app_body, bg=self.CARD)
        btn_row.pack(anchor="w", pady=(10, 0))

        def refresh_rule_note(_event=None):
            sel = app_list.curselection()
            if not sel:
                app_rule_note.config(
                    text="Select an application to see the requirement-based recommendation.")
                return
            action, reason = self.db.evaluate_application_rule(
                applications[sel[0]])
            app_rule_note.config(
                text=f"Recommended action: {action}. {reason}")

        app_list.bind("<<ListboxSelect>>", refresh_rule_note)
        refresh_rule_note()

        def approve():
            sel = app_list.curselection()
            if not sel:
                return
            justification = app_justification.get("1.0", tk.END).strip()
            result = self.db.approve_application(
                applications[sel[0]]["id"], justification)
            messagebox.showinfo("Application", result)
            self.build_dashboard()

        def reject():
            sel = app_list.curselection()
            if not sel:
                return
            justification = app_justification.get("1.0", tk.END).strip()
            result = self.db.reject_application(
                applications[sel[0]]["id"], justification)
            messagebox.showinfo("Application", result)
            self.build_dashboard()

        tk.Button(btn_row, text="Approve", command=approve, relief="flat", bg=self.SUCCESS, fg="white",
                  activebackground="#166b3a", activeforeground="white", font=("Segoe UI", 10, "bold"),
                  padx=16, pady=8, cursor="hand2").pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="Reject", command=reject, relief="flat", bg=self.DANGER, fg="white",
                  activebackground="#a73a2f", activeforeground="white", font=("Segoe UI", 10, "bold"),
                  padx=16, pady=8, cursor="hand2").pack(side="left")

        review_card, review_body = self.make_card(
            left, "Reviews", "Moderated student feedback")
        review_card.pack(fill="both", expand=True)
        review_list = self.styled_listbox(review_body, height=12)
        review_list.pack(fill="both", expand=True)
        for r in self.db.get_reviews():
            review_list.insert(
                tk.END, f"{r['code']}  |  {r['student_name']}  |  {r['stars']} stars  |  {'Hidden' if r['hidden'] else 'Visible'}  |  {r['visible_text']}")

        control_card, control_body = self.make_card(
            right, "Semester Controls", "Manage the college period and the student quota from one place")
        control_card.pack(fill="x", pady=(0, 12))
        tk.Label(control_body, text=f"Current Period: {self.db.get_current_period()}", bg=self.CARD, fg=self.TEXT, font=(
            "Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 8))
        tk.Label(control_body, text="Next Period", bg=self.CARD,
                 fg=self.TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        period_var = tk.StringVar(value=self.db.get_current_period())
        ttk.Combobox(control_body, textvariable=period_var, values=[
                     "Setup", "Registration", "Running", "Grading"], state="readonly").pack(fill="x", pady=(4, 10))
        tk.Label(control_body, text="Active Student Quota", bg=self.CARD,
                 fg=self.TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        quota_entry = tk.Entry(control_body, relief="solid",
                               bd=1, font=("Segoe UI", 10))
        quota_entry.insert(0, str(self.db.get_student_quota()))
        quota_entry.pack(fill="x", pady=(4, 10), ipady=4)

        def apply_controls():
            try:
                quota = int(quota_entry.get().strip())
            except ValueError:
                messagebox.showerror(
                    "Invalid quota", "Student quota must be a whole number.")
                return
            self.db.set_setting("student_quota", quota)
            result = self.db.set_current_period(period_var.get())
            messagebox.showinfo("Semester", result)
            self.build_dashboard()

        tk.Button(control_body, text="Apply Controls", command=apply_controls, relief="flat", bg=self.NAV, fg="white",
                  activebackground=self.NAV_LIGHT, activeforeground="white", font=("Segoe UI", 10, "bold"),
                  padx=16, pady=8, cursor="hand2").pack(anchor="w")

        taboo_card, taboo_body = self.make_card(
            right, "Taboo Words", "Configured by the registrar")
        taboo_card.pack(fill="x", pady=(0, 12))
        words_list = self.styled_listbox(taboo_body, height=6)
        words_list.pack(fill="x")
        for word in self.db.get_taboo_words():
            words_list.insert(tk.END, word)
        add_row = tk.Frame(taboo_body, bg=self.CARD)
        add_row.pack(fill="x", pady=(10, 0))
        word_entry = tk.Entry(add_row, relief="solid",
                              bd=1, font=("Segoe UI", 10))
        word_entry.pack(side="left", fill="x", expand=True, ipady=5)

        def add_word():
            if word_entry.get().strip():
                self.db.add_taboo_word(word_entry.get().strip())
                self.build_dashboard()

        tk.Button(add_row, text="Add", command=add_word, relief="flat", bg=self.GOLD, fg=self.NAV,
                  activebackground="#c79310", activeforeground=self.NAV, font=("Segoe UI", 10, "bold"),
                  padx=14, pady=8, cursor="hand2").pack(side="left", padx=(8, 0))

        complaint_card, complaint_body = self.make_card(
            right, "Complaints", "Resolve and assign warnings")
        complaint_card.pack(fill="both", expand=True)
        complaints = self.db.get_complaints()
        complaint_list = self.styled_listbox(complaint_body, height=13)
        complaint_list.pack(fill="both", expand=True)
        for c in complaints:
            complaint_list.insert(
                tk.END, f"#{c['id']}  |  {c['filed_by']} -> {c['against_name']}  |  {c['status']}")
        c_btns = tk.Frame(complaint_body, bg=self.CARD)
        c_btns.pack(anchor="w", pady=(10, 0))

        def warn_accused():
            sel = complaint_list.curselection()
            if not sel:
                return
            self.db.resolve_complaint(complaints[sel[0]]["id"], True)
            self.build_dashboard()

        def warn_filer():
            sel = complaint_list.curselection()
            if not sel:
                return
            self.db.resolve_complaint(complaints[sel[0]]["id"], False)
            self.build_dashboard()

        tk.Button(c_btns, text="Warn Accused", command=warn_accused, relief="flat", bg=self.GOLD, fg=self.NAV,
                  activebackground="#c79310", activeforeground=self.NAV, font=("Segoe UI", 10, "bold"),
                  padx=14, pady=8, cursor="hand2").pack(side="left", padx=(0, 8))
        tk.Button(c_btns, text="Warn Filer", command=warn_filer, relief="flat", bg=self.NAV, fg="white",
                  activebackground=self.NAV_LIGHT, activeforeground="white", font=("Segoe UI", 10, "bold"),
                  padx=14, pady=8, cursor="hand2").pack(side="left")

        setup_card, setup_body = self.make_card(
            frame, "Class Setup", "During the Setup period, the registrar can adjust instructor, meeting time, and capacity.")
        setup_card.pack(fill="x", padx=24, pady=(12, 0))
        setup_row = tk.Frame(setup_body, bg=self.CARD)
        setup_row.pack(fill="x")
        class_setup_rows = self.db.get_class_setup_rows()
        class_setup_list = self.styled_listbox(setup_row, height=6)
        class_setup_list.pack(side="left", fill="both",
                              expand=True, padx=(0, 12))
        for row_data in class_setup_rows:
            class_setup_list.insert(
                tk.END, f"#{row_data['id']} | {row_data['code']} {row_data['title']} | {row_data['meeting_time']} | cap {row_data['capacity']} | {row_data['instructor'] or 'TBD'}")

        setup_form = tk.Frame(setup_row, bg=self.CARD)
        setup_form.pack(side="left", fill="y")
        instructor_rows = self.db.get_users_by_role("Instructor")
        instructor_map = {
            f"{u['full_name']} ({u['username']})": u["id"] for u in instructor_rows}
        tk.Label(setup_form, text="Instructor", bg=self.CARD,
                 fg=self.TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        instructor_var = tk.StringVar()
        instructor_box = ttk.Combobox(
            setup_form, textvariable=instructor_var, values=list(instructor_map.keys()), state="readonly", width=32)
        instructor_box.pack(fill="x", pady=(4, 10))
        tk.Label(setup_form, text="Meeting Time", bg=self.CARD,
                 fg=self.TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        meeting_entry = tk.Entry(
            setup_form, relief="solid", bd=1, font=("Segoe UI", 10))
        meeting_entry.pack(fill="x", pady=(4, 10), ipady=4)
        tk.Label(setup_form, text="Capacity", bg=self.CARD,
                 fg=self.TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        capacity_entry = tk.Entry(
            setup_form, relief="solid", bd=1, font=("Segoe UI", 10))
        capacity_entry.pack(fill="x", pady=(4, 10), ipady=4)

        def load_setup_form(_event=None):
            sel = class_setup_list.curselection()
            if not sel:
                return
            class_row = class_setup_rows[sel[0]]
            meeting_entry.delete(0, tk.END)
            meeting_entry.insert(0, class_row["meeting_time"])
            capacity_entry.delete(0, tk.END)
            capacity_entry.insert(0, str(class_row["capacity"]))
            for label, user_id in instructor_map.items():
                if user_id == class_row["instructor_id"]:
                    instructor_var.set(label)
                    break

        class_setup_list.bind("<<ListboxSelect>>", load_setup_form)

        def save_setup():
            sel = class_setup_list.curselection()
            if not sel:
                return
            target = class_setup_rows[sel[0]]
            try:
                capacity = int(capacity_entry.get().strip())
            except ValueError:
                messagebox.showerror("Invalid capacity",
                                     "Capacity must be a whole number.")
                return
            instructor_id = instructor_map.get(instructor_var.get())
            if not instructor_id:
                messagebox.showerror("Missing instructor",
                                     "Please choose an instructor.")
                return
            result = self.db.update_class_setup(
                target["id"], instructor_id, meeting_entry.get().strip(), capacity)
            messagebox.showinfo("Class Setup", result)
            self.build_dashboard()

        tk.Button(setup_form, text="Save Class Setup", command=save_setup, relief="flat", bg=self.GOLD, fg=self.NAV,
                  activebackground="#c79310", activeforeground=self.NAV, font=("Segoe UI", 10, "bold"),
                  padx=16, pady=8, cursor="hand2").pack(anchor="w", pady=(4, 0))
        
        grad_card, grad_body = self.make_card(
            frame,
            "Graduation Applications",
            "Review student graduation requests."
        )
        grad_card.pack(fill="x", padx=24, pady=(12, 0))
        
        grad_apps = self.db.get_graduation_applications()
        grad_list = self.styled_listbox(grad_body, height=6)
        grad_list.pack(fill="x")
        
        for g in grad_apps:
            grad_list.insert(
                tk.END,
                f"#{g['id']} | {g['full_name']} ({g['username']}) | {g['status']} | {g['decision_note']}"
            )
            
        note_box = tk.Text(grad_body, height=3, relief="solid", bd=1, font=("Segoe UI", 10))
        note_box.pack(fill="x", pady=(10, 0))

        def approve_grad():
            sel = grad_list.curselection()
            if not sel:
                return
            msg = self.db.decide_graduation(
                grad_apps[sel[0]]["id"],
                True,
                note_box.get("1.0", tk.END)
            )
            messagebox.showinfo("Graduation", msg)
            self.build_dashboard()
            
        def reject_grad():
            sel = grad_list.curselection()
            if not sel:
                return
            msg = self.db.decide_graduation(
                grad_apps[sel[0]]["id"],
                False,
                note_box.get("1.0", tk.END)
            )
            messagebox.showinfo("Graduation", msg)
            self.build_dashboard()

        btns = tk.Frame(grad_body, bg=self.CARD)
        btns.pack(anchor="w", pady=(10, 0))

        tk.Button(btns, text="Approve Graduation", command=approve_grad, bg=self.SUCCESS, fg="white",
                  relief="flat", padx=14, pady=8, font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 8))

        tk.Button(btns, text="Reject Graduation", command=reject_grad, bg=self.DANGER, fg="white",
                  relief="flat", padx=14, pady=8, font=("Segoe UI", 10, "bold")).pack(side="left")
        
        ai_card = self.build_ai_panel(
            frame, self.current_user, "Registrar AI Assistant")
        ai_card.pack(fill="both", expand=False, padx=24, pady=(12, 0))

    def build_student_dashboard(self, frame):
        row = tk.Frame(frame, bg=self.BG)
        row.pack(fill="both", expand=True, padx=24, pady=8)
        tip_card, tip_body = self.make_card(
            row, "Student Tutorial", "New students should start here: keep 2-4 courses, watch period changes, and submit reviews before grades are posted.")
        tip_card.pack(fill="x", pady=(0, 14))
        tk.Label(tip_body, text="1. Register only during Registration or Special Registration.\n2. Keep at least 2 courses to avoid a warning.\n3. Reviews are only allowed while you are in the class and before the grade is posted.\n4. Warnings of 3 or more can suspend your account.",
                 bg=self.CARD, fg=self.TEXT, justify="left", font=("Segoe UI", 10)).pack(anchor="w")

        top = tk.Frame(row, bg=self.BG)
        top.pack(fill="x")

        class_card, class_body = self.make_card(
            top, "Available Classes", "Register or join the wait-list")
        class_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        my_card, my_body = self.make_card(
            top, "My Classes", "Current registrations and grades")
        my_card.pack(side="left", fill="both", expand=True, padx=(10, 0))

        classes = self.db.get_available_classes()
        class_list = self.styled_listbox(class_body, height=11)
        class_list.pack(fill="both", expand=True)
        for c in classes:
            class_list.insert(
                tk.END, f"#{c['id']}  |  {c['code']} {c['title']}  |  {c['meeting_time']}  |  {c['enrolled']}/{c['capacity']}  |  {c['period_state']}")
            
        def apply_grad():
            msg = self.db.apply_for_graduation(self.current_user["id"])
            messagebox.showinfo("Graduation", msg)
            self.build_dashboard()

        tk.Button(
            my_body,
            text="Apply for Graduation",
            command=apply_grad,
            relief="flat",
            bg=self.GOLD,
            fg=self.NAV,
            font=("Segoe UI", 10, "bold"),
            padx=16,
            pady=8,
            cursor="hand2"
        ).pack(anchor="w", pady=(10, 0))

        def register():
            sel = class_list.curselection()
            if not sel:
                return
            msg = self.db.register_student(
                self.current_user["id"], classes[sel[0]]["id"])
            messagebox.showinfo("Registration", msg)
            self.build_dashboard()

        tk.Button(class_body, text="Register / Join Wait-list", command=register, relief="flat", bg=self.NAV, fg="white",
                  activebackground=self.NAV_LIGHT, activeforeground="white", font=("Segoe UI", 10, "bold"),
                  padx=16, pady=8, cursor="hand2").pack(anchor="w", pady=(10, 0))

        reg_list = self.styled_listbox(my_body, height=11)
        reg_list.pack(fill="both", expand=True)
        for r in self.db.get_student_registrations(self.current_user["id"]):
            reg_list.insert(
                tk.END, f"#{r['class_id']}  |  {r['code']} {r['title']}  |  {r['meeting_time']}  |  Grade: {r['grade'] or 'N/A'}")

        bottom = tk.Frame(row, bg=self.BG)
        bottom.pack(fill="both", expand=True, pady=(16, 0))
        review_card, review_body = self.make_card(
            bottom, "Submit Review", "Enter a class ID and add feedback")
        review_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        complaint_card, complaint_body = self.make_card(
            bottom, "File Complaint", "Report a student or instructor")
        complaint_card.pack(side="left", fill="both",
                            expand=True, padx=(10, 0))

        form = tk.Frame(review_body, bg=self.CARD)
        form.pack(fill="x")
        tk.Label(form, text="Class ID", bg=self.CARD, fg=self.TEXT, font=(
            "Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", padx=6, pady=6)
        review_class_id = tk.Entry(
            form, width=10, relief="solid", bd=1, font=("Segoe UI", 10))
        review_class_id.grid(row=1, column=0, padx=6, pady=(0, 10), sticky="w")
        tk.Label(form, text="Stars", bg=self.CARD, fg=self.TEXT, font=(
            "Segoe UI", 10, "bold")).grid(row=0, column=1, sticky="w", padx=6, pady=6)
        stars_var = tk.StringVar(value="5")
        ttk.Combobox(form, textvariable=stars_var, values=["1", "2", "3", "4", "5"], width=10, state="readonly").grid(
            row=1, column=1, padx=6, pady=(0, 10), sticky="w")
        tk.Label(form, text="Review Text", bg=self.CARD, fg=self.TEXT, font=(
            "Segoe UI", 10, "bold")).grid(row=2, column=0, columnspan=2, sticky="w", padx=6, pady=6)
        review_text = tk.Text(form, width=52, height=8,
                              relief="solid", bd=1, font=("Segoe UI", 10))
        review_text.grid(row=3, column=0, columnspan=2,
                         padx=6, pady=(0, 10), sticky="we")

        def submit_review():
            try:
                class_id = int(review_class_id.get().strip())
                stars = int(stars_var.get())
            except ValueError:
                messagebox.showerror(
                    "Invalid", "Enter a valid class ID and stars.")
                return
            msg = self.db.submit_review(
                class_id, self.current_user["id"], stars, review_text.get("1.0", tk.END).strip())
            messagebox.showinfo("Review", msg)
            self.build_dashboard()

        tk.Button(form, text="Submit Review", command=submit_review, relief="flat", bg=self.GOLD, fg=self.NAV,
                  activebackground="#c79310", activeforeground=self.NAV, font=("Segoe UI", 10, "bold"),
                  padx=16, pady=8, cursor="hand2").grid(row=4, column=0, columnspan=2, sticky="w", padx=6)

        tk.Label(complaint_body, text="Against User", bg=self.CARD, fg=self.TEXT, font=(
            "Segoe UI", 10, "bold")).pack(anchor="w", pady=(4, 6))
        possible_targets = self.db.get_users_by_role(
            "Student") + self.db.get_users_by_role("Instructor")
        target_map = {f"{u['full_name']} ({u['username']})": u["id"]
                      for u in possible_targets if u["id"] != self.current_user["id"]}
        target_var = tk.StringVar()
        ttk.Combobox(complaint_body, textvariable=target_var, values=list(
            target_map.keys()), width=42, state="readonly").pack(anchor="w", fill="x")
        tk.Label(complaint_body, text="Complaint Detail", bg=self.CARD, fg=self.TEXT, font=(
            "Segoe UI", 10, "bold")).pack(anchor="w", pady=(12, 6))
        complaint_text = tk.Text(
            complaint_body, width=46, height=8, relief="solid", bd=1, font=("Segoe UI", 10))
        complaint_text.pack(fill="x")

        def file_complaint():
            target = target_var.get()
            detail = complaint_text.get("1.0", tk.END).strip()
            if not target or not detail:
                messagebox.showerror(
                    "Missing info", "Choose a user and enter complaint details.")
                return
            self.db.file_complaint(
                self.current_user["id"], target_map[target], detail)
            messagebox.showinfo("Complaint", "Complaint submitted.")
            self.build_dashboard()

        tk.Button(complaint_body, text="Submit Complaint", command=file_complaint, relief="flat", bg=self.NAV, fg="white",
                  activebackground=self.NAV_LIGHT, activeforeground="white", font=("Segoe UI", 10, "bold"),
                  padx=16, pady=8, cursor="hand2").pack(anchor="w", pady=(12, 0))
        ai_card = self.build_ai_panel(
            frame, self.current_user, "Student AI Assistant")
        ai_card.pack(fill="both", expand=False, padx=24, pady=(12, 0))

    def build_instructor_dashboard(self, frame):
        row = tk.Frame(frame, bg=self.BG)
        row.pack(fill="both", expand=True, padx=24, pady=8)
        top_card, top_body = self.make_card(
            row, "My Assigned Classes", "Select a class to manage students and the wait-list")
        top_card.pack(fill="x", pady=(0, 14))
        classes = self.db.get_instructor_classes(self.current_user["id"])
        class_list = self.styled_listbox(top_body, height=6)
        class_list.pack(fill="x")
        for c in classes:
            class_list.insert(
                tk.END, f"#{c['id']}  |  {c['code']} {c['title']}  |  {c['meeting_time']}")

        bottom = tk.Frame(row, bg=self.BG)
        bottom.pack(fill="both", expand=True)
        student_card, student_body = self.make_card(
            bottom, "Students / Grades", "Assign course grades")
        student_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        wait_card, wait_body = self.make_card(
            bottom, "Wait-list", "Admit students if seats are available")
        wait_card.pack(side="left", fill="both", expand=True, padx=(10, 0))

        students_list = self.styled_listbox(student_body, height=12)
        students_list.pack(fill="both", expand=True)
        wait_list = self.styled_listbox(wait_body, height=12)
        wait_list.pack(fill="both", expand=True)

        grade_row = tk.Frame(student_body, bg=self.CARD)
        grade_row.pack(anchor="w", pady=(10, 0))
        tk.Label(grade_row, text="Grade", bg=self.CARD, fg=self.TEXT,
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 8))
        grade_var = tk.StringVar(value="A")
        ttk.Combobox(grade_row, textvariable=grade_var, values=[
                     "A", "A-", "B+", "B", "B-", "C+", "C", "D", "F"], width=10, state="readonly").pack(side="left")

        current_students = []
        current_waiters = []

        def load_class_data(_event=None):
            nonlocal current_students, current_waiters
            students_list.delete(0, tk.END)
            wait_list.delete(0, tk.END)
            sel = class_list.curselection()
            if not sel:
                return
            class_id = classes[sel[0]]["id"]
            current_students = self.db.get_students_in_class(class_id)
            current_waiters = self.db.get_waitlist(class_id)
            for s in current_students:
                students_list.insert(
                    tk.END, f"{s['full_name']} ({s['username']})  |  GPA: {s['overall_gpa'] or 0.0}  |  Warnings: {s['warnings']}  |  Honor Roll: {'Yes' if s['honor_roll'] else 'No'}  |  Grade: {s['grade'] or 'N/A'}")
            for w in current_waiters:
                wait_list.insert(tk.END, f"{w['full_name']}")

        def assign_grade():
            sel = students_list.curselection()
            if not sel:
                return
            msg = self.db.assign_grade(
                current_students[sel[0]]["id"], grade_var.get())
            messagebox.showinfo("Grade", msg)
            load_class_data()

        def admit_waiter():
            sel_class = class_list.curselection()
            sel_wait = wait_list.curselection()
            if not sel_class or not sel_wait:
                return
            msg = self.db.admit_waitlisted_student(
                current_waiters[sel_wait[0]]["id"], classes[sel_class[0]]["id"])
            messagebox.showinfo("Wait-list", msg)
            load_class_data()

        tk.Button(student_body, text="Assign Grade", command=assign_grade, relief="flat", bg=self.GOLD, fg=self.NAV,
                  activebackground="#c79310", activeforeground=self.NAV, font=("Segoe UI", 10, "bold"),
                  padx=16, pady=8, cursor="hand2").pack(anchor="w", pady=(10, 0))
        tk.Button(wait_body, text="Admit Selected Student", command=admit_waiter, relief="flat", bg=self.NAV, fg="white",
                  activebackground=self.NAV_LIGHT, activeforeground="white", font=("Segoe UI", 10, "bold"),
                  padx=16, pady=8, cursor="hand2").pack(anchor="w", pady=(10, 0))

        extra = tk.Frame(row, bg=self.BG)
        extra.pack(fill="both", expand=True, pady=(14, 0))
        complaint_card, complaint_body = self.make_card(
            extra, "Instructor Complaint", "Report a student in your class to the registrar.")
        complaint_card.pack(side="left", fill="both",
                            expand=True, padx=(0, 10))
        ai_card = self.build_ai_panel(
            extra, self.current_user, "Instructor AI Assistant")
        ai_card.pack(side="left", fill="both", expand=True, padx=(10, 0))

        tk.Label(complaint_body, text="Student in Selected Class", bg=self.CARD,
                 fg=self.TEXT, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(4, 6))
        complaint_target_var = tk.StringVar()
        complaint_target_box = ttk.Combobox(
            complaint_body, textvariable=complaint_target_var, values=[], state="readonly")
        complaint_target_box.pack(fill="x")
        tk.Label(complaint_body, text="Complaint Detail", bg=self.CARD, fg=self.TEXT, font=(
            "Segoe UI", 10, "bold")).pack(anchor="w", pady=(12, 6))
        instructor_complaint_text = tk.Text(
            complaint_body, height=6, relief="solid", bd=1, font=("Segoe UI", 10))
        instructor_complaint_text.pack(fill="both", expand=True)

        def refresh_complaint_targets(_event=None):
            values = [
                f"{s['full_name']} ({s['username']})" for s in current_students]
            complaint_target_box["values"] = values
            if values:
                complaint_target_var.set(values[0])
            else:
                complaint_target_var.set("")

        class_list.bind("<<ListboxSelect>>", lambda event: (
            load_class_data(event), refresh_complaint_targets(event)))

        def file_instructor_complaint():
            target_text = complaint_target_var.get()
            detail = instructor_complaint_text.get("1.0", tk.END).strip()
            if not target_text or not detail:
                messagebox.showerror(
                    "Missing info", "Select a class, choose a student, and enter complaint details.")
                return
            target = next(
                (s for s in current_students if f"{s['full_name']} ({s['username']})" == target_text),
                None,
            )
            if not target:
                messagebox.showerror(
                    "Missing student", "Please choose a student from the selected class.")
                return
            self.db.file_complaint(
                self.current_user["id"], target["student_id"], detail)
            messagebox.showinfo(
                "Complaint", "Complaint submitted to the registrar.")
            self.build_dashboard()

        tk.Button(complaint_body, text="Submit Complaint", command=file_instructor_complaint, relief="flat", bg=self.NAV, fg="white",
                  activebackground=self.NAV_LIGHT, activeforeground="white", font=("Segoe UI", 10, "bold"),
                  padx=16, pady=8, cursor="hand2").pack(anchor="w", pady=(12, 0))


if __name__ == "__main__":
    root = tk.Tk()
    app = College0App(root)
    root.mainloop()
