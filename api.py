from fastapi import FastAPI
from typing import Optional
from pydantic import BaseModel, Field, model_validator
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Real Estate Calculator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # для разработки ок; позже лучше указать конкретный origin
    allow_credentials=True,
    allow_methods=["*"],          # разрешаем OPTIONS/POST/GET...
    allow_headers=["*"],
)


class CalcRequest(BaseModel):
    purchase_price: float = Field(gt=0, description="Цена новой недвижимости")
    monthly_rent: float = Field(ge=0, description="Стоимость аренды в месяц")
    yearly_rent_increase: float = Field(ge=0, description="Удорожание стоимости аренды за год")
    monthly_free_money: float = Field(ge=0, description='Свободных денег для вложений в месяц')
    all_free_money: float = Field(ge=0, description='Свободных денег для вложений уже есть')
    invest_percent: float = Field(ge=0, description="Процентов годовых на вкладе")
    yearly_apart_price_change: float = Field(description="Изменение цены новой недвижимости в год")
    monthly_unexpected_expenses: float = Field(ge=0, description="Непредвиденные расходы в месяц")
    #yearly_new_building_price_change: float = Field(ge=0, description="Рост цены в новостройке засчет приближения к сроку сдачи")
    #is_new_building: bool = Field(default=False, description="Новостройка?")
    has_mortgage: bool = Field(default=False, description="Есть ипотека?")
    mortgage_term: Optional[float] = Field(default=None, gt=0, description="Срок ипотеки (лет)")
    ipotek_percent: Optional[float] = Field(ge=0, description="Процент по ипотеке годовых")



    @model_validator(mode="after")
    def check_mortgage_fields(self):
        if self.has_mortgage:
            if self.all_free_money > self.purchase_price:
                raise ValueError("all_free_money не может быть больше purchase_price")
            if self.mortgage_term > 31:
                raise ValueError('Ипотеку выдают не более, чем на 30 лет')
        return self



class CalcResponse(BaseModel):
    monthly_cashflow: float
    yearly_cashflow: float
    gross_yield_percent: float

@app.post("/api/calc", response_model=CalcResponse)
def calc(req: CalcRequest) -> CalcResponse:
    monthly_cashflow = req.monthly_rent - req.monthly_unexpected_expenses
    yearly_cashflow = monthly_cashflow * 12

    # “Грубая доходность” (без тонкостей NOI/вакансии/налогов) — чисто для демонстрации
    yearly_rent = req.monthly_rent * 12
    gross_yield_percent = (yearly_rent / req.purchase_price) * 100

    return CalcResponse(
        monthly_cashflow=round(monthly_cashflow, 2),
        yearly_cashflow=round(yearly_cashflow, 2),
        gross_yield_percent=round(gross_yield_percent, 2),
    )


@app.get("/")
def root():
    return {"status": "ok", "hint": "Open /docs or POST /api/calc"}
