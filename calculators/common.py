

def monthly_rate_from_percent(yearly_percent: float) -> float:
    """Годовая ставка -> месячная.
    Позже можно заменить.
    """
    return (yearly_percent / 100.0) / 12.0


def build_warnings(req, rent_schedule, buy_schedule): 
    warnings = []
    if req.monthly_free_money < buy_schedule[0].mortgage_payment:
        warnings.append('Внимание! Платеж по ипотеке больше ежемесячного бюджета свободных денег.')
    if req.mortgage_mode == 'none' and req.all_free_money < req.purchase_price:
        warnings.append('Внимание! Отложенных средств не хватит на данный объект недвижимости. ')
    return warnings

