import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
import joblib

# --- Paths ---
DATA_PATH = os.path.join('data', 'nifty_50.csv')  # your dataset
MODEL_DIR = os.path.join('ml', 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'linear_model.pkl')
SCALER_X_PATH = os.path.join(MODEL_DIR, 'scaler_X.pkl')
SCALER_Y_PATH = os.path.join(MODEL_DIR, 'scaler_y.pkl')

# Create models directory if it doesn't exist
os.makedirs(MODEL_DIR, exist_ok=True)


# --- Load Data ---
df = pd.read_csv(DATA_PATH)
df.columns = df.columns.str.strip().str.replace('*', '', regex=False).str.replace(' ', '_')

df = pd.read_csv(DATA_PATH)

try:
    df = pd.read_csv(DATA_PATH, encoding='utf-8-sig')
except UnicodeDecodeError:
    # Fallback if utf-8 fails
    df = pd.read_csv(DATA_PATH, encoding='ISO-8859-1')

# Fix date parsing for Indian date format
df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y')

# Sort by date to make sure it's in order
df = df.sort_values('Date')

# Keep necessary columns
df = df[['Date', 'Open', 'High', 'Low', 'Close']]

# Convert Date and sort
df['Date'] = pd.to_datetime(df['Date'])
df = df.sort_values('Date')

# --- Feature Engineering ---
df['Daily_Change'] = df['Close'] - df['Open']
df['Percent_Change'] = ((df['Close'] - df['Open']) / df['Open']) * 100
df['MA_7'] = df['Close'].rolling(window=7).mean()
df['MA_30'] = df['Close'].rolling(window=30).mean()
df['Volatility'] = df['Percent_Change'].rolling(window=7).std()

df = df.dropna()

# --- Prepare Dataset ---
features = ['Open', 'High', 'Low', 'Daily_Change', 'Percent_Change', 'MA_7', 'MA_30', 'Volatility']
X = df[features].values
y = df['Close'].shift(-1).dropna().values  # predict next day's close

# Align X and y (since y shifted)
X = X[:-1]
y = y.reshape(-1, 1)

# --- Scale Data ---
scaler_X = MinMaxScaler()
scaler_y = MinMaxScaler()
X_scaled = scaler_X.fit_transform(X)
y_scaled = scaler_y.fit_transform(y)

# --- Train Model ---
model = LinearRegression()
model.fit(X_scaled, y_scaled)

# --- Save Model and Scalers ---
joblib.dump(model, MODEL_PATH)
joblib.dump(scaler_X, SCALER_X_PATH)
joblib.dump(scaler_y, SCALER_Y_PATH)

print(f"Model saved at: {MODEL_PATH}")
print("Training complete! You can now use the Predict Next Close Price page.")
