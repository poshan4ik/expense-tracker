"""
Главное окно: две вкладки «Расходы» и «Статистика».

В этом файле нет SQL — только интерфейс и кнопки.
"""

# ── Импорты: подключаем всё, чем будем пользоваться ──

import customtkinter as ctk          # современные кнопки, поля, вкладки (тёмная тема)
from tkinter import messagebox, ttk  # messagebox — окна ошибок, ttk — таблица
from datetime import date            # сегодняшняя дата для поля «Дата»

# matplotlib рисует круговую диаграмму прямо в окне tkinter
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Явно перечисляем нужные константы из theme.py (цвета, шрифты, списки)
from theme import (
    BG_MAIN, BG_CARD, ACCENT,
    BTN_SAVE,
    TEXT_MAIN, TEXT_DIM, BORDER,
    RADIUS, PADDING, GAP,
    WIN_WIDTH, WIN_HEIGHT, WIN_MIN_W, WIN_MIN_H,
    FONT_FAMILY, FONT_SIZE, FONT_HEADER, FONT_NORMAL, FONT_SMALL,
    ROW_HEIGHT,
    CATEGORIES, FORM_CATEGORIES, FILTER_CATEGORIES,
)
from database import init_db, add_expense, get_expenses
from logic import (validate_expense_input, total_sum, format_amount,
                   sum_by_category)

# Включаем тёмную тему для всех виджетов
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ── Вспомогательные функции: создают стандартные элементы интерфейса ──

def ui_entry(parent, **kwargs):
    """Поле ввода сразу в цветах тёмной темы — не повторяем цвета каждый раз."""
    return ctk.CTkEntry(parent, height=36, border_color=BORDER,
                        fg_color=BG_MAIN, text_color=TEXT_MAIN, **kwargs)


def ui_button(parent, text, fg, hover, command, text_color=BG_MAIN, width=130):
    """Кнопка сразу в шрифте и цветах тёмной темы."""
    return ctk.CTkButton(parent, text=text, width=width, height=36,
                         fg_color=fg, hover_color=hover, text_color=text_color,
                         font=(FONT_FAMILY, FONT_SIZE, "bold"), command=command)


