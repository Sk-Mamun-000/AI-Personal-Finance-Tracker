"""
AI Personal Finance & Expense Tracker — Streamlit Frontend.

Run with:
    streamlit run frontend/streamlit_app.py

Requires the FastAPI backend running at BACKEND_URL (default http://localhost:8000).
"""
import os
import datetime as dt

import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="AI Finance Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Styling — glassmorphism-inspired theme
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }
    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.95);
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.06);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        padding: 18px 20px;
        margin-bottom: 10px;
    }
    .metric-label { color: #94a3b8; font-size: 0.85rem; font-weight: 500; }
    .metric-value { color: #f1f5f9; font-size: 1.7rem; font-weight: 700; }
    .score-badge {
        display: inline-block; padding: 6px 14px; border-radius: 999px;
        font-weight: 700; font-size: 1.1rem;
        background: linear-gradient(90deg,#6366f1,#8b5cf6); color: white;
    }
    h1, h2, h3 { color: #f1f5f9 !important; }
    .stButton>button {
        border-radius: 10px; border: none;
        background: linear-gradient(90deg,#6366f1,#8b5cf6); color: white; font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state / API helpers
# ---------------------------------------------------------------------------
if "token" not in st.session_state:
    st.session_state.token = None
    st.session_state.user = None


def api_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}


def api_get(path, params=None):
    r = requests.get(f"{BACKEND_URL}{path}", headers=api_headers(), params=params)
    return r


def api_post(path, json_body=None, data=None):
    r = requests.post(f"{BACKEND_URL}{path}", headers=api_headers(), json=json_body, data=data)
    return r


def api_put(path, json_body=None):
    r = requests.put(f"{BACKEND_URL}{path}", headers=api_headers(), json=json_body)
    return r


def api_delete(path):
    r = requests.delete(f"{BACKEND_URL}{path}", headers=api_headers())
    return r


# ---------------------------------------------------------------------------
# Auth screens
# ---------------------------------------------------------------------------
def login_register_screen():
    st.markdown("<h1 style='text-align:center;'>💰 AI Personal Finance Tracker</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#94a3b8;'>Track. Predict. Save smarter — with AI.</p>", unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["🔐 Login", "🆕 Register"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
        if submitted:
            resp = api_post("/api/auth/login", data={"username": email, "password": password})
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.token = data["access_token"]
                st.session_state.user = data["user"]
                st.success("Logged in!")
                st.rerun()
            else:
                st.error(resp.json().get("detail", "Login failed"))

    with tab_register:
        with st.form("register_form"):
            name = st.text_input("Full Name")
            email_r = st.text_input("Email", key="reg_email")
            password_r = st.text_input("Password", type="password", key="reg_pass")
            submitted_r = st.form_submit_button("Create Account", use_container_width=True)
        if submitted_r:
            resp = api_post("/api/auth/register", json_body={
                "full_name": name, "email": email_r, "password": password_r
            })
            if resp.status_code == 201:
                data = resp.json()
                st.session_state.token = data["access_token"]
                st.session_state.user = data["user"]
                st.success("Account created!")
                st.rerun()
            else:
                st.error(resp.json().get("detail", "Registration failed"))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
def render_metric(label, value, prefix="₹"):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{prefix}{value:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)


def dashboard_page():
    st.header("📊 Dashboard")
    resp = api_get("/api/dashboard/summary")
    if resp.status_code != 200:
        st.warning("Could not load dashboard. Add some income/expenses first.")
        return
    d = resp.json()

    c1, c2, c3, c4 = st.columns(4)
    with c1: render_metric("Total Income", d["total_income"])
    with c2: render_metric("Total Expenses", d["total_expenses"])
    with c3: render_metric("Savings", d["savings"])
    with c4: render_metric("Today's Spending", d["today_spending"])

    c5, c6 = st.columns([1, 2])
    with c5:
        st.markdown("### 🤖 AI Financial Score")
        score = d["financial_score"]
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=score,
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#8b5cf6"},
                "steps": [
                    {"range": [0, 40], "color": "#7f1d1d"},
                    {"range": [40, 70], "color": "#78350f"},
                    {"range": [70, 100], "color": "#14532d"},
                ],
            },
            domain={"x": [0, 1], "y": [0, 1]},
        ))
        fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10),
                           paper_bgcolor="rgba(0,0,0,0)", font_color="#f1f5f9")
        st.plotly_chart(fig, use_container_width=True)

    with c6:
        st.markdown("### 🧾 Recent Transactions")
        if d["recent_transactions"]:
            df = pd.DataFrame(d["recent_transactions"])
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
            st.dataframe(
                df[["date", "category", "description", "amount", "is_anomaly"]],
                use_container_width=True, hide_index=True,
            )
        else:
            st.info("No transactions yet.")


# ---------------------------------------------------------------------------
# Expenses page
# ---------------------------------------------------------------------------
CATEGORIES = ["Food", "Transport", "Shopping", "Bills", "Education",
              "Entertainment", "Medical", "Investment", "Travel", "Others"]
PAYMENT_MODES = ["Cash", "Card", "UPI", "Net Banking", "Wallet", "Other"]


def expenses_page():
    st.header("💸 Expense Management")

    with st.expander("➕ Add New Expense", expanded=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            description = st.text_input("Description (e.g. 'Pizza', 'Uber ride')", key="exp_desc")
        with col2:
            if st.button("🤖 Suggest Category"):
                if description:
                    r = api_post("/api/expenses/categorize", json_body={"text": description})
                    if r.status_code == 200:
                        res = r.json()
                        st.session_state["suggested_cat"] = res["category"]
                        st.success(f"AI suggests: **{res['category']}** ({res['confidence']*100:.0f}% confidence)")

        default_cat_idx = CATEGORIES.index(st.session_state.get("suggested_cat", "Others")) \
            if st.session_state.get("suggested_cat") in CATEGORIES else 9

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0)
        with c2:
            category = st.selectbox("Category", CATEGORIES, index=default_cat_idx)
        with c3:
            payment_mode = st.selectbox("Payment Mode", PAYMENT_MODES)
        with c4:
            date = st.date_input("Date", value=dt.date.today())
        tags = st.text_input("Tags (comma separated)")

        if st.button("Save Expense", use_container_width=True):
            payload = {
                "amount": amount, "category": category, "description": description,
                "payment_mode": payment_mode, "tags": tags,
                "date": dt.datetime.combine(date, dt.datetime.min.time()).isoformat(),
            }
            r = api_post("/api/expenses/", json_body=payload)
            if r.status_code == 201:
                res = r.json()
                st.success("Expense added!")
                if res.get("is_anomaly"):
                    st.warning("⚠️ Unusual Expense Detected — this is well outside your usual spending in this category.")
                st.rerun()
            else:
                st.error(r.text)

    st.markdown("### 🔍 Filter & Search")
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        f_category = st.selectbox("Category", ["All"] + CATEGORIES, key="f_cat")
    with fc2:
        f_month = st.text_input("Month (YYYY-MM)", value=dt.date.today().strftime("%Y-%m"))
    with fc3:
        f_search = st.text_input("Search description")
    with fc4:
        f_payment = st.selectbox("Payment Mode", ["All"] + PAYMENT_MODES, key="f_pay")

    params = {"month": f_month} if f_month else {}
    if f_category != "All":
        params["category"] = f_category
    if f_payment != "All":
        params["payment_mode"] = f_payment
    if f_search:
        params["search"] = f_search

    r = api_get("/api/expenses/", params=params)
    if r.status_code == 200 and r.json():
        df = pd.DataFrame(r.json())
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        st.dataframe(df, use_container_width=True, hide_index=True)

        del_id = st.number_input("Expense ID to delete", min_value=0, step=1)
        if st.button("🗑️ Delete Expense"):
            dr = api_delete(f"/api/expenses/{del_id}")
            if dr.status_code == 204:
                st.success("Deleted.")
                st.rerun()
    else:
        st.info("No expenses found for these filters.")


# ---------------------------------------------------------------------------
# Income page
# ---------------------------------------------------------------------------
INCOME_SOURCES = ["Salary", "Freelancing", "Business", "Interest", "Investment", "Gift", "Others"]


def income_page():
    st.header("💵 Income Management")

    with st.expander("➕ Add Income", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0, key="inc_amt")
        with c2:
            source = st.selectbox("Source", INCOME_SOURCES)
        with c3:
            date = st.date_input("Date", value=dt.date.today(), key="inc_date")
        description = st.text_input("Description", key="inc_desc")

        if st.button("Save Income", use_container_width=True):
            payload = {
                "amount": amount, "source": source, "description": description,
                "date": dt.datetime.combine(date, dt.datetime.min.time()).isoformat(),
            }
            r = api_post("/api/income/", json_body=payload)
            if r.status_code == 201:
                st.success("Income added!")
                st.rerun()
            else:
                st.error(r.text)

    r = api_get("/api/income/")
    if r.status_code == 200 and r.json():
        df = pd.DataFrame(r.json())
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No income records yet.")


# ---------------------------------------------------------------------------
# Budget planner
# ---------------------------------------------------------------------------
def budget_page():
    st.header("📅 Budget Planner")

    with st.expander("➕ Create Budget", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            scope = st.selectbox("Scope", ["Overall"] + CATEGORIES)
        with c2:
            month = st.text_input("Month (YYYY-MM)", value=dt.date.today().strftime("%Y-%m"), key="b_month")
        with c3:
            limit = st.number_input("Limit (₹)", min_value=0.0, step=500.0)

        if st.button("Save Budget", use_container_width=True):
            payload = {"month": month, "limit_amount": limit,
                       "category": None if scope == "Overall" else scope}
            r = api_post("/api/budgets/", json_body=payload)
            if r.status_code == 201:
                st.success("Budget created!")
                st.rerun()
            else:
                st.error(r.text)

    r = api_get("/api/budgets/")
    if r.status_code == 200 and r.json():
        for b in r.json():
            label = b["category"] or "Overall"
            pct = min(b["percent_used"], 100)
            color = "#22c55e" if pct < 70 else ("#f59e0b" if pct < 100 else "#ef4444")
            st.markdown(f"**{label}** — {b['month']} — ₹{b['spent']:,.0f} / ₹{b['limit_amount']:,.0f} ({b['percent_used']}%)")
            st.markdown(f"""
            <div style="background:#1e293b;border-radius:8px;height:14px;margin-bottom:14px;">
                <div style="background:{color};width:{pct}%;height:14px;border-radius:8px;"></div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No budgets set yet.")


# ---------------------------------------------------------------------------
# AI Insights page
# ---------------------------------------------------------------------------
def ai_insights_page():
    st.header("🤖 AI Insights")

    st.markdown("### 💬 Ask the AI Financial Advisor")
    question = st.text_input("e.g. 'How can I save more?' or 'Can I buy a laptop worth 50000?'")
    if st.button("Ask AI"):
        r = api_post("/api/dashboard/advisor", json_body={"question": question})
        if r.status_code == 200:
            st.info(r.json()["answer"])

    st.markdown("---")
    st.markdown("### 📈 Expense Prediction")
    horizon = st.selectbox("Predict for:", ["week", "month", "year"])
    if st.button("Run Prediction"):
        r = api_get(f"/api/dashboard/predict/{horizon}")
        if r.status_code == 200:
            res = r.json()
            c1, c2, c3 = st.columns(3)
            c1.metric("Predicted Amount", f"₹{res['predicted_amount']:,.0f}")
            c2.metric("Confidence", f"{res['confidence_score']*100:.0f}%")
            c3.metric("Model Used", res["model_used"])

    st.markdown("---")
    st.markdown("### 🔍 Spending Pattern Analysis")
    if st.button("Analyze Spending Pattern"):
        r = api_get("/api/dashboard/spending-pattern")
        if r.status_code == 200:
            res = r.json()
            if "category_breakdown" in res:
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Highest spending category:** {res['highest_spending_category']}")
                    st.write(f"**Most expensive day:** {res['most_expensive_day']}")
                    st.write(f"**Most expensive month:** {res['most_expensive_month']}")
                    st.write(f"**Avg daily expense:** ₹{res['average_daily_expense']:,.0f}")
                    st.write(f"**Avg monthly expense:** ₹{res['average_monthly_expense']:,.0f}")
                with c2:
                    fig = px.pie(
                        names=list(res["category_breakdown"].keys()),
                        values=list(res["category_breakdown"].values()),
                        hole=0.4, title="Category Breakdown",
                    )
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#f1f5f9")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(res.get("message", "No data."))

    st.markdown("---")
    st.markdown("### ⚠️ Anomaly Detection")
    if st.button("Scan for Unusual Transactions"):
        r = api_get("/api/dashboard/anomalies")
        if r.status_code == 200 and r.json():
            st.dataframe(pd.DataFrame(r.json()), use_container_width=True, hide_index=True)
        else:
            st.success("No anomalies detected. Your spending looks consistent!")

    st.markdown("---")
    st.markdown("### 📝 AI Monthly Summary")
    if st.button("Generate Monthly Summary"):
        r = api_get("/api/dashboard/monthly-summary")
        if r.status_code == 200:
            res = r.json()
            st.success(res["summary"])


# ---------------------------------------------------------------------------
# Charts page
# ---------------------------------------------------------------------------
def charts_page():
    st.header("📊 Data Visualization")

    exp_r = api_get("/api/expenses/")
    inc_r = api_get("/api/income/")
    if exp_r.status_code != 200 or not exp_r.json():
        st.info("Add some expenses to see charts.")
        return

    exp_df = pd.DataFrame(exp_r.json())
    exp_df["date"] = pd.to_datetime(exp_df["date"])
    inc_df = pd.DataFrame(inc_r.json()) if inc_r.status_code == 200 and inc_r.json() else pd.DataFrame()

    c1, c2 = st.columns(2)
    with c1:
        fig = px.pie(exp_df, names="category", values="amount", hole=0.45, title="Expense by Category")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#f1f5f9")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        daily = exp_df.groupby(exp_df["date"].dt.date)["amount"].sum().reset_index()
        fig2 = px.line(daily, x="date", y="amount", title="Monthly / Daily Spending Trend", markers=True)
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#f1f5f9")
        st.plotly_chart(fig2, use_container_width=True)

    if not inc_df.empty:
        inc_df["date"] = pd.to_datetime(inc_df["date"])
        combined = pd.DataFrame({
            "Type": ["Income"] * len(inc_df) + ["Expense"] * len(exp_df),
            "Amount": list(inc_df["amount"]) + list(exp_df["amount"]),
        })
        fig3 = px.bar(combined.groupby("Type")["Amount"].sum().reset_index(),
                       x="Type", y="Amount", title="Income vs Expense", color="Type")
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#f1f5f9")
        st.plotly_chart(fig3, use_container_width=True)

    exp_df["day_of_week"] = exp_df["date"].dt.day_name()
    exp_df["week"] = exp_df["date"].dt.isocalendar().week
    heat = exp_df.pivot_table(index="day_of_week", columns="week", values="amount", aggfunc="sum", fill_value=0)
    fig4 = px.imshow(heat, title="Spending Heatmap (Day of Week vs Week)", color_continuous_scale="Purples")
    fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#f1f5f9")
    st.plotly_chart(fig4, use_container_width=True)


# ---------------------------------------------------------------------------
# Goals page
# ---------------------------------------------------------------------------
def goals_page():
    st.header("🎯 Savings Goals")

    with st.expander("➕ New Goal", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            title = st.text_input("Goal title")
        with c2:
            target = st.number_input("Target Amount (₹)", min_value=0.0, step=500.0)
        with c3:
            current = st.number_input("Current Saved (₹)", min_value=0.0, step=100.0)
        target_date = st.date_input("Target Date", value=dt.date.today() + dt.timedelta(days=90))

        if st.button("Create Goal", use_container_width=True):
            payload = {
                "title": title, "target_amount": target, "current_amount": current,
                "target_date": dt.datetime.combine(target_date, dt.datetime.min.time()).isoformat(),
            }
            r = api_post("/api/dashboard/goals", json_body=payload)
            if r.status_code == 201:
                st.success("Goal created!")
                st.rerun()

    r = api_get("/api/dashboard/goals")
    if r.status_code == 200 and r.json():
        for g in r.json():
            pct = min(g["current_amount"] / g["target_amount"] * 100, 100) if g["target_amount"] else 0
            st.markdown(f"**{g['title']}** — ₹{g['current_amount']:,.0f} / ₹{g['target_amount']:,.0f} ({pct:.0f}%)")
            st.progress(pct / 100)
    else:
        st.info("No savings goals yet.")


# ---------------------------------------------------------------------------
# Reports / export page
# ---------------------------------------------------------------------------
def reports_page():
    st.header("📤 Reports & Export")
    month = st.text_input("Month (YYYY-MM)", value=dt.date.today().strftime("%Y-%m"), key="report_month")

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📄 Download PDF Report", use_container_width=True):
            r = api_get("/api/reports/pdf", params={"month": month})
            if r.status_code == 200:
                st.download_button("Save PDF", r.content, file_name=f"finance_report_{month}.pdf", mime="application/pdf")
    with c2:
        if st.button("📊 Download Excel Report", use_container_width=True):
            r = api_get("/api/reports/excel", params={"month": month})
            if r.status_code == 200:
                st.download_button("Save Excel", r.content, file_name=f"finance_report_{month}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with c3:
        if st.button("📁 Download CSV Export", use_container_width=True):
            r = api_get("/api/reports/csv")
            if r.status_code == 200:
                st.download_button("Save CSV", r.content, file_name="expenses_export.csv", mime="text/csv")


# ---------------------------------------------------------------------------
# Notifications page
# ---------------------------------------------------------------------------
def notifications_page():
    st.header("🔔 Notifications")
    r = api_get("/api/dashboard/notifications")
    if r.status_code == 200 and r.json():
        for n in r.json():
            icon = {"warning": "⚠️", "success": "✅", "info": "ℹ️"}.get(n["type"], "🔔")
            st.markdown(f"{icon} **{n['title']}** — {n['message']}")
    else:
        st.info("No notifications.")


# ---------------------------------------------------------------------------
# Settings page
# ---------------------------------------------------------------------------
def settings_page():
    st.header("⚙️ Settings")
    user = st.session_state.user
    with st.form("settings_form"):
        name = st.text_input("Full Name", value=user["full_name"])
        currency = st.selectbox("Currency", ["INR", "USD", "EUR", "GBP"],
                                 index=["INR", "USD", "EUR", "GBP"].index(user.get("currency", "INR")))
        dark_mode = st.checkbox("Dark Mode", value=user.get("dark_mode", False))
        submitted = st.form_submit_button("Save Settings")
    if submitted:
        r = api_put("/api/auth/me", json_body={"full_name": name, "currency": currency, "dark_mode": dark_mode})
        if r.status_code == 200:
            st.session_state.user = r.json()
            st.success("Settings updated!")


# ---------------------------------------------------------------------------
# Main app / navigation
# ---------------------------------------------------------------------------
def main():
    if not st.session_state.token:
        login_register_screen()
        return

    with st.sidebar:
        st.markdown(f"### 👋 Welcome, {st.session_state.user['full_name']}")
        page = st.radio("Navigate", [
            "📊 Dashboard", "💸 Expenses", "💵 Income", "📅 Budget Planner",
            "🤖 AI Insights", "📊 Charts", "🎯 Savings Goals",
            "📤 Reports & Export", "🔔 Notifications", "⚙️ Settings",
        ])
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()

    pages = {
        "📊 Dashboard": dashboard_page,
        "💸 Expenses": expenses_page,
        "💵 Income": income_page,
        "📅 Budget Planner": budget_page,
        "🤖 AI Insights": ai_insights_page,
        "📊 Charts": charts_page,
        "🎯 Savings Goals": goals_page,
        "📤 Reports & Export": reports_page,
        "🔔 Notifications": notifications_page,
        "⚙️ Settings": settings_page,
    }
    pages[page]()


if __name__ == "__main__":
    main()
