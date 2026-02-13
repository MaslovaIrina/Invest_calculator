import os
os.environ["MPLBACKEND"] = "Agg"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from schemas_living import CalcRequest, CalcResponse
from calculators.rent import calc_rent
from calculators.buy import calc_buy_schedule
from calculators.charts import build_main_chart_png_base64, build_mortgage_bar_chart_png_base64, build_mortgage_pie_chart_png_base64
from calculators.common import build_warnings


from schemas_invest import InvestRequest, InvestResponse
#from calculators.invest import find_break_even_capital


app = FastAPI(title="Real Estate Calculator API")

BASE_DIR = Path(__file__).resolve().parent
HTML_DIR = BASE_DIR / "html_files"


#app.mount("/static", StaticFiles(directory=HTML_DIR), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/", response_class=HTMLResponse)
def home():
    return FileResponse(HTML_DIR / "home.html")

@app.get("/calc", response_class=HTMLResponse)
def calc_page():
    return FileResponse(HTML_DIR / "index.html")

@app.get("/investment", response_class=HTMLResponse)
def investment_page():
    print("HIT /investment")
    return FileResponse(HTML_DIR / "invest_calc.html")



@app.post("/api/calc", response_model=CalcResponse)
def calc(req: CalcRequest) -> CalcResponse:
    # 1) расчёты один раз
    rent_schedule = calc_rent(req)
    buy_schedule = calc_buy_schedule(req)
    has_mortgage = any(r.mortgage_payment > 0 for r in buy_schedule)
    final_warnings = build_warnings(req, rent_schedule, buy_schedule)


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
        chart_mortgage_pie_png_base64=chart_mortgage_pie,
        top_text = make_top_text(rent_final, buy_final),
        warnings = final_warnings
    )
    



def make_top_text(rent_final, buy_final):
    if buy_final > rent_final:
        return 'Покупка выгоднее аренды на ' + str(round(buy_final - rent_final)) + ' руб'
    else:
        return 'Аренда выгоднее покупки на ' + str(round(rent_final - buy_final)) + ' руб'
    