class ExpenseApp(ctk.CTk):
    """Главное окно приложения «Трекер расходов»."""

    def __init__(self):
        """Настраивает окно и создаёт интерфейс."""
        super().__init__()                       # запускаем главное окно tkinter
        self.title("Трекер расходов")            # заголовок вверху окна
        self.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")  # размер окна 900x600
        self.minsize(WIN_MIN_W, WIN_MIN_H)       # минимальный размер 800x500
        self.configure(fg_color=BG_MAIN)         # фон окна — тёмный

        init_db()               # 1) создать базу данных, если её ещё нет
        self._build_ui()        # 2) нарисовать все элементы интерфейса
        self.load_expenses()    # 3) показать расходы из базы в таблице
        self.update_stats()     # 4) посчитать и показать статистику

    # ─────────────────── Построение интерфейса ───────────────────

    def _build_ui(self):
        """Создаёт две вкладки: «Расходы» (форма + таблица) и «Статистика»."""
        # Вкладки — как вкладки в браузере: «Расходы» и «Статистика»
        self.tabs = ctk.CTkTabview(
            self, fg_color=BG_CARD,
            segmented_button_selected_color=ACCENT,
            segmented_button_selected_hover_color=ACCENT)
        self.tabs.pack(fill="both", expand=True, padx=PADDING, pady=PADDING)
        self.tabs.add("Расходы")
        self.tabs.add("Статистика")

        # Вкладка расходов: форма сверху (строка 0), таблица снизу (строка 1)
        tab = self.tabs.tab("Расходы")
        tab.configure(fg_color=BG_MAIN)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(1, weight=1)  # строка таблицы тянется на всё окно
        self._build_form(tab)    # карточка «Добавить расход»
        self._build_table(tab)   # карточка с таблицей расходов
        self._build_stats_tab(self.tabs.tab("Статистика"))

    def _build_form(self, parent):
        """Карточка с формой: сумма, категория, дата, описание, кнопка."""
        # Карточка — рамка со скруглёнными углами
        form = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=RADIUS)
        form.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=(8, GAP))
        ctk.CTkLabel(form, text="Добавить расход", font=FONT_HEADER,
                     text_color=TEXT_MAIN).pack(anchor="w", padx=PADDING, pady=(PADDING, GAP))

        # Сетка из 5 колонок: сумма, категория, дата, описание, кнопка
        fields = ctk.CTkFrame(form, fg_color="transparent")
        fields.pack(fill="x", padx=PADDING, pady=(0, GAP))
        for i in range(5):
            fields.grid_columnconfigure(i, weight=1)

        # Подписи над полями
        captions = ["Сумма", "Категория", "Дата (ДД.ММ.ГГГГ)", "Описание"]
        for column, caption in enumerate(captions):
            ctk.CTkLabel(fields, text=caption, font=FONT_SMALL,
                         text_color=TEXT_DIM).grid(row=0, column=column, sticky="w")

        # Поле «Сумма» — сюда вводят, сколько потратили
        self.amount_entry = ui_entry(fields, placeholder_text="Например: 1500")
        self.amount_entry.grid(row=1, column=0, sticky="ew", padx=(0, GAP))

        # Список категорий — выпадающий список из theme.py
        self.category_menu = ctk.CTkOptionMenu(
            fields, values=FORM_CATEGORIES, height=36, fg_color=BG_MAIN,
            button_color=ACCENT, button_hover_color=ACCENT,
            dropdown_fg_color=BG_CARD, dropdown_hover_color=BORDER, font=FONT_NORMAL)
        self.category_menu.set(FORM_CATEGORIES[0])  # по умолчанию «Выберите категорию»
        self.category_menu.grid(row=1, column=1, sticky="ew", padx=(0, GAP))

        # Поле «Дата» — сегодняшнее число по умолчанию
        self.date_entry = ui_entry(fields)
        self.date_entry.insert(0, date.today().strftime("%d.%m.%Y"))
        self.date_entry.grid(row=1, column=2, sticky="ew", padx=(0, GAP))

        # Поле «Описание» — можно оставить пустым
        self.desc_entry = ui_entry(fields, placeholder_text="Не обязательно")
        self.desc_entry.grid(row=1, column=3, sticky="ew", padx=(0, GAP))

        # Зелёная кнопка «Сохранить» — при нажатии вызовет save_expense
        ui_button(fields, "Сохранить", BTN_SAVE, "#26C493",
                  self.save_expense).grid(row=1, column=4, sticky="e")

    def _build_table(self, parent):
        """Карточка с таблицей: фильтр, кнопка удаления, итог."""
        card = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=RADIUS)
        card.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=(8, GAP), pady=(0, 8))
        card.grid_columnconfigure(0, weight=1)  # таблица занимает всю ширину
        card.grid_rowconfigure(1, weight=1)     # и всю высоту карточки

        # Заголовок «Расходы» и фильтр по категории
        head = ctk.CTkFrame(card, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=PADDING, pady=(PADDING, GAP))
        ctk.CTkLabel(head, text="Расходы", font=FONT_HEADER,
                     text_color=TEXT_MAIN).pack(side="left")
        # Фильтр: выбираешь категорию — таблица сразу перерисовывается
        self.filter_menu = ctk.CTkOptionMenu(
            head, values=FILTER_CATEGORIES, width=180, height=32,
            fg_color=BG_MAIN, button_color=ACCENT, button_hover_color=ACCENT,
            dropdown_fg_color=BG_CARD, dropdown_hover_color=BORDER,
            font=FONT_SMALL, command=self._on_filter_change)
        self.filter_menu.set("Все")
        self.filter_menu.pack(side="right")

        # Обычная плоская таблица: колонки вместо колонок-заголовков
        self._setup_tree_style()
        self.tree = ttk.Treeview(card, columns=("date", "category", "amount", "description"),
                                 show="headings")
        self.tree.heading("date", text="Дата", anchor="w")
        self.tree.heading("category", text="Категория", anchor="w")
        self.tree.heading("amount", text="Сумма", anchor="e")   # суммы — по правому краю
        self.tree.heading("description", text="Описание", anchor="w")
        self.tree.column("date", width=110, anchor="w", stretch=False)
        self.tree.column("category", width=180, anchor="w")
        self.tree.column("amount", width=120, anchor="e", stretch=False)
        self.tree.column("description", width=280, anchor="w")
        scrollbar = ctk.CTkScrollbar(card, command=self.tree.yview)  # полоса прокрутки
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=1, column=0, sticky="nsew", padx=(PADDING, 0))
        scrollbar.grid(row=1, column=1, sticky="ns", padx=(0, 8))

        # Итоговая строка под таблицей
        self.summary_label = ctk.CTkLabel(card, text="Записей: 0 · Итого: 0 ₸",
                                          font=(FONT_FAMILY, FONT_SIZE, "bold"),
                                          text_color=TEXT_MAIN, anchor="w")
        self.summary_label.grid(row=2, column=0, columnspan=2, sticky="w",
                                padx=PADDING, pady=(GAP, PADDING))

    def _setup_tree_style(self):
        """Красит таблицу и её заголовки в цвета тёмной темы."""
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background=BG_MAIN, foreground=TEXT_MAIN,
                        fieldbackground=BG_MAIN, rowheight=ROW_HEIGHT,
                        font=FONT_NORMAL, borderwidth=0)
        style.configure("Treeview.Heading", background=BG_CARD, foreground=TEXT_DIM,
                        font=(FONT_FAMILY, FONT_SIZE, "bold"), borderwidth=0)
        style.map("Treeview", background=[("selected", ACCENT)])  # выделение — фиолетовое

    def _build_stats_tab(self, parent):
        """Вкладка «Статистика»: карточка «Всего потрачено» и диаграмма."""
        parent.configure(fg_color=BG_MAIN)

        # Карточка с общей суммой
        card = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=RADIUS)
        card.pack(fill="x", padx=8, pady=(8, GAP))
        ctk.CTkLabel(card, text="Всего потрачено", font=FONT_SMALL,
                     text_color=TEXT_DIM).pack(anchor="w", padx=PADDING, pady=(PADDING, 4))
        self.total_value = ctk.CTkLabel(card, text="—",
                                        font=(FONT_FAMILY, 22, "bold"), text_color=ACCENT)
        self.total_value.pack(anchor="w", padx=PADDING, pady=(0, PADDING))

        # Карточка с диаграммой
        self.chart_card = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=RADIUS)
        self.chart_card.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        ctk.CTkLabel(self.chart_card, text="Диаграмма по категориям", font=FONT_HEADER,
                     text_color=TEXT_MAIN).pack(anchor="w", padx=PADDING, pady=(PADDING, 0))
        self.chart_holder = ctk.CTkFrame(self.chart_card, fg_color="transparent")
        self.chart_holder.pack(fill="both", expand=True, padx=PADDING, pady=PADDING)

        # Заглушка «нет данных» — показывается, пока в базе пусто
        self.chart_empty = ctk.CTkLabel(self.chart_holder,
                                        text="Пока нет расходов. Добавьте первый!",
                                        font=FONT_NORMAL, text_color=TEXT_DIM)
        self.chart_empty.pack(expand=True)
        self.chart_canvas = None  # холст matplotlib, создадим при первом рисунке

    # ─────────────────── Действия пользователя ───────────────────

    def save_expense(self):
        """Проверяет поля формы и добавляет расход в базу."""
        # Шаг 1: проверяем ввод. Если что-то не так — ловим ошибку ValueError
        try:
            amount, category, expense_date = validate_expense_input(
                self.amount_entry.get(), self.category_menu.get(), self.date_entry.get())
        except ValueError as error:
            # Неверный ввод — показываем окно с ошибкой, программа не падает
            messagebox.showwarning("Ошибка ввода", str(error), parent=self)
            return  # дальше не идём

        # Шаг 2: ввод верный — сохраняем расход в базу данных
        add_expense(amount, category, expense_date, self.desc_entry.get().strip())
        # Шаг 3: очищаем поля (дату оставляем — обычно тратят сегодня)
        self.amount_entry.delete(0, "end")
        self.desc_entry.delete(0, "end")
        self.category_menu.set(FORM_CATEGORIES[0])
        # Шаг 4: перерисовываем таблицу и статистику с новыми данными
        self.load_expenses()
        self.update_stats()

    def _on_filter_change(self, _value):
        """Вызывается, когда пользователь выбрал другую категорию в фильтре."""
        self.load_expenses()

    def load_expenses(self):
        """Показывает в таблице все расходы по фильтру."""
        # Шаг 1: очищаем таблицу от старых строк
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Шаг 2: читаем из базы расходы по выбранному фильтру
        expenses = get_expenses(self.filter_menu.get())

        # Если записей нет — показываем подсказку вместо пустой таблицы
        if not expenses:
            self.tree.insert("", "end",
                             values=("", "Пока нет расходов. Добавьте первый!", "", ""))

        # Шаг 3: добавляем по строке на каждый расход
        for item in expenses:
            self.tree.insert("", "end",
                             values=(item["date"], item["category"],
                                     format_amount(item["amount"]),
                                     item["description"] or "—"))

        self.update_summary(expenses)

    def update_summary(self, expenses):
        """Обновляет строку «Записей: N · Итого: X ₸» под таблицей."""
        count = len(expenses)
        total = total_sum(expenses)
        self.summary_label.configure(
            text=f"Записей: {count} · Итого: {format_amount(total)}")

    def update_stats(self):
        """Обновляет карточку и диаграмму на вкладке «Статистика»."""
        expenses = get_expenses("Все")  # статистика всегда по всем записям
        self.total_value.configure(text=format_amount(total_sum(expenses)))
        self.draw_chart(expenses)

    def draw_chart(self, expenses):
        """Рисует круговую диаграмму; при пустом списке — надпись «нет расходов»."""
        # Убираем старую диаграмму или заглушку
        if self.chart_canvas:
            self.chart_canvas.get_tk_widget().destroy()
            self.chart_canvas = None
        self.chart_empty.pack_forget()
        if not expenses:  # база пустая — показываем заглушку
            self.chart_empty.pack(expand=True)
            return

        # Считаем, сколько потрачено в каждой категории
        sums = sum_by_category(expenses)
        labels = []
        values = []
        colors = []
        for name, color in CATEGORIES:
            if name in sums:
                labels.append(name)
                values.append(sums[name])
                colors.append(color)
        if not labels:  # нечего рисовать — показываем заглушку
            self.chart_empty.pack(expand=True)
            return

        # Рисуем круговую диаграмму и встраиваем её в окно
        figure = Figure(figsize=(6, 3.5), dpi=90)
        figure.patch.set_facecolor(BG_CARD)  # фон диаграммы = цвет карточки
        axes = figure.add_subplot(111)
        axes.pie(values, labels=labels, colors=colors, autopct="%1.0f%%",
                 startangle=90, textprops={"color": TEXT_MAIN, "fontsize": 9})
        figure.tight_layout()
        self.chart_canvas = FigureCanvasTkAgg(figure, master=self.chart_holder)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)
