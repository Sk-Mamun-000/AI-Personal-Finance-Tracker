"""
Budget Planner endpoints: create monthly/category budgets, track progress,
and auto-generate warning notifications at 70% / 90% / 100% utilization.
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import extract, func

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/api/budgets", tags=["Budget Planner"])


def _spent_amount(db: Session, user_id: int, month: str, category=None) -> float:
    year, mon = month.split("-")
    q = db.query(func.sum(models.Expense.amount)).filter(
        models.Expense.user_id == user_id,
        extract("year", models.Expense.date) == int(year),
        extract("month", models.Expense.date) == int(mon),
    )
    if category:
        q = q.filter(models.Expense.category == category)
    return float(q.scalar() or 0.0)


@router.post("/", response_model=schemas.BudgetOut, status_code=201)
def create_budget(
    payload: schemas.BudgetCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    budget = models.Budget(
        user_id=current_user.id,
        category=payload.category,
        month=payload.month,
        limit_amount=payload.limit_amount,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)

    spent = _spent_amount(db, current_user.id, budget.month, budget.category)
    percent = round((spent / budget.limit_amount * 100), 1) if budget.limit_amount else 0
    return schemas.BudgetOut(
        id=budget.id, category=budget.category, month=budget.month,
        limit_amount=budget.limit_amount, spent=spent, percent_used=percent,
    )


@router.get("/", response_model=List[schemas.BudgetOut])
def list_budgets(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
    month: str = None,
):
    q = db.query(models.Budget).filter(models.Budget.user_id == current_user.id)
    if month:
        q = q.filter(models.Budget.month == month)
    budgets = q.all()

    results = []
    for b in budgets:
        spent = _spent_amount(db, current_user.id, b.month, b.category)
        percent = round((spent / b.limit_amount * 100), 1) if b.limit_amount else 0

        # Emit warning notifications at thresholds (idempotent-ish: simple demo logic).
        if percent >= 100:
            msg, ntype = f"Budget exceeded for {b.category.value if b.category else 'Overall'} ({percent}%)", "warning"
        elif percent >= 90:
            msg, ntype = f"Budget at {percent}% for {b.category.value if b.category else 'Overall'} — almost there!", "warning"
        elif percent >= 70:
            msg, ntype = f"Budget at {percent}% for {b.category.value if b.category else 'Overall'}", "info"
        else:
            msg, ntype = None, None

        if msg:
            exists = db.query(models.Notification).filter(
                models.Notification.user_id == current_user.id,
                models.Notification.title == "Budget Alert",
                models.Notification.message == msg,
            ).first()
            if not exists:
                db.add(models.Notification(
                    user_id=current_user.id, title="Budget Alert", message=msg, type=ntype
                ))

        results.append(schemas.BudgetOut(
            id=b.id, category=b.category, month=b.month,
            limit_amount=b.limit_amount, spent=spent, percent_used=percent,
        ))
    db.commit()
    return results


@router.delete("/{budget_id}", status_code=204)
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    b = db.query(models.Budget).filter(
        models.Budget.id == budget_id, models.Budget.user_id == current_user.id
    ).first()
    if b:
        db.delete(b)
        db.commit()
    return None
