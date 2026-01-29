import os
os.environ["MPLBACKEND"] = "Agg"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Response
import io
import matplotlib.pyplot as plt

from schemas import CalcRequest, CalcResponse
from calculators.rent import calc_rent
from calculators.buy import calc_buy_schedule
from calculators.charts import build_chart_png




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

    rent_final = float(rent_schedule[-1].full_invest_balance) if rent_schedule else float(req.all_free_money)

    # Пока упрощение: капитал в покупке = цена - остаток долга
    loan_end = float(buy_schedule[-1].loan_balance) if buy_schedule else 0.0
    buy_final = float(req.purchase_price) - loan_end

    return CalcResponse(
        rent_schedule=rent_schedule,
        buy_schedule=buy_schedule,
        rent_final_balance=round(rent_final, 2),
        buy_final_balance=round(buy_final, 2),
        difference_final=round(buy_final - rent_final, 2),
    )

@app.get("/")
def root():
    return {"status": "ok"}



@app.post("/api/chart")
def chart(req: CalcRequest) -> Response:
    return Response(content=build_chart_png(req), media_type="image/png")

