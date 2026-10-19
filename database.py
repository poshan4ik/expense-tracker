"""
Работа с базой данных SQLite.

Содержит функции для создания таблицы, добавления и получения расходов.
SQL-запросы только здесь — интерфейс (app.py) ничего не знает о структуре БД.
"""

import sqlite3
from datetime import date
from typing import List, Optional, Tuple

# Имя файла базы данных. Он появится рядом с программой при первом запуске.
DB_PATH = "expenses.db"


def get_connection() -> sqlite3.Connection:
    """Создаёт и возвращает соединение с БД."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # чтобы к полям результата обращаться по имени
    return conn


def init_db() -> None:
    """Создаёт таблицу expenses, если её нет."""
    # with сам закрывает соединение и сохраняет изменения
    with get_connection() as conn:
        # CREATE TABLE IF NOT EXISTS — «создай, если ещё нет»
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,  -- номер записи, растёт сам
                amount REAL NOT NULL,                  -- сумма
                category TEXT NOT NULL,                -- категория
                date TEXT NOT NULL,                    -- дата, формат YYYY-MM-DD
                description TEXT DEFAULT ''            -- описание
            )
        """)
        # Индекс по дате — выборка по дате работает быстрее
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date)
        """)


def add_expense(amount: float, category: str, expense_date: date, description: str) -> int:
    """
    Добавляет расход в БД. Возвращает id новой записи.

    Args:
        amount: сумма расхода
        category: категория (например, "🍔 Еда")
        expense_date: дата расхода
        description: описание
    """
    with get_connection() as conn:
        # ? — это заглушки: значения передаются отдельно, это защита от SQL-инъекций
        cursor = conn.execute(
            "INSERT INTO expenses (amount, category, date, description) VALUES (?, ?, ?, ?)",
            (amount, category, expense_date.isoformat(), description)
        )
        return cursor.lastrowid  # id только что добавленной строки


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
            # Показываем все записи: сначала новые
            rows = conn.execute(
                "SELECT * FROM expenses ORDER BY date DESC, id DESC"
            ).fetchall()
        else:
            # WHERE category = ? — фильтр по выбранной категории
            rows = conn.execute(
                "SELECT * FROM expenses WHERE category = ? ORDER BY date DESC, id DESC",
                (category_filter,)
            ).fetchall()
        return rows
