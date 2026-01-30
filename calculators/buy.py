# calculators/buy.py
import math
from typing import Optional, Tuple

from schemas import CalcRequest, MonthMortgageRow
from calculators.common import monthly_rate_from_percent


# ----------------------------
# Small helpers
# ----------------------------

def monthly_growth_from_yearly_linear(yearly_percent: float) -> float:
    """Линейный месячный рост"""
    return (yearly_percent / 100.0) / 12.0


def apply_deposit_interest(balance: float, monthly_rate: float) -> float:
    """
    Начисляем процент на депозит/счёт.
    Если баланс отрицательный — не начисляем.
    """
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
    Подбор срока (в месяцах) по бюджету платежа P:
    - если P слишком мал (<= r*L) — кредит не погасится, вернём очень большое число
    - иначе формула для n через логарифм
    """
    if loan <= 0.0:
        return 0
    if monthly_budget <= 0.0:
        return 10**9

    if r == 0.0:
        return int(math.ceil(loan / monthly_budget))

    # Критическое условие: платеж должен покрывать проценты первого месяца
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
    effective_payment = interest + principal (учитывает последний платеж без переплаты тела)
    """
    if loan_balance <= 0.0:
        return 0.0, 0.0, 0.0, 0.0

    interest_paid = loan_balance * r
    principal_paid = payment - interest_paid

    # Платеж не покрывает проценты: долг растет
    if principal_paid < 0.0:
        new_loan = loan_balance + (-principal_paid)
        return float(interest_paid), 0.0, float(new_loan), float(payment)

    # Последний платеж: не переплачиваем тело
    if principal_paid > loan_balance:
        principal_paid = loan_balance

    new_loan = max(0.0, loan_balance - principal_paid)
    effective_payment = interest_paid + principal_paid
    return float(interest_paid), float(principal_paid), float(new_loan), float(effective_payment)


# ----------------------------
# Main
# ----------------------------

def calc_buy_schedule(req: CalcRequest) -> list[MonthMortgageRow]:
    months_total = int(req.years_of_calculation) * 12
    rows: list[MonthMortgageRow] = []

    # 1) Покупка: считаем, что all_free_money идёт на первоначальный взнос
    down_payment = float(req.all_free_money)
    loan_balance = max(0.0, float(req.purchase_price) - down_payment)

    # 2) Денежный счёт/депозит: после покупки считаем, что свободные деньги = 0
    # (всё ушло на взнос). Дальше депозит формируется ежемесячным денежным потоком.
    buy_balance = 0.0

    # 3) Ставки
    deposit_r = monthly_rate_from_percent(req.invest_percent)  # депозит/инвест доходность (в месяц)
    apart_growth_r = monthly_growth_from_yearly_linear(req.yearly_apart_price_change)

    # 4) Цена квартиры (актив)
    apart_price = float(req.purchase_price)

    # 5) Ипотечные параметры
    mortgage_r = 0.0
    if req.mortgage_mode != "none":
        if req.ipotek_percent is None:
            raise ValueError("ipotek_percent обязателен, если ипотека включена")
        mortgage_r = monthly_rate_from_percent(req.ipotek_percent)

    months_of_mortgage = choose_mortgage_months(req, loan_balance, mortgage_r, months_total)
    planned_payment = choose_mortgage_payment(req, loan_balance, mortgage_r, months_of_mortgage)

    for m in range(1, months_total + 1):
        # --- 1) Обновляем стоимость квартиры ---
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

        # --- 3) Депозит/денежный баланс: ВСЕГДА существует, даже после закрытия ипотеки ---
        # Сначала начисляем % на депозит
        before_balance = buy_balance
        buy_balance = apply_deposit_interest(buy_balance, deposit_r)

        # Потом учитываем денежный поток месяца:
        # monthly_free_money — общий бюджет на жильё/инвестиции
        # monthly_unexpected_expenses — внезапные траты (есть всегда)
        cash_after_housing = float(req.monthly_free_money) - mortgage_payment - float(req.monthly_unexpected_expenses)

        buy_balance += cash_after_housing
        buy_balance_change = buy_balance - before_balance

        # --- 4) Сколько квартиры "выкуплено" ---
        paid_apart_part = float(req.purchase_price) - loan_balance
        if paid_apart_part < 0.0:
            paid_apart_part = 0.0
        if paid_apart_part > float(req.purchase_price):
            paid_apart_part = float(req.purchase_price)

        rows.append(MonthMortgageRow(
            month=m,
            mortgage_payment=round(mortgage_payment, 2),
            interest_paid=round(interest_paid, 2),
            principal_paid=round(principal_paid, 2),
            loan_balance=round(loan_balance, 2),

            buy_balance_change=round(buy_balance_change, 2),
            paid_apart_part=round(paid_apart_part, 2),
            buy_balance=round(buy_balance, 2),
            apart_price=round(apart_price, 2),
        ))

    return rows
