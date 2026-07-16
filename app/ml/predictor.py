"""
Expense Prediction using scikit-learn.

Aggregates historical daily expenses into a time series, engineers simple
time-based features, then trains Linear Regression and Random Forest models,
picking whichever backtests better, to forecast next week / next month /
next year totals. Confidence score is derived from backtest R^2 and the
amount of history available.
"""
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "datasets", "models")
os.makedirs(MODEL_DIR, exist_ok=True)


def _build_daily_series(expenses: list) -> pd.DataFrame:
    """expenses: list of dicts with 'date' (datetime) and 'amount' (float)."""
    df = pd.DataFrame(expenses)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"]).dt.date
    daily = df.groupby("date")["amount"].sum().reset_index()
    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.set_index("date").asfreq("D", fill_value=0).reset_index()
    return daily


def _engineer_features(daily: pd.DataFrame) -> pd.DataFrame:
    daily = daily.copy()
    daily["day_index"] = np.arange(len(daily))
    daily["day_of_week"] = daily["date"].dt.dayofweek
    daily["day_of_month"] = daily["date"].dt.day
    daily["month"] = daily["date"].dt.month
    # 7-day rolling average as a lag/momentum feature
    daily["rolling_7"] = daily["amount"].rolling(7, min_periods=1).mean()
    return daily


def train_and_predict(expenses: list, horizon: str = "month", user_id: int = 0) -> dict:
    """
    horizon: 'week' | 'month' | 'year'
    Returns dict: predicted_amount, confidence_score, model_used
    """
    horizon_days = {"week": 7, "month": 30, "year": 365}.get(horizon, 30)

    daily = _build_daily_series(expenses)
    if daily.empty or len(daily) < 10:
        # Not enough history: fall back to a simple average-based heuristic.
        avg_daily = float(daily["amount"].mean()) if not daily.empty else 0.0
        return {
            "predicted_amount": round(avg_daily * horizon_days, 2),
            "confidence_score": 0.35,
            "model_used": "heuristic_average (insufficient history for ML)",
        }

    df = _engineer_features(daily)
    feature_cols = ["day_index", "day_of_week", "day_of_month", "month", "rolling_7"]
    X = df[feature_cols]
    y = df["amount"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    lr = LinearRegression().fit(X_train, y_train)
    rf = RandomForestRegressor(n_estimators=200, random_state=42).fit(X_train, y_train)

    lr_r2 = r2_score(y_test, lr.predict(X_test)) if len(X_test) > 1 else 0.0
    rf_r2 = r2_score(y_test, rf.predict(X_test)) if len(X_test) > 1 else 0.0

    best_model, best_name, best_r2 = (
        (rf, "RandomForestRegressor", rf_r2)
        if rf_r2 >= lr_r2
        else (lr, "LinearRegression", lr_r2)
    )

    # Save trained model for reuse.
    joblib.dump(best_model, os.path.join(MODEL_DIR, f"user_{user_id}_{horizon}_model.pkl"))

    # Forecast forward `horizon_days` and sum predicted daily spend.
    last_index = int(df["day_index"].max())
    last_date = df["date"].max()
    future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=horizon_days)
    rolling_last = float(df["rolling_7"].iloc[-1])

    future_df = pd.DataFrame({
        "day_index": np.arange(last_index + 1, last_index + 1 + horizon_days),
        "day_of_week": future_dates.dayofweek,
        "day_of_month": future_dates.day,
        "month": future_dates.month,
        "rolling_7": rolling_last,  # simple assumption: momentum holds
    })

    preds = best_model.predict(future_df[feature_cols])
    preds = np.clip(preds, 0, None)  # expenses can't be negative
    total_predicted = float(preds.sum())

    # Confidence: blend of backtest R^2 (clipped to [0,1]) and data volume.
    r2_component = float(np.clip(best_r2, 0, 1))
    volume_component = float(np.clip(len(df) / 180, 0, 1))  # 180 days = full confidence
    confidence = round(0.7 * r2_component + 0.3 * volume_component, 2)
    confidence = max(confidence, 0.3)  # never claim near-zero confidence

    return {
        "predicted_amount": round(total_predicted, 2),
        "confidence_score": confidence,
        "model_used": best_name,
    }
