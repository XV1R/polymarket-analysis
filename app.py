from fastapi import FastAPI, HTTPException
from market import MarketAPI
from dotenv import load_dotenv
from typing import Optional, Union
import json
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger("polymarket.api")

load_dotenv()
app = FastAPI()
market = MarketAPI()

logger.info("FastAPI application initialized")

@app.get("/")
async def root():
    logger.debug("Root endpoint accessed")
    return {"message": "Hello World"}

@app.get('/markets/{condition_id}')
async def get_market(condition_id: str) -> Union[list, dict]:
    logger.info(f"Fetching market trades for condition_id: {condition_id}")
    resp = market.get_trades_for_market(condition_id, limit=1)
    if resp is None:
        logger.warning(f"Failed to fetch trades for condition_id: {condition_id}")
        raise HTTPException(status_code=404, detail=f"No trades found for condition_id: {condition_id}")
    logger.debug(f"Successfully fetched trades for condition_id: {condition_id}")
    return resp

@app.get("/markets/{condition_id}/user-distribution")
async def get_user_distribution(condition_id: str) -> Union[list, dict]:
    logger.info(f"Fetching user distribution for condition_id: {condition_id}")
    trades = market.get_trades_for_market(condition_id)
    if trades is None:
        logger.warning(f"No trades found for condition_id: {condition_id}")
        raise HTTPException(status_code=404, detail=f"No trades found for condition_id: {condition_id}")
    logger.debug(f"Successfully fetched user distribution for condition_id: {condition_id}")
    return trades


@app.get("/markets/{condition_id}/stats")
async def get_market_stats(condition_id: str) -> Union[list, dict]: 
    logger.info(f"Fetching market stats for condition_id: {condition_id}")
    trades = market.get_trades_for_market(condition_id)
    if trades is None:
        logger.warning(f"No trades found for stats, condition_id: {condition_id}")
        raise HTTPException(status_code=404, detail=f"No trades found for condition_id: {condition_id}")
    logger.debug(f"Successfully fetched stats for condition_id: {condition_id}")
    return trades


def write_data(market: MarketAPI, out: str, cap: int = 10_000, closed: bool = False) -> None:
    logger.info(f"Starting data write to {out}, cap: {cap}, closed: {closed}")
    count = 0
    while count < cap:
        logger.debug(f"Fetching markets batch, offset: {count}")
        j = market.get_markets(limit=500, offset=count, closed=closed).json()
        with open(out, "a") as f:
            for record in j:
                f.write(json.dumps(record) + '\n')
        logger.info(f"Dumped count {count}")
        count += 500
    logger.info(f"Completed data write to {out}")

def main():
    data_path = "closed-markets.json"
    if not os.path.exists(data_path):
        logger.info(f"Data file {data_path} not found, creating it")
        write_data(market, data_path,cap=500,closed=True)
        logger.info(f"Data written to {data_path}")
    else:
        logger.info(f"Data already exists at {data_path}")
        
if __name__ == "__main__":
    main()

