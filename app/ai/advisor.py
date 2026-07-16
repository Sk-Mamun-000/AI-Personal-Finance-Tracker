"""
AI Financial Advisor.

Answers natural-language questions like "How can I save more?",
"Am I overspending?", "Can I buy a laptop worth 50000 next month?"

Uses the user's real transaction data to compute a financial context, then
either (a) calls an LLM API with that context for a nuanced answer, or
(b) falls back to a deterministic, rule-based advisor (default — no key
needed, fully explainable, good for a project demo).
"""
import re
from app.config import get_settings

settings = get_settings()


def _extract_amount(question: str):
    match = re.search(r"(\d[\d,]*\.?\d*)", question)
    if match:
        try:
            return float(match.group(1).replace(",", ""))
        except ValueError:
            return None
    return None


def _rule_based_advice(question: str, context: dict) -> str:
    q = question.lower()
    income = context["total_income"]
    expense = context["total_expenses"]
    savings = income - expense
    savings_rate = (savings / income * 100) if income > 0 else 0
    top_category = context.get("top_category", "N/A")

    if "buy" in q or "afford" in q or "purchase" in q:
        amount = _extract_amount(question)
        if amount:
            if savings >= amount:
                remaining = savings - amount
                return (
                    f"Based on your current savings of ₹{savings:,.0f} this month, "
                    f"you can afford this ₹{amount:,.0f} purchase and would still have "
                    f"₹{remaining:,.0f} left. However, consider whether this fits your "
                    f"budget goals before committing."
                )
            shortfall = amount - savings
            return (
                f"Your current savings this month are ₹{savings:,.0f}, which is "
                f"₹{shortfall:,.0f} short of the ₹{amount:,.0f} you're planning to spend. "
                f"Consider waiting, or reducing spending in your top category "
                f"({top_category}) to free up funds."
            )
        return (
            "I can give you a precise answer if you include the amount you're planning "
            "to spend, e.g. 'Can I buy a laptop worth 60000?'"
        )

    if "overspend" in q or "over spending" in q or "too much" in q:
        if savings_rate < 0:
            return (
                f"Yes — you're spending more than you earn this month "
                f"(income ₹{income:,.0f} vs expenses ₹{expense:,.0f}). "
                f"Your biggest spending category is {top_category}. Consider setting a "
                f"strict budget there first."
            )
        if savings_rate < 20:
            return (
                f"You're not overspending, but your savings rate is only "
                f"{savings_rate:.1f}%, which is below the recommended 20%. "
                f"Your top category is {top_category} — trimming it slightly could help."
            )
        return (
            f"No signs of overspending. Your savings rate is a healthy "
            f"{savings_rate:.1f}% this month. Keep it up!"
        )

    if "save" in q:
        tips = [
            f"Your highest spending category is {top_category} — a 10-15% cut there "
            f"could meaningfully boost savings.",
            "Automate a fixed percentage of income into savings/investments right "
            "after payday, before it gets spent.",
            "Review recurring subscriptions (streaming, memberships) for ones you "
            "no longer use.",
        ]
        return " ".join(tips)

    return (
        f"Here's a quick snapshot: income ₹{income:,.0f}, expenses ₹{expense:,.0f}, "
        f"savings rate {savings_rate:.1f}%, top spending category: {top_category}. "
        f"Ask me things like 'How can I save more?', 'Am I overspending?', or "
        f"'Can I buy a phone worth 20000?' for tailored advice."
    )


def _llm_advice(question: str, context: dict):
    try:
        if settings.ai_provider == "openai" and settings.openai_api_key:
            import openai
            client = openai.OpenAI(api_key=settings.openai_api_key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content":
                        "You are a helpful, concise personal finance advisor. "
                        f"User's financial context: {context}. Keep answers under 120 words."},
                    {"role": "user", "content": question},
                ],
                temperature=0.4,
                max_tokens=200,
            )
            return resp.choices[0].message.content.strip()
    except Exception:
        pass
    return None


def get_financial_advice(question: str, context: dict) -> str:
    if settings.ai_provider in ("openai", "gemini"):
        llm_answer = _llm_advice(question, context)
        if llm_answer:
            return llm_answer
    return _rule_based_advice(question, context)
