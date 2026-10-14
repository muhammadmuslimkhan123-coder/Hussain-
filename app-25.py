import streamlit as st
import sqlite3
import hashlib
from datetime import date, datetime
from pathlib import Path
import pandas as pd

# ============================================================
# Government Girls High School Sial - Smart Education Portal
# Created by Masooma Batool
# Python-only application code using Streamlit + SQLite.
# The school-building photo below is illustrative, not verified
# as an official photo of this exact school.
# ============================================================

APP_TITLE = "Government Girls High School Sial"
DB_PATH = Path("school_lms.db")
BUILDING_IMAGE = "https://images.unsplash.com/photo-1580582932707-520aed937b7b?auto=format&fit=crop&w=1600&q=85"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------- Database helpers ----------------------
def connect_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def init_db():
    with connect_db() as conn:
        cur = conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            guardian_name TEXT,
            class_section TEXT NOT NULL,
            roll_no TEXT,
            phone TEXT,
            fee_status TEXT DEFAULT 'Unpaid'
        );
        CREATE TABLE IF NOT EXISTS attendance(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            attendance_date TEXT NOT NULL,
            status TEXT NOT NULL,
            subject TEXT DEFAULT '',
            FOREIGN KEY(student_id) REFERENCES students(id)
        );
        CREATE TABLE IF NOT EXISTS results(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            exam_name TEXT NOT NULL,
            subject TEXT NOT NULL,
            marks REAL NOT NULL,
            total_marks REAL NOT NULL,
            exam_date TEXT NOT NULL,
            FOREIGN KEY(student_id) REFERENCES students(id)
        );
        CREATE TABLE IF NOT EXISTS assignments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            class_section TEXT NOT NULL,
            subject TEXT NOT NULL,
            due_date TEXT NOT NULL,
            details TEXT DEFAULT '',
            teacher_name TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS submissions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id INTEGER NOT NULL,
            student_name TEXT NOT NULL,
            answer_text TEXT NOT NULL,
            submitted_at TEXT NOT NULL,
            status TEXT DEFAULT 'Submitted',
            feedback TEXT DEFAULT '',
            FOREIGN KEY(assignment_id) REFERENCES assignments(id)
        );
        CREATE TABLE IF NOT EXISTS quizzes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            class_section TEXT NOT NULL,
            subject TEXT NOT NULL,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_option TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS quiz_attempts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            student_name TEXT NOT NULL,
            selected_option TEXT NOT NULL,
            score INTEGER NOT NULL,
            attempted_at TEXT NOT NULL,
            FOREIGN KEY(quiz_id) REFERENCES quizzes(id)
        );
        CREATE TABLE IF NOT EXISTS fees(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            paid_date TEXT DEFAULT '',
            FOREIGN KEY(student_id) REFERENCES students(id)
        );
        CREATE TABLE IF NOT EXISTS lectures(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            class_section TEXT NOT NULL,
            subject TEXT NOT NULL,
            video_url TEXT NOT NULL,
            notes TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS library(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_title TEXT NOT NULL,
            author TEXT DEFAULT '',
            subject TEXT DEFAULT '',
            available INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS notices(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            notice_date TEXT NOT NULL,
            category TEXT DEFAULT 'General'
        );
        CREATE TABLE IF NOT EXISTS timetable(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_section TEXT NOT NULL,
            day_name TEXT NOT NULL,
            period TEXT NOT NULL,
            subject TEXT NOT NULL,
            teacher_name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_title TEXT NOT NULL,
            event_date TEXT NOT NULL,
            details TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            recipient TEXT DEFAULT 'Admin',
            message TEXT NOT NULL,
            sent_at TEXT NOT NULL
        );
        """)

        # Demo accounts are created only when missing. Change passwords before real use.
        demo_users = [
            ("admin", "Admin@123", "Admin", "School Administrator"),
            ("principal", "Principal@123", "Principal", "Lubaba Batool (Demo Principal)"),
            ("teacher", "Teacher@123", "Teacher", "Ayesha Noor (Sample Teacher)"),
            ("student", "Student@123", "Student", "Demo Student"),
            ("parent", "Parent@123", "Parent", "Demo Parent/Guardian"),
        ]
        for username, password, role, full_name in demo_users:
            cur.execute(
                "INSERT OR IGNORE INTO users(username,password_hash,role,full_name) VALUES(?,?,?,?)",
                (username, hash_password(password), role, full_name)
            )

        # Seed clearly fictional/sample teacher records are shown in the Staff section.
        # Add one example student, notice, book and lecture only if the database is empty.
        cur.execute("SELECT COUNT(*) FROM students")
        if cur.fetchone()[0] == 0:
            cur.execute(
                "INSERT INTO students(student_name,guardian_name,class_section,roll_no,phone,fee_status) VALUES(?,?,?,?,?,?)",
                ("Demo Student", "Demo Guardian", "6-A", "6001", "", "Unpaid")
            )
        cur.execute("SELECT COUNT(*) FROM notices")
        if cur.fetchone()[0] == 0:
            cur.execute(
                "INSERT INTO notices(title,message,notice_date,category) VALUES(?,?,?,?)",
                ("Welcome to the LMS", "This is a sample notice. Admin can add official school notices.", str(date.today()), "General")
            )
        cur.execute("SELECT COUNT(*) FROM library")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO library(book_title,author,subject,available) VALUES(?,?,?,1)",
                        ("General Science - Sample Record", "School Library", "Science"))
        cur.execute("SELECT COUNT(*) FROM lectures")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO lectures(title,class_section,subject,video_url,notes) VALUES(?,?,?,?,?)",
                        ("Sample Science Lecture", "6-A", "Science", "https://www.youtube.com/", "Replace with an approved lecture link."))

init_db()

def query_df(sql, params=()):
    with connect_db() as conn:
        return pd.read_sql_query(sql, conn, params=params)

def execute(sql, params=()):
    with connect_db() as conn:
        conn.execute(sql, params)
        conn.commit()

def get_students():
    return query_df("SELECT * FROM students ORDER BY class_section, roll_no")

def class_options():
    return [f"{grade}-{section}" for grade in range(6, 11) for section in "ABC"]

def login(username, password):
    rows = query_df(
        "SELECT username, role, full_name FROM users WHERE username=? AND password_hash=?",
        (username, hash_password(password))
    )
    return rows.iloc[0].to_dict() if not rows.empty else None

# ---------------------- Styling ----------------------
st.markdown("""
<style>
    .stApp { background-color: #fffafa; }
    [data-testid="stSidebar"] { background-color: #7d1724; }
    [data-testid="stSidebar"] * { color: white !important; }
    .hero-title { color: #8b1525; font-size: 2.1rem; font-weight: 800; }
    .hero-subtitle { color: #444; font-size: 1.05rem; }
    div[data-testid="stMetric"] {
        background: #fff0f1; border: 1px solid #efc5cb;
        padding: 12px; border-radius: 12px;
    }
    .small-note { color: #666; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# ---------------------- Header / school gate banner ----------------------
st.markdown(
    '<div style="background:#8b1525;color:white;text-align:center;padding:18px;border-radius:12px;'
    'border:5px solid #e5c5a1;">'
    '<div style="font-size:0.95rem;letter-spacing:2px;">GOVERNMENT OF THE PUNJAB</div>'
    '<div style="font-size:2rem;font-weight:900;">GOVT. GIRLS HIGH SCHOOL SIAL</div>'
    '<div style="font-size:0.95rem;">LEARN • LEAD • SUCCEED</div></div>',
    unsafe_allow_html=True
)
st.caption("Education & Learning Management System | Web application created by Masooma Batool")

with st.expander("School building image"):
    st.image(BUILDING_IMAGE, use_container_width=True, caption="Illustrative school-building photo. This is not verified as the actual Government Girls High School Sial building.")
    st.markdown("Official school-building photo can be substituted here when the school provides a verified image.")

# ---------------------- Login ----------------------
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    left, right = st.columns([1.25, 1])
    with left:
        st.markdown('<div class="hero-title">Welcome to Smart School Portal</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-subtitle">One place for classes, attendance, quizzes, assignments, results, fees and school notices.</div>', unsafe_allow_html=True)
        st.image(BUILDING_IMAGE, use_container_width=True)
        st.info("For demonstration, the school photo is illustrative. Use an official photo before publishing.")
    with right:
        st.subheader("🔐 Secure Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
        if submitted:
            user = login(username.strip(), password)
            if user:
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Incorrect username or password.")
        with st.expander("Demo login accounts"):
            st.write("Admin: `admin` / `Admin@123`")
            st.write("Principal: `principal` / `Principal@123`")
            st.write("Teacher: `teacher` / `Teacher@123`")
            st.write("Student: `student` / `Student@123`")
            st.write("Parent: `parent` / `Parent@123`")
            st.warning("These are demo passwords. Change them and add proper security before real deployment.")
    st.stop()

user = st.session_state.user
role = user["role"]
st.sidebar.title("🎓 School Portal")
st.sidebar.write(f"**User:** {user['full_name']}")
st.sidebar.write(f"**Role:** {role}")
if st.sidebar.button("Logout", use_container_width=True):
    st.session_state.user = None
    st.rerun()

pages = [
    "Dashboard", "Staff & Classes", "Students", "Online Quiz & Exams",
    "Assignments", "Attendance", "Results & Report Cards", "Fee Management",
    "Video Lectures", "Digital Library", "Notifications", "Timetable & Date Sheet",
    "AI Study Assistant", "Reports & Analytics", "School Notices & Events",
    "Parent Portal", "Messages"
]
page = st.sidebar.radio("Navigation", pages)

# ---------------------- Dashboard ----------------------
if page == "Dashboard":
    st.title(f"{role} Dashboard")
    students_df = get_students()
    total_students = len(students_df)
    total_assignments = int(query_df("SELECT COUNT(*) AS n FROM assignments").iloc[0]["n"])
    total_notices = int(query_df("SELECT COUNT(*) AS n FROM notices").iloc[0]["n"])
    total_books = int(query_df("SELECT COUNT(*) AS n FROM library").iloc[0]["n"])
    a, b, c, d = st.columns(4)
    a.metric("Students", total_students)
    b.metric("Assignments", total_assignments)
    c.metric("Notices", total_notices)
    d.metric("Library Books", total_books)
    st.subheader("Quick access")
    st.write("Use the menu to manage attendance, exams, assignments, fees, lectures and notices.")
    st.subheader("Latest notices")
    notices = query_df("SELECT title,message,notice_date,category FROM notices ORDER BY id DESC LIMIT 5")
    if notices.empty:
        st.info("No notices available.")
    else:
        st.dataframe(notices, use_container_width=True, hide_index=True)
    st.subheader("School details")
    st.write("**School:** Government Girls High School Sial")
    st.write("**Principal:** Lubaba Batool (sample project setting; confirm before official use)")
    st.write("**Sections:** Classes 6 to 10, Sections A, B and C")
    st.write("**Project:** Created by Masooma Batool")

# ---------------------- Staff & Classes ----------------------
elif page == "Staff & Classes":
    st.title("Staff & Classes")
    st.warning("The staff names below are fictional sample names for the project, not verified school employees. Replace them with approved staff records.")
    staff = pd.DataFrame([
        ["Lubaba Batool", "Principal", "School leadership and administration"],
        ["Ayesha Noor", "English Teacher", "Classes 6-A, 7-A"],
        ["Sana Iqbal", "Mathematics Teacher", "Classes 6-B, 8-A"],
        ["Hira Fatima", "Science Teacher", "Classes 6-C, 7-B"],
        ["Nadia Akram", "Urdu Teacher", "Classes 7-C, 8-B"],
        ["Maham Khalid", "Computer Teacher", "Classes 8-C, 9-A"],
        ["Farah Riaz", "Physics Teacher", "Classes 9-B, 10-A"],
        ["Sadia Bibi", "Chemistry Teacher", "Classes 9-C, 10-B"],
        ["Kiran Shah", "Biology Teacher", "Classes 10-C, 9-A"],
        ["Rabia Aslam", "Islamiat Teacher", "Classes 6-A, 8-A"],
        ["Mehwish Tariq", "Pakistan Studies Teacher", "Classes 9-B, 10-A"],
        ["Shazia Parveen", "General Teacher", "Classes 6-B, 7-A"],
        ["Amna Yousaf", "General Teacher", "Classes 6-C, 8-B"],
        ["Bushra Ahmed", "General Teacher", "Classes 7-B, 9-C"],
        ["Komal Rani", "General Teacher", "Classes 7-C, 10-B"],
        ["Uzma Javed", "General Teacher", "Classes 8-C, 10-C"],
        ["Noreen Akhtar", "Library In-charge", "Library catalogue and book records"],
        ["Saira Bano", "Clerk", "Student records and fee registers"],
        ["Shabana Kausar", "Peon", "Office support and school errands"],
        ["Rukhsana Bibi", "Peon", "Classroom and campus support"],
    ], columns=["Staff Name (Sample)", "Role", "Assigned Work"])
    st.dataframe(staff, use_container_width=True, hide_index=True)
    st.subheader("Class / Section list")
    st.write(", ".join(class_options()))
    st.write("Project campus assumptions: 18 classrooms and 2 main gates.")
    st.caption("Staff assignments are demonstration data and should be reviewed by school administration.")

# ---------------------- Students ----------------------
elif page == "Students":
    st.title("Student Management")
    if role in ["Admin", "Principal", "Teacher"]:
        with st.expander("➕ Add student"):
            with st.form("add_student_form"):
                name = st.text_input("Student name")
                guardian = st.text_input("Parent / guardian name")
                cls = st.selectbox("Class / section", class_options())
                roll = st.text_input("Roll number")
                phone = st.text_input("Contact number (optional)")
                add_student = st.form_submit_button("Save student")
            if add_student:
                if name.strip():
                    try:
                        execute("INSERT INTO students(student_name,guardian_name,class_section,roll_no,phone) VALUES(?,?,?,?,?)",
                                (name.strip(), guardian.strip(), cls, roll.strip(), phone.strip()))
                        st.success("Student added.")
                        st.rerun()
                    except sqlite3.Error as e:
                        st.error(f"Could not save student: {e}")
                else:
                    st.error("Please enter the student name.")
    students = get_students()
    st.dataframe(students, use_container_width=True, hide_index=True)
    if role in ["Admin", "Principal"]:
        st.subheader("Remove student")
        if not students.empty:
            selected = st.selectbox("Select student", students["id"].tolist(), format_func=lambda x: f"ID {x}: {students.loc[students.id == x, 'student_name'].iloc[0]}")
            if st.button("Delete selected student"):
                execute("DELETE FROM students WHERE id=?", (int(selected),))
                st.warning("Student record deleted.")
                st.rerun()

# ---------------------- Quiz and exams ----------------------
elif page == "Online Quiz & Exams":
    st.title("Online Quiz & Exam System")
    if role in ["Admin", "Principal", "Teacher"]:
        with st.expander("Create MCQ quiz"):
            with st.form("quiz_create"):
                title = st.text_input("Quiz title")
                cls = st.selectbox("Class / section", class_options(), key="quiz_cls")
                subject = st.text_input("Subject")
                question = st.text_area("Question")
                oa = st.text_input("Option A")
                ob = st.text_input("Option B")
                oc = st.text_input("Option C")
                od = st.text_input("Option D")
                correct = st.selectbox("Correct option", ["A", "B", "C", "D"])
                save_quiz = st.form_submit_button("Save quiz")
            if save_quiz:
                if all(x.strip() for x in [title, subject, question, oa, ob, oc, od]):
                    execute("""INSERT INTO quizzes(title,class_section,subject,question,option_a,option_b,option_c,option_d,correct_option)
                               VALUES(?,?,?,?,?,?,?,?,?)""", (title, cls, subject, question, oa, ob, oc, od, correct))
                    st.success("Quiz saved.")
                    st.rerun()
                else:
                    st.error("Please fill in all quiz fields.")
    quizzes = query_df("SELECT * FROM quizzes ORDER BY id DESC")
    if quizzes.empty:
        st.info("No quizzes yet. A teacher or admin can create one.")
    else:
        quiz_ids = quizzes["id"].tolist()
        qid = st.selectbox("Choose a quiz", quiz_ids, format_func=lambda x: f"{quizzes.loc[quizzes.id == x, 'title'].iloc[0]} ({quizzes.loc[quizzes.id == x, 'class_section'].iloc[0]})")
        q = query_df("SELECT * FROM quizzes WHERE id=?", (int(qid),)).iloc[0]
        st.subheader(q["title"])
        st.caption(f"{q['subject']} • {q['class_section']}")
        st.write(q["question"])
        chosen = st.radio("Choose answer", ["A", "B", "C", "D"], format_func=lambda x: f"{x}. {q['option_' + x.lower()]}", key=f"answer_{qid}")
        student_name = st.text_input("Student name for attempt", value=user["full_name"] if role == "Student" else "", key=f"student_name_{qid}")
        if st.button("Submit quiz", key=f"submit_{qid}"):
            if student_name.strip():
                score = 1 if chosen == q["correct_option"] else 0
                execute("INSERT INTO quiz_attempts(quiz_id,student_name,selected_option,score,attempted_at) VALUES(?,?,?,?,?)",
                        (int(qid), student_name.strip(), chosen, score, datetime.now().isoformat(timespec="seconds")))
                st.success(f"Quiz submitted. Score: {score}/1")
            else:
                st.error("Enter the student name.")
    if role in ["Admin", "Principal", "Teacher"]:
        st.subheader("Quiz attempts")
        st.dataframe(query_df("SELECT quiz_id,student_name,selected_option,score,attempted_at FROM quiz_attempts ORDER BY id DESC"),
                     use_container_width=True, hide_index=True)

# ---------------------- Assignments ----------------------
elif page == "Assignments":
    st.title("Assignment Submission System")
    if role in ["Admin", "Principal", "Teacher"]:
        with st.expander("Create assignment"):
            with st.form("assignment_form"):
                atitle = st.text_input("Assignment title")
                aclass = st.selectbox("Class / section", class_options(), key="assignment_class")
                asubject = st.text_input("Subject", key="assignment_subject")
                due = st.date_input("Due date", value=date.today())
                details = st.text_area("Instructions")
                teacher_name = st.text_input("Teacher name", value=user["full_name"])
                create = st.form_submit_button("Publish assignment")
            if create:
                if atitle.strip() and asubject.strip():
                    execute("INSERT INTO assignments(title,class_section,subject,due_date,details,teacher_name) VALUES(?,?,?,?,?,?)",
                            (atitle.strip(), aclass, asubject.strip(), str(due), details.strip(), teacher_name.strip()))
                    st.success("Assignment published.")
                    st.rerun()
                else:
                    st.error("Title and subject are required.")
    assignments = query_df("SELECT * FROM assignments ORDER BY due_date")
    if assignments.empty:
        st.info("No assignments have been published.")
    else:
        st.dataframe(assignments.drop(columns=["id"]), use_container_width=True, hide_index=True)
        aid = st.selectbox("Select assignment to submit", assignments["id"].tolist(),
                           format_func=lambda x: f"{assignments.loc[assignments.id == x, 'title'].iloc[0]} — {assignments.loc[assignments.id == x, 'class_section'].iloc[0]}")
        with st.form("submission_form"):
            sname = st.text_input("Student name", value=user["full_name"] if role == "Student" else "")
            answer = st.text_area("Answer / submission text")
            submit_assignment = st.form_submit_button("Submit assignment")
        if submit_assignment:
            if sname.strip() and answer.strip():
                execute("INSERT INTO submissions(assignment_id,student_name,answer_text,submitted_at) VALUES(?,?,?,?)",
                        (int(aid), sname.strip(), answer.strip(), datetime.now().isoformat(timespec="seconds")))
                st.success("Assignment submitted.")
            else:
                st.error("Enter student name and answer.")
    if role in ["Admin", "Principal", "Teacher"]:
        st.subheader("Submissions")
        st.dataframe(query_df("SELECT * FROM submissions ORDER BY id DESC"), use_container_width=True, hide_index=True)

# ---------------------- Attendance ----------------------
elif page == "Attendance":
    st.title("Attendance Management")
    students = get_students()
    if students.empty:
        st.info("Add students first.")
    else:
        with st.form("attendance_form"):
            sid = st.selectbox("Student", students["id"].tolist(),
                               format_func=lambda x: f"{students.loc[students.id == x, 'student_name'].iloc[0]} — {students.loc[students.id == x, 'class_section'].iloc[0]}")
            att_date = st.date_input("Date", value=date.today())
            subject = st.text_input("Subject (optional)")
            status = st.selectbox("Attendance", ["Present", "Absent", "Leave"])
            save_att = st.form_submit_button("Save attendance")
        if save_att:
            execute("INSERT INTO attendance(student_id,attendance_date,status,subject) VALUES(?,?,?,?)",
                    (int(sid), str(att_date), status, subject.strip()))
            st.success("Attendance saved.")
    st.subheader("Attendance records")
    st.dataframe(query_df("""SELECT attendance.id, students.student_name, students.class_section,
                                    attendance.attendance_date, attendance.subject, attendance.status
                             FROM attendance JOIN students ON students.id=attendance.student_id
                             ORDER BY attendance.attendance_date DESC"""),
                 use_container_width=True, hide_index=True)

# ---------------------- Results ----------------------
elif page == "Results & Report Cards":
    st.title("Results & Report Cards")
    students = get_students()
    if students.empty:
        st.info("Add students first.")
    elif role in ["Admin", "Principal", "Teacher"]:
        with st.form("result_form"):
            sid = st.selectbox("Student", students["id"].tolist(),
                               format_func=lambda x: f"{students.loc[students.id == x, 'student_name'].iloc[0]} — {students.loc[students.id == x, 'class_section'].iloc[0]}")
            exam = st.text_input("Exam name")
            subject = st.text_input("Subject")
            marks = st.number_input("Marks obtained", min_value=0.0, value=0.0)
            total = st.number_input("Total marks", min_value=1.0, value=100.0)
            exam_date = st.date_input("Exam date", value=date.today())
            save_result = st.form_submit_button("Save result")
        if save_result:
            if marks <= total and exam.strip() and subject.strip():
                execute("INSERT INTO results(student_id,exam_name,subject,marks,total_marks,exam_date) VALUES(?,?,?,?,?,?)",
                        (int(sid), exam.strip(), subject.strip(), marks, total, str(exam_date)))
                st.success("Result saved.")
            else:
                st.error("Enter exam and subject; marks obtained must not exceed total marks.")
    results = query_df("""SELECT students.student_name, students.class_section, results.exam_name,
                                 results.subject, results.marks, results.total_marks, results.exam_date
                          FROM results JOIN students ON students.id=results.student_id
                          ORDER BY results.exam_date DESC""")
    if not results.empty:
        results["Percentage"] = (results["marks"] / results["total_marks"] * 100).round(2)
    st.dataframe(results, use_container_width=True, hide_index=True)
    if not results.empty:
        st.download_button("Download results as CSV", results.to_csv(index=False).encode("utf-8"),
                           file_name="school_results.csv", mime="text/csv")

# ---------------------- Fees ----------------------
elif page == "Fee Management":
    st.title("Fee Management")
    students = get_students()
    if students.empty:
        st.info("Add students first.")
    else:
        with st.expander("Add fee record"):
            with st.form("fee_form"):
                sid = st.selectbox("Student", students["id"].tolist(),
                                   format_func=lambda x: f"{students.loc[students.id == x, 'student_name'].iloc[0]} — {students.loc[students.id == x, 'class_section'].iloc[0]}")
                month = st.text_input("Fee month (e.g. October 2026)")
                amount = st.number_input("Amount (PKR)", min_value=0.0, value=0.0)
                status = st.selectbox("Payment status", ["Unpaid", "Paid", "Concession"])
                paid_date = st.date_input("Payment date", value=date.today()) if status == "Paid" else None
                save_fee = st.form_submit_button("Save fee")
            if save_fee:
                if month.strip():
                    execute("INSERT INTO fees(student_id,month,amount,status,paid_date) VALUES(?,?,?,?,?)",
                            (int(sid), month.strip(), amount, status, str(paid_date) if paid_date else ""))
                    execute("UPDATE students SET fee_status=? WHERE id=?", (status, int(sid)))
                    st.success("Fee record saved.")
                    st.rerun()
                else:
                    st.error("Enter the fee month.")
    fees = query_df("""SELECT fees.id, students.student_name, students.class_section, fees.month,
                              fees.amount, fees.status, fees.paid_date
                       FROM fees JOIN students ON students.id=fees.student_id ORDER BY fees.id DESC""")
    st.dataframe(fees, use_container_width=True, hide_index=True)
    if not fees.empty:
        st.metric("Recorded fee amount (PKR)", f"{fees['amount'].sum():,.0f}")

# ---------------------- Video lectures ----------------------
elif page == "Video Lectures":
    st.title("Video Lectures")
    if role in ["Admin", "Principal", "Teacher"]:
        with st.expander("Add video lecture"):
            with st.form("lecture_form"):
                title = st.text_input("Lecture title")
                cls = st.selectbox("Class / section", class_options(), key="lecture_class")
                subject = st.text_input("Subject", key="lecture_subject")
                url = st.text_input("Video URL (YouTube or approved platform)")
                notes = st.text_area("Notes")
                save_lecture = st.form_submit_button("Add lecture")
            if save_lecture:
                if title.strip() and subject.strip() and url.strip():
                    execute("INSERT INTO lectures(title,class_section,subject,video_url,notes) VALUES(?,?,?,?,?)",
                            (title.strip(), cls, subject.strip(), url.strip(), notes.strip()))
                    st.success("Lecture added.")
                    st.rerun()
                else:
                    st.error("Title, subject and video URL are required.")
    lectures = query_df("SELECT * FROM lectures ORDER BY id DESC")
    if lectures.empty:
        st.info("No lectures available.")
    for _, row in lectures.iterrows():
        with st.container(border=True):
            st.subheader(row["title"])
            st.caption(f"{row['class_section']} • {row['subject']}")
            st.write(row["notes"])
            st.link_button("Open video lecture", row["video_url"])

# ---------------------- Digital library ----------------------
elif page == "Digital Library":
    st.title("Digital Library")
    if role in ["Admin", "Principal", "Teacher"]:
        with st.expander("Add a book"):
            with st.form("book_form"):
                title = st.text_input("Book title")
                author = st.text_input("Author / publisher")
                subject = st.text_input("Subject")
                available = st.selectbox("Availability", ["Available", "Issued"])
                save_book = st.form_submit_button("Add book")
            if save_book:
                if title.strip():
                    execute("INSERT INTO library(book_title,author,subject,available) VALUES(?,?,?,?)",
                            (title.strip(), author.strip(), subject.strip(), 1 if available == "Available" else 0))
                    st.success("Book added.")
                    st.rerun()
                else:
                    st.error("Book title is required.")
    books = query_df("SELECT id,book_title,author,subject,available FROM library ORDER BY book_title")
    if not books.empty:
        books["Status"] = books["available"].map({1: "Available", 0: "Issued"})
        st.dataframe(books.drop(columns=["available"]), use_container_width=True, hide_index=True)
        search = st.text_input("Search books")
        if search:
            st.dataframe(books[books.astype(str).apply(lambda col: col.str.contains(search, case=False)).any(axis=1)],
                         use_container_width=True, hide_index=True)

# ---------------------- Notifications ----------------------
elif page == "Notifications":
    st.title("Notifications")
    st.write("This page displays school notices and reminders. Email/SMS delivery requires a configured service.")
    notices = query_df("SELECT title,message,notice_date,category FROM notices ORDER BY id DESC")
    st.dataframe(notices, use_container_width=True, hide_index=True)

# ---------------------- Timetable ----------------------
elif page == "Timetable & Date Sheet":
    st.title("Timetable & Date Sheet")
    if role in ["Admin", "Principal", "Teacher"]:
        with st.expander("Add timetable entry"):
            with st.form("timetable_form"):
                cls = st.selectbox("Class / section", class_options(), key="tt_class")
                day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
                period = st.text_input("Period / time", placeholder="e.g. 08:00–08:40")
                subject = st.text_input("Subject", key="tt_subject")
                teacher = st.text_input("Teacher name")
                save_tt = st.form_submit_button("Save timetable")
            if save_tt:
                if period.strip() and subject.strip() and teacher.strip():
                    execute("INSERT INTO timetable(class_section,day_name,period,subject,teacher_name) VALUES(?,?,?,?,?)",
                            (cls, day, period.strip(), subject.strip(), teacher.strip()))
                    st.success("Timetable entry saved.")
                    st.rerun()
                else:
                    st.error("Period, subject and teacher are required.")
    st.subheader("Class timetable")
    selected_class = st.selectbox("Choose class", class_options(), key="view_tt_class")
    timetable = query_df("SELECT day_name,period,subject,teacher_name FROM timetable WHERE class_section=? ORDER BY id",
                         (selected_class,))
    st.dataframe(timetable, use_container_width=True, hide_index=True)
    st.subheader("Date sheet")
    st.info("Enter exam dates as school notices or timetable entries. A dedicated exam date-sheet module can be expanded later.")

# ---------------------- AI study assistant ----------------------
elif page == "AI Study Assistant":
    st.title("AI Study Assistant")
    st.info("This basic assistant gives study guidance without an external AI service. Real AI answers require an API and an internet connection.")
    topic = st.text_input("Enter a subject or topic")
    level = st.selectbox("Class", [f"Class {n}" for n in range(6, 11)])
    task = st.selectbox("What do you need?", ["Explain a topic simply", "Make a revision plan", "Create practice questions", "Study tips"])
    if st.button("Get study help"):
        if not topic.strip():
            st.warning("Please enter a topic.")
        elif task == "Explain a topic simply":
            st.write(f"**{topic}:** Read the definition first, identify the key terms, review one example, and then explain the idea in your own words. For {level}, keep your notes short and clear.")
        elif task == "Make a revision plan":
            st.write(f"**Revision plan for {topic}:** 1) Review notes for 15 minutes. 2) Write five key points. 3) Practise questions for 20 minutes. 4) Check mistakes. 5) Revise again tomorrow.")
        elif task == "Create practice questions":
            st.write(f"Practice prompts for {topic}:")
            st.write("1. Define the topic in your own words.")
            st.write("2. List three important facts.")
            st.write("3. Explain one example.")
            st.write("4. Write two short-answer questions and answer them.")
            st.write("5. What part needs more revision?")
        else:
            st.write(f"Study tips for {topic}: study in short sessions, put your phone aside, test yourself without notes, take breaks, and review difficult points again.")

# ---------------------- Reports ----------------------
elif page == "Reports & Analytics":
    st.title("Reports & Analytics")
    students = get_students()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total students", len(students))
    c2.metric("Total attendance entries", int(query_df("SELECT COUNT(*) n FROM attendance").iloc[0]["n"]))
    c3.metric("Total results", int(query_df("SELECT COUNT(*) n FROM results").iloc[0]["n"]))
    st.subheader("Students by class")
    if not students.empty:
        class_counts = students.groupby("class_section").size().reset_index(name="students")
        st.bar_chart(class_counts.set_index("class_section"))
        st.dataframe(class_counts, use_container_width=True, hide_index=True)
    st.subheader("Attendance summary")
    att_summary = query_df("SELECT status, COUNT(*) AS count FROM attendance GROUP BY status")
    st.dataframe(att_summary, use_container_width=True, hide_index=True)
    st.subheader("Result summary")
    result_summary = query_df("""SELECT exam_name, subject, ROUND(AVG(marks * 100.0 / total_marks),2) AS average_percentage
                                 FROM results GROUP BY exam_name,subject""")
    st.dataframe(result_summary, use_container_width=True, hide_index=True)
    st.caption("Reports use records entered into this demo database.")

# ---------------------- Notices & events ----------------------
elif page == "School Notices & Events":
    st.title("School Notices & Events")
    if role in ["Admin", "Principal"]:
        with st.expander("Publish a notice"):
            with st.form("notice_form"):
                title = st.text_input("Notice title")
                message = st.text_area("Notice message")
                ndate = st.date_input("Notice date", value=date.today())
                category = st.selectbox("Category", ["General", "Exam", "Holiday", "Event", "Admission", "Fee"])
                publish = st.form_submit_button("Publish notice")
            if publish:
                if title.strip() and message.strip():
                    execute("INSERT INTO notices(title,message,notice_date,category) VALUES(?,?,?,?)",
                            (title.strip(), message.strip(), str(ndate), category))
                    st.success("Notice published.")
                    st.rerun()
                else:
                    st.error("Title and message are required.")
        with st.expander("Add school event"):
            with st.form("event_form"):
                event_title = st.text_input("Event title")
                event_date = st.date_input("Event date", value=date.today())
                details = st.text_area("Event details")
                add_event = st.form_submit_button("Add event")
            if add_event:
                if event_title.strip():
                    execute("INSERT INTO events(event_title,event_date,details) VALUES(?,?,?)",
                            (event_title.strip(), str(event_date), details.strip()))
                    st.success("Event added.")
                    st.rerun()
                else:
                    st.error("Enter event title.")
    st.subheader("Notices")
    st.dataframe(query_df("SELECT title,message,notice_date,category FROM notices ORDER BY notice_date DESC"),
                 use_container_width=True, hide_index=True)
    st.subheader("Events")
    st.dataframe(query_df("SELECT event_title,event_date,details FROM events ORDER BY event_date"),
                 use_container_width=True, hide_index=True)

# ---------------------- Parent portal ----------------------
elif page == "Parent Portal":
    st.title("Parent / Guardian Portal")
    st.write("Parents can review their child's attendance, results and fee records. This demo uses student-name lookup; production should use verified parent accounts and strict access controls.")
    students = get_students()
    if students.empty:
        st.info("No student records available.")
    else:
        selected_student = st.selectbox("Select student", students["student_name"].tolist())
        student_row = students[students["student_name"] == selected_student].iloc[0]
        st.write(f"**Class:** {student_row['class_section']} | **Roll number:** {student_row['roll_no']}")
        st.subheader("Attendance")
        st.dataframe(query_df("""SELECT attendance_date,status,subject FROM attendance WHERE student_id=? ORDER BY attendance_date DESC""",
                              (int(student_row["id"]),)), use_container_width=True, hide_index=True)
        st.subheader("Results")
        st.dataframe(query_df("""SELECT exam_name,subject,marks,total_marks,exam_date FROM results WHERE student_id=? ORDER BY exam_date DESC""",
                              (int(student_row["id"]),)), use_container_width=True, hide_index=True)
        st.subheader("Fees")
        st.dataframe(query_df("SELECT month,amount,status,paid_date FROM fees WHERE student_id=? ORDER BY id DESC",
                              (int(student_row["id"]),)), use_container_width=True, hide_index=True)

# ---------------------- Messages ----------------------
elif page == "Messages":
    st.title("Messages & Communication")
    with st.form("message_form"):
        recipient = st.selectbox("Send to", ["Admin", "Principal", "Teacher", "Parent", "Student"])
        message = st.text_area("Message")
        send = st.form_submit_button("Send message")
    if send:
        if message.strip():
            execute("INSERT INTO messages(sender,recipient,message,sent_at) VALUES(?,?,?,?)",
                    (user["full_name"], recipient, message.strip(), datetime.now().isoformat(timespec="seconds")))
            st.success("Message saved.")
        else:
            st.error("Please write a message.")
    st.subheader("Message history")
    if role in ["Admin", "Principal"]:
        msgs = query_df("SELECT sender,recipient,message,sent_at FROM messages ORDER BY id DESC")
    else:
        msgs = query_df("SELECT sender,recipient,message,sent_at FROM messages WHERE sender=? OR recipient=? ORDER BY id DESC",
                        (user["full_name"], role))
    st.dataframe(msgs, use_container_width=True, hide_index=True)

# ---------------------- Footer ----------------------
st.divider()
st.caption("Government Girls High School Sial | Smart Education & LMS Portal | Created by Masooma Batool")
st.caption("Prototype notice: change demo passwords, confirm staff details, use an official building photo, and review security before real-world deployment.")
