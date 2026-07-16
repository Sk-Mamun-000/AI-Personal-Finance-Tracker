# 💰 AI Personal Finance & Expense Tracker

An AI-powered personal finance management system built with **FastAPI**, **SQLAlchemy**,
**Streamlit**, and **scikit-learn**. Track income and expenses, plan budgets, get AI-generated
financial advice, forecast future spending with ML, and export professional reports — all from
a modern glassmorphism-styled dashboard.

Built as a final-year B.Tech/B.E. Computer Science project demonstrating full-stack Python
development, applied machine learning, and clean software architecture.

---

## ✅ What's implemented

| Area | Status |
|---|---|
| JWT authentication (register/login/logout, bcrypt hashing) | ✅ |
| Profile management | ✅ |
| Expense CRUD + filtering (category/date/month/amount/tags/payment mode) + search | ✅ |
| Income CRUD (Salary, Freelancing, Business, Interest, Investment, Gift, Others) | ✅ |
| Budget planner with 70/90/100% threshold warnings | ✅ |
| Smart expense categorization (rule-based NLP, optional OpenAI/Gemini) | ✅ |
| AI financial advisor (Q&A: "Can I afford X?", "Am I overspending?", "How to save more?") | ✅ |
| Expense prediction (Linear Regression + Random Forest, auto-picks the better model) | ✅ |
| Spending pattern analysis (top category, priciest day/month, averages) | ✅ |
| Anomaly detection (Isolation Forest + z-score fallback) | ✅ |
| AI Financial Score (0–100, composite of savings rate / income consistency / expense habits / budget control) | ✅ |
| AI monthly summary report generator | ✅ |
| Interactive charts (pie, line trend, income vs expense, heatmap) via Plotly | ✅ |
| Savings goal tracker | ✅ |
| Notifications (budget alerts, anomaly alerts, goal achieved) | ✅ |
| PDF / Excel / CSV export | ✅ |
| Settings (currency, dark mode UI, profile) | ✅ |
| Docker + docker-compose (backend, Streamlit frontend, PostgreSQL) | ✅ |
| Unit / API / integration tests (pytest) | ✅ |
| Seed script with 4 months of realistic sample data | ✅ |

### 📌 Documented future scope (not implemented in this build)

