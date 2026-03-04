from flask import Flask, render_template, request, redirect, session
from models import create_tables, get_connection
import os


app = Flask(__name__)
app.secret_key = "secretkey"

create_tables()

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ======================
# LOGIN
# ======================
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        role = request.form["role"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()
        cur = conn.cursor()

        if role == "admin":
            cur.execute("SELECT * FROM admin WHERE username=? AND password=?",(email,password))
            user = cur.fetchone()
            if user:
                session["role"]="admin"
                return redirect("/admin")

        elif role == "student":
            cur.execute("SELECT * FROM student WHERE email=? AND password=? AND is_active=1",(email,password))
            user = cur.fetchone()
            if user:
                session["role"]="student"
                session["user_id"]=user["id"]
                return redirect("/student")

        elif role == "company":
            cur.execute("""SELECT * FROM company 
                           WHERE email=? AND password=? 
                           AND approval_status='Approved' AND is_active=1""",
                        (email,password))
            user = cur.fetchone()
            if user:
                session["role"]="company"
                session["user_id"]=user["id"]
                return redirect("/company")

        return "Invalid Credentials"

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ======================
# ADMIN DASHBOARD
# ======================
@app.route("/admin")
def admin_dashboard():
    if session.get("role")!="admin":
        return redirect("/")

    conn = get_connection()
    cur = conn.cursor()

    students = cur.execute("SELECT COUNT(*) FROM student").fetchone()[0]
    companies = cur.execute("SELECT COUNT(*) FROM company").fetchone()[0]
    drives = cur.execute("SELECT COUNT(*) FROM drive").fetchone()[0]
    applications = cur.execute("SELECT COUNT(*) FROM application").fetchone()[0]

    return render_template("admin_dashboard.html",
                           students=students,
                           companies=companies,
                           drives=drives,
                           applications=applications)


@app.route("/admin/companies")
def admin_companies():
    if session.get("role")!="admin":
        return redirect("/")

    conn = get_connection()
    companies = conn.execute("SELECT * FROM company").fetchall()
    return render_template("admin_companies.html", companies=companies)


@app.route("/admin/approve_company/<int:id>")
def approve_company(id):
    conn = get_connection()
    conn.execute("UPDATE company SET approval_status='Approved' WHERE id=?",(id,))
    conn.commit()
    return redirect("/admin/companies")


@app.route("/admin/reject_company/<int:id>")
def reject_company(id):
    conn = get_connection()
    conn.execute("UPDATE company SET approval_status='Rejected' WHERE id=?",(id,))
    conn.commit()
    return redirect("/admin/companies")

@app.route("/admin/drives")
def admin_drives():
    if session.get("role") != "admin":
        return redirect("/")

    conn = get_connection()
    drives = conn.execute("""
        SELECT drive.*, company.company_name 
        FROM drive
        JOIN company ON drive.company_id = company.id
    """).fetchall()

    return render_template("admin_drives.html", drives=drives)

@app.route("/admin/students")
def admin_students():
    if session.get("role") != "admin":
        return redirect("/")

    conn = get_connection()
    students = conn.execute("SELECT * FROM student").fetchall()
    return render_template("admin_students.html", students=students)

@app.route("/admin/applications")
def admin_applications():
    if session.get("role") != "admin":
        return redirect("/")

    conn = get_connection()
    applications = conn.execute("""
        SELECT application.*, student.name, drive.job_title
        FROM application
        JOIN student ON application.student_id = student.id
        JOIN drive ON application.drive_id = drive.id
    """).fetchall()

    return render_template("admin_applications.html", applications=applications)

@app.route("/admin/approve_drive/<int:id>")
def approve_drive(id):
    conn = get_connection()
    conn.execute("UPDATE drive SET status='Approved' WHERE id=?", (id,))
    conn.commit()
    return redirect("/admin/drives")

# ======================
# COMPANY DASHBOARD
# ======================
@app.route("/register_company", methods=["GET","POST"])
def register_company():
    if request.method == "POST":
        company_name = request.form["company_name"]
        hr_contact = request.form["hr_contact"]
        email = request.form["email"]
        password = request.form["password"]
        website = request.form["website"]

        conn = get_connection()
        conn.execute(
            """INSERT INTO company 
            (company_name,hr_contact,email,password,website)
            VALUES (?,?,?,?,?)""",
            (company_name,hr_contact,email,password,website)
        )
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register_company.html")
@app.route("/company")
def company_dashboard():
    if session.get("role")!="company":
        return redirect("/")

    company_id=session["user_id"]
    conn=get_connection()
    drives=conn.execute("SELECT * FROM drive WHERE company_id=?",(company_id,)).fetchall()
    return render_template("company_dashboard.html",drives=drives)


@app.route("/create_drive",methods=["GET","POST"])
def create_drive():
    if session.get("role")!="company":
        return redirect("/")

    if request.method=="POST":
        company_id=session["user_id"]
        job=request.form["job"]
        desc=request.form["desc"]
        elig=request.form["elig"]
        deadline=request.form["deadline"]

        conn=get_connection()
        conn.execute("""INSERT INTO drive(company_id,job_title,job_description,eligibility,deadline)
                        VALUES(?,?,?,?,?)""",
                     (company_id,job,desc,elig,deadline))
        conn.commit()
        return redirect("/company")

    return render_template("create_drive.html")

# ======================
# STUDENT DASHBOARD
# ======================

@app.route("/register_student", methods=["GET","POST"])
def register_student():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        phone = request.form["phone"]

        conn = get_connection()
        conn.execute(
            "INSERT INTO student (name,email,password,phone) VALUES (?,?,?,?)",
            (name,email,password,phone)
        )
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register_student.html")


@app.route("/student")
def student_dashboard():
    if session.get("role")!="student":
        return redirect("/")

    student_id=session["user_id"]
    conn=get_connection()

    drives=conn.execute("SELECT * FROM drive WHERE status='Approved'").fetchall()

    applications=conn.execute("""
        SELECT drive.job_title, application.status 
        FROM application
        JOIN drive ON drive.id=application.drive_id
        WHERE application.student_id=?
    """,(student_id,)).fetchall()
    

    return render_template("student_dashboard.html",
                           drives=drives,
                           applications=applications)


@app.route("/apply/<int:drive_id>")
def apply_drive(drive_id):
    if session.get("role")!="student":
        return redirect("/")

    student_id=session["user_id"]
    conn=get_connection()
    try:
        conn.execute("INSERT INTO application(student_id,drive_id) VALUES(?,?)",
                     (student_id,drive_id))
        conn.commit()
    except:
        return "Already Applied"

    return redirect("/student")

@app.route("/admin/blacklist_student/<int:id>")
def blacklist_student(id):

    if session.get("role") != "admin":
        return redirect("/")

    conn = get_connection()
    conn.execute("UPDATE student SET is_active = 0 WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin/students")

@app.route("/admin/activate_student/<int:id>")
def activate_student(id):

    if session.get("role") != "admin":
        return redirect("/")

    conn = get_connection()
    conn.execute("UPDATE student SET is_active = 1 WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin/students")

@app.route("/student/edit_profile", methods=["GET","POST"])
def edit_profile():

    if session.get("role") != "student":
        return redirect("/")

    student_id = session["user_id"]
    conn = get_connection()

    if request.method == "POST":

        name = request.form["name"]
        phone = request.form["phone"]

        conn.execute("""
        UPDATE student
        SET name=?, phone=?
        WHERE id=?
        """,(name,phone,student_id))

        conn.commit()
        conn.close()

        return redirect("/student")

    student = conn.execute(
        "SELECT * FROM student WHERE id=?",
        (student_id,)
    ).fetchone()

    conn.close()

@app.route("/company/applications/<int:drive_id>")
def company_applications(drive_id):

    if session.get("role") != "company":
        return redirect("/")

    conn = get_connection()

    applications = conn.execute("""
    SELECT application.id, student.name, student.email,
           application.status
    FROM application
    JOIN student ON student.id = application.student_id
    WHERE application.drive_id = ?
    """,(drive_id,)).fetchall()

    conn.close()

    return render_template(
        "company_applications.html",
        applications=applications,
        drive_id=drive_id
    )
@app.route("/company/shortlist/<int:app_id>/<int:drive_id>")
def shortlist_student(app_id, drive_id):

    if session.get("role") != "company":
        return redirect("/")

    conn = get_connection()

    conn.execute(
        "UPDATE application SET status='Shortlisted' WHERE id=?",
        (app_id,)
    )

    conn.commit()
    conn.close()

    return redirect(f"/company/applications/{drive_id}")

    return render_template("edit_profile.html", student=student)
if __name__=="__main__":
    app.run(debug=True, port=5001)