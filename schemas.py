from typing import Optional, Literal
from pydantic import BaseModel, Field, model_validator


class CalcRequest(BaseModel):
    years_of_calculation: int = Field(gt=0)  # На сколько лет расчет

    purchase_price: float = Field(gt=0) # Цена объекта недвижимости

    monthly_rent: float = Field(ge=0) # Стоимость аренды в месяц
    yearly_rent_increase: float = Field(ge=0) # На сколько процентов в год увеличивается стоимость аренды

    monthly_free_money: float = Field(ge=0) # 
    all_free_money: float = Field(ge=0) # Начальный капитал
    invest_percent: float = Field(ge=0) # Под какой процент депозит

    yearly_apart_price_change: float # На сколько процентов в год меняется цена недвижимости
    monthly_unexpected_expenses: float = Field(ge=0) # Непредвиденные расчеты в месяц

    mortgage_mode: Literal["none", "full_term", "fixed_term", "by_budget"] = "none"
    ipotek_percent: Optional[float] = Field(default=None, ge=0)

    mortgage_term_years: Optional[float] = Field(default=None, gt=0)           # для fixed_term
    mortgage_monthly_budget: Optional[float] = Field(default=None, ge=0)       # для by_budget (если None/0 -> берем monthly_free_money)

    @model_validator(mode="after")
    def check_mortgage(self):
        if self.mortgage_mode != "none":
            if self.ipotek_percent is None:
                raise ValueError("ipotek_percent обязателен, если mortgage_mode != none")

        if self.mortgage_mode == "fixed_term":
            if self.mortgage_term_years is None:
                raise ValueError("mortgage_term_years обязателен для fixed_term")
            if self.mortgage_term_years > 30:
                raise ValueError("Ипотеку выдают не более чем на 30 лет")

        if self.mortgage_mode == "by_budget":
            if self.mortgage_monthly_budget is not None and self.mortgage_monthly_budget < 0:
                raise ValueError("mortgage_monthly_budget не может быть отрицательным")

        return self


class MonthRentaRow(BaseModel):
    month: int
    rent_payment: float
    full_rental_price: float
    invest_profit: float
    balance_change: float
    full_invest_balance: float


class MonthMortgageRow(BaseModel):
    month: int
    mortgage_payment: float
    interest_paid: float
    principal_paid: float
    loan_balance: float

    buy_balance_change: float
    paid_apart_part: float
    buy_balance: float
    deposit_change: float
    apart_price: float

    net_worth_buy: float  





class CalcResponse(BaseModel):
    rent_schedule: list[MonthRentaRow]
    buy_schedule: list[MonthMortgageRow]
    rent_final_balance: float
    buy_final_balance: float
    difference_final: float
    
    chart_main_base64: str
    chart_mortgage_base64: str
    chart_mortgage_pie_png_base64: str
