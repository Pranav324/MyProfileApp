# MyProfileApp

Lightweight Flask web app for user registration, authentication, profile management, and password reset. Designed for learning and small projects — contributions welcome to scale features and improve security.

---

## Author Name
-- **Pranav Bhagwat**

## Quick overview

MyProfileApp implements:
- User registration with server-side validation
- Secure password storage (Werkzeug hashing)
- Login / logout with session handling
- Protected profile page showing user details
- "Forgot password" flow with reset token and reset form
- Client-side helpers (password visibility toggles, match indicator)
- Cache-control and history-cleaning measures to avoid stale authenticated views

---

## Features

- Register: validate name, email (Gmail), username, mobile, password rules
- Login: safe verification using hashed passwords
- Profile: authenticated-only page with avatar and details
- Forgot / Reset password: token generation, DB token storage, reset form and validation
- Logout: clears session and attempts to remove profile page from browser history
- Static assets: CSS/JS in `static/`, Jinja templates in `templates/`
- DB: SQLite database at `database/users.db` (simple single-file DB)

---

## Prerequisites

- Windows or Linux/macOS
- Python 3.8+ (your environment uses Python 3.13)
- Git (for contributions)

Recommended packages:
- Flask
- Werkzeug

Example install:
```bash
# from project root (flask_workspace)
python -m venv .venv
.venv\Scripts\activate      # Windows
# or: source .venv/bin/activate  # macOS/Linux

pip install flask werkzeug
# (If you maintain requirements.txt)
pip install -r requirements.txt
```

---

## Run locally (Windows)

1. Open terminal in project directory:
```bash
cd c:\Users\Dell\Downloads\FLK\flask_workspace
```

2. (Optional) Create DB backup:
```powershell
copy database\users.db database\users.db.bak
```

3. Start app:
```bash
python app.py
```

4. Open browser: http://127.0.0.1:5000

---

## Database notes & migrations

- The app uses `database/users.db`.
- On startup `app.py` runs a small helper to add `reset_token` column if missing:
  - This is safe to run repeatedly.
- Manual SQLite commands (if needed):
```bash
sqlite3 database\users.db
-- show columns
PRAGMA table_info(users);
-- delete test users
DELETE FROM users;
.quit
```

---

## Key file layout

- app.py — Flask application, routes and DB helpers
- templates/
  - base.html, register.html, login.html, forgot.html, reset.html, profile.html, ...
- static/
  - css/style.css
  - js/main.js
  - images/
- database/users.db — SQLite DB file

---

## Troubleshooting (common issues)

- Invalid credentials after reset/register
  - Ensure passwords are hashed at registration/reset (app uses Werkzeug).
  - Confirm stored password starts with `pbkdf2:` in DB.
  - Clear old test users if schema changes: use `DELETE FROM users;` in sqlite CLI.
- Reset page not found
  - Confirm `reset.html` exists and `forgot` route exposes a valid `/reset/<token>` link for testing.
- Browser caching/back button shows profile after logout
  - App sets cache headers and manipulates history; test in incognito to confirm behavior.

---

## Security & production notes

- Replace `app.secret_key` with a secure random key for production.
- Use HTTPS in production.
- Remove dev-only behaviors (exposing reset links in UI).
- Consider stronger email confirmation and token expiry for reset tokens.
- Use database migrations (Alembic) for schema changes in larger projects.

---

## Testing

Manual flow to verify:
1. Register new user.
2. Check DB for hashed password.
3. Login with same credentials.
4. Visit profile, then logout; verify Back does not reveal sensitive content.
5. Use Forgot: generate token, visit `/reset/<token>`, update password, verify login works.

Automated tests: add pytest tests that:
- Create a temporary DB
- Register/login flows
- Reset token lifecycle
- Route protections for `/profile`

---

## Contribution

Contributions welcome. Suggested ways to help:
- Add automated tests (pytest)
- Improve UX (custom modals, accessibility)
- Add email sending for reset links (SMTP or services)
- Add account verification and token expiry
- Implement migrations (Alembic) for schema management
- Containerize (Docker) and add CI workflows

How to contribute:
1. Fork the repo
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit changes and push
4. Open a Pull Request with description and screenshots/tests
5. Report issues via GitHub Issues

Please follow standard GitHub PR etiquette and include tests where appropriate.

---

## License

MIT — see LICENSE file if included.

---

## Contact / Maintainer

Open issues and PRs on the repository. Include reproducer steps and server logs for errors.

Thank you for checking out MyProfileApp — contributions and improvements are encouraged.
