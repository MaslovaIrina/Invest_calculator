from typing import Optional, Literal
from pydantic import BaseModel, Field, model_validator


class InvestRequest(BaseModel):
    
    years_of_calculation: int = Field(gt=0)  # На сколько лет расчет
    all_free_money: float = Field(ge=0) # Начальный капитал
    invest_percent: float = Field(ge=0) # Под какой процент депозит
    deposit_refill: Literal["none", "every_year", "every_month"] = "none"
    deposit_refill_amount: Optional[float] = Field(default=None, ge=0)

    purchase_price: float = Field(gt=0) # Цена объекта недвижимости
    yearly_apart_price_change: float # На сколько процентов в год меняется цена недвижимости во вторичке
    new_building: Literal["none", "yes"] = "none" # Новостройка?
    year_new_buildeing_ready: Optional[float] = Field(default=None, ge=0) # Через сколько будет готов объект
    yearly_new_building_price_change: Optional[float] = Field(default=None, ge=0) # Ожидаемое подорожание новостройки за период строительства, проценты

    mortgage_mode: Literal["none", "full_term", "fixed_term", "by_budget"] = "none"
    ipotek_percent: Optional[float] = Field(default=None, ge=0)
    mortgage_term_years: Optional[float] = Field(default=None, gt=0)           # для fixed_term
    mortgage_monthly_budget: Optional[float] = Field(default=None, ge=0)   


    k_min: float = Field(ge=0, default=0) # пороговый поиск по капиталу


class InvestResponse(BaseModel):
    
    break_even_capital: float | None  # None если не найдено в диапазоне
    found: bool
    message: str