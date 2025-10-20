from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

# ------------------- Blueprint -------------------
auth_routes = Blueprint('auth_routes', __name__)

# ------------------- Database Setup -------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'data', 'users.db')
DB_PATH = os.path.normpath(DB_PATH)

def init_db():
    os.makedirs(os.path.join(BASE_DIR, '..', 'data'), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # User profile table
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            full_name TEXT,
            age INTEGER,
            occupation TEXT,
            salary REAL,
            expenses REAL,
            investment_amt REAL,
            savings_goal TEXT,
            risk_profile TEXT,
            investment_experience TEXT,
            investment_horizon TEXT,
            preferred_instruments TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

# Initialize DB
init_db()

@auth_routes.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        try:
            # Use "with" to auto-handle connection closing
            with sqlite3.connect(DB_PATH, timeout=5) as conn:
                c = conn.cursor()
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
                conn.commit()

                # Fetch user_id
                c.execute("SELECT id FROM users WHERE username = ?", (username,))
                user_id = c.fetchone()[0]

            # Save in session
            session['user_id'] = user_id
            session['username'] = username
            session['just_signed_up'] = True

            flash('Signup successful! Please complete your profile.', 'info')
            return redirect(url_for('auth_routes.profile'))

        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose another.', 'danger')
        except sqlite3.OperationalError as e:
            flash(f'Database is busy, try again. ({str(e)})', 'danger')

    return render_template('signup.html')

# ------------------- Profile Route -------------------
@auth_routes.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash("You need to login first!", "warning")
        return redirect(url_for('auth_routes.login'))

    # Only show profile form right after signup
    if not session.get('just_signed_up'):
        return redirect(url_for('finance_routes.home'))

    if request.method == 'POST':
        full_name = request.form['full_name']
        age = request.form['age']
        occupation = request.form['occupation']
        salary = request.form['salary']
        expenses = request.form['expenses']
        investment_amt = request.form['investment_amt']
        savings_goal = request.form['savings_goal']
        risk_profile = request.form['risk_profile']
        investment_experience = request.form['investment_experience']
        investment_horizon = request.form['investment_horizon']
        preferred_instruments = ', '.join(request.form.getlist('preferred_instruments'))

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO user_profile (
                user_id, full_name, age, occupation, salary, expenses, investment_amt,
                savings_goal, risk_profile, investment_experience, investment_horizon, preferred_instruments
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session['user_id'], full_name, age, occupation, salary, expenses, investment_amt,
            savings_goal, risk_profile, investment_experience, investment_horizon, preferred_instruments
        ))
        conn.commit()
        conn.close()

        session.pop('just_signed_up', None)  # Remove flag
        flash('Profile saved successfully!', 'success')
        return redirect(url_for('finance_routes.home'))

    return render_template('profile.html')

# ------------------- Login Route -------------------
@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('finance_routes.home'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

# ------------------- Logout Route -------------------
@auth_routes.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth_routes.login'))

@auth_routes.route('/view-profile')
def view_profile():
    if 'user_id' not in session:
        flash("You need to login first!", "warning")
        return redirect(url_for('auth_routes.login'))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets you access columns by name
    c = conn.cursor()
    c.execute("SELECT * FROM user_profile WHERE user_id = ?", (session['user_id'],))
    profile = c.fetchone()
    conn.close()

    return render_template('view_profile.html', profile=profile)

