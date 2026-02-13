# calculators/buy.py
import math
from typing import Tuple

from schemas_living import CalcRequest, MonthMortgageRow
from calculators.common import monthly_rate_from_percent
from calculators.mortgage import calc_annuity_payment, calc_months_by_budget, choose_mortgage_months, choose_mortgage_payment, apply_mortgage_month


# ----------------------------
# Helpers
# ----------------------------


def apply_deposit_interest(balance: float, monthly_rate: float) -> float:
    """Начисляем процент на депозит. Баланс не может стать отрицательным."""
    if balance <= 0.0 or monthly_rate <= 0.0:
        return balance
    return balance * (1.0 + monthly_rate)



# ----------------------------
# Main
# ----------------------------

def calc_buy_schedule(req: CalcRequest) -> list[MonthMortgageRow]:
    months_total = int(req.years_of_calculation) * 12
    rows: list[MonthMortgageRow] = []

    # 1) Покупка: из all_free_money оплачиваем максимум purchase_price
    purchase_price = float(req.purchase_price)
    all_free_money = float(req.all_free_money)

    down_payment_used = min(all_free_money, purchase_price)
    loan_balance = max(0.0, purchase_price - down_payment_used)

    # 2) Остаток денег (если all_free_money > purchase_price) идёт на депозит
    buy_balance = max(0.0, all_free_money - down_payment_used)

    # 3) Ставки и рост цены квартиры
    deposit_r = monthly_rate_from_percent(req.invest_percent)
    apart_growth_r = monthly_rate_from_percent(req.yearly_apart_price_change)

    apart_price = purchase_price

    # 4) Ипотека: параметры
    mortgage_r = 0.0
    if req.mortgage_mode != "none" and loan_balance > 0.0:
        if req.ipotek_percent is None:
            raise ValueError("ipotek_percent обязателен, если ипотека включена")
        mortgage_r = monthly_rate_from_percent(req.ipotek_percent)

    months_of_mortgage = choose_mortgage_months(req, loan_balance, mortgage_r, months_total)
    planned_payment = choose_mortgage_payment(req, loan_balance, mortgage_r, months_of_mortgage)


    for m in range(1, months_total + 1):
        # --- 1) Стоимость квартиры растёт ---
        apart_price_change = apart_price * apart_growth_r
        apart_price += apart_price_change

        # --- 2) Ипотека активна? ---
        mortgage_active = (
            req.mortgage_mode != "none"
            and m <= months_of_mortgage
            and loan_balance > 0.0
        )

        if mortgage_active:
            interest_paid, principal_paid, loan_balance, effective_payment = apply_mortgage_month(
                loan_balance=loan_balance,
                r=mortgage_r,
                payment=planned_payment,
            )
            mortgage_payment = effective_payment
        else:
            mortgage_payment = 0.0
            interest_paid = 0.0
            principal_paid = 0.0

        # --- 3) Депозит: всегда есть, НО мы его не уменьшаем ---
        before_balance = buy_balance
        buy_balance = apply_deposit_interest(buy_balance, deposit_r)

        # Денежный поток месяца: сколько осталось после ипотеки и unexpected
        cap = req.monthly_free_money
        cash_after_housing = cap - mortgage_payment
        
        #if cash_after_housing < -1e-9:
        #    raise ValueError("Ипотечный платеж превышает доступный месячный бюджет.")

        # Остаток добавляем на депозит
        buy_balance += cash_after_housing
        deposit_change = buy_balance - before_balance

        buy_balance_change = buy_balance - before_balance +  apart_price_change

        # --- 4) Сколько квартиры “выкуплено” ---
        paid_apart_part = purchase_price - loan_balance
        if paid_apart_part < 0.0:
            paid_apart_part = 0.0
        if paid_apart_part > purchase_price:
            paid_apart_part = purchase_price

        # --- 5) Выгода/капитал в сценарии покупки ---
        net_worth_buy = apart_price + buy_balance - loan_balance

        rows.append(MonthMortgageRow(
            month=m,
            mortgage_payment=round(mortgage_payment, 2),
            interest_paid=round(interest_paid, 2),
            principal_paid=round(principal_paid, 2),
            loan_balance=round(loan_balance, 2),

            buy_balance_change=round(buy_balance_change, 2),
            paid_apart_part=round(paid_apart_part, 2),
            buy_balance=round(buy_balance, 2),
            deposit_change=round(cash_after_housing, 2),
            apart_price=round(apart_price, 2),

            net_worth_buy=round(net_worth_buy, 2),
        ))

    return rows
