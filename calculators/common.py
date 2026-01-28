def monthly_rate_from_percent(yearly_percent: float) -> float:
    """Годовая ставка -> месячная.
    Позже можно заменить.
    """
    return (yearly_percent / 100.0) / 12.0