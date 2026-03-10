from schemas_invest import InvestRequest
from calculators.common import monthly_rate_from_percent
from calculators.mortgage import (
    choose_mortgage_months,
    choose_mortgage_payment,
    apply_mortgage_month,
)
from calculators.buy import apply_deposit_interest


def find_break_even_capital(req: InvestRequest):
    "Вызов всех функций, полный расчет"

    deposit_list, months = calc_deposit(req)
    property_price_list = calc_property_price(req, months)

    results = []

    for start_month in months:
        start_capital = deposit_list[start_month]
        start_price = property_price_list[start_month]
        months_left = months[-1] - start_month

        result = run_buy_from_month(
            req=req,
            start_month=start_month,
            start_capital=start_capital,
            start_price=start_price,
            months_left=months_left,
        )
        results.append(result)

    best_result = max(results, key=lambda x: x["final_net_worth"])
    deposit_final = float(deposit_list[-1])
    best_buy_final = float(best_result["final_net_worth"])
    difference_final = best_buy_final - deposit_final

    if best_buy_final > deposit_final:
        message = (
            f"Лучший месяц входа: {best_result['start_month']}. "
            f"Покупка выгоднее депозита на {round(difference_final)} руб."
        )
        found = True
    else:
        message = (
            f"На заданном горизонте депозит выгоднее покупки на "
            f"{round(deposit_final - best_buy_final)} руб."
        )
        found = False

    return {
        "found": found,
        "message": message,
        "best_month": int(best_result["start_month"]),
        "best_buy_final": round(best_buy_final),
        "deposit_final": round(deposit_final),
        "difference_final": round(difference_final),
        "results": results,
    }


def calc_deposit(req):
    "Подсчет депозита на весь срок"
    r_deposit = monthly_rate_from_percent(req.invest_percent)
    deposit = float(req.all_free_money)
    total_months = int(req.years_of_calculation) * 12

    deposit_list = [deposit]

    for month in range(1, total_months + 1):
        deposit *= (1 + r_deposit)

        if req.deposit_refill == "every_month":
            deposit += float(req.deposit_refill_amount or 0.0)
        elif req.deposit_refill == "every_year" and month % 12 == 0:
            deposit += float(req.deposit_refill_amount or 0.0)

        deposit_list.append(deposit)

    months = list(range(total_months + 1))
    return deposit_list, months


def calc_property_price(req, months):
    apart_price = float(req.purchase_price)
    apart_price_list = [apart_price]
    r_apart = monthly_rate_from_percent(req.yearly_apart_price_change)

    for _ in months[1:]:
        apart_price *= (1 + r_apart)
        apart_price_list.append(apart_price)

    return apart_price_list


def run_buy_from_month(req, start_month, start_capital, start_price, months_left):
    "Один расчет с заданного месяца до конца"

    apart_price = float(start_price)

    # Что смогли внести сразу
    down_payment_used = min(float(start_capital), apart_price)

    # Остаток долга
    loan_balance = max(0.0, apart_price - down_payment_used)

    # Денежный остаток после первого взноса
    buy_balance = max(0.0, float(start_capital) - down_payment_used)

    apart_growth_r = monthly_rate_from_percent(req.yearly_apart_price_change)
    deposit_r = monthly_rate_from_percent(req.invest_percent)

    months_of_mortgage = 0
    planned_payment = 0.0
    mortgage_r = 0.0

    if loan_balance > 0.0 and req.mortgage_mode != "none":
        if req.ipotek_percent is None:
            raise ValueError("ipotek_percent обязателен, если ипотека включена")

        mortgage_r = monthly_rate_from_percent(req.ipotek_percent)

        months_of_mortgage = choose_mortgage_months(
            req=req,
            loan=loan_balance,
            r=mortgage_r,
            months_total=months_left,
        )

        planned_payment = choose_mortgage_payment(
            req=req,
            loan=loan_balance,
            r=mortgage_r,
            months_of_mortgage=months_of_mortgage,
        )

    total_mortgage_paid = 0.0
    net_worth_buy = apart_price + buy_balance - loan_balance
    schedule = []

    for month in range(1, months_left + 1):
        before_apart_price = apart_price
        before_buy_balance = buy_balance

        # 1) Квартира дорожает
        apart_price *= (1 + apart_growth_r)
        apart_price_change = apart_price - before_apart_price

        # 2) Остаток денег продолжает жить как депозит
        buy_balance = apply_deposit_interest(buy_balance, deposit_r)

        actual_last_payment = 0.0
        interest_paid = 0.0
        principal_paid = 0.0

        # 3) Платим ипотеку из денежного остатка
        if loan_balance > 0.0 and month <= months_of_mortgage and req.mortgage_mode != "none":
            interest_paid, principal_paid, loan_balance, effective_payment = apply_mortgage_month(
                loan_balance=loan_balance,
                r=mortgage_r,
                payment=planned_payment,
            )
            actual_last_payment = effective_payment
            total_mortgage_paid += effective_payment
            buy_balance -= effective_payment

        # 4) Итоговый капитал = квартира + денежный остаток - долг
        net_worth_buy = apart_price + buy_balance - loan_balance

        buy_balance_change = (buy_balance - before_buy_balance) + apart_price_change
        paid_apart_part = max(0.0, apart_price - loan_balance)

        schedule.append({
            "month_from_start": int(month),
            "calendar_month": int(start_month + month),
            "mortgage_payment": round(float(actual_last_payment), 2),
            "interest_paid": round(float(interest_paid), 2),
            "principal_paid": round(float(principal_paid), 2),
            "loan_balance": round(float(loan_balance), 2),
            "buy_balance_change": round(float(buy_balance_change), 2),
            "paid_apart_part": round(float(paid_apart_part), 2),
            "buy_balance": round(float(buy_balance), 2),
            "apart_price": round(float(apart_price), 2),
            "net_worth_buy": round(float(net_worth_buy), 2),
        })

    return {
        "start_month": int(start_month),
        "start_capital": round(float(start_capital)),
        "start_price": round(float(start_price)),
        "months_left": int(months_left),
        "mortgage_payment": round(float(planned_payment)),
        "total_mortgage_paid": round(float(total_mortgage_paid)),
        "loan_left": round(float(loan_balance)),
        "buy_balance": round(float(buy_balance)),
        "final_net_worth": round(float(net_worth_buy)),
        "schedule": schedule,
    }