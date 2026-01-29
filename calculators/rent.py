from schemas import CalcRequest, MonthRentaRow
from calculators.common import monthly_rate_from_percent


def calc_rent(req: CalcRequest) -> list[MonthRentaRow]:
    months = int(req.years_of_calculation) * 12
    rows: list[MonthRentaRow] = []

    full_rental_price = 0.0
    invest_balance = float(req.all_free_money)

    monthly_rent = float(req.monthly_rent)
    invest_rate = monthly_rate_from_percent(req.invest_percent)
    yearly_rent_increase_factor = 1 + (req.yearly_rent_increase / 100.0)

    for m in range(1, months + 1):
        if m % 12 == 1 and m != 1:
            monthly_rent *= yearly_rent_increase_factor

        full_rental_price += monthly_rent

        invest_profit = invest_balance * invest_rate
        balance_change = (
            req.monthly_free_money
            + invest_profit
            - monthly_rent
            - req.monthly_unexpected_expenses
        )
        invest_balance += balance_change

        rows.append(MonthRentaRow(
            month=m,
            rent_payment=round(monthly_rent, 2),
            full_rental_price=round(full_rental_price, 2),
            invest_profit=round(invest_profit, 2),
            balance_change=round(balance_change, 2),
            full_invest_balance=round(invest_balance, 2),
        ))

    return rows
