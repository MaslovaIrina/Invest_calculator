from schemas import CalcRequest, MonthMortgageRow
from calculators.common import monthly_rate_from_percent


def get_mortgage_params(req: CalcRequest, loan_balance: float) -> tuple[int, float, float]:
    """Параметры ипотеки: (months_of_mortgage, r, mortgage_payment)."""
    if not req.has_mortgage:
        return 0, 0.0, 0.0

    if req.mortgage_term is None or req.ipotek_percent is None:
        raise ValueError("mortgage_term и ipotek_percent обязательны, если has_mortgage=True")

    months_of_mortgage = int(req.mortgage_term * 12)
    if months_of_mortgage <= 0:
        raise ValueError("mortgage_term должен быть > 0")

    r = monthly_rate_from_percent(req.ipotek_percent)

    if r == 0.0:
        mortgage_payment = loan_balance / months_of_mortgage
    else:
        p = (1 + r) ** months_of_mortgage
        mortgage_payment = loan_balance * (r * p) / (p - 1)

    return months_of_mortgage, r, mortgage_payment


def calc_buy_schedule(req: CalcRequest) -> list[MonthMortgageRow]:
    """График выплат по ипотеке.

    Упрощение: сумма кредита = purchase_price (без первоначального взноса).
    Если ипотеки нет — долг = 0.
    """
    months = int(req.years_of_calculation) * 12
    rows: list[MonthMortgageRow] = []

    loan_balance = float(req.purchase_price) if req.has_mortgage else 0.0
    months_of_mortgage, r, mortgage_payment = get_mortgage_params(req, loan_balance)

    for m in range(1, months + 1):
        if not req.has_mortgage or m > months_of_mortgage or loan_balance <= 0.0:
            rows.append(MonthMortgageRow(
                month=m,
                mortgage_payment=0.0,
                interest_paid=0.0,
                principal_paid=0.0,
                loan_balance=round(loan_balance, 2),
            ))
            continue

        interest_paid = loan_balance * r
        principal_paid = mortgage_payment - interest_paid

        # Последний платёж: не уходим "в минус" по долгу
        if principal_paid > loan_balance:
            principal_paid = loan_balance
            mortgage_payment_effective = interest_paid + principal_paid
        else:
            mortgage_payment_effective = mortgage_payment

        loan_balance = max(0.0, loan_balance - principal_paid)

        rows.append(MonthMortgageRow(
            month=m,
            mortgage_payment=round(mortgage_payment_effective, 2),
            interest_paid=round(interest_paid, 2),
            principal_paid=round(principal_paid, 2),
            loan_balance=round(loan_balance, 2),
        ))

    return rows
