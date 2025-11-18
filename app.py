from fastapi import FastAPI, HTTPException
from market import MarketAPI
from trades import TradeStorage
from dotenv import load_dotenv
from typing import Optional, Union
from contextlib import asynccontextmanager
import logging
import polars as pl
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger("polymarket.api")
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("FastAPI application starting up...")
    if not os.path.exists("data.parquet"):
        write_data(market, out="data.parquet", cap=10_000, closed=True)
    logger.info("FastAPI application initialized")
    yield
    # Shutdown (if needed)
    logger.info("FastAPI application shutting down...")

app = FastAPI(lifespan=lifespan)
market = MarketAPI()
tstorage = TradeStorage()

@app.get("/")
async def root():
    logger.debug("Root endpoint accessed")
    return {"message": "Hello World"}

@app.get('/markets/{condition_id}')
async def get_market_trades(condition_id: str) -> Union[list, dict]:
    logger.info(f"Fetching market trades for condition_id: {condition_id}")
    trades_df: pl.DataFrame = tstorage.get_trades_df(condition_id)
    if not trades_df.is_empty():
        logger.info(f"Returning {trades_df.height} cached trades")
        return trades_df.to_dicts()
    
    logger.info(f"No trades found in storage for condition_id: {condition_id}, fetching from market API")
    trades: Optional[Union[list, dict]] = market.get_trades_for_market(condition_id, limit=100)
    if trades is None:
        logger.warning(f"Failed to fetch trades for condition_id: {condition_id}")
        raise HTTPException(status_code=404, detail=f"No trades found for condition_id: {condition_id}")
    
    logger.debug(f"Successfully fetched trades for condition_id: {condition_id}")
    # Save to storage
    tstorage.insert_trades(trades)
    
    # Return as list of dicts
    if isinstance(trades, dict):
        return [trades]
    return trades

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
async def get_market_stats(condition_id: str) ->Union[list, dict]: 
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
    all_records = []
    while count < cap:
        logger.debug(f"Fetching markets batch, offset: {count}")
        response = market.get_markets(limit=500, offset=count, closed=closed).json()
        # If the API returns a dict with a key like 'markets', adjust this accordingly
        if isinstance(response, dict) and 'markets' in response:
            records = response['markets']
        else:
            records = response
        if not records:
            break
        all_records.extend(records)
        logger.info(f"Appended {len(records)} records at offset {count}")
        if len(records) < 500:
            # Last batch, no more data
            break
        count += 500
    if all_records:
        df = pl.DataFrame(all_records)
        df.write_parquet(out)
        logger.info(f"Written {len(all_records)} records to {out} as parquet.")
    else:
        logger.warning("No data fetched to write as parquet.")
    logger.info(f"Completed data write to {out}")