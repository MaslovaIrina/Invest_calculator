# calculators/buy.py
import math
from typing import Tuple

from schemas import CalcRequest, MonthMortgageRow
from calculators.common import monthly_rate_from_percent


# ----------------------------
# Helpers
# ----------------------------

def monthly_growth_from_yearly_linear(yearly_percent: float) -> float:
    """Линейный месячный рост: yearly% / 12."""
    return (yearly_percent / 100.0) / 12.0


def apply_deposit_interest(balance: float, monthly_rate: float) -> float:
    """Начисляем процент на депозит. Баланс не может стать отрицательным."""
    if balance <= 0.0 or monthly_rate <= 0.0:
        return balance
    return balance * (1.0 + monthly_rate)


def calc_annuity_payment(loan: float, r: float, n_months: int) -> float:
    """Аннуитетный платеж."""
    if loan <= 0.0 or n_months <= 0:
        return 0.0
    if r == 0.0:
        return loan / n_months
    p = (1.0 + r) ** n_months
    return loan * (r * p) / (p - 1.0)


def calc_months_by_budget(loan: float, r: float, monthly_budget: float) -> int:
    """
    Подбор срока по бюджету платежа P.
    Если P слишком мал (<= r*L) — кредит не погасится, вернём очень большое число.
    """
    if loan <= 0.0:
        return 0
    if monthly_budget <= 0.0:
        return 10**9

    if r == 0.0:
        return int(math.ceil(loan / monthly_budget))

    if monthly_budget <= r * loan:
        return 10**9

    n = math.log(monthly_budget / (monthly_budget - r * loan)) / math.log(1.0 + r)
    return int(math.ceil(n))


def choose_mortgage_months(req: CalcRequest, loan: float, r: float, months_total: int) -> int:
    """
    mortgage_mode:
      - none       : ипотеки нет
      - full_term  : ипотека на весь срок расчёта
      - fixed_term : ипотека на заданный срок (mortgage_term_years)
      - by_budget  : срок подбирается под платеж (mortgage_monthly_budget или monthly_free_money)
    """
    if loan <= 0.0 or req.mortgage_mode == "none":
        return 0

    if req.mortgage_mode == "full_term":
        return months_total

    if req.mortgage_mode == "fixed_term":
        if req.mortgage_term_years is None:
            raise ValueError("mortgage_term_years обязателен для fixed_term")
        return int(req.mortgage_term_years * 12)

    if req.mortgage_mode == "by_budget":
        budget = req.mortgage_monthly_budget or 0.0
        if budget <= 0.0:
            budget = req.monthly_free_money
        return calc_months_by_budget(loan, r, budget)

    raise ValueError(f"Unknown mortgage_mode: {req.mortgage_mode}")


def choose_mortgage_payment(req: CalcRequest, loan: float, r: float, months_of_mortgage: int) -> float:
    """
    Выбираем месячный платеж:
      - by_budget  : платеж = mortgage_monthly_budget (или monthly_free_money)
      - иначе      : аннуитет по сроку
    """
    if loan <= 0.0 or req.mortgage_mode == "none" or months_of_mortgage <= 0:
        return 0.0

    if req.mortgage_mode == "by_budget":
        payment = req.mortgage_monthly_budget or 0.0
        if payment <= 0.0:
            payment = req.monthly_free_money
        return float(payment)

    return float(calc_annuity_payment(loan, r, months_of_mortgage))


def apply_mortgage_month(loan_balance: float, r: float, payment: float) -> Tuple[float, float, float, float]:
    """
    Один месяц ипотеки.
    Возвращает: (interest_paid, principal_paid, new_loan_balance, effective_payment)
    effective_payment = interest + principal (с учетом последнего платежа без переплаты тела)
    """
    if loan_balance <= 0.0:
        return 0.0, 0.0, 0.0, 0.0

    interest_paid = loan_balance * r
    principal_paid = payment - interest_paid

    # Платеж не покрывает проценты: долг растёт -> это сценарий "не тянет ипотеку"
    if principal_paid < 0.0:
        raise ValueError("Платеж меньше процентов по ипотеке — кредит не погашается. Увеличьте платеж или уменьшите сумму/ставку.")

    # Последний платеж: не переплачиваем тело
    if principal_paid > loan_balance:
        principal_paid = loan_balance

    new_loan = max(0.0, loan_balance - principal_paid)
    effective_payment = interest_paid + principal_paid
    return float(interest_paid), float(principal_paid), float(new_loan), float(effective_payment)


def monthly_payment_capacity(req: CalcRequest) -> float:
    """
    Сколько пользователь реально может отдать в месяц на ипотеку/инвестирование.
    По твоему правилу: платеж должен укладываться в бюджет.
    """
    cap = float(req.monthly_free_money) - float(req.monthly_unexpected_expenses)
    return cap


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
    apart_growth_r = monthly_growth_from_yearly_linear(req.yearly_apart_price_change)

    apart_price = purchase_price

    # 4) Ипотека: параметры
    mortgage_r = 0.0
    if req.mortgage_mode != "none" and loan_balance > 0.0:
        if req.ipotek_percent is None:
            raise ValueError("ipotek_percent обязателен, если ипотека включена")
        mortgage_r = monthly_rate_from_percent(req.ipotek_percent)

    months_of_mortgage = choose_mortgage_months(req, loan_balance, mortgage_r, months_total)
    planned_payment = choose_mortgage_payment(req, loan_balance, mortgage_r, months_of_mortgage)

    # 5) Проверка “не тянет ипотеку” 
    cap = monthly_payment_capacity(req)
    if planned_payment > 0.0 and planned_payment > cap:
        raise ValueError(
            f"Платёж по ипотеке ({planned_payment:.2f}) больше доступного бюджета в месяц ({cap:.2f}). "
            "Уменьшите платёж/срок/сумму кредита или увеличьте monthly_free_money."
        )

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
        cap = monthly_payment_capacity(req)
        cash_after_housing = cap - mortgage_payment
        
        if cash_after_housing < -1e-9:
            raise ValueError("Ипотечный платеж превышает доступный месячный бюджет.")

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
