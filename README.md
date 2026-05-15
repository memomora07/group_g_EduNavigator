# College0 — AI-Enabled College Management System

## Overview

College0 is a local college management system built with Python, Tkinter, and SQLite.

The project simulates how a college manages:

* students
* instructors
* registrars
* course registration
* grading
* complaints
* reviews
* graduation
* semester workflows

The system also includes a local AI assistant that answers questions about the college system.

---

# Features

## Visitor Features

* View top students and class rankings
* Apply as a student or instructor
* Ask general questions using the AI assistant

## Student Features

* Register for classes
* Join waitlists
* Submit reviews
* File complaints
* Apply for graduation
* View grades and GPA

## Instructor Features

* View assigned classes
* View student records
* Admit waitlisted students
* Assign grades

## Registrar Features

* Approve/reject applications
* Manage semester periods
* Handle complaints
* Review instructor GPA reports
* Manage warnings, suspensions, and fines

---

# AI Assistant

The system includes a local AI assistant that:

* answers questions using information stored in the database,
* gives role-based responses,
* and supports college-specific knowledge not available in general LLMs.

---

# Technologies Used

* Python
* Tkinter
* SQLite

---

# How to Run

```bash id="9k9j4f"
python college0_ccny_gui.py
```

---

# Demo Accounts

## Registrar

Username:

```bash id="h4fc02"
registrar
```

Password:

```bash id="d6h1tp"
admin123
```

## Student

Username:

```bash id="hl6pn0"
s1001
```

Password:

```bash id="3k6thw"
temp123
```

## Instructor

Username:

```bash id="8zhh7l"
i2001
```

Password:

```bash id="q7t2vh"
teach123
```

---

# Main Features Implemented

* Semester lifecycle system
* Registration + waitlists
* GPA and warning system
* Review moderation with taboo words
* Graduation workflow
* Complaint system
* AI assistant
* Role-based dashboards

---

# Notes

* Built as a local desktop GUI application
* Designed for educational/demo purposes
* Uses one consistent GUI window