These were in the original wishlist but need external services, hardware access, or
paid APIs that don't belong hard-coded into a student project by default. They're
straightforward to add on top of this architecture — notes on how are in
[Future Scope](#-future-scope) below:

- Receipt OCR (Tesseract)
- Voice expense entry
- Google Login (OAuth)
- Google Calendar bill reminders
- Automated email delivery of monthly reports
- Multi-user org/team support (current build is single-tenant per user account)
- Alembic migration files (the schema is Alembic-ready; `alembic init` + one
  `alembic revision --autogenerate` gets you versioned migrations — omitted here
  since SQLite dev setups typically just use `init_db()`)

---

## 🏗️ Architecture

```
Finance_AI_Tracker/
├── app/
│   ├── main.py                # FastAPI app entrypoint, routers, CORS, rate limiting
│   ├── config.py               # Settings via pydantic-settings / .env
│   ├── database.py             # SQLAlchemy engine/session/Base
│   ├── models.py                # ORM models: User, Expense, Income, Budget, etc.
│   ├── schemas.py                # Pydantic request/response schemas
│   ├── auth.py                    # JWT + bcrypt password hashing
│   ├── ai/
│   │   ├── categorizer.py          # Smart expense categorization
│   │   ├── advisor.py               # AI financial advisor Q&A
│   │   └── financial_score.py        # 0-100 financial health score
│   ├── ml/
│   │   ├── predictor.py               # Linear Regression / Random Forest forecasting
│   │   └── anomaly.py                  # Isolation Forest anomaly detection
│   ├── routers/
│   │   ├── auth_router.py               # /api/auth/*
│   │   ├── expense_router.py             # /api/expenses/*
│   │   ├── income_router.py               # /api/income/*
│   │   ├── budget_router.py                # /api/budgets/*
│   │   ├── dashboard_router.py              # /api/dashboard/* (AI/ML/goals/notifications)
│   │   └── reports_router.py                 # /api/reports/* (PDF/Excel/CSV)
│   └── utils/
│       └── export.py                          # PDF & Excel report builders
├── frontend/
│   └── streamlit_app.py           # Full Streamlit UI (dashboard, forms, charts)
├── tests/
│   └── test_api.py                 # pytest suite
├── datasets/                        # trained ML models saved here at runtime
├── reports/                          # generated report artifacts
├── seed_data.py                       # demo user + 4 months of sample transactions
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

**Design principles applied:** layered architecture (routers → services/ai/ml →
models), dependency injection via FastAPI `Depends`, Pydantic-validated I/O at every
boundary, stateless JWT auth, and ML models saved/reloadable via `joblib`.

---

## 🚀 Installation Guide

### 1. Clone & set up a virtual environment
```bash
cd Finance_AI_Tracker
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env — at minimum set a real SECRET_KEY.
# AI_PROVIDER defaults to "none" — the app works fully offline with rule-based
# AI categorization/advice. Set AI_PROVIDER=openai and OPENAI_API_KEY to use a
# real LLM instead.
```

### 4. Seed sample data (recommended for first run / demo)
```bash
python seed_data.py
# Prints demo login credentials, e.g. demo@financetracker.ai / Demo@1234
```

### 5. Run the backend (FastAPI)
```bash
uvicorn app.main:app --reload
# API docs: http://localhost:8000/docs
```

### 6. Run the frontend (Streamlit), in a second terminal
```bash
streamlit run frontend/streamlit_app.py
# UI: http://localhost:8501
```

### Docker (alternative, runs backend + frontend + PostgreSQL together)
```bash
docker-compose up --build
# Backend:  http://localhost:8000/docs
# Frontend: http://localhost:8501
```

### Run tests
```bash
pytest -v
```

---

## 📖 API Documentation

Interactive Swagger docs are auto-generated by FastAPI at **`/docs`** (ReDoc at `/redoc`)
once the backend is running. Key endpoint groups:

- `POST /api/auth/register`, `POST /api/auth/login`, `GET/PUT /api/auth/me`
- `POST/GET/PUT/DELETE /api/expenses/` + `POST /api/expenses/categorize`
- `POST/GET/DELETE /api/income/`
- `POST/GET/DELETE /api/budgets/`
- `GET /api/dashboard/summary`, `/financial-score`, `/spending-pattern`, `/anomalies`,
  `/monthly-summary`
- `POST /api/dashboard/advisor` — AI financial Q&A
- `GET /api/dashboard/predict/{week|month|year}` — ML expense forecast
- `POST/GET /api/dashboard/goals`, `GET/PUT /api/dashboard/notifications`
- `GET /api/reports/pdf`, `/excel`, `/csv`

All endpoints except `/api/auth/register`, `/api/auth/login`, and
`/api/expenses/categorize` require a Bearer JWT (`Authorization: Bearer <token>`).

---

## 🤖 How the AI/ML features work

- **Smart categorization** — keyword/NLP rule engine covering common merchants and
  spend types (Pizza→Food, Uber→Transport, Netflix→Entertainment, Electricity→Bills,
  etc.), with an optional LLM path if you supply an OpenAI/Gemini key.
- **AI Financial Advisor** — computes real context (this month's income/expenses/top
  category) and either asks an LLM or runs a deterministic rule engine to answer
  savings/affordability/overspending questions.
- **Expense Prediction** — builds a daily time series from transaction history,
  engineers day-of-week/day-of-month/rolling-average features, trains both Linear
  Regression and Random Forest, backtests with a train/test split, and picks
  whichever generalizes better. Confidence blends backtest R² with data volume.
- **Anomaly Detection** — Isolation Forest over `(amount, category)`, with a z-score
  fallback when history is too small for the forest to be meaningful. New
  transactions are also checked in real time against their category's history.
- **AI Financial Score** — weighted composite: savings rate (35%), income
  consistency (20%, coefficient of variation across recent months), expense habits
  (25%, anomaly ratio), budget adherence (20%, % of budgets kept under limit).

---

## 🔒 Security notes

- Passwords hashed with **bcrypt** (via passlib), never stored in plaintext.
- **JWT** bearer tokens with configurable expiry.
- Pydantic schemas validate all input (rejects malformed types/ranges).
- SQLAlchemy ORM parameterizes all queries (no raw SQL string concatenation) →
  protects against SQL injection.
- `slowapi` rate limiting wired on the root endpoint as a demonstrated pattern;
  extend `@limiter.limit(...)` to other routes for production.
- CORS is wide-open (`*`) for local development — **tighten `allow_origins` in
  `app/main.py` before deploying**.
- XSS/CSRF: Streamlit and the JSON API architecture avoid classic server-rendered-HTML
  injection vectors; if you add a browser-based SPA frontend later, add explicit
  CSRF tokens for cookie-based sessions (this build uses header-based JWT, which is
  inherently CSRF-resistant).

---

## 🔮 Future Scope

- **Receipt OCR** — add `pytesseract` + `Pillow`, a new `/api/expenses/ocr` endpoint
  accepting an image upload, extract total/date/merchant, and prefill the add-expense
  form.
- **Voice expense entry** — capture audio in the Streamlit frontend, transcribe via
  `openai-whisper` or a cloud STT API, then pass the transcript into the existing
  `/api/expenses/categorize` + add-expense flow.
- **Google Login** — add `authlib` OAuth2 flow, map Google profile to the existing
  `User` model.
- **Google Calendar bill reminders** — use the Google Calendar API to create events
  from recurring `Expense`/`Budget` records.
- **Emailed monthly reports** — schedule (e.g. APScheduler/Celery beat) a monthly job
  that calls `/api/dashboard/monthly-summary` + `/api/reports/pdf` and emails the
  result via SMTP/SendGrid.
- **Alembic migrations** — run `alembic init alembic`, point `sqlalchemy.url` at
  `DATABASE_URL`, then `alembic revision --autogenerate -m "init"` to version the
  schema already defined in `app/models.py`.

---

## 📊 ER Diagram (textual)

```
User (1) ───< Expense
User (1) ───< Income
User (1) ───< Budget
User (1) ───< SavingsGoal
User (1) ───< Notification
User (1) ───< FinancialReport
User (1) ───< Prediction
```

Each child table holds a `user_id` foreign key back to `User`; all queries are scoped
to `current_user.id` via the JWT-authenticated dependency, so users only ever see
their own data.

---

## 🧑‍💻 Tech Stack Summary

**Backend:** Python 3.12, FastAPI, SQLAlchemy ORM, SQLite (dev) / PostgreSQL (prod)
**Frontend:** Streamlit (Plotly charts, glassmorphism theme)
**Auth:** JWT (python-jose) + bcrypt (passlib)
**AI:** rule-based NLP categorizer/advisor with optional OpenAI/Gemini integration
**ML:** scikit-learn — Linear Regression, Random Forest, Isolation Forest
**Reports:** ReportLab (PDF), openpyxl (Excel), csv (CSV)
**Testing:** pytest + FastAPI TestClient
**Deployment:** Docker, docker-compose (backend + frontend + PostgreSQL)

---

## 📄 License

Provided as an educational/academic project template. Adapt freely for coursework.
