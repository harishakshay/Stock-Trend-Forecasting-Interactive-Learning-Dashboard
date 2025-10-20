import pandas as pd
import matplotlib.pyplot as plt
import os
from sklearn.preprocessing import MinMaxScaler

import os
import pandas as pd

def load_data(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found.")
    
    ext = os.path.splitext(file_path)[1].lower()

    try:
        # --- Read file safely with fallback encodings ---
        if ext == '.csv':
            df = pd.read_csv(file_path, encoding='utf-8-sig', on_bad_lines='skip')
        elif ext in ['.xls', '.xlsx']:
            df = pd.read_excel(file_path)
        else:
            raise ValueError("File must be CSV or Excel.")
    except UnicodeDecodeError:
        # Fallback for non-UTF encodings
        df = pd.read_csv(file_path, encoding='ISO-8859-1', on_bad_lines='skip')

    # --- Clean data ---
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # remove unnamed columns
    df.dropna(how='any', inplace=True)                    # remove missing rows
    df.reset_index(drop=True, inplace=True)

    # --- Ensure proper date handling ---
    if 'Date' in df.columns:
        try:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
            df = df.dropna(subset=['Date'])
            df.sort_values('Date', inplace=True)
            df.reset_index(drop=True, inplace=True)
        except Exception as e:
            print(f"Warning: Could not parse Date column - {e}")

    return df

def preprocess_data(df, column='Close*', scale=True):
    data = df[[column]].values
    scaler = None
    if scale:
        scaler = MinMaxScaler(feature_range=(0,1))
        data = scaler.fit_transform(data)
    return data, scaler

def plot_stock(df, column='Close*'):
    plt.figure(figsize=(12,6))
    plt.plot(df['Date'], df[column], label=f'{column} Price')
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.title(f"{column} Price Trend")
    plt.legend()
    plt.grid(True)
    plt.show()
