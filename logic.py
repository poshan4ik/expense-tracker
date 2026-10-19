"""
Бизнес-логика: проверка ввода и расчёты.

Не зависит от интерфейса и базы данных — только функции над числами и списками.
"""

from datetime import date, datetime
from typing import List, Dict


# ── Проверка ввода (validate) ──
# Функции принимают то, что ввёл пользователь, и либо возвращают
# готовое значение, либо бросают ошибку ValueError с понятным текстом.

def validate_amount(text: str) -> float:
    """Проверяет сумму: непустая, положительное число. Иначе — ValueError."""
    text = text.strip().replace(",", ".").replace(" ", "")
    if not text:
        raise ValueError("Введите сумму")
    try:
        value = float(text)
    except ValueError:
        raise ValueError("Сумма должна быть числом (например: 1500 или 1500.50)")
    if value <= 0:
        raise ValueError("Сумма должна быть положительной")
    return value


def validate_date(text: str) -> date:
    """Проверяет дату в формате ДД.ММ.ГГГГ. Иначе — ValueError."""
    text = text.strip()
    if not text:
        raise ValueError("Введите дату")
    try:
        # strptime разбирает текст по шаблону %d.%m.%Y
        return datetime.strptime(text, "%d.%m.%Y").date()
    except ValueError:
        raise ValueError("Дата в формате ДД.ММ.ГГГГ (например: 15.01.2024)")


def validate_expense_input(amount_text: str, category: str, date_text: str) -> tuple[float, str, date]:
    """Проверяет всю форму сразу. Возвращает (сумма, категория, дата)."""
    amount = validate_amount(amount_text)
    if not category or category == "Выберите категорию":
        raise ValueError("Выберите категорию")
    expense_date = validate_date(date_text)
    return amount, category, expense_date


# ── Расчёты ──
# Работают со списком расходов: [{"amount": 100, "category": "Еда", ...}, ...]

def total_sum(expenses: List) -> float:
    """Общая сумма всех расходов."""
    total = 0
    for e in expenses:
        total = total + e["amount"]
    return total


def sum_by_category(expenses: List) -> Dict[str, float]:
    """Суммы по категориям для диаграммы: {категория: сумма}."""
    by_cat: Dict[str, float] = {}
    for e in expenses:
        category = e["category"]
        if category in by_cat:
            by_cat[category] = by_cat[category] + e["amount"]
        else:
            by_cat[category] = e["amount"]
    return by_cat


def format_amount(amount: float) -> str:
    """Оформляет сумму: пробел между разрядами и знак ₸. Пример: 1 500.00 ₸."""
    if amount == 0:
        return "0 ₸"
    # :,.2f = разделитель разрядов запятой, 2 знака после точки
    text = f"{amount:,.2f}".replace(",", " ")
    return text + " ₸"
