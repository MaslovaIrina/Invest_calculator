# schemas.py
from typing import Optional
from pydantic import BaseModel, Field, model_validator

class CalcRequest(BaseModel):
    years_of_calculation: float = Field(gt=0, description="На сколько лет расчет")
    purchase_price: float = Field(gt=0, description="Цена новой недвижимости") #
    monthly_rent: float = Field(ge=0, description="Стоимость аренды в месяц") #
    yearly_rent_increase: float = Field(ge=0, description="Удорожание стоимости аренды за год") #
    monthly_free_money: float = Field(ge=0, description='Свободных денег для вложений\аренды в месяц') #
    all_free_money: float = Field(ge=0, description='Свободных денег для вложений уже есть')
    invest_percent: float = Field(ge=0, description="Процентов годовых на вкладе")
    yearly_apart_price_change: float = Field(description="Изменение цены новой недвижимости в год")
    monthly_unexpected_expenses: float = Field(ge=0, description="Непредвиденные расходы в месяц")
    #yearly_new_building_price_change: float = Field(ge=0, description="Рост цены в новостройке засчет приближения к сроку сдачи")
    #is_new_building: bool = Field(default=False, description="Новостройка?")
    has_mortgage: bool = Field(default=False, description="Есть ипотека?")
    mortgage_term: Optional[float] = Field(default=None, gt=0, description="Срок ипотеки (лет)")
    ipotek_percent: Optional[float] = Field(default=None, ge=0, description="Процент по ипотеке годовых")

    @model_validator(mode="after")
    def check_mortgage_fields(self):
        if self.has_mortgage:
            if self.mortgage_term is None or self.ipotek_percent is None:
                raise ValueError("Для ипотеки нужны mortgage_term и ipotek_percent")
            if self.mortgage_term > 30:
                raise ValueError("Ипотеку выдают не более чем на 30 лет")
        return self

class MonthRow(BaseModel):
    month: int
    mortgage_payment: float
    interest_paid: float
    principal_paid: float
    loan_balance: float

class CalcResponse(BaseModel):
    schedule: list[MonthRow]
    monthly_cashflow: float # костыль
    yearly_cashflow: float  # костыль
    gross_yield_percent: float  # костыль
