"""
AI Financial Score (0-100).

Composite score based on:
  - Savings rate        (35%)
  - Income consistency  (20%)
  - Expense habits       (25%)  -> volatility / anomaly frequency
  - Budget control       (20%)  -> % of budgets not exceeded
"""
import numpy as np


def _score_savings_rate(income: float, expense: float) -> float:
    if income <= 0:
        return 0.0
    rate = (income - expense) / income
    # 0% savings -> 0 pts, 30%+ savings -> 100 pts, linear in between, clipped
    return float(np.clip(rate / 0.30 * 100, 0, 100))


def _score_income_consistency(monthly_incomes: list) -> float:
    if len(monthly_incomes) < 2:
        return 70.0  # not enough history, neutral score
    arr = np.array(monthly_incomes, dtype=float)
    mean = arr.mean()
    if mean == 0:
        return 0.0
    cv = arr.std() / mean  # coefficient of variation
    return float(np.clip(100 - cv * 100, 0, 100))


def _score_expense_habits(anomaly_count: int, total_transactions: int) -> float:
    if total_transactions == 0:
        return 70.0
    anomaly_ratio = anomaly_count / total_transactions
    return float(np.clip(100 - anomaly_ratio * 300, 0, 100))


def _score_budget_control(budgets_within_limit: int, total_budgets: int) -> float:
    if total_budgets == 0:
        return 70.0
    return float(np.clip(budgets_within_limit / total_budgets * 100, 0, 100))


def compute_financial_score(
    income: float,
    expense: float,
    monthly_incomes: list,
    anomaly_count: int,
    total_transactions: int,
    budgets_within_limit: int,
    total_budgets: int,
) -> dict:
    savings_rate_score = _score_savings_rate(income, expense)
    income_consistency_score = _score_income_consistency(monthly_incomes)
    expense_habits_score = _score_expense_habits(anomaly_count, total_transactions)
    budget_control_score = _score_budget_control(budgets_within_limit, total_budgets)

    final_score = (
        savings_rate_score * 0.35
        + income_consistency_score * 0.20
        + expense_habits_score * 0.25
        + budget_control_score * 0.20
    )

    if final_score >= 80:
        verdict = "Excellent financial health"
    elif final_score >= 60:
        verdict = "Good, with room to improve"
    elif final_score >= 40:
        verdict = "Fair — needs attention"
    else:
        verdict = "At risk — review your spending urgently"

    return {
        "score": round(final_score, 1),
        "savings_rate": round(savings_rate_score, 1),
        "income_consistency": round(income_consistency_score, 1),
        "expense_control": round(expense_habits_score, 1),
        "budget_adherence": round(budget_control_score, 1),
        "verdict": verdict,
    }
