from fastapi import FastAPI
from market import MarketAPI
from dotenv import load_dotenv
from typing import Optional
import polars as pl
import json
import os

load_dotenv()
app = FastAPI()
market = MarketAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/markets/{condition_id}/user-distribution")
async def get_user_distribution(condition_id: str) -> dict:
    trades: Optional[dict] = market.get_trades_for_market(condition_id)
    if trades is None:
        return {"error": "No trades found"}
    return trades
    #trades_df = pl.from_dict(trades)


@app.get("/markets/{condition_id}/stats")
async def get_market_stats(condition_id: str) -> dict: 
    trades: Optional[dict] = market.get_trades_for_market(condition_id)
    if trades is None:
        return {"error": "No trades found"}
    return trades
    #trades_df = pl.from_dict(trades)


def write_data(market: MarketAPI, out: str, cap: int = 10_000, closed: bool = False) -> None:
    count = 0
    while count < cap:
        j = market.get_markets(limit=500, offset=count, closed=closed).json()
        with open(out, "a") as f:
            for record in j:
                f.write(json.dumps(record) + '\n')
        print(f"Dumped count {count}")
        count += 500

def main():
    data_path = "closed-markets.json"
    if not os.path.exists(data_path):
        write_data(market, data_path,cap=500,closed=True)
        print(f"Data written to {data_path}")
    else:
        print(f"Data already exists at {data_path}")
        
if __name__ == "__main__":
    main()

