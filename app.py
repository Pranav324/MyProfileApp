from urllib import response
from flask import Flask, render_template, request, redirect, url_for, session, flash,jsonify
import os
import sqlite3
import re
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "users.db")

def ensure_reset_token_column():
    """Add reset_token column to users table if it doesn't exist (safe to call repeatedly)."""
    if not os.path.exists(DB_PATH):
        print("DB not found:", DB_PATH)
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(users);")
        cols = [row[1] for row in cur.fetchall()]
        if "reset_token" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN reset_token TEXT;")
            conn.commit()
            print("Added column reset_token to users table.")
        conn.close()
    except Exception as e:
        print("Could not ensure reset_token column:", e)

# call it once at startup
ensure_reset_token_column()

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-me"  # change for production

# Server-side validation helpers
NAME_RE = re.compile(r'^[A-Za-z][A-Za-z ]+[A-Za-z]$')
EMAIL_RE = re.compile(r'^[A-Za-z0-9._%+-]+@gmail\.com$')
MOBILE_RE = re.compile(r'^\d{10}$')
USERNAME_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*@gmail\.com$')
PASSWORD_RE = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[^A-Za-z0-9]).{6,}$')

def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        repassword = request.form.get("repassword", "").strip()
        mobile = request.form.get("mobile", "").strip()
        address = request.form.get("address", "").strip()

        # Validation
        if not NAME_RE.match(name):
            flash("Name must start/end with letter, min 3 chars.", "danger")
            return redirect(url_for("register"))
        
        if not EMAIL_RE.match(email):
            flash("Email must be a valid Gmail address.", "danger")
            return redirect(url_for("register"))
        
        if not USERNAME_RE.match(username):
            flash("Username must be a valid Gmail address.", "danger")
            return redirect(url_for("register"))
        
        if not MOBILE_RE.match(mobile):
            flash("Mobile must be 10 digits.", "danger")
            return redirect(url_for("register"))
        
        if not PASSWORD_RE.match(password):
            flash("Password must have letter, digit, special char, min 6 chars.", "danger")
            return redirect(url_for("register"))
        
        if password != repassword:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        # Check if user already exists
        existing = query_db("SELECT id FROM users WHERE email = ? OR username = ?", 
                           (email, username), one=True)
        if existing:
            flash("Email or username already registered.", "danger")
            return redirect(url_for("register"))

        # HASH PASSWORD BEFORE STORING
        hashed_password = generate_password_hash(password)
        print(f"DEBUG: Hashed password = {hashed_password}")  # temporary debug

        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (name, email, username, password, mobile, Address, created_at) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))",
                (name, email, username, hashed_password, mobile, address)
            )
            conn.commit()
            conn.close()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError as e:
            print(f"DEBUG: IntegrityError = {e}")
            flash("Email or username already exists.", "danger")
            return redirect(url_for("register"))

    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        print(f"DEBUG: Login attempt with username={username}")  # temporary debug
        
        user = query_db("SELECT id, password FROM users WHERE email = ? OR username = ?",
                        (username, username), one=True)
        
        if user:
            print(f"DEBUG: User found, stored hash = {user['password']}")  # temporary debug
            is_valid = check_password_hash(user["password"], password)
            print(f"DEBUG: Password check result = {is_valid}")  # temporary debug
            
            if is_valid:
                session.clear()
                session["user_id"] = user["id"]
                flash("Logged in.", "success")
                return redirect(url_for("profile"))
        
        flash("Invalid credentials.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/forgot", methods=["GET","POST"])
def forgot():
    if request.method == "POST":
        email = request.form.get("email","").strip()
        user = query_db("SELECT id FROM users WHERE email = ? LIMIT 1", (email,), one=True)
        if not user:
            flash("If the email exists, a reset link will be sent.", "info")
            return redirect(url_for("forgot"))

        import uuid
        token = uuid.uuid4().hex
        query_db("UPDATE users SET reset_token = ? WHERE id = ?", (token, user["id"]))
        # Render forgot page and expose link in dev so you can open it
        reset_path = url_for('reset_password', token=token, _external=False)
        flash("Reset link generated (dev): {}".format(reset_path), "info")
        return render_template("forgot.html", debug_reset_url=reset_path)

    return render_template("forgot.html", debug_reset_url=None)

@app.route("/profile")
def profile():
    uid = session.get("user_id")
    if not uid:
        flash("Please log in to view your profile.", "warning")
        return redirect(url_for("login"))
    user = query_db("SELECT id,name,email,mobile,address,created_at FROM users WHERE id = ? LIMIT 1", (uid,), one=True)
    return render_template("profile.html", user=user)

@app.route("/logout", methods=["POST"])
def logout():
    # Clear the session
    session.clear()
    # Return full response with headers and redirect
    response = jsonify({
        "ok": True,
        "redirect": url_for('index')
    })
    # Set strict cache control headers
    response.headers.add('Cache-Control', 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0')
    response.headers.add('Pragma', 'no-cache')
    response.headers.add('Expires', '0')
    return response

@app.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    if request.method == "POST":
        password = request.form.get("password", "").strip()
        repassword = request.form.get("repassword", "").strip()

        if not PASSWORD_RE.match(password):
            flash("Password must contain letters, digits, special char and be at least 6 chars.", "danger")
            return redirect(url_for("reset_password", token=token))

        if password != repassword:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("reset_password", token=token))

        # find user by token
        user = query_db("SELECT id FROM users WHERE reset_token = ? LIMIT 1", (token,), one=True)
        if not user:
            flash("Invalid or expired reset token.", "danger")
            return redirect(url_for("forgot"))

        # hash password and update DB, clear token
        hashed = generate_password_hash(password)
        query_db("UPDATE users SET password = ?, reset_token = NULL WHERE id = ?", (hashed, user["id"]))

        flash("Password updated. Please log in with your new password.", "success")
        return redirect(url_for("login"))

    # GET: show form
    return render_template("reset.html", token=token)

@app.after_request
def set_cache_headers(response):
    # Prevent browser caching of pages (helps ensure Back triggers a fresh request)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
          

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)

