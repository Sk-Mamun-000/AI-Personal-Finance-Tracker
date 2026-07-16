"""
Dashboard, AI insights (advisor, financial score, monthly summary),
ML predictions, spending-pattern analysis, savings goals, and notifications.
"""
import datetime as dt
import calendar
from collections import Counter
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import extract, func

from app.database import get_db
from app import models, schemas, auth
from app.ai.advisor import get_financial_advice
from app.ai.financial_score import compute_financial_score
from app.ml.predictor import train_and_predict
from app.ml.anomaly import detect_anomalies

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard & AI Insights"])


def _month_bounds(now=None):
    now = now or dt.datetime.utcnow()
    return now.year, now.month


def _sum_for_month(db, model, user_id, year, month, amount_field="amount"):
    q = db.query(func.sum(getattr(model, amount_field))).filter(
        model.user_id == user_id,
        extract("year", model.date) == year,
        extract("month", model.date) == month,
    )
    return float(q.scalar() or 0.0)


def _build_context(db: Session, user: models.User) -> dict:
    year, month = _month_bounds()
    income = _sum_for_month(db, models.Income, user.id, year, month)
    expense = _sum_for_month(db, models.Expense, user.id, year, month)

    cat_totals = (
        db.query(models.Expense.category, func.sum(models.Expense.amount))
        .filter(
            models.Expense.user_id == user.id,
            extract("year", models.Expense.date) == year,
            extract("month", models.Expense.date) == month,
        )
        .group_by(models.Expense.category)
        .all()
    )
    top_category = max(cat_totals, key=lambda x: x[1])[0].value if cat_totals else "N/A"

    return {
        "total_income": income,
        "total_expenses": expense,
        "top_category": top_category,
    }


@router.get("/summary", response_model=schemas.DashboardSummary)
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    year, month = _month_bounds()
    today = dt.datetime.utcnow().date()

    total_income = _sum_for_month(db, models.Income, current_user.id, year, month)
    total_expenses = _sum_for_month(db, models.Expense, current_user.id, year, month)
    savings = total_income - total_expenses
    remaining_balance = savings  # simplistic; extend with carried-over balance if needed

    budget = db.query(models.Budget).filter(
        models.Budget.user_id == current_user.id,
        models.Budget.month == f"{year}-{month:02d}",
        models.Budget.category.is_(None),
    ).first()
    monthly_budget = budget.limit_amount if budget else 0.0

    today_spending = float(
        db.query(func.sum(models.Expense.amount)).filter(
            models.Expense.user_id == current_user.id,
            func.date(models.Expense.date) == today,
        ).scalar() or 0.0
    )

    recent = (
        db.query(models.Expense)
        .filter(models.Expense.user_id == current_user.id)
        .order_by(models.Expense.date.desc())
        .limit(10)
        .all()
    )

    score_data = _financial_score_internal(db, current_user)

    return schemas.DashboardSummary(
        total_income=total_income,
        total_expenses=total_expenses,
        savings=savings,
        remaining_balance=remaining_balance,
        monthly_budget=monthly_budget,
        today_spending=today_spending,
        financial_score=score_data["score"],
        recent_transactions=recent,
    )


def _financial_score_internal(db: Session, user: models.User) -> dict:
    year, month = _month_bounds()
    income = _sum_for_month(db, models.Income, user.id, year, month)
    expense = _sum_for_month(db, models.Expense, user.id, year, month)

    # Last 6 months of income for consistency measure
    monthly_incomes = []
    for i in range(6):
        d = dt.datetime.utcnow() - dt.timedelta(days=30 * i)
        monthly_incomes.append(_sum_for_month(db, models.Income, user.id, d.year, d.month))

    all_expenses = db.query(models.Expense).filter(models.Expense.user_id == user.id).all()
    total_tx = len(all_expenses)
    anomaly_count = sum(1 for e in all_expenses if e.is_anomaly)

    budgets = db.query(models.Budget).filter(models.Budget.user_id == user.id).all()
    within_limit = 0
    for b in budgets:
        spent = _sum_for_month(db, models.Expense, user.id,
                                *(int(x) for x in b.month.split("-")))
        if spent <= b.limit_amount:
            within_limit += 1

    return compute_financial_score(
        income=income, expense=expense, monthly_incomes=monthly_incomes,
        anomaly_count=anomaly_count, total_transactions=total_tx,
        budgets_within_limit=within_limit, total_budgets=len(budgets),
    )


