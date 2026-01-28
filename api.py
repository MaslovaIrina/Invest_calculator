# api.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from schemas import CalcRequest, CalcResponse
from calculators.buy import calc_buy_schedule
from calculators.rent import calc_rent

app = FastAPI(title="Real Estate Calculator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/calc", response_model=CalcResponse)
def calc(req: CalcRequest) -> CalcResponse:
    # schedule: пусть пока будет график ипотеки, если ипотека включена, иначе пусто
    schedule = calc_buy_schedule(req) if req.has_mortgage else calc_rent(req)

    monthly_cashflow = req.monthly_rent - req.monthly_unexpected_expenses
    yearly_cashflow = monthly_cashflow * 12

    yearly_rent = req.monthly_rent * 12
    gross_yield_percent = (yearly_rent / req.purchase_price) * 100

    return CalcResponse(
        schedule=schedule,
        monthly_cashflow=round(monthly_cashflow, 2),
        yearly_cashflow=round(yearly_cashflow, 2),
        gross_yield_percent=round(gross_yield_percent, 2),
    )

@app.get("/")
def root():
    return {"status": "ok"}
