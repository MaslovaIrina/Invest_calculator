# calculators/charts.py
import io
import base64

import matplotlib
matplotlib.use("Agg")  # важно: до pyplot

import matplotlib.pyplot as plt

from schemas_living import MonthRentaRow, MonthMortgageRow


def _png_bytes_to_base64(png: bytes) -> str:
    return base64.b64encode(png).decode("ascii")


def build_main_chart_png_base64(
    rent_schedule: list[MonthRentaRow],
    buy_schedule: list[MonthMortgageRow],
) -> str:
    x_rent = [r.month for r in rent_schedule]
    y_rent = [r.full_invest_balance for r in rent_schedule]

    x_buy = [b.month for b in buy_schedule]
    y_buy = [b.net_worth_buy for b in buy_schedule]

    fig = plt.figure()
    plt.plot(x_rent, y_rent, label="Аренда + депозит")
    plt.plot(x_buy, y_buy, label="Покупка (капитал)")
    plt.xlabel("Месяц")
    plt.ylabel("Баланс")
    plt.legend()
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130)
    plt.close(fig)
    return _png_bytes_to_base64(buf.getvalue())


def build_mortgage_bar_chart_png_base64(
    buy_schedule: list[MonthMortgageRow]
) -> str:
    # Строим график "Проценты vs Тело кредита" по ипотеке
    x = [b.month for b in buy_schedule]
    deposit_balance = [b.deposit_change for b in buy_schedule]
    interest = [b.interest_paid for b in buy_schedule]
    principal = [b.principal_paid for b in buy_schedule]
    deposit_balance = [0 if x < 0 else x for x in deposit_balance]


    fig = plt.figure()
    plt.bar(x, interest, label="Оплата процентов ипотеки")
    plt.bar(x, principal, bottom=interest, label="Тело кредита")
    plt.bar(x, deposit_balance , bottom=[i + p for i, p in zip(interest, principal)], label="Пополнение депозита")
    plt.xlabel("Месяц")
    plt.ylabel("Платёж")
    plt.legend()
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130)
    plt.close(fig)
    return _png_bytes_to_base64(buf.getvalue())
'''

def build_mortgage_bar_chart_png_base64(
    buy_schedule: list[MonthMortgageRow]
) -> str:
    # Строим график "Проценты vs Тело кредита" по ипотеке
    x = [b.month for b in buy_schedule]
    interest = [b.interest_paid for b in buy_schedule]
    principal = [b.principal_paid for b in buy_schedule]


    fig = plt.figure()
    plt.bar(x, interest, label="Оплата процентов ипотеки")
    plt.bar(x, principal, bottom=interest, label="Тело кредита")
    plt.xlabel("Месяц")
    plt.ylabel("Платёж")
    plt.legend()
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130)
    plt.close(fig)
    return _png_bytes_to_base64(buf.getvalue())

'''

def build_mortgage_pie_chart_png_base64(
    buy_schedule: list[MonthMortgageRow]
) -> str: 
    interest = sum(b.interest_paid for b in buy_schedule)
    principal = sum(b.principal_paid for b in buy_schedule)
    labels = ['Выплачено процентов', 'Выплачено тела кредита']

    fig, ax = plt.subplots()
    ax.pie([interest, principal], autopct="%1.1f%%", startangle=90, wedgeprops = {"edgecolor" : "black",
                      'linewidth': 1,
                      'antialiased': True}, textprops={
                          'fontsize': 12,
                          'fontweight': "bold",
                      })
    ax.axis("equal")
    ax.legend(
        labels,
        loc="upper left",
        bbox_to_anchor=(-0.15, 1.1),   # позиция (x,y) в координатах осей
     #   borderaxespad=0.0,
     #   frameon=False,
    )



    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130)
    plt.close(fig)
    return _png_bytes_to_base64(buf.getvalue())

def build_invest_profit_chart_png_base64(
        results: list[dict],
        selected_start_month: int | None,
        deposit_path: list[float],
    ) -> str:
    if not results:
        return ""

    fig = plt.figure(figsize=(11, 5.5))

    # Все линии покупки
    purchase_label_used = False
    for item in results:
        schedule = item.get("schedule") or []
        if len(schedule) < 2:
            continue

        x_buy = [row["calendar_month"] for row in schedule]
        y_buy = [row["buy_profit"] for row in schedule]

        is_selected = (
            selected_start_month is not None
            and item["start_month"] == selected_start_month
        )

        label = None
        if not purchase_label_used:
            label = "Покупка"
            purchase_label_used = True

        if is_selected:
            plt.plot(
                x_buy,
                y_buy,
                color="tab:orange",
                linewidth=2.8,
                alpha=1.0,
                label=label
            )
        else:
            plt.plot(
                x_buy,
                y_buy,
                color="tab:orange",
                linewidth=1.4,
                alpha=0.45,
                label=label
            )

    # Линия депозита
    if deposit_path:
        x_dep = list(range(len(deposit_path)))
        y_dep = [value - deposit_path[0] for value in deposit_path]

        plt.plot(
            x_dep,
            y_dep,
            color="tab:blue",
            linewidth=3.0,
            alpha=1.0,
            label="Депозит"
    )

    plt.axhline(0, color="black", linewidth=0.8, alpha=0.5)
    plt.xlabel("Календарный месяц расчёта")
    plt.ylabel("Накопленная прибыль")
    plt.title("Прибыль депозита и сценариев покупки")
    plt.legend()
    plt.grid(True, alpha=0.2)
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130)
    plt.close(fig)
    return _png_bytes_to_base64(buf.getvalue())



def build_invest_capital_chart_png_base64(results: list[dict], selected_start_month: int | None) -> str:
    if not results:
        return ""

    fig = plt.figure(figsize=(11, 5.5))

    # Все линии покупки: общий капитал
    purchase_label_used = False
    for item in results:
        schedule = item.get("schedule") or []
        if len(schedule) < 2:
            continue

        x_buy = [row["calendar_month"] for row in schedule]
        y_buy = [row["net_worth_buy"] for row in schedule]

        is_selected = (
            selected_start_month is not None
            and item["start_month"] == selected_start_month
        )

        label = None
        if not purchase_label_used:
            label = "Покупка"
            purchase_label_used = True

        if is_selected:
            plt.plot(
                x_buy,
                y_buy,
                color="tab:orange",
                linewidth=2.8,
                alpha=1.0,
                label=label
            )
        else:
            plt.plot(
                x_buy,
                y_buy,
                color="tab:orange",
                linewidth=1.4,
                alpha=0.45,
                label=label
            )

    # Общий капитал депозита
    base_result = None
    if selected_start_month is not None:
        for item in results:
            if item["start_month"] == selected_start_month and item.get("schedule"):
                base_result = item
                break

    if base_result is None:
        for item in results:
            if item.get("schedule"):
                base_result = item
                break

    if base_result is not None:
        start_capital = float(base_result["start_capital"])
        x_dep = [row["calendar_month"] for row in base_result["schedule"]]
        y_dep = [start_capital + row["deposit_profit"] for row in base_result["schedule"]]

        plt.plot(
            x_dep,
            y_dep,
            color="tab:blue",
            linewidth=3.0,
            alpha=1.0,
            label="Депозит"
        )

    plt.xlabel("Календарный месяц расчёта")
    plt.ylabel("Общий капитал")
    plt.title("Общий капитал депозита и сценариев покупки")
    plt.legend()
    plt.grid(True, alpha=0.2)
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130)
    plt.close(fig)
    return _png_bytes_to_base64(buf.getvalue())

