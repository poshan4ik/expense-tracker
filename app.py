"""
Главное окно: две вкладки «Расходы» и «Статистика».

В этом файле нет SQL — только интерфейс и кнопки.
"""

import customtkinter as ctk
from tkinter import messagebox, ttk
from datetime import date

from theme import *
from database import init_db, add_expense, get_expenses, delete_expense
from logic import (validate_expense_input, total_sum, average_expense,
                   top_category, sum_by_category, format_amount,
                   group_by_day, day_title)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


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
        super().__init__()
        self.title("Трекер расходов")
        self.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
        self.minsize(WIN_MIN_W, WIN_MIN_H)
        self.configure(fg_color=BG_MAIN)
        self.selected_id = None  # id выбранной траты, None — ничего не выбрано
        self._row_ids = {}       # связь строк таблицы с id расходов в базе
        init_db()
        self._build_ui()
        self.load_expenses()
        self.update_stats()

    # ─────────────────── Построение интерфейса ───────────────────

    def _build_ui(self):
        """Создаёт две вкладки: «Расходы» (форма + таблица) и «Статистика»."""
        self.tabs = ctk.CTkTabview(
            self, fg_color=BG_CARD,
            segmented_button_selected_color=ACCENT,
            segmented_button_selected_hover_color=ACCENT)
        self.tabs.pack(fill="both", expand=True, padx=PADDING, pady=PADDING)
        self.tabs.add("Расходы")
        self.tabs.add("Статистика")

        tab = self.tabs.tab("Расходы")
        tab.configure(fg_color=BG_MAIN)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(1, weight=1)  # строка таблицы тянется на всё окно
        self._build_form(tab)
        self._build_table(tab)
        self._build_stats_tab(self.tabs.tab("Статистика"))

    def _build_form(self, parent):
        """Карточка с формой: сумма, категория, дата, описание, кнопка."""
        form = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=RADIUS)
        form.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=(8, GAP))
        ctk.CTkLabel(form, text="Добавить расход", font=FONT_HEADER,
                     text_color=TEXT_MAIN).pack(anchor="w", padx=PADDING, pady=(PADDING, GAP))

        fields = ctk.CTkFrame(form, fg_color="transparent")
        fields.pack(fill="x", padx=PADDING, pady=(0, GAP))
        for i in range(5):
            fields.grid_columnconfigure(i, weight=1)

        # Подписи над полями
        captions = ["Сумма", "Категория", "Дата (ДД.ММ.ГГГГ)", "Описание"]
        for column, caption in enumerate(captions):
            ctk.CTkLabel(fields, text=caption, font=FONT_SMALL,
                         text_color=TEXT_DIM).grid(row=0, column=column, sticky="w")

        # Поле «Сумма»
        self.amount_entry = ui_entry(fields, placeholder_text="Например: 1500")
        self.amount_entry.grid(row=1, column=0, sticky="ew", padx=(0, GAP))

        # Список категорий
        self.category_menu = ctk.CTkOptionMenu(
            fields, values=FORM_CATEGORIES, height=36, fg_color=BG_MAIN,
            button_color=ACCENT, button_hover_color=ACCENT,
            dropdown_fg_color=BG_CARD, dropdown_hover_color=BORDER, font=FONT_NORMAL)
        self.category_menu.set(FORM_CATEGORIES[0])
        self.category_menu.grid(row=1, column=1, sticky="ew", padx=(0, GAP))

        # Поле «Дата» — сегодняшнее число по умолчанию
        self.date_entry = ui_entry(fields)
        self.date_entry.insert(0, date.today().strftime("%d.%m.%Y"))
        self.date_entry.grid(row=1, column=2, sticky="ew", padx=(0, GAP))

        # Поле «Описание»
        self.desc_entry = ui_entry(fields, placeholder_text="Не обязательно")
        self.desc_entry.grid(row=1, column=3, sticky="ew", padx=(0, GAP))

        # Зелёная кнопка «Сохранить»
        ui_button(fields, "Сохранить", BTN_SAVE, "#26C493",
                  self.save_expense).grid(row=1, column=4, sticky="e")

    def _build_table(self, parent):
        """Карточка с таблицей: дни с тратами, фильтр, кнопка, итог."""
        card = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=RADIUS)
        card.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=(8, GAP), pady=(0, 8))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        # Заголовок «Расходы» и фильтр по категории
        head = ctk.CTkFrame(card, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=PADDING, pady=(PADDING, GAP))
        ctk.CTkLabel(head, text="Расходы", font=FONT_HEADER,
                     text_color=TEXT_MAIN).pack(side="left")
        self.filter_menu = ctk.CTkOptionMenu(
            head, values=FILTER_CATEGORIES, width=180, height=32,
            fg_color=BG_MAIN, button_color=ACCENT, button_hover_color=ACCENT,
            dropdown_fg_color=BG_CARD, dropdown_hover_color=BORDER,
            font=FONT_SMALL, command=lambda _: self.load_expenses())
        self.filter_menu.set("Все")
        self.filter_menu.pack(side="right")

        # Таблица двухуровневая: первый уровень — дни, второй — траты внутри дня
        self._setup_tree_style()
        self.tree = ttk.Treeview(card, columns=("title", "amount", "description"),
                                 show="tree headings", selectmode="browse")
        self.tree.heading("title", text="Категория", anchor="w")
        self.tree.heading("amount", text="Сумма", anchor="e")
        self.tree.heading("description", text="Описание", anchor="w")
        self.tree.column("title", width=220, anchor="w")
        self.tree.column("amount", width=120, anchor="e", stretch=False)
        self.tree.column("description", width=300, anchor="w")
        scrollbar = ctk.CTkScrollbar(card, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=1, column=0, sticky="nsew", padx=(PADDING, 0))
        scrollbar.grid(row=1, column=1, sticky="ns", padx=(0, 8))

        # Чередование цвета строк по тегам even/odd, дни — жирным
        self.tree.tag_configure("odd", background=ROW_COLORS[0])
        self.tree.tag_configure("even", background=ROW_COLORS[1])
        self.tree.tag_configure("day", background=ROW_COLORS[1],
                                font=(FONT_FAMILY, FONT_SIZE, "bold"))
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Красная кнопка удаления — включается при выборе траты
        self.delete_btn = ui_button(card, "Удалить выбранное", BTN_DELETE,
                                    BTN_DELETE_HOVER, self.delete_selected,
                                    text_color=TEXT_MAIN, width=170)
        self.delete_btn.configure(state="disabled")
        self.delete_btn.grid(row=2, column=0, columnspan=2, padx=PADDING,
                             pady=(GAP, GAP), sticky="w")

        # Итоговая строка под таблицей
        self.summary_label = ctk.CTkLabel(card, text="Записей: 0 · Итого: 0 ₸",
                                          font=(FONT_FAMILY, FONT_SIZE, "bold"),
                                          text_color=TEXT_MAIN, anchor="w")
        self.summary_label.grid(row=3, column=0, columnspan=2, sticky="w",
                                padx=PADDING, pady=(0, PADDING))

    def _setup_tree_style(self):
        """Красит таблицу и её заголовки в цвета тёмной темы."""
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background=BG_MAIN, foreground=TEXT_MAIN,
                        fieldbackground=BG_MAIN, rowheight=ROW_HEIGHT,
                        font=FONT_NORMAL, borderwidth=0)
        style.configure("Treeview.Heading", background=BG_CARD, foreground=TEXT_DIM,
                        font=(FONT_FAMILY, FONT_SIZE, "bold"), borderwidth=0)
        style.map("Treeview", background=[("selected", ACCENT)])

    def _build_stats_tab(self, parent):
        """Вкладка «Статистика»: три карточки и круговая диаграмма."""
        parent.configure(fg_color=BG_MAIN)
        cards = ctk.CTkFrame(parent, fg_color="transparent")
        cards.pack(fill="x", padx=8, pady=(8, GAP))
        for i in range(3):
            cards.grid_columnconfigure(i, weight=1, uniform="stat")

        self.stat_labels = {}
        stats = [("total", "Всего потрачено", BTN_DELETE),
                 ("avg", "Средний расход", ACCENT),
                 ("top", "Топ категория", BTN_SAVE)]
        for column, (key, title, color) in enumerate(stats):
            card = ctk.CTkFrame(cards, fg_color=BG_CARD, corner_radius=RADIUS)
            card.grid(row=0, column=column, padx=6, sticky="ew")
            ctk.CTkLabel(card, text=title, font=FONT_SMALL, text_color=TEXT_DIM
                         ).pack(anchor="w", padx=PADDING, pady=(PADDING, 4))
            value = ctk.CTkLabel(card, text="—", font=(FONT_FAMILY, 22, "bold"),
                                 text_color=color)
            value.pack(anchor="w", padx=PADDING, pady=(0, PADDING))
            self.stat_labels[key] = value

        # Карточка с диаграммой
        self.chart_card = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=RADIUS)
        self.chart_card.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        ctk.CTkLabel(self.chart_card, text="Диаграмма по категориям", font=FONT_HEADER,
                     text_color=TEXT_MAIN).pack(anchor="w", padx=PADDING, pady=(PADDING, 0))
        self.chart_holder = ctk.CTkFrame(self.chart_card, fg_color="transparent")
        self.chart_holder.pack(fill="both", expand=True, padx=PADDING, pady=PADDING)

        # Заглушка «нет данных»
        self.chart_empty = ctk.CTkLabel(self.chart_holder,
                                        text="Пока нет расходов. Добавьте первый!",
                                        font=FONT_NORMAL, text_color=TEXT_DIM)
        self.chart_empty.pack(expand=True)
        self.chart_canvas = None  # холст matplotlib, создадим при первом рисунке

    # ─────────────────── Действия пользователя ───────────────────

    def save_expense(self):
        """Проверяет поля формы и добавляет расход в базу."""
        try:
            amount, category, expense_date = validate_expense_input(
                self.amount_entry.get(), self.category_menu.get(), self.date_entry.get())
        except ValueError as error:
            # Неверный ввод — показываем окно с ошибкой, программа не падает
            messagebox.showwarning("Ошибка ввода", str(error), parent=self)
            return

        add_expense(amount, category, expense_date, self.desc_entry.get().strip())
        self.amount_entry.delete(0, "end")   # очищаем поля,
        self.desc_entry.delete(0, "end")     # дату оставляем —
        self.category_menu.set(FORM_CATEGORIES[0])  # обычно тратят сегодня
        self.load_expenses()
        self.update_stats()

    def delete_selected(self):
        """Удаляет выбранную запись после подтверждения."""
        if self.selected_id is None:
            return
        if not messagebox.askyesno("Подтверждение", "Удалить выбранную запись?",
                                   parent=self):
            return
        delete_expense(self.selected_id)
        self.selected_id = None
        self.load_expenses()
        self.update_stats()

    def load_expenses(self):
        """Показывает в таблице расходы: сначала дни, внутри дня — траты."""
        for row in self.tree.get_children():
            self.tree.delete(row)
        expenses = get_expenses(self.filter_menu.get())
        self._row_ids = {}
        self.selected_id = None  # строки очищены — выбор сбрасываем

        # Если записей нет — показываем подсказку вместо пустой таблицы
        if not expenses:
            self.tree.insert("", "end",
                             values=("", "Пока нет расходов. Добавьте первый!", ""))
            self.update_summary(expenses)
            self._update_delete_button()
            return

        for day, items in group_by_day(expenses).items():
            # Заголовок дня: 📅 Сегодня / Вчера / 05.10.2026 + сумма за день
            day_total = sum(item["amount"] for item in items)
            parent = self.tree.insert("", "end", tags=("day",),
                                      values=(f"📅 {day_title(day)}",
                                              format_amount(day_total), ""))
            for i, item in enumerate(items):  # траты внутри дня
                tag = "even" if i % 2 == 0 else "odd"
                child = self.tree.insert(
                    parent, "end", tags=(tag,),
                    values=(item["category"], format_amount(item["amount"]),
                            item["description"] or "—"))
                self._row_ids[child] = item["id"]

        self.update_summary(expenses)
        self._update_delete_button()

    def update_summary(self, expenses):
        """Обновляет строку «Записей: N · Итого: X ₸» под таблицей."""
        count, total = len(expenses), total_sum(expenses)
        self.summary_label.configure(
            text=f"Записей: {count} · Итого: {format_amount(total)}")

    def update_stats(self):
        """Обновляет карточки и диаграмму на вкладке «Статистика».

        Функции расчётов сами возвращают нули для пустого списка,
        поэтому отдельная проверка «а если записей нет» не нужна.
        """
        expenses = get_expenses("Все")
        self.stat_labels["total"].configure(text=format_amount(total_sum(expenses)))
        self.stat_labels["avg"].configure(text=format_amount(average_expense(expenses)))
        self.stat_labels["top"].configure(text=top_category(expenses)[0])
        self.draw_chart(expenses)

    def draw_chart(self, expenses):
        """Рисует круговую диаграмму; при пустом списке — надпись «нет расходов»."""
        import matplotlib
        matplotlib.use("TkAgg")
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        if self.chart_canvas:  # убираем старую диаграмму
            self.chart_canvas.get_tk_widget().destroy()
            self.chart_canvas = None
        self.chart_empty.pack_forget()
        if not expenses:  # база пустая — показываем заглушку
            self.chart_empty.pack(expand=True)
            return

        sums = sum_by_category(expenses)
        # Эмодзи убираем из подписей — шрифт диаграммы их не рисует
        labels = [name.split(" ", 1)[-1] for name in sums]
        values = list(sums.values())
        colors = [color for name, color in CATEGORIES if name in sums]

        figure = Figure(figsize=(6, 3.5), dpi=90)
        figure.patch.set_facecolor(BG_CARD)  # фон диаграммы = цвет карточки
        axes = figure.add_subplot(111)
        axes.pie(values, labels=labels, colors=colors, autopct="%1.0f%%",
                 startangle=90, textprops={"color": TEXT_MAIN, "fontsize": 9})
        figure.tight_layout()
        self.chart_canvas = FigureCanvasTkAgg(figure, master=self.chart_holder)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)

    # ─────────────────── Прочее ───────────────────

    def _on_select(self, _event=None):
        """Запоминает id траты; на заголовке дня — ничего не выбирается."""
        selection = self.tree.selection()
        item = selection[0] if selection else None
        # В словаре id есть только у трат; у заголовков дня id нет
        self.selected_id = self._row_ids.get(item)
        self._update_delete_button()

    def _update_delete_button(self):
        """Включает кнопку «Удалить» только когда выбрана трата."""
        if self.selected_id is None:
            self.delete_btn.configure(state="disabled")
        else:
            self.delete_btn.configure(state="normal")
