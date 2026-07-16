"""
Export endpoints: PDF report, Excel report, CSV export.
"""
import csv
import io
import datetime as dt

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import extract

from app.database import get_db
from app import models, auth
from app.utils.export import generate_pdf_report, generate_excel_report
from app.routers.dashboard_router import _financial_score_internal, _sum_for_month

router = APIRouter(prefix="/api/reports", tags=["Reports & Export"])


def _month_data(db: Session, user_id: int, month: str):
    year, mon = (int(x) for x in month.split("-"))
    expenses = db.query(models.Expense).filter(
        models.Expense.user_id == user_id,
        extract("year", models.Expense.date) == year,
        extract("month", models.Expense.date) == mon,
    ).order_by(models.Expense.date.desc()).all()
    incomes = db.query(models.Income).filter(
        models.Income.user_id == user_id,
        extract("year", models.Income.date) == year,
        extract("month", models.Income.date) == mon,
    ).all()
    return expenses, incomes


@router.get("/pdf")
def export_pdf(
    month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    expenses, incomes = _month_data(db, current_user.id, month)
    total_income = sum(i.amount for i in incomes)
    total_expense = sum(e.amount for e in expenses)
    score = _financial_score_internal(db, current_user)

    summary = {
        "total_income": total_income,
        "total_expenses": total_expense,
        "savings": total_income - total_expense,
        "financial_score": score["score"],
        "summary_text": f"AI verdict: {score['verdict']}. Savings rate score "
                         f"{score['savings_rate']}/100, budget adherence {score['budget_adherence']}/100.",
    }
    expense_dicts = [
        {"date": e.date, "category": e.category.value, "description": e.description, "amount": e.amount}
        for e in expenses
    ]

    pdf_bytes = generate_pdf_report(current_user.full_name, month, summary, expense_dicts)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=finance_report_{month}.pdf"},
    )


@router.get("/excel")
def export_excel(
    month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    expenses, incomes = _month_data(db, current_user.id, month)
    total_income = sum(i.amount for i in incomes)
    total_expense = sum(e.amount for e in expenses)
    score = _financial_score_internal(db, current_user)

    summary = {
        "total_income": total_income,
        "total_expenses": total_expense,
        "savings": total_income - total_expense,
        "financial_score": score["score"],
    }
    expense_dicts = [
        {"date": e.date, "category": e.category.value, "description": e.description,
         "payment_mode": e.payment_mode.value, "amount": e.amount, "is_anomaly": e.is_anomaly}
        for e in expenses
    ]
    income_dicts = [
        {"date": i.date, "source": i.source.value, "description": i.description, "amount": i.amount}
        for i in incomes
    ]

    excel_bytes = generate_excel_report(month, summary, expense_dicts, income_dicts)
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=finance_report_{month}.xlsx"},
    )


@router.get("/csv")
def export_csv(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    expenses = db.query(models.Expense).filter(models.Expense.user_id == current_user.id).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Date", "Category", "Description", "Payment Mode", "Amount", "Anomaly"])
    for e in expenses:
        writer.writerow([
            e.date.strftime("%Y-%m-%d"), e.category.value, e.description or "-",
            e.payment_mode.value, e.amount, "Yes" if e.is_anomaly else "No",
        ])

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=expenses_export.csv"},
    )
