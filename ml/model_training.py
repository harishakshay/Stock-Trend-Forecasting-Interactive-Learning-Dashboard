import os
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import joblib
from ml.model_utils import load_data, preprocess_data, plot_stock


def create_dataset(data, look_back=1):
  
    X, y = [], []
    for i in range(len(data) - look_back):
        X.append(data[i:(i + look_back), 0])
        y.append(data[i + look_back, 0])
    return np.array(X), np.array(y)

def train_model(file_path, look_back=5, save_model_path='ml/models/linear_model.pkl'):

    df = load_data(file_path)
    print("Data loaded successfully!")

    plot_stock(df, column='Close')

    data, scaler = preprocess_data(df, column='Close', scale=True)
    
    X, y = create_dataset(data, look_back)
    X = X.reshape(X.shape[0], X.shape[1])
    
    train_size = int(len(X)*0.8)
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]
    
    model = LinearRegression()
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
  
    if scaler:
        predictions = scaler.inverse_transform(predictions.reshape(-1,1))
        y_test_scaled = scaler.inverse_transform(y_test.reshape(-1,1))
    else:
        y_test_scaled = y_test

    mse = mean_squared_error(y_test_scaled, predictions)
    print(f"Mean Squared Error: {mse:.4f}")
    
    os.makedirs(os.path.dirname(save_model_path), exist_ok=True)
    joblib.dump(model, save_model_path)
    print(f"Model saved at {save_model_path}")
    
    return model, scaler

if __name__ == "__main__":
    
    file_path = '../data/stock_data.csv'
    model, scaler = train_model(file_path)
