import os
import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "data/processed/transactions_train.csv"
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "transaction_fraud_model.keras"
SCALER_PATH = MODEL_DIR / "transaction_scaler.joblib"

def train_model():
    print(f"Loading data from {DATA_PATH}...")
    if not DATA_PATH.exists():
        print("Error: Training data not found.")
        return

    # Load data (use chunks if large, but for training we might need full dataset or sample)
    # For simplicity, let's load a sample if it's huge, or full if fits in memory.
    # The file could be large (7M rows). Let's load 1M rows for training to be fast.
    df = pd.read_csv(DATA_PATH, nrows=1000000)
    
    print(f"Loaded {len(df)} rows.")
    
    # Features and Target
    feature_cols = ['amount', 'avg_amount', 'is_weekend', 'amount_deviation']
    target_col = 'is_fraud'
    
    X = df[feature_cols]
    y = df[target_col]
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Scale
    print("Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Build Model
    print("Building model...")
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(16, activation='relu', input_shape=(len(feature_cols),)),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(8, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    
    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',
        metrics=['accuracy', tf.keras.metrics.AUC(name='auc')]
    )
    
    # Train
    print("Training model...")
    model.fit(
        X_train_scaled, y_train,
        epochs=5,
        batch_size=2048,
        validation_data=(X_test_scaled, y_test),
        verbose=1
    )
    
    # Save
    print(f"Saving model to {MODEL_PATH}...")
    model.save(MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print("✅ Model training complete.")

if __name__ == "__main__":
    train_model()
