from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
import pandas as pd
import joblib
import os
import numpy as np
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# ------------------ AUTH BLUEPRINT ------------------
auth_routes = Blueprint('auth_routes', __name__)

# ✅ Fix: Absolute database path (works no matter where you run Flask)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'data', 'users.db')
DB_PATH = os.path.normpath(DB_PATH)

# ✅ Initialize database if it doesn’t exist
def init_db():
    os.makedirs(os.path.join(BASE_DIR, '..', 'data'), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                 )''')
    # 👇 New profile table
    c.execute('''CREATE TABLE IF NOT EXISTS user_profile (
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
                )''')
    conn.commit()
    conn.close()

init_db()


# ------------------ AUTH ROUTES ------------------
@auth_routes.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_pw = generate_password_hash(password)

        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
            conn.commit()

            # ✅ Get new user ID
            c.execute("SELECT id FROM users WHERE username=?", (username,))
            user_id = c.fetchone()[0]
            conn.close()

            session['username'] = username
            session['user_id'] = user_id
            session['just_signed_up'] = True  # used to control profile redirect

            flash("Signup successful! Please complete your profile.", "success")
            return redirect(url_for('auth_routes.profile'))  # 👈 redirect to profile after signup

        except sqlite3.IntegrityError:
            flash("Username already exists.", "error")

    return render_template('signup.html')


@auth_routes.route('/view_profile', methods=['GET', 'POST'])
def profile():
    # Ensure user is logged in right after signup
    if 'user_id' not in session:
        return redirect(url_for('auth_routes.login'))

    if request.method == 'POST':
        data = {
            'full_name': request.form.get('full_name'),
            'age': request.form.get('age'),
            'occupation': request.form.get('occupation'),
            'salary': request.form.get('salary'),
            'expenses': request.form.get('expenses'),
            'investment_amt': request.form.get('investment_amt'),
            'savings_goal': request.form.get('savings_goal'),
            'risk_profile': request.form.get('risk_profile'),
            'investment_experience': request.form.get('investment_experience'),
            'investment_horizon': request.form.get('investment_horizon'),
            'preferred_instruments': ', '.join(request.form.getlist('preferred_instruments'))
        }

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''INSERT INTO user_profile (
                        user_id, full_name, age, occupation, salary, expenses,
                        investment_amt, savings_goal, risk_profile,
                        investment_experience, investment_horizon, preferred_instruments
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (session['user_id'], data['full_name'], data['age'], data['occupation'],
                   data['salary'], data['expenses'], data['investment_amt'], data['savings_goal'],
                   data['risk_profile'], data['investment_experience'],
                   data['investment_horizon'], data['preferred_instruments']))
        conn.commit()
        conn.close()

        session.pop('just_signed_up', None)
        flash("Profile saved successfully!", "success")
        return redirect(url_for('finance_routes.home'))

    return render_template('view_profile.html')


@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, password FROM users WHERE username=?", (username,))
        row = c.fetchone()
        conn.close()

        if row and check_password_hash(row[1], password):
            session['username'] = username
            session['user_id'] = row[0]
            flash("Login successful!", "success")
            return redirect(url_for('finance_routes.home'))
        else:
            flash("Invalid credentials.", "error")

    return render_template('login.html')


@auth_routes.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('finance_routes.home'))


# ------------------ FINANCE BLUEPRINT ------------------
finance_routes = Blueprint('finance_routes', __name__)

DATA_PATH = os.path.join('data', 'nifty_50.csv')
MODEL_PATH = os.path.join('ml', 'models', 'linear_model.pkl')
SCALER_X_PATH = os.path.join('ml', 'models', 'scaler_X.pkl')
SCALER_Y_PATH = os.path.join('ml', 'models', 'scaler_y.pkl')


# ---- Helper: Feature Engineering ----
def prepare_features(df):
    df['Daily_Change'] = df['Close'] - df['Open']
    df['Percent_Change'] = ((df['Close'] - df['Open']) / df['Open']) * 100
    df['MA_7'] = df['Close'].rolling(window=7).mean()
    df['MA_30'] = df['Close'].rolling(window=30).mean()
    df['Volatility'] = df['Percent_Change'].rolling(window=7).std()
    df = df.dropna()
    features = ['Open', 'High', 'Low', 'Daily_Change', 'Percent_Change', 'MA_7', 'MA_30', 'Volatility']
    return df, features


# ---- Home Dashboard ----
@finance_routes.route('/')
def home():
    df = pd.read_csv(DATA_PATH)
    dates = df['Date'].astype(str).tolist()
    prices = df['Close'].tolist()
    return render_template('dashboard.html', dates=dates, prices=prices)


# ---- Predict Dashboard ----
@finance_routes.route('/predict-dashboard')
def predict_dashboard():
    try:
        try:
            df = pd.read_csv(DATA_PATH, encoding='utf-8-sig')
        except UnicodeDecodeError:
            df = pd.read_csv(DATA_PATH, encoding='ISO-8859-1')

        df, features = prepare_features(df)
        closes = df['Close'].dropna().values
        last_30 = closes[-30:].tolist()

        if not (os.path.exists(MODEL_PATH) and os.path.exists(SCALER_X_PATH) and os.path.exists(SCALER_Y_PATH)):
            return "Model or scalers not found. Train it first.", 400

        model = joblib.load(MODEL_PATH)
        scaler_X = joblib.load(SCALER_X_PATH)
        scaler_y = joblib.load(SCALER_Y_PATH)

        X_latest = df[features].iloc[-1].values.reshape(1, -1)
        X_latest_scaled = scaler_X.transform(X_latest)
        pred_scaled = model.predict(X_latest_scaled)
        prediction = scaler_y.inverse_transform(pred_scaled.reshape(-1, 1))[0][0]

        recent = closes[-7:]
        trend = "Rising" if recent[-1] > recent[0] else "Falling"
        volatility = round(np.std(recent) / np.mean(recent) * 100, 2)

        risk = "Medium"
        if risk == "Low":
            suggestion = f"{trend} trend with volatility {volatility}%. Low-risk: hold or small investment."
        elif risk == "Medium":
            suggestion = f"{trend} trend with volatility {volatility}%. Medium-risk: moderate buy."
        else:
            suggestion = f"{trend} trend with volatility {volatility}%. High-risk: aggressive investment."

        return render_template(
            'predict_dashboard.html',
            prediction=round(float(prediction), 2),
            suggestion=suggestion,
            trend=trend,
            volatility=volatility,
            last_30_days=last_30
        )

    except Exception as e:
        return f"Error: {str(e)}", 500


# ---- Volatility Dashboard ----
@finance_routes.route('/volatility-dashboard')
def volatility_dashboard():
    df = pd.read_csv(DATA_PATH)
    daily_changes = df['Close'].pct_change()
    volatility = daily_changes.std() * 100
    spikes = daily_changes[daily_changes.abs() > 0.05].count()
    return render_template(
        'volatility_dashboard.html',
        volatility=round(volatility, 2),
        spikes=spikes,
        dates=df['Date'].astype(str).tolist(),
        prices=df['Close'].tolist(),
        daily_changes=daily_changes.fillna(0).tolist()
    )


# ---- Trend Dashboard ----
@finance_routes.route('/trend-dashboard')
def trend_dashboard():
    df = pd.read_csv(DATA_PATH)
    df['20_MA'] = df['Close'].rolling(window=20).mean()
    df['50_MA'] = df['Close'].rolling(window=50).mean()
    df['200_MA'] = df['Close'].rolling(window=200).mean()

    df['Daily_Return'] = df['Close'].pct_change() * 100
    df['Monthly_Return'] = df['Close'].pct_change(30) * 100
    df['Drawdown'] = ((df['Close'].cummax() - df['Close']) / df['Close'].cummax()) * 100

    if 'Volume' not in df.columns:
        df['Volume'] = 0
    volume = df['Volume'].fillna(0)

    delta = df['Close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    roll_up = up.rolling(14).mean()
    roll_down = down.rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + roll_up / roll_down))

    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26

    df['BB_Mid'] = df['Close'].rolling(20).mean()
    df['BB_Std'] = df['Close'].rolling(20).std()
    df['BB_Upper'] = df['BB_Mid'] + 2 * df['BB_Std']
    df['BB_Lower'] = df['BB_Mid'] - 2 * df['BB_Std']

    trend_pct = ((df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1) * 100
    highest_vol = df['Daily_Return'].abs().max()
    support_level = df['Close'].min()

    return render_template(
        'trend_dashboard.html',
        dates=df['Date'].astype(str).tolist(),
        prices=df['Close'].tolist(),
        ma20=df['20_MA'].fillna(0).tolist(),
        ma50=df['50_MA'].fillna(0).tolist(),
        ma200=df['200_MA'].fillna(0).tolist(),
        bb_upper=df['BB_Upper'].fillna(0).tolist(),
        bb_lower=df['BB_Lower'].fillna(0).tolist(),
        daily_return=df['Daily_Return'].fillna(0).tolist(),
        monthly_return=df['Monthly_Return'].fillna(0).tolist(),
        drawdown=df['Drawdown'].fillna(0).tolist(),
        volume=volume.tolist(),
        rsi=df['RSI'].fillna(0).tolist(),
        macd=df['MACD'].fillna(0).tolist(),
        trend_pct=round(trend_pct, 2),
        highest_vol=round(highest_vol, 2),
        support_level=round(support_level, 2)
    )


# ---- Predict Next Close Price API ----
@finance_routes.route('/predict-next', methods=['POST'])
def predict_next():
    try:
        data = request.get_json()
        risk = data.get('risk', 'Medium')

        df = pd.read_csv(DATA_PATH)
        df, features = prepare_features(df)
        last_prices = df['Close'].tail(30).tolist()

        if not (os.path.exists(MODEL_PATH) and os.path.exists(SCALER_X_PATH) and os.path.exists(SCALER_Y_PATH)):
            return jsonify({'error': 'Model or scalers not found. Train it first.'}), 400

        model = joblib.load(MODEL_PATH)
        scaler_X = joblib.load(SCALER_X_PATH)
        scaler_y = joblib.load(SCALER_Y_PATH)

        X_latest = df[features].iloc[-1].values.reshape(1, -1)
        X_latest_scaled = scaler_X.transform(X_latest)
        pred_scaled = model.predict(X_latest_scaled)
        prediction = scaler_y.inverse_transform(pred_scaled.reshape(-1, 1))[0][0]

        daily_return = df['Close'].pct_change().fillna(0) * 100
        trend = "Rising" if df['Close'].iloc[-1] > df['Close'].iloc[-6] else "Falling"
        volatility = round(daily_return.std(), 2)

        if risk == "Low":
            suggestion = f"{trend} trend with volatility {volatility}%. Low-risk: hold or small investment."
        elif risk == "Medium":
            suggestion = f"{trend} trend with volatility {volatility}%. Medium-risk: moderate buy."
        else:
            suggestion = f"{trend} trend with volatility {volatility}%. High-risk: aggressive investment."

        return jsonify({
            'prediction': round(float(prediction), 2),
            'suggestion': suggestion,
            'trend': trend,
            'volatility': volatility,
            'last_30_days': last_prices
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@finance_routes.route('/help_desk')
def help_desk():
    return render_template('help_desk.html')

