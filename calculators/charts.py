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
