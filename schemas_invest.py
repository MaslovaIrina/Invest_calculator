from typing import Optional, Literal
from pydantic import BaseModel, Field, model_validator


class InvestRequest(BaseModel):
    years_of_calculation: int = Field(gt=0)  # На сколько лет расчет
    all_free_money: float = Field(ge=0)  # Начальный капитал
    invest_percent: float = Field(ge=0)  # Под какой процент депозит
    deposit_refill: Literal["none", "every_year", "every_month"] = "none"
    deposit_refill_amount: Optional[float] = Field(default=None, ge=0)

    purchase_price: float = Field(gt=0)  # Цена объекта недвижимости
    yearly_apart_price_change: float  # Рост цены недвижимости в год
    new_building: Literal["none", "yes"] = "none"
    year_new_building_ready: Optional[float] = Field(default=None, ge=0)
    new_building_price_change: Optional[float] = Field(default=None, ge=0)

    mortgage_mode: Literal["none", "fixed_term", "by_budget"] = "none"
    ipotek_percent: Optional[float] = Field(default=None, ge=0)
    mortgage_term_years: Optional[float] = Field(default=None, gt=0)
    mortgage_monthly_budget: Optional[float] = Field(default=None, gt=0)

    k_min: float = Field(ge=0, default=0)

    @model_validator(mode="after")
    def validate_mortgage(self):
        if self.mortgage_mode == "fixed_term" and self.mortgage_term_years is None:
            raise ValueError("mortgage_term_years обязателен для fixed_term")
        if self.mortgage_mode == "by_budget" and self.mortgage_monthly_budget is None:
            raise ValueError("mortgage_monthly_budget обязателен для by_budget")
        return self


class InvestScheduleRow(BaseModel):
    month_from_start: int
    calendar_month: int

    mortgage_payment: float
    interest_paid: float
    principal_paid: float
    loan_balance: float

    buy_balance_change: float
    paid_apart_part: float
    buy_balance: float
    apart_price: float

    net_worth_buy: float


class InvestMonthResult(BaseModel):
    start_month: int
    start_capital: float
    start_price: float
    months_left: int
    mortgage_payment: float
    total_mortgage_paid: float
    final_net_worth: float
    loan_left: float
    buy_balance: float
    schedule: list[InvestScheduleRow] = []


class InvestResponse(BaseModel):
    found: bool
    message: str

    best_month: int | None
    best_buy_final: float | None
    deposit_final: float | None
    difference_final: float | None

    results: list[InvestMonthResult] = []