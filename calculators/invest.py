from schemas_invest import InvestRequest, InvestResponse
from calculators.common import monthly_rate_from_percent

def find_break_even_capital(req: InvestRequest):
    "Вызов всех функций, полный расчет"
    r_deposit = monthly_rate_from_percent(req.invest_percent)
    deposit_list, months = calc_deposit(req, r_deposit) 





    print('AAAAAAAAAAAAAAAAAA')
    return 


def calc_deposit(req, r_deposit):
    "Подсчет депозита на весь срок"
    deposit = req.all_free_money
    total_months = req.years_of_calculation * 12

    deposit_list = [deposit]

    for month in range(1, total_months + 1):
        deposit *= (1 + r_deposit)

        if req.deposit_refill == "every_month":
            deposit += req.deposit_refill_amount
        elif req.deposit_refill == "every_year" and month % 12 == 0:
            deposit += req.deposit_refill_amount

        deposit_list.append(deposit)

    months = list(range(total_months + 1))
    return deposit_list, months




def invest_buy_schedule(req):
    "Один расчет с заданного месяца до конца"
    return
