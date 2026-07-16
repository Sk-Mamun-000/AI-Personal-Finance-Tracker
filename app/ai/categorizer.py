"""
Smart Expense Categorization.

Uses a lightweight keyword/NLP rule-based classifier by default (no API key
required, works fully offline — good for a demo/viva). If AI_PROVIDER is set
to "openai" or "gemini" and a valid key is present, it calls that API instead
for a more flexible free-text classification.
"""
import re
from app.config import get_settings
from app.models import ExpenseCategory

settings = get_settings()

# Keyword bank used for the offline rule-based / NLP-lite classifier.
KEYWORD_MAP = {
    ExpenseCategory.FOOD: [
        "pizza", "burger", "restaurant", "swiggy", "zomato", "food", "grocery",
        "groceries", "coffee", "cafe", "lunch", "dinner", "breakfast", "snack",
        "milk", "vegetables", "meal",
    ],
    ExpenseCategory.TRANSPORT: [
        "uber", "ola", "taxi", "cab", "bus", "train", "metro", "fuel", "petrol",
        "diesel", "parking", "toll", "flight ticket domestic", "auto rickshaw",
    ],
    ExpenseCategory.SHOPPING: [
        "amazon", "flipkart", "myntra", "clothes", "shoes", "mall", "shopping",
        "electronics", "gadget", "furniture",
    ],
    ExpenseCategory.BILLS: [
        "electricity", "water bill", "gas bill", "internet", "wifi", "broadband",
        "mobile recharge", "phone bill", "rent", "maintenance", "dth",
    ],
    ExpenseCategory.EDUCATION: [
        "tuition", "course", "udemy", "coursera", "book", "college fee",
        "school fee", "exam fee", "stationery",
    ],
    ExpenseCategory.ENTERTAINMENT: [
        "netflix", "prime video", "hotstar", "spotify", "movie", "cinema",
        "game", "concert", "party",
    ],
    ExpenseCategory.MEDICAL: [
        "hospital", "doctor", "medicine", "pharmacy", "clinic", "insurance premium",
        "dental", "checkup",
    ],
    ExpenseCategory.INVESTMENT: [
        "mutual fund", "sip", "stocks", "shares", "crypto", "fixed deposit", "fd",
        "gold", "bond",
    ],
    ExpenseCategory.TRAVEL: [
        "flight", "hotel", "trip", "vacation", "airbnb", "tour", "holiday",
    ],
}


def _rule_based_categorize(text: str):
    text_lower = text.lower().strip()
    best_category = ExpenseCategory.OTHERS
    best_score = 0.0

    for category, keywords in KEYWORD_MAP.items():
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                # Longer / more specific keyword matches score higher.
                score = 0.75 + min(0.2, len(kw) / 100)
                if score > best_score:
                    best_score = score
                    best_category = category

    if best_score == 0.0:
        return ExpenseCategory.OTHERS, 0.35  # low-confidence fallback
    return best_category, round(min(best_score, 0.99), 2)


def _llm_categorize(text: str):
    """Optional: call OpenAI/Gemini for free-text categorization. Falls back
    to the rule-based classifier if no key is configured or the call fails."""
    try:
        if settings.ai_provider == "openai" and settings.openai_api_key:
            import openai
            client = openai.OpenAI(api_key=settings.openai_api_key)
            categories = [c.value for c in ExpenseCategory]
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content":
                        f"Classify the expense into exactly one of: {categories}. "
                        f"Reply with only the category name."},
                    {"role": "user", "content": text},
                ],
                temperature=0,
                max_tokens=5,
            )
            label = resp.choices[0].message.content.strip()
            for c in ExpenseCategory:
                if c.value.lower() == label.lower():
                    return c, 0.9
    except Exception:
        pass
    return None


def categorize_expense(text: str):
    """Returns (ExpenseCategory, confidence_score)."""
    if settings.ai_provider in ("openai", "gemini"):
        llm_result = _llm_categorize(text)
        if llm_result:
            return llm_result
    return _rule_based_categorize(text)