@router.get("/financial-score", response_model=schemas.FinancialScoreOut)
def financial_score(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return _financial_score_internal(db, current_user)


@router.post("/advisor", response_model=schemas.AdvisorResponse)
def ai_advisor(
    payload: schemas.AdvisorRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    context = _build_context(db, current_user)
    answer = get_financial_advice(payload.question, context)
    return schemas.AdvisorResponse(answer=answer)


@router.get("/predict/{horizon}", response_model=schemas.PredictionOut)
def predict_expenses(
    horizon: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """horizon: week | month | year"""
    expenses = db.query(models.Expense).filter(models.Expense.user_id == current_user.id).all()
    data = [{"date": e.date, "amount": e.amount} for e in expenses]
    result = train_and_predict(data, horizon=horizon, user_id=current_user.id)

    db.add(models.Prediction(
        user_id=current_user.id, horizon=horizon,
        predicted_amount=result["predicted_amount"],
        confidence_score=result["confidence_score"],
        model_used=result["model_used"],
    ))
    db.commit()

    return schemas.PredictionOut(horizon=horizon, **result)


@router.get("/spending-pattern")
def spending_pattern(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    expenses = db.query(models.Expense).filter(models.Expense.user_id == current_user.id).all()
    if not expenses:
        return {"message": "No expense data yet."}

    cat_counter = Counter()
    day_totals = Counter()
    month_totals = Counter()
    for e in expenses:
        cat_counter[e.category.value] += e.amount
        day_totals[e.date.strftime("%Y-%m-%d")] += e.amount
        month_totals[e.date.strftime("%Y-%m")] += e.amount

    highest_category = max(cat_counter, key=cat_counter.get)
    most_expensive_day = max(day_totals, key=day_totals.get)
    most_expensive_month = max(month_totals, key=month_totals.get)

    num_days = len(day_totals)
    num_months = len(month_totals)
    total = sum(e.amount for e in expenses)

    return {
        "highest_spending_category": highest_category,
        "most_expensive_day": most_expensive_day,
        "most_expensive_month": most_expensive_month,
        "average_daily_expense": round(total / num_days, 2) if num_days else 0,
        "average_monthly_expense": round(total / num_months, 2) if num_months else 0,
        "category_breakdown": dict(cat_counter),
    }


@router.get("/anomalies")
def anomalies(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    expenses = db.query(models.Expense).filter(models.Expense.user_id == current_user.id).all()
    data = [{"id": e.id, "amount": e.amount, "category": e.category.value} for e in expenses]
    anomaly_ids = detect_anomalies(data)

    if anomaly_ids:
        db.query(models.Expense).filter(models.Expense.id.in_(anomaly_ids)).update(
            {models.Expense.is_anomaly: True}, synchronize_session=False
        )
        db.commit()

    flagged = db.query(models.Expense).filter(models.Expense.id.in_(anomaly_ids)).all()
    return [schemas.ExpenseOut.model_validate(e) for e in flagged]


@router.get("/monthly-summary")
def monthly_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """AI-generated monthly financial report: income, expenses, savings,
    recommendations, and next-month prediction."""
    year, month = _month_bounds()
    income = _sum_for_month(db, models.Income, current_user.id, year, month)
    expense = _sum_for_month(db, models.Expense, current_user.id, year, month)
    savings = income - expense
    score = _financial_score_internal(db, current_user)

    expenses = db.query(models.Expense).filter(models.Expense.user_id == current_user.id).all()
    pred = train_and_predict(
        [{"date": e.date, "amount": e.amount} for e in expenses],
        horizon="month", user_id=current_user.id,
    )
    advice = get_financial_advice("How can I save more?", {
        "total_income": income, "total_expenses": expense, "top_category": "N/A"
    })

    summary_text = (
        f"In {calendar.month_name[month]} {year}, you earned ₹{income:,.0f} and spent "
        f"₹{expense:,.0f}, saving ₹{savings:,.0f}. Your AI Financial Score is "
        f"{score['score']}/100 ({score['verdict']}). Next month's expenses are "
        f"predicted at ₹{pred['predicted_amount']:,.0f} "
        f"(confidence {pred['confidence_score']*100:.0f}%). {advice}"
    )

    report = models.FinancialReport(
        user_id=current_user.id, month=f"{year}-{month:02d}",
        total_income=income, total_expense=expense, savings=savings,
        financial_score=score["score"], summary_text=summary_text,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "month": report.month,
        "total_income": income,
        "total_expenses": expense,
        "savings": savings,
        "financial_score": score["score"],
        "next_month_prediction": pred,
        "summary": summary_text,
    }


# ---------- Savings Goals ----------
@router.post("/goals", response_model=schemas.GoalOut, status_code=201)
def create_goal(
    payload: schemas.GoalCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    goal = models.SavingsGoal(user_id=current_user.id, **payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.get("/goals", response_model=List[schemas.GoalOut])
def list_goals(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    goals = db.query(models.SavingsGoal).filter(models.SavingsGoal.user_id == current_user.id).all()
    for g in goals:
        if g.current_amount >= g.target_amount:
            exists = db.query(models.Notification).filter(
                models.Notification.user_id == current_user.id,
                models.Notification.title == f"Goal Achieved: {g.title}",
            ).first()
            if not exists:
                db.add(models.Notification(
                    user_id=current_user.id, title=f"Goal Achieved: {g.title}",
                    message=f"Congratulations! You reached your savings goal of ₹{g.target_amount:,.0f}.",
                    type="success",
                ))
    db.commit()
    return goals


# ---------- Notifications ----------
@router.get("/notifications")
def list_notifications(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    notifs = (
        db.query(models.Notification)
        .filter(models.Notification.user_id == current_user.id)
        .order_by(models.Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": n.id, "title": n.title, "message": n.message,
            "type": n.type, "is_read": n.is_read, "created_at": n.created_at,
        }
        for n in notifs
    ]


@router.put("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    n = db.query(models.Notification).filter(
        models.Notification.id == notification_id, models.Notification.user_id == current_user.id
    ).first()
    if n:
        n.is_read = True
        db.commit()
    return {"message": "ok"}
