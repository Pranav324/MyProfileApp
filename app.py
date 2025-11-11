from urllib import response
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import sqlite3
import re
import hashlib
import time
from werkzeug.security import generate_password_hash, check_password_hash

# Ensure static folder path is correct
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
DB_PATH = os.path.join(BASE_DIR, "database", "users.db")

# Create Flask app with explicit static folder
app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='/static')
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

# --- new helper to build navbar flags per page / session ---
def nav_flags(for_page=None):
    """Return navbar flags based on page and session"""
    user_id = session.get('user_id')
    
    # If user is logged in, show only logout
    if user_id:
        return {
            'show_login': False,
            'show_register': False,
            'show_logout': True
        }
    
    # If user is NOT logged in (on public pages)
    # Show both login and register EXCEPT when on those exact pages
    return {
        'show_login': for_page != 'login',           # Hide login button ONLY on login page
        'show_register': for_page != 'register',     # Hide register button ONLY on register page
        'show_logout': False
    }
# ---------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html", nav=nav_flags("home"))

@app.route("/register", methods=["GET", "POST"])
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
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify(ok=True, redirect=url_for("login"))
            return redirect(url_for("login"))
        except sqlite3.IntegrityError as e:
            print(f"DEBUG: IntegrityError = {e}")
            flash("Email or username already exists.", "danger")
            return redirect(url_for("register"))

    # GET: show registration form and ensure nav shows only Login on top-right
    return render_template("register.html", nav=nav_flags("register"))

@app.route("/login", methods=["GET", "POST"])
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
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return jsonify(ok=True, redirect=url_for("profile"))
                return redirect(url_for("profile"))
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(ok=False, error="Invalid credentials"), 401
        flash("Invalid credentials.", "danger")
        return redirect(url_for("login"))

    # GET: show login form and ensure nav shows only Register on top-right
    return render_template("login.html", nav=nav_flags("login"))

# Add this helper function if missing
def generate_reset_token(user_id):
    """Generate a simple reset token"""
    token = hashlib.sha256(f"{user_id}{time.time()}".encode()).hexdigest()
    return token

def verify_reset_token(token, user_id):
    """Verify token (simplified - in production use proper token validation)"""
    # For now, just check if token is not empty
    return token is not None and len(token) > 0

@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    """Forgot password - send reset link"""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        
        if not email:
            flash("❌ Email is required.", "danger")
            return redirect(url_for("forgot"))
        
        try:
            # Query user by email
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            user = conn.execute(
                "SELECT id, email, name FROM users WHERE LOWER(email) = ?", 
                (email.lower(),)
            ).fetchone()
            conn.close()
            
            if not user:
                # Security: don't reveal if email exists
                flash("✅ If an account exists with that email, a reset link has been sent.", "info")
                return redirect(url_for("login"))
            
            # Generate reset token
            token = generate_reset_token(user["id"])
            
            # Store token in session
            if "reset_tokens" not in session:
                session["reset_tokens"] = {}
            
            session["reset_tokens"][token] = {
                "user_id": user["id"],
                "email": email,
                "created_at": time.time()
            }
            session.modified = True
            
            # Build reset URL (absolute URL for email)
            reset_url = url_for("reset_password", token=token, _external=True)
            
            # For testing: show the link in a flash message
            flash(f"✅ Reset link sent! <a href='{reset_url}' style='color:#0f58eb;text-decoration:underline;'>Click here to reset password</a>", "success")
            
            return redirect(url_for("login"))
        
        except Exception as e:
            flash(f"❌ Error: {str(e)}", "danger")
            return redirect(url_for("forgot"))
    
    return render_template("forgot.html", nav=nav_flags("forgot"))

@app.route("/profile")
def profile():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please login first.", "danger")
        return redirect(url_for("login"))
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("login"))
    
    return render_template("profile.html", user=user, nav=nav_flags("profile"))

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("✅ Logged out successfully.", "success")
    
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(redirect=url_for("index"))
    
    return redirect(url_for("index"))

@app.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Reset password page - GET shows form, POST updates password"""
    # Get reset tokens from session
    reset_tokens = session.get("reset_tokens", {})
    
    # Check if token exists
    if token not in reset_tokens:
        flash("❌ Invalid or expired reset link. Please request a new one.", "danger")
        return redirect(url_for("forgot"))
    
    token_data = reset_tokens[token]
    
    # Check token expiration (30 minutes)
    if time.time() - token_data.get("created_at", 0) > 1800:
        if token in session.get("reset_tokens", {}):
            del session["reset_tokens"][token]
            session.modified = True
        flash("❌ Reset link has expired. Please request a new one.", "danger")
        return redirect(url_for("forgot"))
    
    # Handle POST (form submission)
    if request.method == "POST":
        password = request.form.get("password", "").strip()
        repassword = request.form.get("repassword", "").strip()
        
        # Validation
        if not password or not repassword:
            flash("❌ Both password fields are required.", "danger")
            return redirect(url_for("reset_password", token=token))
        
        if password != repassword:
            flash("❌ Passwords do not match.", "danger")
            return redirect(url_for("reset_password", token=token))
        
        if not PASSWORD_RE.match(password):
            flash("❌ Password must be 6+ chars with letter, number, and symbol.", "danger")
            return redirect(url_for("reset_password", token=token))
        
        try:
            # Get user_id from token
            user_id = token_data["user_id"]
            
            # Update password in database
            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (generate_password_hash(password), user_id)
            )
            conn.commit()
            conn.close()
            
            # Remove token from session
            if token in session.get("reset_tokens", {}):
                del session["reset_tokens"][token]
                session.modified = True
            
            flash("✅ Password reset successfully! Please login.", "success")
            return redirect(url_for("login"))
        
        except Exception as e:
            flash(f"❌ Error updating password: {str(e)}", "danger")
            return redirect(url_for("reset_password", token=token))
    
    # Handle GET (show form)
    return render_template("reset.html", token=token, nav=nav_flags("reset"))

@app.after_request
def set_cache_headers(response):
    # Prevent browser caching of pages (helps ensure Back triggers a fresh request)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
          

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)

