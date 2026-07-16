"""
Database models: User, Expense, Income, Budget, SavingsGoal,
Prediction, Notification, FinancialReport.
"""
import enum
import datetime as dt

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean, Text
)
from sqlalchemy.orm import relationship

from app.database import Base


class PaymentMode(str, enum.Enum):
    CASH = "Cash"
    CARD = "Card"
    UPI = "UPI"
    NET_BANKING = "Net Banking"
    WALLET = "Wallet"
    OTHER = "Other"


class ExpenseCategory(str, enum.Enum):
    FOOD = "Food"
    TRANSPORT = "Transport"
    SHOPPING = "Shopping"
    BILLS = "Bills"
    EDUCATION = "Education"
    ENTERTAINMENT = "Entertainment"
    MEDICAL = "Medical"
    INVESTMENT = "Investment"
    TRAVEL = "Travel"
    OTHERS = "Others"


class IncomeSource(str, enum.Enum):
    SALARY = "Salary"
    FREELANCING = "Freelancing"
    BUSINESS = "Business"
    INTEREST = "Interest"
    INVESTMENT = "Investment"
    GIFT = "Gift"
    OTHERS = "Others"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    currency = Column(String(10), default="INR")
    language = Column(String(10), default="en")
    dark_mode = Column(Boolean, default=False)
    profile_picture = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    expenses = relationship("Expense", back_populates="owner", cascade="all, delete-orphan")
    incomes = relationship("Income", back_populates="owner", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="owner", cascade="all, delete-orphan")
    goals = relationship("SavingsGoal", back_populates="owner", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="owner", cascade="all, delete-orphan")
    reports = relationship("FinancialReport", back_populates="owner", cascade="all, delete-orphan")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(Enum(ExpenseCategory), nullable=False)
    description = Column(String(255), nullable=True)
    payment_mode = Column(Enum(PaymentMode), default=PaymentMode.CASH)
    tags = Column(String(255), nullable=True)  # comma separated
    date = Column(DateTime, default=dt.datetime.utcnow)
    is_recurring = Column(Boolean, default=False)
    recurrence_interval_days = Column(Integer, nullable=True)
    is_anomaly = Column(Boolean, default=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    owner = relationship("User", back_populates="expenses")


class Income(Base):
    __tablename__ = "incomes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    source = Column(Enum(IncomeSource), nullable=False)
    description = Column(String(255), nullable=True)
    date = Column(DateTime, default=dt.datetime.utcnow)
    is_recurring = Column(Boolean, default=False)
    recurrence_interval_days = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    owner = relationship("User", back_populates="incomes")


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(Enum(ExpenseCategory), nullable=True)  # null => overall monthly budget
    month = Column(String(7), nullable=False)  # "YYYY-MM"
    limit_amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    owner = relationship("User", back_populates="budgets")


class SavingsGoal(Base):
    __tablename__ = "savings_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(120), nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    target_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    owner = relationship("User", back_populates="goals")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    horizon = Column(String(20), nullable=False)  # week | month | year
    predicted_amount = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    model_used = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="info")  # info | warning | success
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    owner = relationship("User", back_populates="notifications")


class FinancialReport(Base):
    __tablename__ = "financial_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    month = Column(String(7), nullable=False)
    total_income = Column(Float, default=0.0)
    total_expense = Column(Float, default=0.0)
    savings = Column(Float, default=0.0)
    financial_score = Column(Float, default=0.0)
    summary_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    owner = relationship("User", back_populates="reports")
