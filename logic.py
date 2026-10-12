"""
Бизнес-логика: проверка ввода и расчёты.

Не зависит от интерфейса и базы данных — только функции над числами и списками.
"""

from datetime import date, datetime, timedelta
from typing import List, Tuple, Dict


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


def total_sum(expenses: List) -> float:
    """Общая сумма всех расходов."""
    return sum(e["amount"] for e in expenses)


def average_expense(expenses: List) -> float:
    """Средний расход на одну запись."""
    if not expenses:
        return 0.0
    return total_sum(expenses) / len(expenses)


def top_category(expenses: List) -> Tuple[str, float]:
    """Самая затратная категория: возвращает (категория, сумма)."""
    sums = sum_by_category(expenses)
    if not sums:
        return "—", 0.0
    return max(sums.items(), key=lambda x: x[1])


def sum_by_category(expenses: List) -> Dict[str, float]:
    """Суммы по категориям для диаграммы: {категория: сумма}."""
    by_cat: Dict[str, float] = {}
    for e in expenses:
        by_cat[e["category"]] = by_cat.get(e["category"], 0.0) + e["amount"]
    return by_cat


def format_amount(amount: float) -> str:
    """Оформляет сумму: пробел между разрядами и знак ₸. Пример: 1 500.00 ₸."""
    if amount == 0:
        return "0 ₸"
    s = f"{amount:,.2f}".replace(",", " ")
    return f"{s} ₸"


def group_by_day(expenses: List) -> Dict[str, List]:
    """Группирует расходы по дате: {дата: [расходы этого дня]}."""
    groups: Dict[str, List] = {}
    for e in expenses:
        groups.setdefault(e["date"], []).append(e)
    return groups


def day_title(day: str) -> str:
    """Название дня для заголовка: Сегодня, Вчера или ДД.ММ.ГГГГ."""
    today = date.today()
    if day == today.isoformat():
        return "Сегодня"
    if day == (today - timedelta(days=1)).isoformat():
        return "Вчера"
    year, month, day_num = day.split("-")
    return f"{day_num}.{month}.{year}"
