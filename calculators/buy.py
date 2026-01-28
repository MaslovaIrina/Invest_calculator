from schemas import CalcRequest, MonthRow

def calc_buy_schedule(req: CalcRequest) -> list[MonthRow]:
    months = int((req.mortgage_term or 0) * 12) if req.has_mortgage else 0
    rows: list[MonthRow] = []

    # Заглушка состояний — ДОБАВИТЬ ФОРМУЛЫ
    loan_balance = req.purchase_price

    for m in range(1, months + 1):
        mortgage_payment = 0.0
        interest_paid = 0.0
        principal_paid = 0.0

        rows.append(MonthRow(
            month=m,
            mortgage_payment=mortgage_payment,
            interest_paid=interest_paid,
            principal_paid=principal_paid,
            loan_balance=loan_balance,
        ))
    return rows
