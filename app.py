from flask import Flask, render_template, request, redirect, session,send_from_directory
from models import create_tables, get_connection
from datetime import datetime
import os
import random
import string

def generate_student_uid():
    digits = ''.join(random.choices(string.digits, k=4))
    return f"S{digits}"

def generate_company_uid():
    digits = ''.join(random.choices(string.digits, k=4))
    return f"C{digits}"

def generate_drive_uid():
    digits = ''.join(random.choices(string.digits, k=4))
    return f"D{digits}"

def generate_application_uid():
    digits = ''.join(random.choices(string.digits, k=4))
    return f"A{digits}"


app = Flask(__name__)
app.secret_key = "secretkey"

create_tables()

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
# file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))



# LOGIN

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
            cur.execute(   """SELECT * FROM company 
WHERE email=? 
AND password=? 
AND approval_status='Approved'
AND is_active=1""",
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



# ADMIN DASHBOARD

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

    if session.get("role") != "admin":
        return redirect("/")

    search = request.args.get("search")

    conn = get_connection()

    if search:

        companies = conn.execute("""
        SELECT *
        FROM company
        WHERE company_name LIKE ?
        """,('%'+search+'%',)).fetchall()

    else:

        companies = conn.execute("""
        SELECT *
        FROM company
        """).fetchall()

    conn.close()

    return render_template(
        "admin_companies.html",
        companies=companies
    )

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

    SELECT
        drive.*,
        company.company_name

    FROM drive

    JOIN company
    ON company.id = drive.company_id

    ORDER BY drive.id DESC

    """).fetchall()

    conn.close()

    return render_template(
        "admin_drives.html",
        drives=drives
    )
@app.route("/admin/drive_details/<int:drive_id>")
def admin_drive_details(drive_id):

    if session.get("role") != "admin":
        return redirect("/")

    conn = get_connection()

    drive = conn.execute("""

    SELECT
        drive.*,
        company.company_name

    FROM drive

    JOIN company
    ON company.id = drive.company_id

    WHERE drive.id = ?

    """,(drive_id,)).fetchone()

    conn.close()

    return render_template(
        "admin_drive_details.html",
        drive=drive
    )
@app.route("/admin/students")
def admin_students():

    if session.get("role") != "admin":
        return redirect("/")

    search = request.args.get("search")

    conn = get_connection()

    if search:

        students = conn.execute("""
        SELECT * FROM student
        WHERE name LIKE ?
        OR student_uid LIKE ?
        OR phone LIKE ?
        """,('%'+search+'%','%'+search+'%','%'+search+'%')).fetchall()

    else:

        students = conn.execute("""
        SELECT * FROM student
        """).fetchall()

    conn.close()

    return render_template(
        "admin_students.html",
        students=students
    )

@app.route("/admin/applications")
def admin_applications():

    if session.get("role") != "admin":
        return redirect("/")

    conn = get_connection()

    applications = conn.execute("""

    SELECT
        application.application_uid,
        application.applied_on,
        application.status,

        drive.drive_uid,
        drive.job_title,
        drive.status AS drive_status,
        drive.is_deleted,

        student.student_uid,
        student.name,

        company.company_name

    FROM application

    LEFT JOIN drive
    ON drive.id = application.drive_id

    LEFT JOIN student
    ON student.id = application.student_id

    LEFT JOIN company
    ON company.id = drive.company_id

    ORDER BY application.id DESC

    """).fetchall()

    conn.close()

    return render_template(
        "admin_applications.html",
        applications=applications
    )

    

@app.route("/admin/approve_drive/<int:drive_id>")
def approve_drive(drive_id):

    if session.get("role") != "admin":
        return redirect("/")

    conn = get_connection()

    conn.execute("""
    UPDATE drive
    SET status='Approved'
    WHERE id=? AND is_deleted=0
    """,(drive_id,))

    conn.commit()
    conn.close()

    return redirect("/admin/drives")

@app.route("/admin/reject_drive/<int:drive_id>")
def reject_drive(drive_id):

    if session.get("role") != "admin":
        return redirect("/")

    conn = get_connection()

    conn.execute("""
    UPDATE drive
    SET status='Rejected'
    WHERE id=? AND is_deleted=0
    """,(drive_id,))

    conn.commit()
    conn.close()

    return redirect("/admin/drives")

@app.route("/admin/activate_student/<int:id>")
def activate_student(id):

    if session.get("role") != "admin":
        return redirect("/")

    conn = get_connection()
    conn.execute("UPDATE student SET is_active = 1 WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin/students")

@app.route("/admin/blacklist_student/<int:id>")
def blacklist_student(id):

    if session.get("role") != "admin":
        return redirect("/")

    conn = get_connection()
    conn.execute("UPDATE student SET is_active = 0 WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin/students")

@app.route("/admin/blacklist_company/<int:company_id>")
def blacklist_company(company_id):

    if session.get("role") != "admin":
        return redirect("/")

    conn = get_connection()

    conn.execute("""
    UPDATE company
    SET is_active=0
    WHERE id=?
    """,(company_id,))

    conn.commit()
    conn.close()

    return redirect("/admin/companies")

@app.route("/admin/activate_company/<int:company_id>")
def activate_company(company_id):

    if session.get("role") != "admin":
        return redirect("/")

    conn = get_connection()

    conn.execute("""
    UPDATE company
    SET is_active=1
    WHERE id=?
    """,(company_id,))

    conn.commit()
    conn.close()

    return redirect("/admin/companies")

@app.route("/admin/company/<int:company_id>")
def admin_company_details(company_id):

    if session.get("role") != "admin":
        return redirect("/")

    conn = get_connection()

    company = conn.execute(
        "SELECT * FROM company WHERE id=?",
        (company_id,)
    ).fetchone()

    drives = conn.execute(
        "SELECT * FROM drive WHERE company_id=?",
        (company_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "admin_company_details.html",
        company=company,
        drives=drives
    )

@app.route("/admin/student/<int:student_id>")
def admin_student_details(student_id):

    if session.get("role") != "admin":
        return redirect("/")

    conn = get_connection()

    student = conn.execute(
        "SELECT * FROM student WHERE id=?",
        (student_id,)
    ).fetchone()

    applications = conn.execute("""
    SELECT application.application_uid,
           drive.drive_uid,
           drive.job_title,
           application.status,
           application.applied_on
    FROM application
    JOIN drive ON drive.id = application.drive_id
    WHERE application.student_id=?
    """,(student_id,)).fetchall()

    conn.close()

    return render_template(
        "admin_student_details.html",
        student=student,
        applications=applications
    )

# COMPANY DASHBOARD

@app.route("/register_company", methods=["GET","POST"])
def register_company():
    if request.method == "POST":
        company_name = request.form["company_name"]
        hr_contact = request.form["hr_contact"]
        email = request.form["email"]
        password = request.form["password"]
        website = request.form["website"]
        conn = get_connection()
        company_uid = generate_company_uid()
        description = request.form["description"]
        conn.execute("""
INSERT INTO company(company_uid,company_name,hr_contact,email,password,website,description)
VALUES(?,?,?,?,?,?,?)
""",(company_uid,company_name,hr_contact,email,password,website,description))
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register_company.html")


@app.route("/company")
def company_dashboard():

    if session.get("role") != "company":
        return redirect("/")

    company_id = session["user_id"]

    conn = get_connection()

    # Company details
    company = conn.execute("""
    SELECT company_uid, company_name, email, website, hr_contact
    FROM company
    WHERE id=?
    """,(company_id,)).fetchone()

    # ACTIVE DRIVES
    drives = conn.execute("""
    SELECT drive.*,
    (SELECT COUNT(*) FROM application
     WHERE application.drive_id = drive.id) AS applicants
    FROM drive
    WHERE company_id=? AND is_deleted=0
    ORDER BY id DESC
    """,(company_id,)).fetchall()

    # DELETED DRIVES HISTORY
    deleted_drives = conn.execute("""
    SELECT *
    FROM drive
    WHERE company_id=? AND is_deleted=1
    ORDER BY id DESC
    """,(company_id,)).fetchall()

    conn.close()

    return render_template(
        "company_dashboard.html",
        company=company,
        drives=drives,
        deleted_drives=deleted_drives
    )

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
        drive_uid = generate_drive_uid()

        conn.execute("""
INSERT INTO drive
(drive_uid,company_id,job_title,job_description,eligibility,deadline)
VALUES (?,?,?,?,?,?)
    """,(drive_uid,company_id,job,desc,elig,deadline))
        conn.commit()
        return redirect("/company")

    return render_template("create_drive.html")


@app.route("/company/edit_drive/<int:id>", methods=["GET","POST"])
def edit_drive(id):

    if session.get("role") != "company":
        return redirect("/")

    conn = get_connection()

    if request.method == "POST":

        job = request.form["job_title"]
        desc = request.form["job_description"]
        elig = request.form["eligibility"]
        deadline = request.form["deadline"]

        conn.execute("""
        UPDATE drive
        SET job_title=?, job_description=?, eligibility=?, deadline=?
        WHERE id=?
        """,(job,desc,elig,deadline,id))

        conn.commit()

        return redirect("/company")

    drive = conn.execute(
        "SELECT * FROM drive WHERE id=?",
        (id,)
    ).fetchone()

    return render_template("edit_drive.html", drive=drive)


@app.route("/company/delete_drive/<int:drive_id>")
def delete_drive(drive_id):

    if session.get("role") != "company":
        return redirect("/")

    conn = get_connection()

    conn.execute(
        "UPDATE drive SET is_deleted=1 WHERE id=?",
        (drive_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/company")


@app.route("/company/close_drive/<int:id>")
def close_drive(id):

    if session.get("role") != "company":
        return redirect("/")

    conn = get_connection()

    conn.execute(
        "UPDATE drive SET status='Closed' WHERE id=?",
        (id,)
    )

    conn.commit()

    return redirect("/company")

@app.route("/company/deleted_drives")
def company_deleted_drives():

    if session.get("role") != "company":
        return redirect("/")

    company_id = session["user_id"]

    conn = get_connection()

    drives = conn.execute("""
    SELECT *
    FROM drive
    WHERE company_id=? AND is_deleted=1
    """,(company_id,)).fetchall()

    conn.close()

    return render_template(
        "company_deleted_drives.html",
        drives=drives
    )

@app.route("/company/edit_profile", methods=["GET","POST"])
def company_edit_profile():

    if session.get("role") != "company":
        return redirect("/")

    company_id = session["user_id"]

    conn = get_connection()

    if request.method == "POST":

        name = request.form["company_name"]
        hr = request.form["hr_contact"]
        website = request.form["website"]

        conn.execute("""
        UPDATE company
        SET company_name=?, hr_contact=?, website=?
        WHERE id=?
        """,(name,hr,website,company_id))

        conn.commit()

        return redirect("/company")

    company = conn.execute(
        "SELECT * FROM company WHERE id=?",
        (company_id,)
    ).fetchone()

    return render_template("company_edit_profile.html", company=company)

@app.route("/company/applications/<int:drive_id>")
def company_applications(drive_id):

    if session.get("role") != "company":
        return redirect("/")

    conn = get_connection()
    applications = conn.execute("""
SELECT 
application.id,
application.application_uid,
student.name,
student.email,
student.resume,
application.status
FROM application
JOIN student ON student.id = application.student_id
WHERE application.drive_id=?
""",(drive_id,)).fetchall()

    return render_template(
        "company_applications.html",
        applications=applications,
        drive_id=drive_id
    )


@app.route("/company/shortlist/<int:application_id>")
def shortlist_student(application_id):

    if session.get("role") != "company":
        return redirect("/")

    conn = get_connection()

    conn.execute("""
    UPDATE application
    SET status='Shortlisted'
    WHERE id=?
    """,(application_id,))

    conn.commit()
    conn.close()

    return redirect(request.referrer)

@app.route("/company/select/<int:application_id>")
def select_student(application_id):

    if session.get("role") != "company":
        return redirect("/")

    conn = get_connection()

    conn.execute("""
    UPDATE application
    SET status='Selected'
    WHERE id=?
    """,(application_id,))

    conn.commit()
    conn.close()

    return redirect(request.referrer)
@app.route("/company/reject/<int:application_id>")
def reject_student(application_id):

    if session.get("role") != "company":
        return redirect("/")

    conn = get_connection()

    conn.execute("""
    UPDATE application
    SET status='Rejected'
    WHERE id=?
    """,(application_id,))

    conn.commit()
    conn.close()

    return redirect(request.referrer)


# STUDENT DASHBOARD

@app.route("/register_student", methods=["GET","POST"])
def register_student():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        phone = request.form["phone"]

        conn = get_connection()
        student_uid = generate_student_uid()

        conn.execute("""
        INSERT INTO student (student_uid,name,email,password,phone)
        VALUES (?,?,?,?,?)
        """,(student_uid,name,email,password,phone))
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register_student.html")


@app.route("/student")
def student_dashboard():

    if session.get("role") != "student":
        return redirect("/")

    student_id = session["user_id"]

    conn = get_connection()

    # Student info (includes student_uid for display)
    student = conn.execute(
        "SELECT id, student_uid, name, email, phone, resume FROM student WHERE id=?",
        (student_id,)
    ).fetchone()

    # Available drives
    drives = conn.execute("""
    SELECT 
        drive.id,
        drive.drive_uid,
        drive.job_title,
        drive.eligibility,
        drive.deadline,
        drive.status,
        company.company_name,
        application.id AS applied
    FROM drive
    JOIN company ON company.id = drive.company_id
    LEFT JOIN application 
        ON application.drive_id = drive.id 
        AND application.student_id = ?
    WHERE drive.status='Approved'
    AND drive.is_deleted = 0
    """,(student_id,)).fetchall()

    # Student applications
    applications = conn.execute("""
    SELECT 
        application.application_uid,
        drive.job_title,
        application.status,
        application.applied_on
    FROM application
    JOIN drive ON drive.id = application.drive_id
    WHERE application.student_id=?
    ORDER BY application.id DESC
    """,(student_id,)).fetchall()

    # Placement history
    history = conn.execute("""
    SELECT 
        application.application_uid,
        drive.drive_uid,
        company.company_name,
        drive.job_title,
        application.applied_on
    FROM application
    JOIN drive ON drive.id = application.drive_id
    JOIN company ON company.id = drive.company_id
    WHERE application.student_id=? 
    AND application.status='Selected'
    """,(student_id,)).fetchall()

    conn.close()

    return render_template(
        "student_dashboard.html",
        student=student,
        drives=drives,
        applications=applications,
        history=history
    )

@app.route("/apply/<drive_uid>")
def apply_drive(drive_uid):

    if session.get("role") != "student":
        return redirect("/")

    student_id = session["user_id"]

    conn = get_connection()

    drive = conn.execute(
        "SELECT id FROM drive WHERE drive_uid=?",
        (drive_uid,)
    ).fetchone()

    # check already applied
    existing = conn.execute("""
    SELECT * FROM application
    WHERE student_id=? AND drive_id=?
    """,(student_id,drive["id"])).fetchone()

    if existing:
        conn.close()
        return redirect("/student")

    application_uid = generate_application_uid()

    today = datetime.now().strftime("%Y-%m-%d")

    conn.execute("""
    INSERT INTO application(application_uid,student_id,drive_id,status,applied_on)
    VALUES(?,?,?,?,?)
    """,(application_uid,student_id,drive["id"],"Applied",today))

    conn.commit()
    conn.close()

    return redirect("/student")

@app.route("/student/edit_profile", methods=["GET", "POST"])
def edit_profile():

    if session.get("role") != "student":
        return redirect("/")

    student_id = session["user_id"]

    conn = get_connection()

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]

        conn.execute("""
        UPDATE student
        SET name=?, email=?, phone=?
        WHERE id=?
        """,(name,email,phone,student_id))

        conn.commit()
        conn.close()

        return redirect("/student")

    student = conn.execute(
        "SELECT * FROM student WHERE id=?",
        (student_id,)
    ).fetchone()

    conn.close()

    return render_template(
        "edit_profile.html",
        student=student
    )
@app.route("/upload_resume", methods=["POST"])
def upload_resume():

    if session.get("role") != "student":
        return redirect("/")

    file = request.files["resume"]

    if file.filename == "":
        return redirect("/student")

    if not file.filename.endswith(".pdf"):
        return "Only PDF resumes allowed"

    student_id = session["user_id"]

    conn = get_connection()

    student = conn.execute(
        "SELECT student_uid FROM student WHERE id=?",
        (student_id,)
    ).fetchone()

    student_uid = student["student_uid"]

    filename = f"Resume_{student_uid}.pdf"

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    file.save(filepath)

    conn.execute(
        "UPDATE student SET resume=? WHERE id=?",
        (filename, student_id)
    )

    conn.commit()
    conn.close()

    return redirect("/student")

    
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

if __name__=="__main__":
    app.run(debug=True, port=5002)