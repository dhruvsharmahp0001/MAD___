import sqlite3

DATABASE = "database.db"

def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS student(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_uid TEXT UNIQUE,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        phone TEXT,
        resume TEXT,
        is_active INTEGER DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS company(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_uid TEXT UNIQUE,
        company_name TEXT,
        hr_contact TEXT,
        email TEXT UNIQUE,
        password TEXT,
        website TEXT,
        approval_status TEXT DEFAULT 'Pending',
        is_active INTEGER DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS drive(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        drive_uid TEXT UNIQUE,
        company_id INTEGER,
        job_title TEXT,
        job_description TEXT,
        eligibility TEXT,
        deadline TEXT,
        status TEXT DEFAULT 'Pending'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS application(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        drive_id INTEGER,
        status TEXT DEFAULT 'Applied',
        UNIQUE(student_id, drive_id)
    )
    """)

    # Default admin
    cur.execute("SELECT * FROM admin WHERE username='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO admin(username,password) VALUES('admin','admin123')")

    conn.commit()
    conn.close()