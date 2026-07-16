"""
Income management endpoints: add, list, delete.
"""
import datetime as dt
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import extract

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/api/income", tags=["Income"])


@router.post("/", response_model=schemas.IncomeOut, status_code=201)
def add_income(
    payload: schemas.IncomeCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    income = models.Income(
        user_id=current_user.id,
        amount=payload.amount,
        source=payload.source,
        description=payload.description,
        date=payload.date or dt.datetime.utcnow(),
        is_recurring=payload.is_recurring,
        recurrence_interval_days=payload.recurrence_interval_days,
    )
    db.add(income)
    db.commit()
    db.refresh(income)
    return income


@router.get("/", response_model=List[schemas.IncomeOut])
def list_income(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
    month: Optional[str] = Query(None, description="YYYY-MM"),
):
    q = db.query(models.Income).filter(models.Income.user_id == current_user.id)
    if month:
        year, mon = month.split("-")
        q = q.filter(
            extract("year", models.Income.date) == int(year),
            extract("month", models.Income.date) == int(mon),
        )
    return q.order_by(models.Income.date.desc()).all()


@router.delete("/{income_id}", status_code=204)
def delete_income(
    income_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    income = db.query(models.Income).filter(
        models.Income.id == income_id, models.Income.user_id == current_user.id
    ).first()
    if not income:
        raise HTTPException(status_code=404, detail="Income not found")
    db.delete(income)
    db.commit()
    return None
