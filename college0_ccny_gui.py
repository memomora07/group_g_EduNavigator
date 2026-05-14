
# College0 local Tkinter application.
# Run with: python college0_ccny_gui.py

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import re

DB_NAME = "college0.db"


class College0DB:
    AI_ALIASES = {
        "graduate": "graduation",
        "graduates": "graduation",
        "finish": "graduation",
        "degree": "graduation",
        "warning": "warnings",
        "warn": "warnings",
        "warned": "warnings",
        "suspend": "suspension",
        "suspended": "suspension",
        "ban": "suspension",
        "register": "registration",
        "registered": "registration",
        "enroll": "registration",
        "enrolled": "registration",
        "course": "classes",
        "class": "classes",
        "professor": "instructor",
        "teacher": "instructor",
        "ratings": "rating",
        "reviews": "review",
        "complaints": "complaint",
        "complain": "complaint",
        "taboos": "taboo",
        "banned": "taboo",
        "honours": "honor",
        "semester": "period",
        "term": "period",
    }
    AI_STOP_WORDS = {
        "about", "after", "am", "and", "are", "before", "can", "do",
        "does", "for", "from", "help", "how", "in", "into", "is", "just",
        "like", "need", "now", "of", "on", "please", "right", "show",
        "tell", "that", "the", "them", "they", "this", "was", "were",
        "what", "when", "where", "which", "who", "with", "work", "works",
        "would", "your",
    }

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
            suspended INTEGER DEFAULT 0,
            graduated INTEGER DEFAULT 0
        )
        """)
        # Migration: add `graduated` column for legacy databases that
        # were created before this column existed. SQLite doesn't support
        # ADD COLUMN IF NOT EXISTS, so guard the ALTER.
        try:
            cur.execute("ALTER TABLE users ADD COLUMN graduated INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
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
            status TEXT DEFAULT 'Open',
            complaint_type TEXT DEFAULT 'General Complaint',
            class_id INTEGER,
            FOREIGN KEY(class_id) REFERENCES classes(id)
        )
        """)
        try:
            cur.execute("ALTER TABLE complaints ADD COLUMN complaint_type TEXT DEFAULT 'General Complaint'")
        except sqlite3.OperationalError:
            pass
        try:
            cur.execute("ALTER TABLE complaints ADD COLUMN class_id INTEGER")
        except sqlite3.OperationalError:
            pass
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
        CREATE TABLE IF NOT EXISTS instructor_grade_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER NOT NULL,
            instructor_id INTEGER NOT NULL,
            class_gpa REAL NOT NULL,
            concern TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            justification TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            UNIQUE(class_id, concern, status),
            FOREIGN KEY(class_id) REFERENCES classes(id),
            FOREIGN KEY(instructor_id) REFERENCES users(id)
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
        cur.execute("""
        CREATE TABLE IF NOT EXISTS fines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        reason TEXT NOT NULL,
        paid INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )   
    """)
        self.conn.commit()

    def seed_data(self):
        cur = self.conn.cursor()
        default_semester = "Spring 2026"

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

        def ensure_class(course_code, instructor_id, meeting_time, capacity):
            cur.execute("SELECT id FROM courses WHERE code=?", (course_code,))
            course_row = cur.fetchone()
            if not course_row:
                return
            course_id = course_row["id"]
            cur.execute("""
                SELECT id
                FROM classes
                WHERE course_id=? AND semester=? AND meeting_time=?
            """, (course_id, default_semester, meeting_time))
            if cur.fetchone():
                return
            cur.execute("""
                INSERT INTO classes(course_id, instructor_id, semester, period_state, meeting_time, capacity)
                VALUES (?, ?, ?, 'Registration', ?, ?)
            """, (course_id, instructor_id, default_semester, meeting_time, capacity))

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
            ("CS210", "Computer Architecture", 0),
            ("CS220", "Web Development", 0),
            ("CS230", "Cybersecurity Basics", 0),
            ("CS240", "Mobile App Design", 0),
            ("CS250", "Machine Learning Foundations", 0),
            ("MATH101", "Discrete Math", 1),
            ("MATH201", "Linear Algebra", 0),
            ("STAT201", "Applied Statistics", 0),
            ("ENG101", "Academic Writing", 1),
            ("HIST110", "World History", 0),
            ("ART105", "Art Appreciation", 0),
        ]
        for code, title, req in courses:
            cur.execute(
                "INSERT OR IGNORE INTO courses(code, title, required) VALUES (?, ?, ?)", (code, title, req))

        class_specs = [
            ("CS101", instructor1, "Mon 10:00-12:00", 3),
            ("CS102", instructor1, "Fri 10:00-12:00", 3),
            ("CS201", instructor2, "Wed 14:00-16:00", 2),
            ("CS205", instructor3, "Tue 09:00-11:00", 2),
            ("CS210", instructor2, "Tue 13:00-15:00", 3),
            ("CS220", instructor1, "Thu 09:00-11:00", 3),
            ("CS230", instructor3, "Fri 13:00-15:00", 3),
            ("CS240", instructor1, "Wed 09:00-11:00", 2),
            ("CS250", instructor3, "Mon 14:00-16:00", 2),
            ("MATH101", instructor2, "Thu 12:00-14:00", 3),
            ("MATH201", instructor2, "Tue 15:30-17:30", 3),
            ("STAT201", instructor2, "Wed 16:00-18:00", 3),
            ("ENG101", instructor1, "Mon 08:00-10:00", 3),
            ("HIST110", instructor3, "Thu 15:00-17:00", 3),
            ("ART105", instructor3, "Fri 09:00-11:00", 3),
        ]
        for course_code, inst, meeting, cap in class_specs:
            ensure_class(course_code, inst, meeting, cap)

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
        if row["warnings"] >= 3 and not suspended:
            suspended = 1
            self.issue_fine(
                user_id,
                500,
                "Automatic fine: 3 warnings reached = suspension"
            )

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

    def issue_fine(self, user_id, amount, reason):

        self.conn.execute("""
            INSERT INTO fines(user_id, amount, reason, created_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, amount, reason, datetime.now().isoformat()))
        self.conn.commit()

    def pay_fine(self, user_id):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT role, warnings, suspended
            FROM users
            WHERE id = ?
        """, (user_id,))
        user_row = cur.fetchone()
        if not user_row:
            return "User not found."

        cur.execute("""
            UPDATE fines
            SET paid = 1
            WHERE user_id = ? AND paid = 0
        """, (user_id,))
        paid_count = cur.rowcount

        cur.execute("""
            SELECT COUNT(*) AS cnt
            FROM fines
            WHERE user_id = ? AND reason = ? AND paid = 1
        """, (user_id, "Automatic fine: 3 warnings reached = suspension"))
        has_paid_suspension_fine = cur.fetchone()["cnt"] > 0

        restored_status = False
        if user_row["role"] == "Student" and has_paid_suspension_fine and (
            user_row["suspended"] or user_row["warnings"] >= 3
        ):
            self.conn.execute("""
            UPDATE users
            SET suspended = 0,
                warnings = CASE WHEN warnings >= 3 THEN 2 ELSE warnings END
            WHERE id = ?
        """, (user_id,))
            restored_status = True

        self.conn.commit()
        if paid_count > 0 and restored_status:
            return "Fine paid successfully. Student status restored to active."
        if paid_count > 0:
            return "Fine paid successfully."
        if restored_status:
            return "Paid suspension fine found. Student status restored to active."
        return "No unpaid fines found."

    def get_user_fines(self, user_id):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, amount, reason, paid, created_at
            FROM fines
            WHERE user_id=?
            ORDER BY paid ASC, id DESC
        """, (user_id,))
        return cur.fetchall()

    def get_all_fines(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT f.id, f.amount, f.reason, f.paid, f.created_at,
                   u.full_name, u.username
            FROM fines f
            JOIN users u ON u.id = f.user_id
            ORDER BY f.paid ASC, f.id DESC
        """)
        return cur.fetchall()

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

        # When the system enters Special Registration, give students the
        # widest possible set of options by reopening any cancelled classes.
        # Instructor warnings / suspensions from the audit are NOT rolled
        # back — only the class availability is restored so affected
        # students can pick those classes again.
        reopened_count = 0
        if requested_period == "Special Registration":
            cur = self.conn.cursor()
            cur.execute("SELECT COUNT(*) AS c FROM classes WHERE cancelled=1")
            reopened_count = cur.fetchone()["c"]
            if reopened_count:
                self.conn.execute("UPDATE classes SET cancelled=0 WHERE cancelled=1")
                message_parts.append(
                    f"{reopened_count} previously cancelled class(es) were reopened for the Special Registration window."
                )

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
               cl.cancelled,
               u.full_name AS instructor
        FROM classes cl
        JOIN courses c ON c.id = cl.course_id
        LEFT JOIN users u ON u.id = cl.instructor_id
        ORDER BY cl.cancelled, c.code
        """)
        return cur.fetchall()

    def reactivate_class(self, class_id):
        """Bring a cancelled class back online. Only the registrar may do
        this, and only during the Setup period — that's when the class
        catalog is being prepared for a fresh semester."""
        if self.get_current_period() != "Setup":
            return "Classes can only be reactivated during the Setup period."
        cur = self.conn.cursor()
        cur.execute("SELECT cancelled FROM classes WHERE id=?", (class_id,))
        row = cur.fetchone()
        if not row:
            return "Class not found."
        if not row["cancelled"]:
            return "That class is already active."
        self.conn.execute(
            "UPDATE classes SET cancelled=0, period_state='Setup' WHERE id=?",
            (class_id,),
        )
        self.conn.commit()
        return "Class reactivated and ready for registration."

    def update_class_setup(self, class_id, instructor_id, meeting_time, capacity):
        if self.get_current_period() != "Setup":
            return "Class setup is only editable during the Setup period."
        if not meeting_time.strip():
            return "Meeting time cannot be empty."
        if capacity <= 0:
            return "Capacity must be greater than 0."
        self.conn.execute(
            "UPDATE classes SET instructor_id=?, meeting_time=?, capacity=?, period_state='Setup' WHERE id=?",
            (instructor_id, meeting_time.strip(), capacity, class_id),
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

    def get_student_degree_audit(self, student_id):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT code, title
            FROM courses
            WHERE required = 1
            ORDER BY code
        """)
        required_courses = [dict(row) for row in cur.fetchall()]

        cur.execute("""
            SELECT cl.id AS class_id, c.code, c.title, cl.meeting_time, r.grade
            FROM registrations r
            JOIN classes cl ON cl.id = r.class_id
            JOIN courses c ON c.id = cl.course_id
            WHERE r.student_id = ?
            ORDER BY c.code
        """, (student_id,))
        rows = [dict(row) for row in cur.fetchall()]

        required_progress = []
        for course in required_courses:
            matching = [row for row in rows if row["code"] == course["code"]]
            passed = any((row["grade"] or "").upper() not in {"", "F"} for row in matching)
            in_progress = any(not row["grade"] for row in matching)
            failed = any((row["grade"] or "").upper() == "F" for row in matching)
            if passed:
                status = "Completed"
            elif in_progress:
                status = "In Progress"
            elif failed:
                status = "Needs Retake"
            else:
                status = "Missing"
            required_progress.append(
                {"code": course["code"], "title": course["title"], "status": status}
            )

        return {
            "required_courses": required_progress,
            "graded_rows": [row for row in rows if row["grade"]],
            "active_rows": [row for row in rows if not row["grade"]],
            "completed_count": sum(1 for row in rows if row["grade"] != ""),
        }

    def get_student_registration_count(self, student_id):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM registrations WHERE student_id=?",
            (student_id,),
        )
        return cur.fetchone()["cnt"]

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
        # Spec: "A student can retake the same class if s/he got an F before."
        # If a prior F record exists for the same (class_id, student_id), clear
        # it so the UNIQUE constraint does not block a legitimate retake.
        cur.execute(
            "SELECT id, grade FROM registrations WHERE class_id=? AND student_id=?",
            (class_id, student_id),
        )
        existing = cur.fetchone()
        retake_note = ""
        if existing and existing["grade"] == "F":
            cur.execute("DELETE FROM registrations WHERE id=?", (existing["id"],))
            retake_note = " (Retake of a previously failed class.)"
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
            total_registrations = self.get_student_registration_count(student_id)
            if total_registrations == 1:
                return "Registration successful." + retake_note + " Alert: students should stay enrolled in at least 2 classes."
            return "Registration successful." + retake_note
        except sqlite3.IntegrityError:
            return "Already registered for this class."

    def unenroll_student(self, student_id, class_id):
        cur = self.conn.cursor()
        current_period = self.get_current_period()
        if current_period not in {"Registration", "Special Registration"}:
            return "Unenrollment is only allowed during the Registration or Special Registration period."

        cur.execute(
            "SELECT id, grade FROM registrations WHERE student_id=? AND class_id=?",
            (student_id, class_id),
        )
        registration = cur.fetchone()
        if not registration:
            return "You are not enrolled in that class."
        if registration["grade"]:
            return "You cannot unenroll after a grade has been posted."

        cur.execute("DELETE FROM registrations WHERE id=?", (registration["id"],))

        # Per spec ("wait-list that only the course instructor can let in"),
        # do NOT auto-admit the next wait-listed student here. The instructor
        # must explicitly admit a wait-listed student via the dashboard.
        waitlist_note = ""
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM waitlist WHERE class_id=?",
            (class_id,),
        )
        waiting = cur.fetchone()["cnt"]
        if waiting:
            waitlist_note = f" A seat is now open; {waiting} student(s) are waiting and the instructor can admit one."

        self.conn.commit()
        total_registrations = self.get_student_registration_count(student_id)
        alert_note = ""
        if total_registrations == 1:
            alert_note = " Alert: students should stay enrolled in at least 2 classes."
        return "Unenrolled successfully." + waitlist_note + alert_note

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
        """Instructor admits a wait-listed student. Per spec, the instructor
        is the only path off the wait-list, and this is an explicit override:
        the instructor may admit even when the class is already at capacity
        (the class total increases accordingly)."""
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
        enrolled = cur.fetchone()["cnt"]
        try:
            cur.execute(
                "INSERT INTO registrations(class_id, student_id) VALUES (?, ?)",
                (class_id, row["student_id"]),
            )
        except sqlite3.IntegrityError:
            return "That student is already enrolled in the class."
        cur.execute("DELETE FROM waitlist WHERE id=?", (wait_id,))
        self.conn.commit()
        new_total = enrolled + 1
        if enrolled >= capacity:
            return (
                f"Wait-listed student admitted via instructor override. "
                f"Class is now over capacity ({new_total}/{capacity})."
            )
        return f"Wait-listed student admitted. Class is now {new_total}/{capacity}."

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
            if warning_count == 1:
                return "Review submitted. Alert: taboo words were detected and you received 1 warning."
            if warning_count == 2:
                return "Review submitted. Alert: repeated taboo words were detected, your review was hidden, and you received 2 warnings."
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

    def file_complaint(self, filed_by, against_user, detail, complaint_type="General Complaint", class_id=None):
        self.conn.execute("""
            INSERT INTO complaints(filed_by, against_user, detail, complaint_type, class_id)
            VALUES (?, ?, ?, ?, ?)
        """, (filed_by, against_user, detail, complaint_type, class_id))
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
            self.issue_warning(
                student_id, "reckless_graduation_application", 1)
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

        cur.execute(
            "SELECT student_id FROM graduation_applications WHERE id=?", (grad_id,))
        row = cur.fetchone()
        if not row:
            return "Graduation application not found."

        self.conn.execute("""
            UPDATE graduation_applications
            SET status=?, decision_note=?
            WHERE id=?
        """, (status, final_note, grad_id))

        if approve:
            # Spec: graduating student "leaves the system with a Bachelor's
            # degree." Mark as graduated (and inactive) rather than suspended,
            # because suspension implies disciplinary action.
            self.conn.execute(
                "UPDATE users SET graduated=1, suspended=1 WHERE id=?",
                (row["student_id"],)
            )

        self.conn.commit()
        if approve:
            return "Graduation approved. The student has graduated with a Bachelor's degree."
        return f"Graduation application {status.lower()}."

    def get_users_by_role(self, role):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, full_name, username FROM users WHERE role=? ORDER BY full_name", (role,))
        return cur.fetchall()

    def get_complaints(self):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT c.id, c.filed_by, c.against_user,
               uf.full_name AS filed_by, uf.role AS filed_by_role,
               ua.full_name AS against_name, ua.role AS against_role,
               c.detail, c.status, c.complaint_type, c.class_id,
               co.code AS class_code, co.title AS class_title
        FROM complaints c
        JOIN users uf ON uf.id = c.filed_by
        JOIN users ua ON ua.id = c.against_user
        LEFT JOIN classes cl ON cl.id = c.class_id
        LEFT JOIN courses co ON co.id = cl.course_id
        ORDER BY c.id DESC
        """)
        return cur.fetchall()

    def deregister_student_by_registrar(self, student_id, class_id):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT r.id, c.code, c.title
            FROM registrations r
            JOIN classes cl ON cl.id = r.class_id
            JOIN courses c ON c.id = cl.course_id
            WHERE r.student_id=? AND r.class_id=?
        """, (student_id, class_id))
        row = cur.fetchone()
        if not row:
            return "The student is not currently registered in that class."
        self.conn.execute("DELETE FROM registrations WHERE id=?", (row["id"],))
        self.conn.commit()
        return f"Student was de-registered from {row['code']} {row['title']}."

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

    def decide_complaint(self, complaint_id, action):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM complaints WHERE id=?", (complaint_id,))
        row = cur.fetchone()
        if not row:
            return "Complaint not found."
        if row["status"] != "Open":
            return "Complaint is already resolved."

        if action == "warn_accused":
            self.issue_warning(
                row["against_user"], f"complaint_against_{complaint_id}", 1
            )
            status = "Resolved - warning issued to accused"
        elif action == "warn_filer":
            self.issue_warning(
                row["filed_by"], f"complaint_filer_{complaint_id}", 1
            )
            status = "Resolved - warning issued to filer"
        elif action == "deregister_student":
            if row["complaint_type"] != "Instructor Report" or not row["class_id"]:
                return "Only instructor reports tied to a class can de-register a student."
            result = self.deregister_student_by_registrar(
                row["against_user"], row["class_id"]
            )
            if not result.startswith("Student was de-registered"):
                return result
            status = "Resolved - student de-registered"
        else:
            return "Unknown complaint action."

        self.conn.execute(
            "UPDATE complaints SET status=? WHERE id=?", (status, complaint_id)
        )
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
        review_count = self.audit_instructor_class_performance()
        if review_count:
            messages.append(
                f"{review_count} instructor class GPA case(s) were sent to the registrar for review."
            )
        return " ".join(messages[:4])

    def audit_instructor_class_performance(self):
        cur = self.conn.cursor()
        queued_reviews = 0

        cur.execute("""
            SELECT cl.id AS class_id, cl.instructor_id, c.code
            FROM classes cl
            JOIN courses c ON c.id = cl.course_id
            WHERE cl.cancelled = 0
        """)

        for row in cur.fetchall():
            class_id = row["class_id"]
            instructor_id = row["instructor_id"]

            cur.execute("""
                SELECT r.grade
                FROM registrations r
                Where r.class_id = ? AND r.grade <> ''
            """, (class_id,))

            grades = cur.fetchall()
            points = {"A": 4.0, "A-": 3.7, "B+": 3.3, "B": 3.0,
                      "B-": 2.7, "C+": 2.3, "C": 2.0, "D": 1.0, "F": 0.0}

            values = [points[g["grade"]]
                      for g in grades if g["grade"] in points]

            if not values:
                continue

            class_gpa = round(sum(values) / len(values), 2)

            if class_gpa > 3.5:
                queued_reviews += self.queue_instructor_grade_review(
                    class_id, instructor_id, class_gpa, "High class GPA"
                )
            elif class_gpa < 2.5:
                queued_reviews += self.queue_instructor_grade_review(
                    class_id, instructor_id, class_gpa, "Low class GPA"
                )

        self.conn.commit()
        return queued_reviews

    def queue_instructor_grade_review(self, class_id, instructor_id, class_gpa, concern):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id
            FROM instructor_grade_reviews
            WHERE class_id=? AND concern=? AND status='Pending'
        """, (class_id, concern))
        if cur.fetchone():
            return 0
        self.conn.execute("""
            INSERT INTO instructor_grade_reviews(
                class_id, instructor_id, class_gpa, concern, status, justification, created_at
            )
            VALUES (?, ?, ?, ?, 'Pending', '', ?)
        """, (class_id, instructor_id, class_gpa, concern, datetime.now().isoformat()))
        return 1

    def get_instructor_grade_reviews(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT igr.id, igr.class_id, igr.instructor_id, igr.class_gpa, igr.concern,
                   igr.status, igr.justification, igr.created_at,
                   c.code, c.title, u.full_name AS instructor_name
            FROM instructor_grade_reviews igr
            JOIN classes cl ON cl.id = igr.class_id
            JOIN courses c ON c.id = cl.course_id
            JOIN users u ON u.id = igr.instructor_id
            ORDER BY CASE WHEN igr.status='Pending' THEN 0 ELSE 1 END, igr.id DESC
        """)
        return cur.fetchall()

    def decide_instructor_grade_review(self, review_id, action, justification=""):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT *
            FROM instructor_grade_reviews
            WHERE id=?
        """, (review_id,))
        review = cur.fetchone()
        if not review:
            return "Instructor GPA review not found."
        if review["status"] != "Pending":
            return "This instructor GPA review was already resolved."

        note = justification.strip()
        if action in {"warn", "fire"} and not note:
            return "A justification is required before warning or firing the instructor."

        if action == "justify":
            final_status = "Cleared with justification"
        elif action == "warn":
            final_status = "Resolved - warning issued"
            self.issue_warning(
                review["instructor_id"], f"instructor_grade_review_warn_{review_id}", 1
            )
        elif action == "fire":
            final_status = "Resolved - instructor fired"
            self.conn.execute(
                "UPDATE users SET suspended=1 WHERE id=?",
                (review["instructor_id"],)
            )
        else:
            return "Unknown instructor review action."

        self.conn.execute("""
            UPDATE instructor_grade_reviews
            SET status=?, justification=?
            WHERE id=?
        """, (final_status, note or "Adequate justification accepted.", review_id))
        self.conn.commit()

        if action == "justify":
            return "Instructor GPA review cleared with justification."
        if action == "warn":
            return "Instructor warned after registrar review."
        return "Instructor fired after registrar review."

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
            # Spec honor-roll rule: semester GPA > 3.75 OR overall GPA > 3.5
            # (the latter only after >1 semester). We don't track semesters
            # per student, so we approximate the "more than one semester"
            # qualifier with "graded in at least 4 classes" before applying
            # the overall-GPA branch of the rule.
            honor_roll = 1 if (gpa > 3.75 or (gpa > 3.5 and len(grades) >= 4)) else 0
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
               COALESCE(u.graduated, 0) AS graduated,
               sp.gpa, sp.overall_gpa, sp.honor_roll, ip.avg_rating
        FROM users u
        LEFT JOIN student_profiles sp ON sp.user_id = u.id
        LEFT JOIN instructor_profiles ip ON ip.user_id = u.id
        WHERE u.id = ?
        """, (user_id,))
        return cur.fetchone()

    def normalize_ai_tokens(self, text):
        tokens = []
        for raw in re.findall(r"[a-z0-9']+", text.lower()):
            token = self.AI_ALIASES.get(raw, raw)
            if token in self.AI_STOP_WORDS:
                continue
            if len(token) <= 2 and token not in {"ai", "cs", "gpa"}:
                continue
            tokens.append(token)
        return tokens

    def build_local_knowledge(self, user=None):
        facts = []

        def add_fact(text, *keywords):
            manual_keywords = {
                self.AI_ALIASES.get(keyword.lower(), keyword.lower())
                for keyword in keywords
            }
            facts.append({
                "text": text,
                "priority_keywords": manual_keywords,
                "keywords": manual_keywords | set(self.normalize_ai_tokens(text)),
            })

        current_period = self.get_current_period()
        quota = self.get_student_quota()
        active_students = self.get_active_student_count()
        required_courses = [
            row["code"] for row in self.conn.execute(
                "SELECT code FROM courses WHERE required=1 ORDER BY code"
            ).fetchall()
        ]
        taboo_words = self.get_taboo_words()
        available_classes = self.get_available_classes()
        complaints = self.get_complaints()

        instructor_rows = self.conn.execute("""
        SELECT u.full_name, ROUND(COALESCE(ip.avg_rating, 0), 2) AS avg_rating
        FROM instructor_profiles ip
        JOIN users u ON u.id = ip.user_id
        ORDER BY u.full_name
        """).fetchall()

        add_fact(
            f"Current semester period: {current_period}. Registration actions are only allowed during Registration or Special Registration.",
            "period", "registration", "semester", "current"
        )
        add_fact(
            f"Student admission quota: {active_students} active students out of {quota}. Student applicants normally need GPA above 3.0 and open quota for admission.",
            "admission", "quota", "student", "gpa", "rules"
        )
        add_fact(
            f"Graduation rules: a student needs 8 completed classes and all required courses passed: {', '.join(required_courses)}. Applying too early is automatically rejected and gives 1 warning.",
            "graduation", "requirements", "required", "graduate", "finish", "degree"
        )
        add_fact(
            "Warning and suspension rules: 3 warnings trigger suspension and a $500 fine. GPA below 2.0 after grading suspends a student. GPA from 2.0 to 2.25 gives a warning. Failing the same course twice suspends the student. Instructors with class GPA above 3.5 or below 2.5 are sent to the registrar for review, where the registrar can accept a justification, warn the instructor, or fire the instructor.",
            "warnings", "suspension", "gpa", "fine", "failed", "rules"
        )
        add_fact(
            "Registration limits: students can register only during Registration or Special Registration, may take at most 4 courses, cannot register while suspended, cannot keep time-conflicting classes, and full classes move students to the wait-list.",
            "registration", "limits", "waitlist", "conflict", "suspended"
        )
        add_fact(
            f"Taboo words policy: the current blocked words are {', '.join(taboo_words)}. Reviews with 1 or 2 taboo words are masked and give 1 warning. Reviews with 3 or more taboo words are hidden and give 2 warnings.",
            "taboo", "policy", "review", "warnings", "blocked", "words"
        )
        add_fact(
            "Honor roll rules: a GPA above 3.75 marks the student as honor roll. If an honor-roll student still has warnings, the system removes one warning once.",
            "honor", "honor_roll", "gpa", "warnings", "rules"
        )
        add_fact(
            f"Complaint rules: students can file complaints against other students or instructors, instructors can file complaints against students in their own class, and the registrar can warn the accused, warn the filer, or de-register a reported student from the instructor's class after review. Students who reach 3 warnings are suspended and fined automatically. There are currently {len(complaints)} complaint records.",
            "complaint", "rules", "registrar", "student", "instructor", "warning", "deregister", "fine", "suspension"
        )
        add_fact(
            f"Current available classes: {len(available_classes)} active classes are listed this period.",
            "classes", "available", "current", "catalog", "offerings"
        )
        for row in available_classes:
            open_seats = max(row["capacity"] - row["enrolled"], 0)
            add_fact(
                f"Available class: {row['code']} {row['title']} with {row['instructor'] or 'TBA'} at {row['meeting_time']}. Seats filled: {row['enrolled']}/{row['capacity']} with {open_seats} open.",
                "classes", "available", "current", row["code"], row["title"], row["instructor"] or "tba"
            )
        if instructor_rows:
            ratings_summary = ", ".join(
                f"{row['full_name']} {row['avg_rating']:.2f}" for row in instructor_rows
            )
            add_fact(
                f"Instructor ratings: {ratings_summary}. Instructors with an average rating below 2.0 receive a warning.",
                "instructor", "rating", "review", "teaching"
            )

        top_students, top_classes, low_classes = self.public_rankings()
        for row in top_students[:3]:
            add_fact(
                f"Top GPA student: {row['full_name']} with GPA {row['overall_gpa']}.",
                "gpa", "honor", "student", "top"
            )
        for row in top_classes[:2]:
            add_fact(
                f"Highly rated class: {row['code']} {row['title']} rated {row['avg_stars']}.",
                "classes", "rating", "review", row["code"], row["title"]
            )
        for row in low_classes[:2]:
            add_fact(
                f"Low rated class: {row['code']} {row['title']} rated {row['avg_stars']}.",
                "classes", "rating", "review", row["code"], row["title"], "low"
            )

        if user and user["role"] == "Student":
            summary = self.get_user_summary(user["id"])
            if summary:
                add_fact(
                    f"Student status: {summary['full_name']} currently has {summary['warnings']} warnings, suspended status {bool(summary['suspended'])}, and GPA {summary['overall_gpa'] or 0}.",
                    "student", "warnings", "suspension", "gpa", "status", "my"
                )
            registrations = self.get_student_registrations(user["id"])
            if registrations:
                joined = "; ".join(
                    f"{row['code']} {row['title']} at {row['meeting_time']} grade {row['grade'] or 'not posted'}"
                    for row in registrations
                )
                add_fact(
                    f"Student schedule: you are currently taking {len(registrations)} classes: {joined}.",
                    "student", "classes", "taking", "schedule", "my", "registration"
                )
            for row in self.get_student_registrations(user["id"]):
                add_fact(
                    f"Student class: {row['code']} {row['title']} at {row['meeting_time']} grade {row['grade'] or 'not posted'}.",
                    "student", "classes", "taking", row["code"], row["title"], "grade"
                )
            else:
                add_fact(
                    "Student schedule: you are not currently registered for any classes.",
                    "student", "classes", "taking", "schedule", "my", "registration"
                )
        if user and user["role"] == "Instructor":
            summary = self.get_user_summary(user["id"])
            if summary:
                add_fact(
                    f"Instructor status: {summary['full_name']} currently has average rating {summary['avg_rating'] or 0} and suspended status {bool(summary['suspended'])}.",
                    "instructor", "rating", "status", "teaching"
                )
            classes = self.get_instructor_classes(user["id"])
            if classes:
                joined = "; ".join(
                    f"{row['code']} {row['title']} at {row['meeting_time']}"
                    for row in classes
                )
                add_fact(
                    f"Instructor teaching schedule: you currently teach {len(classes)} classes: {joined}.",
                    "instructor", "classes", "teach", "teaching", "schedule", "my"
                )
            for row in classes:
                add_fact(
                    f"Instructor teaches {row['code']} {row['title']} at {row['meeting_time']}.",
                    "instructor", "classes", "teach", row["code"], row["title"]
                )
                students = self.get_students_in_class(row["id"])
                if students:
                    roster = "; ".join(
                        f"{student['full_name']} ({student['username']}) warnings {student['warnings']} GPA {student['overall_gpa'] or 0} grade {student['grade'] or 'not posted'}"
                        for student in students
                    )
                    add_fact(
                        f"Instructor student roster for {row['code']} {row['title']}: {len(students)} students enrolled. {roster}.",
                        "instructor", "students", "student", "roster", row["code"], row["title"], "class"
                    )
                else:
                    add_fact(
                        f"Instructor student roster for {row['code']} {row['title']}: there are no enrolled students right now.",
                        "instructor", "students", "student", "roster", row["code"], row["title"], "class"
                    )
            if not classes:
                add_fact(
                    "Instructor teaching schedule: you do not currently have any assigned classes.",
                    "instructor", "classes", "teach", "teaching", "schedule", "my"
                )
        if user and user["role"] == "Registrar":
            pending_grads = len([
                row for row in self.get_graduation_applications()
                if row["status"] == "Pending"
            ])
            add_fact(
                f"Registrar management summary: there are {pending_grads} pending graduation applications and {len(complaints)} complaint records to review.",
                "registrar", "graduation", "complaint", "management", "pending"
            )
        return facts

    def answer_question(self, question, user=None):
        question_lower = question.lower().strip()
        if not question_lower:
            return {
                "answer": "Ask about admissions, registration periods, graduation rules, classes, taboo words, complaints, or your current records.",
                "used_external": False,
            }
        facts = self.build_local_knowledge(user)
        scored = []
        tokens = self.normalize_ai_tokens(question_lower)
        token_set = set(tokens)
        for fact in facts:
            priority_overlap = token_set & fact["priority_keywords"]
            secondary_overlap = token_set & (
                fact["keywords"] - fact["priority_keywords"]
            )
            score = (len(priority_overlap) * 5) + (len(secondary_overlap) * 2)
            if score > 0:
                scored.append((score, fact["text"]))
        scored.sort(reverse=True)
        if scored:
            best_score = scored[0][0]
            best = [
                fact for score, fact in scored[:4]
                if score >= max(5, best_score - 3)
            ]
            return {
                "answer": "Local college info:\n- " + "\n- ".join(best),
                "used_external": False,
            }
        return {
            "answer": (
                "No strong match was found in the College0 local knowledge store (vector DB).\n\n"
                "This question would now be forwarded to an external general-purpose LLM "
                "for a possible answer.\n\n"
                "WARNING: External LLM answers are NOT verified against College0 records "
                "and may be hallucinated, outdated, or simply incorrect. Treat the response "
                "as a hint only and confirm anything important with a registrar or instructor."
            ),
            "used_external": True,
        }


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
    WARNING_BG = "#fff1a8"
    WARNING_BORDER = "#d7b83f"
    WARNING_TEXT = "#5f4a00"
    GRADE_POINTS = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}

    def __init__(self, root):
        self.root = root
        self.root.title("EduNavigator - CCNY Style Demo")
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
        self.public_gpa_auto_value = None
        self.public_role_widget = None
        self.public_page_mode = "Dashboard"
        self.configure_styles()
        self.build_shell()
        self.refresh_header_status()
        self.open_main_dashboard()

    def show_confetti(self, parent):
        import random

        canvas = tk.Canvas(parent, bg=self.BG, highlightthickness=0)
        canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        canvas.update_idletasks()

        width = canvas.winfo_width()
        height = canvas.winfo_height()

        pieces = []
        colors = ["#f0d18d", "#6a4a98", "#a14567", "#2d8c5f", "#bb4f69"]

        for _ in range(50):
            x = random.randint(0, max(width, 1))
            y = random.randint(-height, 0)
            size = random.randint(5, 10)
            color = random.choice(colors)

            piece = canvas.create_rectangle(
                x, y, x + size, y + size, fill=color, outline=""
            )
            pieces.append((piece, random.randint(3, 7)))

        canvas.create_text(
            width // 2,
            height // 2,
            text="Application Submitted!",
            fill=self.NAV_DARK,
            font=("Segoe UI", 22, "bold"),
        )

        def animate(step=0):
            for piece, speed in pieces:
                canvas.move(piece, 0, speed)

            if step < 100:
                canvas.after(30, lambda: animate(step + 1))
            else:
                canvas.destroy()

        animate()

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
            text="EduNavigator – CCNY Intelligent Academic Navigation System",
            bg=self.NAV,
            fg="white",
            font=("Segoe UI", 18, "bold"),
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
        self.header_logout_btn = tk.Button(
            status_wrap,
            text="Logout",
            command=self.logout_user,
            relief="flat",
            bg=self.GOLD,
            fg=self.NAV,
            activebackground="#d8b96d",
            activeforeground=self.NAV,
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=4,
            cursor="hand2",
        )

        body = tk.Frame(self.root, bg=self.BG)
        body.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(body, bg=self.NAV, width=286)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        sidebar_scroll, _sidebar_canvas, sidebar_content = self.create_scrollable_frame(
            self.sidebar, self.NAV, scrollbar_shell_bg=self.GOLD
        )
        sidebar_scroll.pack(fill="both", expand=True)

        self.content = tk.Frame(body, bg=self.BG)
        self.content.pack(side="left", fill="both", expand=True)

        tk.Label(sidebar_content, text="MENU", bg=self.NAV, fg="#f1e9ff", font=(
            "Segoe UI", 11, "bold")).pack(anchor="w", padx=20, pady=(22, 8))

        nav_items = [
            ("Dashboard", self.open_main_dashboard),
            ("Apply as Student", lambda: self.open_public_application("Student")),
            ("Apply as Instructor", lambda: self.open_public_application("Instructor")),
            ("Login", lambda: self.show_page("Login", "Login")),
            ("Logout", self.logout_user),
            ("Submit Review", self.open_review_page),
            ("File Complaint", self.open_complaint_page),
            ("AI Assistant", self.open_ai_page),
            ("Help", self.show_help),
            ("Exit", self.root.destroy),
        ]
        for label, command in nav_items:
            btn = tk.Label(
                sidebar_content,
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
            btn.bind("<Enter>", lambda e,
                     b=btn: b.configure(bg=self.NAV_LIGHT))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=self.NAV))

            tk.Frame(
                sidebar_content,
                bg="#8065ac",
                height=1
            ).pack(fill="x", padx=14)

            self.nav_buttons[label] = btn

        tk.Label(sidebar_content, text="Demo Access", bg=self.NAV, fg=self.GOLD, font=(
            "Segoe UI", 10, "bold")).pack(anchor="w", padx=20, pady=(18, 4))
        demo_text = "Registrar\nregistrar / admin123\n\nStudent\ns1001 / temp123\n\nInstructor\ni2001 / teach123"
        tk.Label(sidebar_content, text=demo_text, justify="left", bg=self.NAV,
                 fg="#efe8ff", font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(8, 0))

        footer = tk.Frame(sidebar_content, bg=self.NAV)
        footer.pack(fill="x", pady=20)
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
            self.public_page_mode = "Dashboard"
            self.build_public_page()
            self.show_page("Public", "Dashboard")

    def logout_user(self):
        if not self.current_user:
            messagebox.showinfo("Logout", "No user is currently logged in.")
            return
        self.current_user = None
        self.refresh_header_status()
        self.public_page_mode = "Dashboard"
        self.build_public_page()
        self.build_dashboard_placeholder()
        self.show_page("Public", "Dashboard")
        messagebox.showinfo("Logout", "You have been logged out successfully.")

    def open_public_application(self, role):
        self.public_page_mode = role
        self.build_public_page()
        self.show_page("Public", f"Apply as {role}")
        self.set_public_role(role)

    def open_review_page(self):
        if not self.current_user or self.current_user["role"] != "Student":
            messagebox.showerror(
                "Access denied", "Please log in as a student first.")
            return
        self.build_review_page()
        self.show_page("Review", "Submit Review")

    def open_complaint_page(self):
        if not self.current_user or self.current_user["role"] != "Student":
            messagebox.showerror(
                "Access denied", "Please log in as a student first.")
            return
        self.build_complaint_page()
        self.show_page("Complaint", "File Complaint")

    def build_complaint_page(self):
        frame = self.prepare_scrollable_page("Complaint")

        wrapper = tk.Frame(frame, bg=self.BG)
        wrapper.pack(fill="both", expand=True, padx=24, pady=24)

        self.section_title(wrapper, "File Complaint",
                           "Report an issue with another user")

        card, body = self.make_card(wrapper, "Complaint Form")
        card.pack(fill="x", pady=20)

        tk.Label(body, text="Select User", bg=self.CARD).pack(anchor="w")

        users = [
            user for user in
            (self.db.get_users_by_role("Instructor") +
             self.db.get_users_by_role("Student"))
            if user["id"] != self.current_user["id"]
        ]

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
                detail,
                "Student Complaint",
            )

            messagebox.showinfo("Success", "Complaint submitted")
            detail_box.delete("1.0", tk.END)

        tk.Button(body, text="Submit Complaint",
                  command=submit,
                  bg=self.NAV, fg="white").pack(pady=10)

    def open_ai_page(self):
        self.build_ai_page()
        self.show_page("AI", "AI Assistant")

    def build_review_page(self):
        frame = self.prepare_scrollable_page("Review")

        wrapper = tk.Frame(frame, bg=self.BG)
        wrapper.pack(fill="both", expand=True, padx=24, pady=24)

        self.section_title(wrapper, "Submit Review",
                           "Leave feedback for your classes")

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

        tk.Label(body, text="Star Rating", bg=self.CARD).pack(anchor="w")
        stars_var = tk.IntVar(value=5)
        stars_row = tk.Frame(body, bg=self.CARD)
        stars_row.pack(anchor="w", pady=5)
        star_buttons = []

        def refresh_star_buttons():
            selected_stars = stars_var.get()
            for index, button in enumerate(star_buttons, start=1):
                if index <= selected_stars:
                    button.configure(text="★", fg=self.GOLD)
                else:
                    button.configure(text="☆", fg=self.MUTED)

        for index in range(1, 6):
            button = tk.Button(
                stars_row,
                text="☆",
                command=lambda value=index: (stars_var.set(value), refresh_star_buttons()),
                relief="flat",
                bd=0,
                bg=self.CARD,
                activebackground=self.CARD,
                activeforeground=self.GOLD,
                fg=self.MUTED,
                font=("Segoe UI Symbol", 20, "bold"),
                cursor="hand2",
                padx=2,
                pady=0,
            )
            button.pack(side="left", padx=(0, 4))
            star_buttons.append(button)
        refresh_star_buttons()

    # Review text
        tk.Label(body, text="Review", bg=self.CARD).pack(anchor="w")
        review_box = tk.Text(body, height=4)
        review_box.pack(fill="x", pady=5)

        def submit():
            selected = class_var.get()
            if not selected:
                messagebox.showerror("Error", "Select a class")
                return

            stars = stars_var.get()
            if stars < 1 or stars > 5:
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

            if "received 2 warnings" in result:
                messagebox.showwarning("Warning", result)
            elif "received 1 warning" in result:
                messagebox.showwarning("Warning", result)
            else:
                messagebox.showinfo("Result", result)

        tk.Button(body, text="Submit Review",
                command=submit,
                bg=self.NAV, fg="white").pack(pady=10)

    def build_ai_page(self):
        frame = self.prepare_scrollable_page("AI")

        wrapper = tk.Frame(frame, bg=self.BG)
        wrapper.pack(fill="both", expand=True, padx=24, pady=24)
        ai_title = self.get_ai_panel_title(self.current_user)

        self.section_title(
            wrapper,
            ai_title,
            "Ask questions about registrations, GPA, classes, reviews, warnings, and semester rules."
        )
        ai_card = self.build_ai_panel(
            wrapper,
            self.current_user,
            ai_title
        )

        ai_card.pack(fill="both", expand=True, pady=(20, 0))

    def show_help(self):
        messagebox.showinfo(
            "Help",
            "Use the left menu to view the home page, submit an application, or log in with one of the demo accounts.",
        )

    def set_public_role(self, role, preserve_manual_value=False):
        if self.public_role_var is not None:
            self.public_role_var.set(role)
        if self.public_gpa_entry is not None:
            default_value = "3.20" if role == "Student" else "0.00"
            current_value = self.public_gpa_entry.get().strip()
            should_replace = not preserve_manual_value or current_value in {
                "",
                "0.00",
                "3.20",
                self.public_gpa_auto_value,
            }
            self.public_gpa_entry.configure(state="normal")
            if should_replace:
                self.public_gpa_entry.delete(0, tk.END)
                self.public_gpa_entry.insert(0, default_value)
                self.public_gpa_auto_value = default_value
            if role == "Instructor":
                self.public_gpa_entry.configure(
                    state="readonly",
                    readonlybackground=self.CARD,
                    fg=self.TEXT,
                )
            else:
                self.public_gpa_entry.configure(state="normal")
        if self.public_name_entry is not None:
            self.public_name_entry.focus_set()

    def clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

    def ensure_mousewheel_support(self):
        if getattr(self, "_mousewheel_bound", False):
            return
        self.root.bind_all("<MouseWheel>", self.handle_mousewheel, add="+")
        self.root.bind_all(
            "<Button-4>", self.handle_mousewheel_linux_up, add="+")
        self.root.bind_all(
            "<Button-5>", self.handle_mousewheel_linux_down, add="+")
        self._mousewheel_bound = True

    def find_scroll_target(self, widget):
        current = widget
        while current is not None:
            target = getattr(current, "_college0_scroll_target", None)
            if target is not None:
                return target
            current = current.master
        return None

    def handle_mousewheel(self, event):
        widget = self.root.winfo_containing(event.x_root, event.y_root)
        target = self.find_scroll_target(widget)
        if target is None:
            return
        step = int(-event.delta / 120)
        if step:
            target.yview_scroll(step, "units")

    def handle_mousewheel_linux_up(self, event):
        widget = self.root.winfo_containing(event.x_root, event.y_root)
        target = self.find_scroll_target(widget)
        if target is not None:
            target.yview_scroll(-1, "units")

    def handle_mousewheel_linux_down(self, event):
        widget = self.root.winfo_containing(event.x_root, event.y_root)
        target = self.find_scroll_target(widget)
        if target is not None:
            target.yview_scroll(1, "units")

    def create_scrollable_frame(self, parent, bg, scrollbar_shell_bg=None):
        self.ensure_mousewheel_support()
        container = tk.Frame(parent, bg=bg)
        canvas = tk.Canvas(
            container,
            bg=bg,
            highlightthickness=0,
            bd=0,
            relief="flat",
        )
        scrollbar_shell = tk.Frame(
            container,
            bg=scrollbar_shell_bg or self.BORDER,
            width=30,
            highlightthickness=1,
            highlightbackground=self.NAV_DARK,
        )
        scrollbar = tk.Scrollbar(
            scrollbar_shell,
            orient="vertical",
            command=canvas.yview,
            width=22,
            troughcolor=self.NAV_DARK,
            bg=self.GOLD,
            activebackground="#d8b96d",
            relief="raised",
            bd=2,
            highlightbackground=self.NAV_DARK,
            highlightcolor=self.NAV_DARK,
            elementborderwidth=2,
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_shell.pack(side="right", fill="y")
        scrollbar_shell.pack_propagate(False)
        scrollbar.pack(fill="y", expand=True, padx=3, pady=3)

        inner = tk.Frame(canvas, bg=bg)
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        for widget in (container, canvas, inner, scrollbar_shell, scrollbar):
            widget._college0_scroll_target = canvas

        inner.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(window_id, width=event.width),
        )
        return container, canvas, inner

    def prepare_scrollable_page(self, page_name, bg=None):
        page = self.pages[page_name]
        self.clear_frame(page)
        container, _canvas, inner = self.create_scrollable_frame(
            page, bg or self.BG)
        container.pack(fill="both", expand=True)
        return inner

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
                          selectforeground=self.TEXT, activestyle="none",
                          exportselection=False)

    def section_title(self, parent, title, subtitle=""):
        tk.Label(parent, text=title, bg=self.BG, fg=self.NAV_DARK,
                 font=("Segoe UI", 24, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(parent, text=subtitle, bg=self.BG, fg=self.MUTED,
                     font=("Segoe UI", 11)).pack(anchor="w", pady=(6, 0))

    def get_ai_panel_title(self, user=None):
        if not user:
            return "Visitor AI Assistant"
        return {
            "Student": "Student Academic Assistant",
            "Instructor": "Instructor Teaching Assistant",
            "Registrar": "Registrar Management Assistant",
        }.get(user["role"], "College0 AI Assistant")

    def get_ai_suggestions(self, user=None):
        if not user:
            return [
                "What classes are available right now?",
                "What is the current semester period?",
                "What are graduation requirements?",
            ]
        if user["role"] == "Student":
            return [
                "What classes am I taking?",
                "What is the current semester period?",
                "What are graduation requirements?",
            ]
        if user["role"] == "Instructor":
            return [
                "Which classes do I teach?",
                "Which students are in my classes?",
                "How do instructor ratings work?",
            ]
        if user["role"] == "Registrar":
            return [
                "What are graduation requirements?",
                "What are the complaint rules?",
                "What taboo words are blocked?",
            ]
        return [
            "What classes are available right now?",
            "What is the current semester period?",
            "What are graduation requirements?",
        ]

    def get_ai_role_hint(self, user=None):
        if not user:
            return "Visitors can ask general questions about current classes, semester periods, and college requirements."
        if user["role"] == "Student":
            return "Students can ask about their own schedule, graduation rules, warnings, registration limits, and local college policies."
        if user["role"] == "Instructor":
            return "Instructors can ask about classes they teach and the students enrolled in those classes."
        if user["role"] == "Registrar":
            return "Registrars can ask about complaints, taboo words, graduation reviews, and management rules."
        return "Ask about the local college system and role-specific records."

    def get_ai_followups(self, user=None, question_text="", answer_text="", used_external=False):
        if used_external:
            return self.get_ai_suggestions(user)

        prompts = []
        tokens = set(self.db.normalize_ai_tokens(
            f"{question_text} {answer_text}"))

        if "graduation" in tokens:
            prompts.extend([
                "What are the required courses?",
                "How many completed classes are needed for graduation?",
            ])
            if user and user["role"] == "Student":
                prompts.append("Can I apply for graduation now?")
        if "registration" in tokens or "classes" in tokens:
            prompts.append("What is the current semester period?")
            if user and user["role"] == "Student":
                prompts.append("What classes am I taking?")
            else:
                prompts.append("What classes are available right now?")
        if "warnings" in tokens or "suspension" in tokens:
            prompts.extend([
                "What is the taboo words policy?",
                "What are the complaint rules?",
            ])
        if "taboo" in tokens:
            prompts.extend([
                "How many warnings do taboo words cause?",
                "What are the complaint rules?",
            ])
        if "complaint" in tokens:
            prompts.extend([
                "How do warning and suspension rules work?",
                "What taboo words are blocked?",
            ])
        if "instructor" in tokens or "students" in tokens:
            prompts.extend([
                "Which classes do I teach?",
                "Which students are in my classes?",
            ])
        if "period" in tokens:
            prompts.extend([
                "What classes are available right now?",
                "What are registration limits?",
            ])

        if not prompts:
            prompts = self.get_ai_suggestions(user)

        deduped = []
        for prompt in prompts:
            if prompt not in deduped:
                deduped.append(prompt)
        return deduped[:3]

    def build_ai_panel(self, parent, user=None, title="EduNavigator AI Assistant"):
        card, body = self.make_card(
            parent,
            title,
            "Answers come from the local College0 knowledge store first. If nothing matches, the app warns that an external LLM answer could hallucinate.",
        )
        role_hint = tk.Label(
            body,
            text=self.get_ai_role_hint(user),
            bg=self.CARD_ALT,
            fg=self.TEXT,
            font=("Segoe UI", 10),
            justify="left",
            anchor="w",
            padx=12,
            pady=10,
            wraplength=780,
        )
        role_hint.pack(fill="x", pady=(0, 10))

        warning_box = tk.Frame(body, bg=self.WARNING_BORDER)
        tk.Label(
            warning_box,
            text="External AI response may contain hallucinations.",
            bg=self.WARNING_BG,
            fg=self.WARNING_TEXT,
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=8,
            anchor="w",
            justify="left",
        ).pack(fill="x", padx=1, pady=1)
        warning_box.pack(fill="x", pady=(0, 10))
        warning_box.pack_forget()

        source_label = tk.Label(
            body,
            text="Current answer source: local EduNavigator knowledge store is ready.",
            bg=self.CARD,
            fg=self.MUTED,
            font=("Segoe UI", 9),
        )
        source_label.pack(anchor="w", pady=(0, 8))

        status_label = tk.Label(
            body,
            text="Ready for a question. Press Ctrl+Enter to ask.",
            bg=self.CARD,
            fg=self.NAV_DARK,
            font=("Segoe UI", 9, "bold"),
        )
        status_label.pack(anchor="w", pady=(0, 10))

        suggestions = tk.Frame(body, bg=self.CARD)
        suggestions.pack(fill="x", pady=(0, 10))
        tk.Label(
            suggestions,
            text="Try a demo question",
            bg=self.CARD,
            fg=self.TEXT,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 6))

        question = tk.Text(body, height=4, relief="solid",
                           bd=1, font=("Segoe UI", 10))
        question.pack(fill="x", pady=(0, 10))
        tk.Label(
            body,
            text="Type your own question or use a suggestion button. Ctrl+Enter submits the question.",
            bg=self.CARD,
            fg=self.MUTED,
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(0, 8))
        answer = tk.Text(body, height=8, relief="solid", bd=1,
                         font=("Segoe UI", 10), wrap="word")
        answer.pack(fill="both", expand=True)
        answer.insert(
            "1.0", "Answers will appear here. The AI checks local college knowledge first.")
        answer.config(state="disabled")

        followup_wrap = tk.Frame(body, bg=self.CARD)
        followup_wrap.pack(fill="x", pady=(10, 0))
        tk.Label(
            followup_wrap,
            text="Suggested follow-up questions",
            bg=self.CARD,
            fg=self.TEXT,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 6))
        followup_row = tk.Frame(followup_wrap, bg=self.CARD)
        followup_row.pack(anchor="w", fill="x")

        button_row = tk.Frame(suggestions, bg=self.CARD)
        button_row.pack(anchor="w", fill="x")

        def fill_question(prompt):
            question.delete("1.0", tk.END)
            question.insert("1.0", prompt)
            question.focus_set()

        def set_answer(text):
            answer.config(state="normal")
            answer.delete("1.0", tk.END)
            answer.insert("1.0", text)
            answer.config(state="disabled")

        def render_followups(prompts):
            for widget in followup_row.winfo_children():
                widget.destroy()
            for prompt in prompts:
                tk.Button(
                    followup_row,
                    text=prompt,
                    command=lambda value=prompt: fill_question(value),
                    relief="flat",
                    bg=self.CARD_ALT,
                    fg=self.NAV_DARK,
                    activebackground="#efe7fb",
                    activeforeground=self.NAV_DARK,
                    font=("Segoe UI", 9, "bold"),
                    padx=10,
                    pady=6,
                    cursor="hand2",
                ).pack(side="left", padx=(0, 8), pady=(0, 4))

        for prompt in self.get_ai_suggestions(user):
            tk.Button(
                button_row,
                text=prompt,
                command=lambda value=prompt: fill_question(value),
                relief="flat",
                bg=self.CARD_ALT,
                fg=self.NAV_DARK,
                activebackground="#efe7fb",
                activeforeground=self.NAV_DARK,
                font=("Segoe UI", 9, "bold"),
                padx=10,
                pady=6,
                cursor="hand2",
            ).pack(side="left", padx=(0, 8), pady=(0, 4))
        render_followups(self.get_ai_suggestions(user))

        def ask_ai():
            question_text = question.get("1.0", tk.END).strip()
            status_label.config(
                text="Searching the local college knowledge store...")
            response = self.db.answer_question(question_text, user)
            set_answer(response["answer"])
            if response["used_external"]:
                warning_box.pack(fill="x", pady=(0, 10), before=source_label)
                source_label.config(
                    text="Current answer source: external fallback placeholder. Keep the hallucination warning in mind.",
                    fg=self.WARNING_TEXT,
                )
                status_label.config(
                    text="No strong local match found. External fallback would be used here.")
            else:
                warning_box.pack_forget()
                source_label.config(
                    text="Current answer source: local EduNavigator knowledge store.",
                    fg=self.MUTED,
                )
                status_label.config(
                    text="Local answer found from the college knowledge store.")
            render_followups(
                self.get_ai_followups(
                    user,
                    question_text,
                    response["answer"],
                    response["used_external"],
                )
            )

        def clear_ai():
            question.delete("1.0", tk.END)
            set_answer(
                "Answers will appear here. The AI checks local college knowledge first.")
            warning_box.pack_forget()
            source_label.config(
                text="Current answer source: local EduNavigator knowledge store is ready.",
                fg=self.MUTED,
            )
            status_label.config(
                text="Ready for a question. Press Ctrl+Enter to ask.")
            render_followups(self.get_ai_suggestions(user))

        question.bind("<Control-Return>", lambda event: (ask_ai(), "break")[1])

        action_row = tk.Frame(body, bg=self.CARD)
        action_row.pack(anchor="w", pady=(10, 0))
        tk.Button(action_row, text="Ask AI", command=ask_ai, relief="flat", bg=self.NAV, fg="white",
                  activebackground=self.NAV_LIGHT, activeforeground="white", font=("Segoe UI", 10, "bold"),
                  padx=16, pady=8, cursor="hand2").pack(side="left")
        tk.Button(action_row, text="Clear", command=clear_ai, relief="flat", bg=self.CARD_ALT, fg=self.NAV_DARK,
                  activebackground="#efe7fb", activeforeground=self.NAV_DARK, font=("Segoe UI", 10, "bold"),
                  padx=16, pady=8, cursor="hand2").pack(side="left", padx=(8, 0))
        return card

    def build_student_planner_card(self, parent):
        audit = self.db.get_student_degree_audit(self.current_user["id"])
        card, body = self.make_card(
            parent,
            "Graduation & GPA Planner",
            "Creative feature: preview projected grades, GPA outcomes, and graduation readiness.",
        )
        card.pack(fill="x", pady=(16, 0))

        tk.Label(
            body,
            text=(
                f"Completed classes: {audit['completed_count']}/8"
                f"  |  Required courses tracked: {len(audit['required_courses'])}"
            ),
            bg=self.CARD,
            fg=self.TEXT,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 10))

        required_lines = [
            f"{course['code']} {course['title']}: {course['status']}"
            for course in audit["required_courses"]
        ]
        tk.Label(
            body,
            text="Required course progress:\n" + "\n".join(required_lines),
            justify="left",
            anchor="w",
            bg=self.CARD_ALT,
            fg=self.TEXT,
            font=("Segoe UI", 10),
            padx=12,
            pady=10,
        ).pack(fill="x", pady=(0, 12))

        projected_vars = {}
        if audit["active_rows"]:
            tk.Label(
                body,
                text="Projected grades for your active classes",
                bg=self.CARD,
                fg=self.TEXT,
                font=("Segoe UI", 10, "bold"),
            ).pack(anchor="w", pady=(0, 8))
            planner_grid = tk.Frame(body, bg=self.CARD)
            planner_grid.pack(fill="x", pady=(0, 10))
            for row in audit["active_rows"]:
                grade_var = tk.StringVar(value="B")
                projected_vars[row["class_id"]] = grade_var
                line = tk.Frame(planner_grid, bg=self.CARD)
                line.pack(fill="x", pady=3)
                tk.Label(
                    line,
                    text=f"{row['code']} {row['title']} | {row['meeting_time']}",
                    bg=self.CARD,
                    fg=self.TEXT,
                    font=("Segoe UI", 10),
                ).pack(side="left")
                ttk.Combobox(
                    line,
                    textvariable=grade_var,
                    values=list(self.GRADE_POINTS.keys()),
                    state="readonly",
                    width=5,
                ).pack(side="right")
        else:
            tk.Label(
                body,
                text="No active classes are waiting for grades right now.",
                bg=self.CARD_ALT,
                fg=self.MUTED,
                font=("Segoe UI", 10),
                padx=12,
                pady=10,
            ).pack(fill="x", pady=(0, 10))

        result_var = tk.StringVar(
            value="Choose projected grades and click Preview Outcome to estimate your semester path."
        )

        def preview_outcome():
            graded_rows = audit["graded_rows"]
            projected_rows = []
            for row in audit["active_rows"]:
                projected_rows.append(
                    dict(row) | {
                        "projected_grade": projected_vars[row["class_id"]].get() or "B"
                    }
                )

            graded_points = sum(
                self.GRADE_POINTS.get((row["grade"] or "").upper(), 0.0)
                for row in graded_rows
            )
            projected_points = sum(
                self.GRADE_POINTS[row["projected_grade"]]
                for row in projected_rows
            )
            projected_semester_gpa = (
                projected_points / len(projected_rows) if projected_rows else None
            )
            total_completed_after_term = audit["completed_count"] + len(projected_rows)
            total_graded_after_term = len(graded_rows) + len(projected_rows)
            projected_overall_gpa = (
                (graded_points + projected_points) / total_graded_after_term
                if total_graded_after_term
                else 0.0
            )

            missing_required = []
            for course in audit["required_courses"]:
                currently_passed = course["status"] == "Completed"
                projected_pass = any(
                    row["code"] == course["code"] and row["projected_grade"] != "F"
                    for row in projected_rows
                )
                if not (currently_passed or projected_pass):
                    missing_required.append(course["code"])

            status_note = "Projected status: in good standing."
            if projected_overall_gpa < 2.0:
                status_note = "Projected status: below 2.0, which would put you in automatic termination range."
            elif projected_overall_gpa <= 2.25:
                status_note = "Projected status: between 2.0 and 2.25, which would trigger a registrar interview warning."

            honor_note = "Honor roll outlook: not yet."
            if projected_semester_gpa is not None and projected_semester_gpa > 3.75:
                honor_note = "Honor roll outlook: yes, this semester projection reaches the honor-roll threshold."
            elif projected_overall_gpa > 3.5 and total_graded_after_term > len(projected_rows):
                honor_note = "Honor roll outlook: yes, your projected overall GPA would stay above 3.5."

            if total_completed_after_term >= 8 and not missing_required:
                graduation_note = "Graduation outlook: eligible to apply after these classes are completed."
            else:
                graduation_note = (
                    f"Graduation outlook: not ready yet. Missing required courses: "
                    f"{', '.join(missing_required) if missing_required else 'none'}, "
                    f"completed classes after term: {total_completed_after_term}/8."
                )

            lines = []
            if projected_semester_gpa is None:
                lines.append(
                    "Projected semester GPA: no active in-progress classes to estimate."
                )
            else:
                lines.append(f"Projected semester GPA: {projected_semester_gpa:.2f}")
            lines.append(f"Projected overall GPA: {projected_overall_gpa:.2f}")
            lines.append(status_note)
            lines.append(honor_note)
            lines.append(graduation_note)
            result_var.set("\n".join(lines))

        tk.Button(
            body,
            text="Preview Outcome",
            command=preview_outcome,
            relief="flat",
            bg=self.GOLD,
            fg=self.NAV,
            font=("Segoe UI", 10, "bold"),
            padx=16,
            pady=8,
            cursor="hand2",
        ).pack(anchor="w", pady=(0, 10))

        tk.Label(
            body,
            textvariable=result_var,
            justify="left",
            anchor="w",
            wraplength=860,
            bg="#fff8e8",
            fg=self.TEXT,
            font=("Segoe UI", 10),
            padx=12,
            pady=10,
        ).pack(fill="x")

        return card

    def make_feature_card(self, parent, badge, title, items, extra_items=None):
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

        if extra_items:
            dropdown_frame = tk.Frame(body, bg=self.FEATURE)

            def toggle_dropdown():
                if dropdown_frame.winfo_ismapped():
                    dropdown_frame.pack_forget()
                    view_btn.config(text="Click to view more")
                else:
                    dropdown_frame.pack(anchor="w", fill="x", pady=(8, 0))
                    view_btn.config(text="Hide list")

            view_btn = tk.Button(
                body,
                text="Click to view more",
                command=toggle_dropdown,
                bg=self.GOLD,
                fg=self.NAV_DARK,
                relief="flat",
                font=("Segoe UI", 9, "bold"),
                cursor="hand2",
            )
            view_btn.pack(anchor="w", pady=(10, 0))

            for item in extra_items:
                tk.Label(
                    dropdown_frame,
                    text=f"• {item}",
                    bg=self.FEATURE,
                    fg="white",
                    wraplength=220,
                    justify="left",
                    font=("Segoe UI", 9),
                ).pack(anchor="w", pady=2)

        return card
    ####

    def build_public_page(self):
        frame = self.prepare_scrollable_page("Public")

        hero = tk.Frame(frame, bg=self.BG)
        hero.pack(fill="x", padx=30, pady=(28, 16))

        tk.Label(
            hero,
            text="Welcome to EduNavigator",
            bg=self.BG,
            fg=self.NAV_DARK,
            font=("Segoe UI", 30, "bold"),
        ).pack()

        tk.Frame(hero, bg=self.BORDER, height=1).pack(
            fill="x", padx=180, pady=14
        )

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

        student_items = [
            f"{r['full_name']} - GPA {r['overall_gpa']}" for r in top_students
        ] or [
            "Amy S. - GPA 3.9",
            "John D. - GPA 3.8",
            "Linda K. - GPA 3.7",
        ]

        top_class_items = [
            f"{r['code']} {r['title']} ({r['avg_stars']})" for r in top_classes
        ] or [
            "Advanced Python (4.8)",
            "Data Science (4.6)",
            "Creative Writing (4.5)",
        ]

        low_class_items = [
            f"{r['code']} {r['title']} ({r['avg_stars']})" for r in low_classes
        ] or [
            "Intro to Algebra (2.3)",
            "History 101 (2.5)",
            "Art Appreciation (2.6)",
        ]

        top_more_items = [
            "Machine Learning (4.7)",
            "Web Development (4.6)",
            "Cybersecurity Basics (4.5)",
            "Calculus II (4.4)",
            "Linear Algebra (4.3)",
            "Operating Systems (4.2)",
            "Computer Graphics (4.1)",
            "Mobile App Design (4.0)",
            "Human-Computer Interaction (3.9)",
            "Intro to AI (3.8)",
        ]

        low_more_items = [
            "Statistics Lab (2.7)",
            "Chemistry Recitation (2.6)",
            "Physics I (2.5)",
            "Public Speaking (2.4)",
            "Technical Writing (2.4)",
            "Biology Lab (2.3)",
            "Economics 101 (2.2)",
            "Pre-Calculus (2.1)",
            "Philosophy 101 (2.0)",
            "World History (1.9)",
        ]

        groups = [
            ("TOP", "Top Rated Classes", top_class_items, top_more_items),
            ("LOW", "Lowest Rated Classes", low_class_items, low_more_items),
            ("GPA", "Highest GPA Students", student_items, None),
            (
                "CCNY",
                "College Highlights",
                [
                    "Small college community",
                    "Hands-on learning",
                    "AI-enabled assistance",
                ],
                None,
            ),
        ]

        for badge, title, items, extra_items in groups:
            card = self.make_feature_card(
                ranking_row, badge, title, items, extra_items
            )
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
            frame,
            "Visitor Application",
            "Apply as a student or instructor while keeping the same project workflow.",
        )
        app_card.pack(fill="x", padx=24, pady=16)

        form = tk.Frame(app_body, bg=self.CARD)
        form.pack(fill="x")
        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(2, weight=1)

        tk.Label(
            form,
            text="Full Name",
            bg=self.CARD,
            fg=self.TEXT,
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=6, pady=6)

        self.public_name_entry = tk.Entry(
            form, width=34, relief="solid", bd=1, font=("Segoe UI", 10)
        )
        self.public_name_entry.grid(
            row=1, column=0, padx=6, pady=(0, 10), sticky="we"
        )

        tk.Label(
            form,
            text="Apply As",
            bg=self.CARD,
            fg=self.TEXT,
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=1, sticky="w", padx=6, pady=6)

        if self.public_page_mode == "Dashboard":
            self.public_role_var = tk.StringVar(value="Student")

            self.public_role_widget = ttk.Combobox(
                form,
                textvariable=self.public_role_var,
                values=["Student", "Instructor"],
                state="readonly",
                font=("Segoe UI", 10),
            )
            self.public_role_widget.bind(
                "<<ComboboxSelected>>",
                lambda _event: self.set_public_role(
                    self.public_role_var.get(), preserve_manual_value=True
                ),
            )
        else:
            self.public_role_var = tk.StringVar(value=self.public_page_mode)

            self.public_role_widget = tk.Entry(
                form,
                textvariable=self.public_role_var,
                width=20,
                relief="solid",
                bd=1,
                font=("Segoe UI", 10),
                state="readonly",
                readonlybackground=self.CARD,
                fg=self.TEXT,
            )

        self.public_role_widget.grid(
            row=1, column=1, padx=6, pady=(0, 10), sticky="we"
        )

        tk.Label(
            form,
            text="GPA",
            bg=self.CARD,
            fg=self.TEXT,
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=2, sticky="w", padx=6, pady=6)

        self.public_gpa_entry = tk.Entry(
            form, width=12, relief="solid", bd=1, font=("Segoe UI", 10)
        )
        self.public_gpa_entry.insert(0, "3.20")
        self.public_gpa_entry.grid(
            row=1, column=2, padx=6, pady=(0, 10), sticky="we"
        )

        tk.Label(
            form,
            text="Student applications use GPA. Instructor applications keep GPA fixed at 0.00.",
            bg=self.CARD,
            fg=self.MUTED,
            font=("Segoe UI", 9),
        ).grid(row=2, column=0, columnspan=3, sticky="w", padx=6, pady=(0, 10))

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
                    "Missing name", "Please enter the applicant's full name."
                )
                return

            self.db.submit_application(name, role, gpa)

            messagebox.showinfo(
                "Submitted",
                "Application submitted successfully."
            )

            self.show_confetti(frame)

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

    def build_login_page(self):
        frame = self.prepare_scrollable_page("Login")
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
        frame = self.prepare_scrollable_page("Dashboard")
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
            if not self.header_logout_btn.winfo_ismapped():
                self.header_logout_btn.pack(anchor="e", pady=(8, 0))
        else:
            text = f"Guest mode | {self.db.get_current_period()}"
            if self.header_logout_btn.winfo_ismapped():
                self.header_logout_btn.pack_forget()
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
        frame = self.prepare_scrollable_page("Dashboard")
        user = self.current_user
        self.refresh_header_status()
        summary = self.db.get_user_summary(user["id"])
        top = tk.Frame(frame, bg=self.BG)
        top.pack(fill="x", padx=24, pady=22)
        is_graduated = bool(summary["graduated"]) if "graduated" in summary.keys() else False
        status_label = "Graduated" if is_graduated else ("Yes" if summary["suspended"] else "No")
        status_field = "Status" if is_graduated else "Suspended"
        subtitle = f"{user['full_name']} | Warnings: {summary['warnings']} | {status_field}: {status_label}"
        if user["role"] == "Student":
            subtitle += f" | GPA: {summary['overall_gpa'] or 0.0}"
        elif user["role"] == "Instructor":
            subtitle += f" | Avg Rating: {round(summary['avg_rating'] or 0.0, 2)}"
        self.section_title(top, f"{user['role']} Dashboard", subtitle)

        quick = tk.Frame(frame, bg=self.BG)
        quick.pack(fill="x", padx=24, pady=(0, 12))
        if is_graduated:
            status_value = "Graduated"
            status_color = self.NAV
        elif summary["suspended"]:
            status_value = "Suspended"
            status_color = self.DANGER
        else:
            status_value = "Active"
            status_color = self.SUCCESS
        for title, value, color in [
            ("Warnings", str(summary["warnings"]), self.GOLD),
            ("Status", status_value, status_color),
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
            complaint_target = c["class_code"] if c["class_code"] else c["against_role"]
            complaint_list.insert(
                tk.END,
                f"#{c['id']}  |  {c['complaint_type']}  |  {c['filed_by']} -> {c['against_name']}  |  {complaint_target}  |  {c['status']}"
            )

        def show_complaint_popup(_event=None):
            sel = complaint_list.curselection()
            if not sel:
                return
            complaint = complaints[sel[0]]
            top = tk.Toplevel(self.root)
            top.title(f"Complaint #{complaint['id']}")
            top.geometry("640x420")
            top.minsize(560, 360)
            top.configure(bg=self.BG)
            top.transient(self.root)
            top.lift()
            top.focus_force()
            top.grab_set()

            card, body = self.make_card(
                top,
                f"Complaint #{complaint['id']}",
                f"{complaint['filed_by']} -> {complaint['against_name']} | {complaint['status']}",
            )
            card.pack(fill="both", expand=True, padx=18, pady=18)

            meta_lines = [
                f"Type: {complaint['complaint_type']}",
                f"Filed by: {complaint['filed_by']} ({complaint['filed_by_role']})",
                f"Against: {complaint['against_name']} ({complaint['against_role']})",
            ]
            if complaint["class_code"]:
                meta_lines.append(
                    f"Class: {complaint['class_code']} {complaint['class_title']}"
                )
            tk.Label(
                body,
                text="\n".join(meta_lines),
                justify="left",
                anchor="w",
                bg=self.CARD,
                fg=self.MUTED,
                font=("Segoe UI", 10),
            ).pack(fill="x", pady=(0, 12))

            tk.Label(
                body,
                text="Complaint Detail",
                bg=self.CARD,
                fg=self.TEXT,
                font=("Segoe UI", 11, "bold"),
            ).pack(anchor="w", pady=(0, 6))

            detail_box = tk.Text(
                body,
                height=12,
                relief="solid",
                bd=1,
                font=("Segoe UI", 10),
                wrap="word",
                bg="white",
                fg=self.TEXT,
                disabledforeground=self.TEXT,
                insertbackground=self.TEXT,
                padx=10,
                pady=10,
            )
            detail_box.pack(fill="both", expand=True)
            detail_box.insert("1.0", complaint["detail"] or "No complaint detail provided.")
            detail_box.configure(state="disabled")

            tk.Button(
                body,
                text="Close",
                command=top.destroy,
                relief="flat",
                bg=self.NAV,
                fg="white",
                activebackground=self.NAV_LIGHT,
                activeforeground="white",
                font=("Segoe UI", 10, "bold"),
                padx=16,
                pady=8,
                cursor="hand2",
            ).pack(anchor="e", pady=(12, 0))

        complaint_list.bind("<<ListboxSelect>>", show_complaint_popup)
        complaint_list.bind("<Double-Button-1>", show_complaint_popup)
        c_btns = tk.Frame(complaint_body, bg=self.CARD)
        c_btns.pack(anchor="w", pady=(10, 0))

        def warn_accused():
            sel = complaint_list.curselection()
            if not sel:
                return
            result = self.db.decide_complaint(
                complaints[sel[0]]["id"], "warn_accused")
            messagebox.showinfo("Complaint", result)
            self.build_dashboard()

        def warn_filer():
            sel = complaint_list.curselection()
            if not sel:
                return
            result = self.db.decide_complaint(
                complaints[sel[0]]["id"], "warn_filer")
            messagebox.showinfo("Complaint", result)
            self.build_dashboard()

        def deregister_student():
            sel = complaint_list.curselection()
            if not sel:
                return
            result = self.db.decide_complaint(
                complaints[sel[0]]["id"], "deregister_student")
            if result.startswith("Resolved"):
                messagebox.showinfo("Complaint", result)
            else:
                messagebox.showwarning("Complaint", result)
            self.build_dashboard()

        tk.Button(c_btns, text="Warn Accused", command=warn_accused, relief="flat", bg=self.GOLD, fg=self.NAV,
                  activebackground="#c79310", activeforeground=self.NAV, font=("Segoe UI", 10, "bold"),
                  padx=14, pady=8, cursor="hand2").pack(side="left", padx=(0, 8))
        tk.Button(c_btns, text="Warn Filer", command=warn_filer, relief="flat", bg=self.NAV, fg="white",
                  activebackground=self.NAV_LIGHT, activeforeground="white", font=("Segoe UI", 10, "bold"),
                  padx=14, pady=8, cursor="hand2").pack(side="left", padx=(0, 8))
        tk.Button(c_btns, text="De-register Student", command=deregister_student, relief="flat", bg="#b14444", fg="white",
                  activebackground="#933838", activeforeground="white", font=("Segoe UI", 10, "bold"),
                  padx=14, pady=8, cursor="hand2").pack(side="left")

        setup_card, setup_body = self.make_card(
            frame, "Class Setup", "During the Setup period, the registrar can adjust instructor, meeting time, and capacity. Cancelled classes can also be reactivated here.")
        setup_card.pack(fill="x", padx=24, pady=(12, 0))
        setup_row = tk.Frame(setup_body, bg=self.CARD)
        setup_row.pack(fill="x")
        class_setup_rows = self.db.get_class_setup_rows()
        selected_setup_class_id = None
        class_setup_list = self.styled_listbox(setup_row, height=6)
        class_setup_list.pack(side="left", fill="both",
                              expand=True, padx=(0, 12))
        def refresh_setup_list(select_class_id=None):
            nonlocal class_setup_rows, selected_setup_class_id
            class_setup_rows = self.db.get_class_setup_rows()
            class_setup_list.delete(0, tk.END)
            selected_index = None
            for index, row_data in enumerate(class_setup_rows):
                cancelled_tag = "  [CANCELLED]" if row_data["cancelled"] else ""
                class_setup_list.insert(
                    tk.END,
                    f"#{row_data['id']} | {row_data['code']} {row_data['title']} | {row_data['meeting_time']} | cap {row_data['capacity']} | {row_data['instructor'] or 'TBD'}{cancelled_tag}"
                )
                if select_class_id is not None and row_data["id"] == select_class_id:
                    selected_index = index
            if selected_index is not None:
                selected_setup_class_id = select_class_id
                class_setup_list.selection_clear(0, tk.END)
                class_setup_list.selection_set(selected_index)
                class_setup_list.activate(selected_index)
                class_setup_list.see(selected_index)
                load_setup_form()

        refresh_setup_list()

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
            nonlocal selected_setup_class_id
            sel = class_setup_list.curselection()
            if not sel:
                return
            class_row = class_setup_rows[sel[0]]
            selected_setup_class_id = class_row["id"]
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
            nonlocal class_setup_rows, selected_setup_class_id
            if selected_setup_class_id is None:
                messagebox.showerror(
                    "Missing class", "Please select a class to update."
                )
                return
            target = next(
                (row for row in class_setup_rows if row["id"] == selected_setup_class_id),
                None,
            )
            if target is None:
                messagebox.showerror(
                    "Missing class", "The selected class could not be found."
                )
                return
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
            if result == "Class setup updated.":
                refresh_setup_list(target["id"])
                self.show_page("Dashboard", "Dashboard")

        tk.Button(setup_form, text="Save Class Setup", command=save_setup, relief="flat", bg=self.GOLD, fg=self.NAV,
                  activebackground="#c79310", activeforeground=self.NAV, font=("Segoe UI", 10, "bold"),
                  padx=16, pady=8, cursor="hand2").pack(anchor="w", pady=(4, 0))

        def reactivate_selected_class():
            nonlocal selected_setup_class_id
            sel = class_setup_list.curselection()
            if not sel:
                messagebox.showerror(
                    "Missing class",
                    "Please select a class from the list to reactivate."
                )
                return
            target = class_setup_rows[sel[0]]
            if not target["cancelled"]:
                messagebox.showinfo(
                    "Already active",
                    f"{target['code']} {target['title']} is already active — nothing to reactivate."
                )
                return
            result = self.db.reactivate_class(target["id"])
            messagebox.showinfo("Reactivate Class", result)
            if result.startswith("Class reactivated"):
                refresh_setup_list(target["id"])

        # Only show the Reactivate button when the system is in the Setup
        # period — that's the only time reactivation is permitted by spec.
        if self.db.get_current_period() == "Setup":
            tk.Button(
                setup_form,
                text="Reactivate Selected Class",
                command=reactivate_selected_class,
                relief="flat",
                bg=self.SUCCESS,
                fg="white",
                activebackground="#166b3a",
                activeforeground="white",
                font=("Segoe UI", 10, "bold"),
                padx=16,
                pady=8,
                cursor="hand2",
            ).pack(anchor="w", pady=(8, 0))
            tk.Label(
                setup_form,
                text="Cancelled classes are tagged [CANCELLED] in the list.",
                bg=self.CARD,
                fg=self.MUTED,
                font=("Segoe UI", 9),
                justify="left",
                wraplength=320,
            ).pack(anchor="w", pady=(6, 0))
        else:
            tk.Label(
                setup_form,
                text="To reactivate a cancelled class, switch to the Setup period.",
                bg=self.CARD,
                fg=self.MUTED,
                font=("Segoe UI", 9),
                justify="left",
                wraplength=320,
            ).pack(anchor="w", pady=(8, 0))

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

        note_box = tk.Text(grad_body, height=3, relief="solid",
                           bd=1, font=("Segoe UI", 10))
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

        fine_card, fine_body = self.make_card(
            frame,
            "Student Fines",
            "View suspension fines and payment status."
        )
        fine_card.pack(fill="x", padx=24, pady=(12, 0))

        all_fines = self.db.get_all_fines()
        fine_list = self.styled_listbox(fine_body, height=6)
        fine_list.pack(fill="x")

        if all_fines:
            for f in all_fines:
                status = "Paid" if f["paid"] else "Unpaid"
                fine_list.insert(
                    tk.END,
                    f"#{f['id']} | {f['full_name']} ({f['username']}) | ${f['amount']} | {status} | {f['reason']}"
                )
        else:
            fine_list.insert(tk.END, "No fines found.")

        grade_review_card, grade_review_body = self.make_card(
            frame,
            "Instructor GPA Reviews",
            "During and after grading, class GPA outliers are routed here for registrar review."
        )
        grade_review_card.pack(fill="x", padx=24, pady=(12, 0))

        grade_reviews = self.db.get_instructor_grade_reviews()
        grade_review_list = self.styled_listbox(grade_review_body, height=6)
        grade_review_list.pack(fill="x")
        for review in grade_reviews:
            grade_review_list.insert(
                tk.END,
                f"#{review['id']} | {review['instructor_name']} | {review['code']} {review['title']} | GPA {review['class_gpa']} | {review['concern']} | {review['status']}"
            )

        tk.Label(
            grade_review_body,
            text="Registrar Justification / Decision Note",
            bg=self.CARD,
            fg=self.TEXT,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(10, 4))
        grade_review_note = tk.Text(
            grade_review_body, height=3, relief="solid", bd=1, font=("Segoe UI", 10)
        )
        grade_review_note.pack(fill="x")

        def show_grade_review_popup(_event=None):
            sel = grade_review_list.curselection()
            if not sel:
                return
            review = grade_reviews[sel[0]]
            top = tk.Toplevel(self.root)
            top.title(f"Instructor GPA Review #{review['id']}")
            top.geometry("560x320")
            top.configure(bg=self.BG)
            top.transient(self.root)

            card, body = self.make_card(
                top,
                f"Instructor GPA Review #{review['id']}",
                f"{review['instructor_name']} | {review['code']} {review['title']} | GPA {review['class_gpa']} | {review['status']}",
            )
            card.pack(fill="both", expand=True, padx=18, pady=18)

            tk.Label(
                body,
                text=f"Concern: {review['concern']}",
                bg=self.CARD,
                fg=self.DANGER if review["concern"] == "Low class GPA" else self.NAV_DARK,
                font=("Segoe UI", 11, "bold"),
            ).pack(anchor="w")

            tk.Label(
                body,
                text=("Registrar review required. Accept a justification, issue a warning, "
                      "or fire the instructor if the explanation is not adequate."),
                bg=self.CARD,
                fg=self.TEXT,
                font=("Segoe UI", 10),
                wraplength=480,
                justify="left",
            ).pack(anchor="w", pady=(8, 10))

            detail_box = tk.Text(
                body, height=8, relief="solid", bd=1, font=("Segoe UI", 10), wrap="word"
            )
            detail_box.pack(fill="both", expand=True)
            detail_box.insert(
                "1.0",
                review["justification"] or "No registrar justification has been recorded yet."
            )
            detail_box.configure(state="disabled")

            tk.Button(
                body,
                text="Close",
                command=top.destroy,
                relief="flat",
                bg=self.NAV,
                fg="white",
                activebackground=self.NAV_LIGHT,
                activeforeground="white",
                font=("Segoe UI", 10, "bold"),
                padx=16,
                pady=8,
                cursor="hand2",
            ).pack(anchor="e", pady=(12, 0))

        grade_review_list.bind("<<ListboxSelect>>", show_grade_review_popup)
        grade_review_list.bind("<Double-Button-1>", show_grade_review_popup)

        grade_review_btns = tk.Frame(grade_review_body, bg=self.CARD)
        grade_review_btns.pack(anchor="w", pady=(10, 0))

        def resolve_grade_review(action):
            sel = grade_review_list.curselection()
            if not sel:
                return
            result = self.db.decide_instructor_grade_review(
                grade_reviews[sel[0]]["id"],
                action,
                grade_review_note.get("1.0", tk.END)
            )
            messagebox.showinfo("Instructor GPA Review", result)
            self.build_dashboard()

        tk.Button(
            grade_review_btns,
            text="Accept Justification",
            command=lambda: resolve_grade_review("justify"),
            relief="flat",
            bg=self.SUCCESS,
            fg="white",
            activebackground="#166b3a",
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=8,
            cursor="hand2",
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            grade_review_btns,
            text="Warn Instructor",
            command=lambda: resolve_grade_review("warn"),
            relief="flat",
            bg=self.GOLD,
            fg=self.NAV,
            activebackground="#c79310",
            activeforeground=self.NAV,
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=8,
            cursor="hand2",
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            grade_review_btns,
            text="Fire Instructor",
            command=lambda: resolve_grade_review("fire"),
            relief="flat",
            bg=self.DANGER,
            fg="white",
            activebackground="#a73a2f",
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=8,
            cursor="hand2",
        ).pack(side="left")

        ai_card = self.build_ai_panel(
            frame, self.current_user, "Registrar Management Assistant")
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

        registrations = self.db.get_student_registrations(self.current_user["id"])
        class_status = {}
        for registration in registrations:
            class_status[registration["class_id"]] = (
                "Completed" if registration["grade"] else "Enrolled"
            )

        classes = self.db.get_available_classes()
        class_list = self.styled_listbox(class_body, height=11)
        class_list.pack(fill="both", expand=True)
        for c in classes:
            status_note = ""
            if c["id"] in class_status:
                status_note = f" | {class_status[c['id']]}"
            class_list.insert(
                tk.END, f"#{c['id']}  |  {c['code']} {c['title']}  |  {c['meeting_time']}  |  {c['enrolled']}/{c['capacity']}  |  {c['period_state']}{status_note}")

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
        for r in registrations:
            reg_list.insert(
                tk.END, f"#{r['class_id']}  |  {r['code']} {r['title']}  |  {r['meeting_time']}  |  Grade: {r['grade'] or 'N/A'}")

        def unenroll():
            sel = reg_list.curselection()
            if not sel:
                messagebox.showerror(
                    "Missing class", "Select a class from My Classes first."
                )
                return
            msg = self.db.unenroll_student(
                self.current_user["id"], registrations[sel[0]]["class_id"]
            )
            messagebox.showinfo("Unenroll", msg)
            self.build_dashboard()

        tk.Button(my_body, text="Unenroll Selected Class", command=unenroll, relief="flat", bg=self.DANGER, fg="white",
                  activebackground="#a73a2f", activeforeground="white", font=("Segoe UI", 10, "bold"),
                  padx=16, pady=8, cursor="hand2").pack(anchor="w", pady=(10, 0))

        self.build_student_planner_card(row)

        fine_card, fine_body = self.make_card(
            row,
            "My Fines",
            "Students with 3 warnings must pay a fine to the registrar."
        )
        fine_card.pack(fill="x", pady=(16, 0))

        fines = [f for f in self.db.get_user_fines(self.current_user["id"]) if not f["paid"]]
        fine_list = self.styled_listbox(fine_body, height=5)
        fine_list.pack(fill="x")

        if fines:
            for f in fines:
                fine_list.insert(
                    tk.END,
                    f"#{f['id']} | ${f['amount']} | Unpaid | {f['reason']}"
                )
        else:
            fine_list.insert(tk.END, "No unpaid fines found.")

        def pay_my_fines():
            msg = self.db.pay_fine(self.current_user["id"])
            messagebox.showinfo("Fine Payment", msg)
            self.build_dashboard()

        tk.Button(
            fine_body,
            text="Pay Unpaid Fines",
            command=pay_my_fines,
            relief="flat",
            bg=self.GOLD,
            fg=self.NAV,
            font=("Segoe UI", 10, "bold"),
            padx=16,
            pady=8,
            cursor="hand2"
        ).pack(anchor="w", pady=(10, 0))

        student_summary = self.db.get_user_summary(self.current_user["id"])
        if (student_summary["overall_gpa"] or 0) >= 3.7:
            dean_label = tk.Label(
                row,
                text="🏆 Dean's List Student",
                bg="#fff3cd",
                fg="#7a5c00",
                font=("Segoe UI", 12, "bold"),
                padx=18,
                pady=10
            )
            dean_label.pack(fill="x", pady=(14, 0))

        ai_card = self.build_ai_panel(
            frame, self.current_user, "Student Academic Assistant")
        ai_card.pack(fill="both", expand=False, padx=24, pady=(12, 0))

    def build_instructor_dashboard(self, frame):
        # Suspended-instructor banner: per spec, an instructor with 3 warnings
        # or whose every class was cancelled is suspended and cannot teach
        # next semester. Surface that as a prominent, unmissable banner so
        # the instructor is not confused about their account state.
        summary = self.db.get_user_summary(self.current_user["id"])
        if summary and summary["suspended"]:
            banner = tk.Frame(frame, bg=self.DANGER, bd=0, highlightthickness=2,
                              highlightbackground="#7a1d2f")
            banner.pack(fill="x", padx=24, pady=(0, 12))
            inner = tk.Frame(banner, bg=self.DANGER)
            inner.pack(fill="x", padx=18, pady=14)
            tk.Label(
                inner,
                text="ACCOUNT SUSPENDED",
                bg=self.DANGER,
                fg="white",
                font=("Segoe UI", 18, "bold"),
            ).pack(anchor="w")
            tk.Label(
                inner,
                text="YOU CAN'T TEACH NEXT SEMESTER",
                bg=self.DANGER,
                fg="#fff1a8",
                font=("Segoe UI", 16, "bold"),
            ).pack(anchor="w", pady=(6, 0))
            tk.Label(
                inner,
                text=("Your instructor account "
                      "has been suspended due to accumulated warnings or all of "
                      "your classes being cancelled. Please contact the "
                      "registrar to discuss your status."),
                bg=self.DANGER,
                fg="white",
                font=("Segoe UI", 11, "bold"),
                wraplength=900,
                justify="left",
            ).pack(anchor="w", pady=(6, 0))
            tk.Label(
                inner,
                text=f"Current warnings on record: {summary['warnings']}",
                bg=self.DANGER,
                fg="#ffe0e0",
                font=("Segoe UI", 10),
            ).pack(anchor="w", pady=(8, 0))

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
            extra, self.current_user, "Instructor Teaching Assistant")
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
            sel_class = class_list.curselection()
            target_text = complaint_target_var.get()
            detail = instructor_complaint_text.get("1.0", tk.END).strip()
            if not sel_class or not target_text or not detail:
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
            selected_class = classes[sel_class[0]]
            self.db.file_complaint(
                self.current_user["id"],
                target["student_id"],
                detail,
                "Instructor Report",
                selected_class["id"],
            )
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
