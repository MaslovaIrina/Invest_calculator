from typing import Optional

from pydantic import BaseModel, Field, model_validator


class CalcRequest(BaseModel):
    years_of_calculation: int = Field(gt=0, description="На сколько лет расчет")

    purchase_price: float = Field(gt=0, description="Цена недвижимости")

    monthly_rent: float = Field(ge=0, description="Аренда в месяц")
    yearly_rent_increase: float = Field(ge=0, description="Рост аренды в год, %")

    monthly_free_money: float = Field(ge=0, description="Доступная сумма в месяц на жильё/инвестиции")
    all_free_money: float = Field(ge=0, description="Начальный капитал для инвестиций")
    invest_percent: float = Field(ge=0, description="Процент годовых по вкладу, %")

    yearly_apart_price_change: float = Field(description="Изменение цены недвижимости в год, %")
    monthly_unexpected_expenses: float = Field(ge=0, description="Непредвиденные расходы в месяц")

    has_mortgage: bool = Field(default=False, description="Есть ипотека?")
    mortgage_term: Optional[float] = Field(default=None, gt=0, description="Срок ипотеки (лет)")
    ipotek_percent: Optional[float] = Field(default=None, ge=0, description="Процент по ипотеке годовых, %")

    @model_validator(mode="after")
    def check_mortgage_fields(self):
        if self.has_mortgage:
            if self.mortgage_term is None or self.ipotek_percent is None:
                raise ValueError("Для ипотеки нужны mortgage_term и ipotek_percent")
            if self.mortgage_term > 30:
                raise ValueError("Ипотеку выдают не более чем на 30 лет")
        return self


class MonthRentaRow(BaseModel):
    month: int
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


class CalcResponse(BaseModel):
    rent_schedule: list[MonthRentaRow]
    buy_schedule: list[MonthMortgageRow]

    rent_final_balance: float
    buy_final_balance: float
    difference_final: float

    monthly_cashflow: float
    yearly_cashflow: float
    gross_yield_percent: float
