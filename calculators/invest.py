from schemas_invest import InvestRequest
from calculators.common import monthly_rate_from_percent
from calculators.mortgage import (
    choose_mortgage_months,
    choose_mortgage_payment,
    apply_mortgage_month,
)
from calculators.buy import apply_deposit_interest


def find_break_even_capital(req: InvestRequest):
    """
    Ищем не лучший итог в конце периода,
    а первый сценарий, где покупка начинает обгонять депозит по прибыли.
    """

    deposit_list, months = calc_deposit(req)
    property_price_list = calc_property_price(req, months)
    rent_income_list = calc_rent_income(req, months)

    results = []

    for start_month in months[:-1]:
        start_capital = deposit_list[start_month]
        start_price = property_price_list[start_month]
        months_left = months[-1] - start_month

        result = run_buy_from_month(
            req=req,
            start_month=start_month,
            start_capital=start_capital,
            start_price=start_price,
            months_left=months_left,
            deposit_list=deposit_list,
            rent_income_list=rent_income_list,
        )
        results.append(result)

    deposit_final = float(deposit_list[-1])

    profitable_results = [
        r for r in results
        if r["first_outperform_calendar_month"] is not None
    ]

    if profitable_results:
        found_result = min(
            profitable_results,
            key=lambda x: (
                x["first_outperform_calendar_month"],
                x["start_month"],
            )
        )

        return {
            "found": True,
            "message": (
                f"Покупка впервые обгоняет депозит в сценарии входа "
                f"на {found_result['start_month']}-м месяце. "
                f"Само пересечение происходит на "
                f"{found_result['first_outperform_calendar_month']}-м месяце расчёта."
            ),
            "start_month_to_buy": int(found_result["start_month"]),
            "cross_calendar_month": int(found_result["first_outperform_calendar_month"]),
            "deposit_profit_at_switch": round(float(found_result["deposit_profit_at_switch"])),
            "buy_profit_at_switch": round(float(found_result["buy_profit_at_switch"])),
            "difference_at_switch": round(float(found_result["difference_at_switch"])),
            "deposit_final": round(deposit_final),
            "buy_final_for_found_scenario": round(float(found_result["final_net_worth"])),
            "chart_profit_base64": "",
            "chart_capital_base64": "",
            "deposit_path": [round(float(x), 2) for x in deposit_list],
            "results": results,
        }

    return {
        "found": False,
        "message": "На заданном горизонте ни один сценарий покупки не обгоняет депозит по прибыли.",
        "start_month_to_buy": None,
        "cross_calendar_month": None,
        "deposit_profit_at_switch": None,
        "buy_profit_at_switch": None,
        "difference_at_switch": None,
        "deposit_final": round(deposit_final),
        "buy_final_for_found_scenario": None,
        "chart_profit_base64": "",
        "chart_capital_base64": "",
        "deposit_path": [round(float(x), 2) for x in deposit_list],
        "results": results,
    }


def calc_deposit(req):
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


def calc_rent_income(req, months):
    """
    Общая календарная шкала аренды.
    Аренда растёт раз в год, а не каждый месяц.
    Рост применяется на 12, 24, 36... месяце общего расчёта.
    """
    if getattr(req, "rent_after_purchase", "no") != "yes":
        return [0.0 for _ in months]

    rent_income = float(req.monthly_rent_income or 0.0)
    yearly_growth = float(req.yearly_rent_growth or 0.0)

    rent_income_list = [rent_income]

    for month in months[1:]:
        if month % 12 == 0:
            rent_income *= (1 + yearly_growth / 100.0)
        rent_income_list.append(rent_income)

    return rent_income_list


def run_buy_from_month(
    req,
    start_month,
    start_capital,
    start_price,
    months_left,
    deposit_list,
    rent_income_list,
):
    apart_price = float(start_price)

    down_payment_used = min(float(start_capital), apart_price)
    loan_balance = max(0.0, apart_price - down_payment_used)
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

    first_outperform_month_from_start = None
    first_outperform_calendar_month = None
    deposit_profit_at_switch = None
    buy_profit_at_switch = None
    difference_at_switch = None

    schedule = [
        {
            "month_from_start": 0,
            "calendar_month": int(start_month),
            "deposit_profit": 0.0,
            "buy_profit": 0.0,
            "rent_income": 0.0,
            "mortgage_payment": 0.0,
            "interest_paid": 0.0,
            "principal_paid": 0.0,
            "loan_balance": round(float(loan_balance), 2),
            "buy_balance_change": 0.0,
            "paid_apart_part": round(float(apart_price - loan_balance), 2),
            "buy_balance": round(float(buy_balance), 2),
            "apart_price": round(float(apart_price), 2),
            "net_worth_buy": round(float(net_worth_buy), 2),
        }
    ]

    for month in range(1, months_left + 1):
        calendar_month = start_month + month

        before_apart_price = apart_price
        before_buy_balance = buy_balance

        apart_price *= (1 + apart_growth_r)
        apart_price_change = apart_price - before_apart_price

        buy_balance = apply_deposit_interest(buy_balance, deposit_r)

        rent_income = 0.0
        if getattr(req, "rent_after_purchase", "no") == "yes":
            rent_income = float(rent_income_list[calendar_month])
            buy_balance += rent_income

        actual_payment = 0.0
        interest_paid = 0.0
        principal_paid = 0.0

        if loan_balance > 0.0 and month <= months_of_mortgage and req.mortgage_mode != "none":
            interest_paid, principal_paid, loan_balance, effective_payment = apply_mortgage_month(
                loan_balance=loan_balance,
                r=mortgage_r,
                payment=planned_payment,
            )
            actual_payment = effective_payment
            total_mortgage_paid += effective_payment
            buy_balance -= effective_payment

        net_worth_buy = apart_price + buy_balance - loan_balance

        deposit_profit = float(deposit_list[calendar_month] - start_capital)
        buy_profit = float(net_worth_buy - start_capital)

        if first_outperform_calendar_month is None and buy_profit > deposit_profit:
            first_outperform_month_from_start = int(month)
            first_outperform_calendar_month = int(calendar_month)
            deposit_profit_at_switch = float(deposit_profit)
            buy_profit_at_switch = float(buy_profit)
            difference_at_switch = float(buy_profit - deposit_profit)

        buy_balance_change = (buy_balance - before_buy_balance) + apart_price_change
        paid_apart_part = max(0.0, apart_price - loan_balance)

        schedule.append({
            "month_from_start": int(month),
            "calendar_month": int(calendar_month),
            "deposit_profit": round(float(deposit_profit), 2),
            "buy_profit": round(float(buy_profit), 2),
            "rent_income": round(float(rent_income), 2),
            "mortgage_payment": round(float(actual_payment), 2),
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
        "first_outperform_month_from_start": first_outperform_month_from_start,
        "first_outperform_calendar_month": first_outperform_calendar_month,
        "deposit_profit_at_switch": round(float(deposit_profit_at_switch), 2) if deposit_profit_at_switch is not None else None,
        "buy_profit_at_switch": round(float(buy_profit_at_switch), 2) if buy_profit_at_switch is not None else None,
        "difference_at_switch": round(float(difference_at_switch), 2) if difference_at_switch is not None else None,
        "schedule": schedule,
    }