"""
Pydantic request/response schemas.
"""
from __future__ import annotations
import datetime as dt
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

from app.models import ExpenseCategory, IncomeSource, PaymentMode


# ---------- Auth ----------
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    currency: str
    language: str
    dark_mode: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    currency: Optional[str] = None
    language: Optional[str] = None
    dark_mode: Optional[bool] = None


# ---------- Expense ----------
class ExpenseCreate(BaseModel):
    amount: float = Field(gt=0)
    category: Optional[ExpenseCategory] = None
    description: Optional[str] = None
    payment_mode: PaymentMode = PaymentMode.CASH
    tags: Optional[str] = None
    date: Optional[dt.datetime] = None
    is_recurring: bool = False
    recurrence_interval_days: Optional[int] = None


class ExpenseUpdate(BaseModel):
    amount: Optional[float] = None
    category: Optional[ExpenseCategory] = None
    description: Optional[str] = None
    payment_mode: Optional[PaymentMode] = None
    tags: Optional[str] = None
    date: Optional[dt.datetime] = None


class ExpenseOut(BaseModel):
    id: int
    amount: float
    category: ExpenseCategory
    description: Optional[str]
    payment_mode: PaymentMode
    tags: Optional[str]
    date: dt.datetime
    is_anomaly: bool

    class Config:
        from_attributes = True


# ---------- Income ----------
class IncomeCreate(BaseModel):
    amount: float = Field(gt=0)
    source: IncomeSource
    description: Optional[str] = None
    date: Optional[dt.datetime] = None
    is_recurring: bool = False
    recurrence_interval_days: Optional[int] = None


class IncomeOut(BaseModel):
    id: int
    amount: float
    source: IncomeSource
    description: Optional[str]
    date: dt.datetime

    class Config:
        from_attributes = True


# ---------- Budget ----------
class BudgetCreate(BaseModel):
    category: Optional[ExpenseCategory] = None
    month: str  # "YYYY-MM"
    limit_amount: float = Field(gt=0)


class BudgetOut(BaseModel):
    id: int
    category: Optional[ExpenseCategory]
    month: str
    limit_amount: float
    spent: float = 0.0
    percent_used: float = 0.0

    class Config:
        from_attributes = True


# ---------- Savings Goal ----------
class GoalCreate(BaseModel):
    title: str
    target_amount: float = Field(gt=0)
    current_amount: float = 0.0
    target_date: Optional[dt.datetime] = None


class GoalOut(BaseModel):
    id: int
    title: str
    target_amount: float
    current_amount: float
    target_date: Optional[dt.datetime]

    class Config:
        from_attributes = True


# ---------- AI / ML ----------
class CategorizeRequest(BaseModel):
    text: str


class CategorizeResponse(BaseModel):
    category: ExpenseCategory
    confidence: float


class AdvisorRequest(BaseModel):
    question: str


class AdvisorResponse(BaseModel):
    answer: str


class PredictionOut(BaseModel):
    horizon: str
    predicted_amount: float
    confidence_score: float
    model_used: str


class FinancialScoreOut(BaseModel):
    score: float
    savings_rate: float
    income_consistency: float
    expense_control: float
    budget_adherence: float
    verdict: str


class DashboardSummary(BaseModel):
    total_income: float
    total_expenses: float
    savings: float
    remaining_balance: float
    monthly_budget: float
    today_spending: float
    financial_score: float
    recent_transactions: List[ExpenseOut]
