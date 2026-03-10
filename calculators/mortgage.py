import math
from typing import Tuple
from schemas_living import CalcRequest

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


def choose_mortgage_months(req, loan: float, r: float, months_total: int) -> int:
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




def choose_mortgage_payment(req, loan: float, r: float, months_of_mortgage: int) -> float:
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


