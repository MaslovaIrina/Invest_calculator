# calculators/charts.py
import io
import matplotlib.pyplot as plt

from schemas import CalcRequest
from calculators.rent import calc_rent
from calculators.buy import calc_buy_schedule


def build_chart_png(req: CalcRequest) -> bytes:
    rent_schedule = calc_rent(req)
    buy_schedule = calc_buy_schedule(req)

    x_rent = [r.month for r in rent_schedule]
    y_rent = [r.full_invest_balance for r in rent_schedule]

    x_buy = [b.month for b in buy_schedule]
    y_buy = [b.buy_balance for b in buy_schedule]

    fig = plt.figure()
    plt.plot(x_rent, y_rent, label="Rent: invest balance")
    plt.plot(x_buy, y_buy, label="Buy: buy balance")
    plt.xlabel("Month")
    plt.ylabel("Value")
    plt.legend()
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
