"""
Работа с базой данных SQLite.

Содержит функции для создания таблицы, добавления, получения и удаления расходов.
SQL запросы инкапсулированы здесь, интерфейс не знает о структуре БД.
"""

import sqlite3
from datetime import date
from typing import List, Optional, Tuple

DB_PATH = "expenses.db"


def get_connection() -> sqlite3.Connection:
    """Создаёт и возвращает соединение с БД."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # доступ к колонкам по имени
    return conn


def init_db() -> None:
    """Создаёт таблицу expenses, если её нет."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,          -- ISO формат YYYY-MM-DD
                description TEXT DEFAULT ''
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date)
        """)


def add_expense(amount: float, category: str, expense_date: date, description: str) -> int:
    """
    Добавляет расход в БД.

    Args:
        amount: сумма расхода
        category: категория (например, "🍔 Еда")
        expense_date: дата расхода
        description: описание

    Returns:
        id созданной записи
    """
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO expenses (amount, category, date, description) VALUES (?, ?, ?, ?)",
            (amount, category, expense_date.isoformat(), description)
        )
        return cursor.lastrowid


def get_expenses(category_filter: str = "Все") -> List[sqlite3.Row]:
    """
    Возвращает список расходов, отсортированных по дате (новые сверху).

    Args:
        category_filter: "Все" или название категории

    Returns:
        Список строк БД (sqlite3.Row)
    """
    with get_connection() as conn:
        if category_filter == "Все":
            rows = conn.execute(
                "SELECT * FROM expenses ORDER BY date DESC, id DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM expenses WHERE category = ? ORDER BY date DESC, id DESC",
                (category_filter,)
            ).fetchall()
        return rows


def delete_expense(expense_id: int) -> bool:
    """
    Удаляет расход по ID.

    Args:
        expense_id: идентификатор записи

    Returns:
        True, если запись была удалена
    """
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        return cursor.rowcount > 0