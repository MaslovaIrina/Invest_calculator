import os
os.environ["MPLBACKEND"] = "Agg"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from schemas import CalcRequest, CalcResponse
from calculators.rent import calc_rent
from calculators.buy import calc_buy_schedule
from calculators.charts import build_main_chart_png_base64, build_mortgage_bar_chart_png_base64, build_mortgage_pie_chart_png_base64


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
    # 1) расчёты один раз
    rent_schedule = calc_rent(req)
    buy_schedule = calc_buy_schedule(req)
    has_mortgage = any(r.mortgage_payment > 0 for r in buy_schedule)


    # 2) графики из готовых расписаний
    chart_main = build_main_chart_png_base64(rent_schedule, buy_schedule)
    chart_mortgage = ""
    chart_mortgage_pie = ""
    if has_mortgage:
        chart_mortgage = build_mortgage_bar_chart_png_base64(buy_schedule)
        chart_mortgage_pie = build_mortgage_pie_chart_png_base64(buy_schedule)

    # 3) финальные значения 
    rent_final = float(rent_schedule[-1].full_invest_balance) if rent_schedule else float(req.all_free_money)
    buy_final = float(buy_schedule[-1].net_worth_buy) if buy_schedule else 0.0

    return CalcResponse(
        rent_schedule=rent_schedule,
        buy_schedule=buy_schedule,
        rent_final_balance=round(rent_final),
        buy_final_balance=round(buy_final),
        difference_final=round(buy_final - rent_final),
        chart_main_base64=chart_main,
        chart_mortgage_base64=chart_mortgage,
        chart_mortgage_pie_png_base64=chart_mortgage_pie
    )
    

@app.get("/")
def root():
    return {"status": "ok"}




