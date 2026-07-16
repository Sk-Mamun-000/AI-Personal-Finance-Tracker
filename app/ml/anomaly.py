"""
Anomaly Detection using scikit-learn's Isolation Forest.

Flags unusual transactions (e.g. an outlier ₹50,000 "Food" expense) based on
amount + category context. Falls back to a simple z-score rule when there's
too little history to train Isolation Forest meaningfully.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


def detect_anomalies(expenses: list) -> list:
    """
    expenses: list of dicts with 'id', 'amount', 'category' (string)
    Returns: list of expense ids flagged as anomalies.
    """
    if len(expenses) < 8:
        return _zscore_fallback(expenses)

    df = pd.DataFrame(expenses)
    df["category_code"] = df["category"].astype("category").cat.codes

    X = df[["amount", "category_code"]].values
    model = IsolationForest(
        n_estimators=150, contamination="auto", random_state=42
    )
    df["anomaly_flag"] = model.fit_predict(X)  # -1 = anomaly, 1 = normal

    return df.loc[df["anomaly_flag"] == -1, "id"].tolist()


def _zscore_fallback(expenses: list) -> list:
    if len(expenses) < 3:
        return []
    df = pd.DataFrame(expenses)
    mean = df["amount"].mean()
    std = df["amount"].std() or 1.0
    df["z"] = (df["amount"] - mean) / std
    return df.loc[df["z"].abs() > 2.5, "id"].tolist()


def check_single_transaction(amount: float, category_history: list) -> bool:
    """
    Quick real-time check for a single new transaction against the user's
    historical amounts in the same category. Returns True if unusual.
    """
    if len(category_history) < 5:
        return False
    arr = np.array(category_history, dtype=float)
    mean, std = arr.mean(), (arr.std() or 1.0)
    z = (amount - mean) / std
    return bool(abs(z) > 2.5)
