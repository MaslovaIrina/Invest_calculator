from fastapi import FastAPI
from pydantic import BaseModel, Field
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
    purchase_price: float = Field(gt=0, description="Цена объекта")
    monthly_rent: float = Field(ge=0, description="Аренда в месяц")
    monthly_expenses: float = Field(ge=0, description="Расходы в месяц")
    monthly_salary: float = Field(ge=0, description='Зарплата')

class CalcResponse(BaseModel):
    monthly_cashflow: float
    yearly_cashflow: float
    gross_yield_percent: float

@app.post("/api/calc", response_model=CalcResponse)
def calc(req: CalcRequest) -> CalcResponse:
    monthly_cashflow = req.monthly_rent - req.monthly_expenses
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
