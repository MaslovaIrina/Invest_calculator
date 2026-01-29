from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from schemas import CalcRequest, CalcResponse
from calculators.rent import calc_rent
from calculators.buy import calc_buy_schedule

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
    rent_schedule = calc_rent(req)
    buy_schedule = calc_buy_schedule(req)

    rent_final_balance = float(rent_schedule[-1].full_invest_balance) if rent_schedule else float(req.all_free_money)

    loan_balance_end = float(buy_schedule[-1].loan_balance) if buy_schedule else float(req.purchase_price)
    buy_final_balance = float(req.purchase_price) - loan_balance_end

    # костыли для текущего UI (можно будет убрать позже)
    monthly_cashflow = req.monthly_rent - req.monthly_unexpected_expenses
    yearly_cashflow = monthly_cashflow * 12
    yearly_rent = req.monthly_rent * 12
    gross_yield_percent = (yearly_rent / req.purchase_price) * 100

    return CalcResponse(
        rent_schedule=rent_schedule,
        buy_schedule=buy_schedule,
        rent_final_balance=round(rent_final_balance, 2),
        buy_final_balance=round(buy_final_balance, 2),
        difference_final=round(buy_final_balance - rent_final_balance, 2),
        monthly_cashflow=round(monthly_cashflow, 2),
        yearly_cashflow=round(yearly_cashflow, 2),
        gross_yield_percent=round(gross_yield_percent, 2),
    )


@app.get("/")
def root():
    return {"status": "ok", "hint": "Open /docs or POST /api/calc"}
