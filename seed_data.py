"""
Seed the database with a demo user and ~4 months of realistic sample
transactions, so the dashboard, charts, and AI/ML features have data to
work with immediately after setup.

Run with:
    python seed_data.py
"""
import random
import datetime as dt

from app.database import SessionLocal, init_db
from app import models, auth

random.seed(42)

DEMO_EMAIL = "demo@financetracker.ai"
DEMO_PASSWORD = "Demo@1234"

CATEGORY_RANGES = {
    models.ExpenseCategory.FOOD: (100, 900),
    models.ExpenseCategory.TRANSPORT: (50, 500),
    models.ExpenseCategory.SHOPPING: (300, 4000),
    models.ExpenseCategory.BILLS: (500, 3000),
    models.ExpenseCategory.EDUCATION: (200, 5000),
    models.ExpenseCategory.ENTERTAINMENT: (150, 1200),
    models.ExpenseCategory.MEDICAL: (200, 2500),
    models.ExpenseCategory.INVESTMENT: (1000, 10000),
    models.ExpenseCategory.TRAVEL: (500, 8000),
    models.ExpenseCategory.OTHERS: (100, 1000),
}

DESCRIPTIONS = {
    models.ExpenseCategory.FOOD: ["Pizza", "Groceries", "Swiggy order", "Cafe coffee", "Lunch"],
    models.ExpenseCategory.TRANSPORT: ["Uber ride", "Fuel", "Metro card recharge", "Auto fare"],
    models.ExpenseCategory.SHOPPING: ["Amazon order", "New shoes", "Flipkart electronics"],
    models.ExpenseCategory.BILLS: ["Electricity bill", "Internet bill", "Mobile recharge", "Rent"],
    models.ExpenseCategory.EDUCATION: ["Udemy course", "College fee", "Books"],
    models.ExpenseCategory.ENTERTAINMENT: ["Netflix subscription", "Movie tickets", "Concert"],
    models.ExpenseCategory.MEDICAL: ["Doctor visit", "Pharmacy", "Health checkup"],
    models.ExpenseCategory.INVESTMENT: ["SIP mutual fund", "Stock purchase"],
    models.ExpenseCategory.TRAVEL: ["Flight ticket", "Hotel booking", "Weekend trip"],
    models.ExpenseCategory.OTHERS: ["Miscellaneous", "Gift purchase"],
}


def seed():
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(models.User).filter(models.User.email == DEMO_EMAIL).first()
        if existing:
            print(f"Demo user already exists: {DEMO_EMAIL} / {DEMO_PASSWORD}")
            return

        user = models.User(
            full_name="Demo User",
            email=DEMO_EMAIL,
            hashed_password=auth.hash_password(DEMO_PASSWORD),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        today = dt.datetime.utcnow()
        start = today - dt.timedelta(days=120)

        # Monthly salary income
        d = start
        while d < today:
            db.add(models.Income(
                user_id=user.id, amount=random.randint(45000, 55000),
                source=models.IncomeSource.SALARY, description="Monthly salary",
                date=d.replace(day=1),
            ))
            d = (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1)

        # Occasional freelance income
        for _ in range(6):
            rand_day = start + dt.timedelta(days=random.randint(0, 119))
            db.add(models.Income(
                user_id=user.id, amount=random.randint(2000, 15000),
                source=models.IncomeSource.FREELANCING, description="Freelance project",
                date=rand_day,
            ))

        # Daily-ish expenses across categories
        d = start
        while d < today:
            for _ in range(random.randint(1, 4)):
                category = random.choice(list(CATEGORY_RANGES.keys()))
                low, high = CATEGORY_RANGES[category]
                amount = round(random.uniform(low, high), 2)
                desc = random.choice(DESCRIPTIONS[category])
                db.add(models.Expense(
                    user_id=user.id, amount=amount, category=category,
                    description=desc, payment_mode=random.choice(list(models.PaymentMode)),
                    date=d + dt.timedelta(hours=random.randint(8, 22)),
                ))
            d += dt.timedelta(days=1)

        # A couple of intentional anomalies for the ML demo
        db.add(models.Expense(
            user_id=user.id, amount=50000, category=models.ExpenseCategory.FOOD,
            description="Unusually large food order", date=today - dt.timedelta(days=3),
            is_anomaly=True,
        ))
        db.add(models.Expense(
            user_id=user.id, amount=25000, category=models.ExpenseCategory.SHOPPING,
            description="Surprise big purchase", date=today - dt.timedelta(days=7),
            is_anomaly=True,
        ))

        # Sample budget
        db.add(models.Budget(
            user_id=user.id, category=None, month=today.strftime("%Y-%m"), limit_amount=40000,
        ))
        db.add(models.Budget(
            user_id=user.id, category=models.ExpenseCategory.FOOD,
            month=today.strftime("%Y-%m"), limit_amount=6000,
        ))

        # Sample savings goal
        db.add(models.SavingsGoal(
            user_id=user.id, title="Emergency Fund", target_amount=100000,
            current_amount=35000, target_date=today + dt.timedelta(days=180),
        ))

        db.commit()
        print("Seed complete!")
        print(f"Demo login -> email: {DEMO_EMAIL} | password: {DEMO_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
