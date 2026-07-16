"""
Expense management endpoints: CRUD, filtering, search, and AI-assisted
categorization for free-text expense descriptions.
"""
import datetime as dt
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import extract

from app.database import get_db
from app import models, schemas, auth
from app.ai.categorizer import categorize_expense
from app.ml.anomaly import check_single_transaction

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])


@router.post("/categorize", response_model=schemas.CategorizeResponse)
def categorize(payload: schemas.CategorizeRequest):
    """Given free text like 'Pizza' or 'Uber ride', suggest a category."""
    category, confidence = categorize_expense(payload.text)
    return schemas.CategorizeResponse(category=category, confidence=confidence)


@router.post("/", response_model=schemas.ExpenseOut, status_code=201)
def add_expense(
    payload: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    category = payload.category
    if category is None and payload.description:
        category, _ = categorize_expense(payload.description)
    if category is None:
        category = models.ExpenseCategory.OTHERS

    expense = models.Expense(
        user_id=current_user.id,
        amount=payload.amount,
        category=category,
        description=payload.description,
        payment_mode=payload.payment_mode,
        tags=payload.tags,
        date=payload.date or dt.datetime.utcnow(),
        is_recurring=payload.is_recurring,
        recurrence_interval_days=payload.recurrence_interval_days,
    )

    # Real-time anomaly check against category history.
    history = [
        e.amount for e in db.query(models.Expense)
        .filter(models.Expense.user_id == current_user.id, models.Expense.category == category)
        .all()
    ]
    expense.is_anomaly = check_single_transaction(payload.amount, history)

    db.add(expense)
    db.commit()
    db.refresh(expense)

    if expense.is_anomaly:
        db.add(models.Notification(
            user_id=current_user.id,
            title="Unusual Expense Detected",
            message=f"₹{expense.amount:,.0f} spent on {expense.category.value} looks unusual "
                    f"compared to your history.",
            type="warning",
        ))
        db.commit()

    return expense


@router.get("/", response_model=List[schemas.ExpenseOut])
def list_expenses(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
    category: Optional[models.ExpenseCategory] = None,
    payment_mode: Optional[models.PaymentMode] = None,
    month: Optional[str] = Query(None, description="YYYY-MM"),
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
):
    q = db.query(models.Expense).filter(models.Expense.user_id == current_user.id)

    if category:
        q = q.filter(models.Expense.category == category)
    if payment_mode:
        q = q.filter(models.Expense.payment_mode == payment_mode)
    if month:
        year, mon = month.split("-")
        q = q.filter(
            extract("year", models.Expense.date) == int(year),
            extract("month", models.Expense.date) == int(mon),
        )
    if min_amount is not None:
        q = q.filter(models.Expense.amount >= min_amount)
    if max_amount is not None:
        q = q.filter(models.Expense.amount <= max_amount)
    if tag:
        q = q.filter(models.Expense.tags.contains(tag))
    if search:
        q = q.filter(models.Expense.description.contains(search))

    return q.order_by(models.Expense.date.desc()).all()


@router.put("/{expense_id}", response_model=schemas.ExpenseOut)
def update_expense(
    expense_id: int,
    payload: schemas.ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    expense = db.query(models.Expense).filter(
        models.Expense.id == expense_id, models.Expense.user_id == current_user.id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(expense, field, value)

    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/{expense_id}", status_code=204)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    expense = db.query(models.Expense).filter(
        models.Expense.id == expense_id, models.Expense.user_id == current_user.id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()
    return None
