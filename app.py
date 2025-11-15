from fastapi import FastAPI, HTTPException
from market import MarketAPI
from dotenv import load_dotenv
from typing import Optional, Union
import polars as pl
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("polymarket.api")

def write_data(market: MarketAPI, out: str, cap: int = 10_000, closed: bool = False) -> None:
    """
    Write data to a parquet file
    Args:
        market: MarketAPI object
        out: Path to the parquet file
        cap: Maximum number of markets to fetch
        closed: Whether to fetch closed markets
    Returns:
        None
    """
    logger.info(f"Starting data write to {out} (parquet), cap: {cap}, closed: {closed}")
    all_records = []
    count = 0
    while count < cap:
        logger.debug(f"Fetching markets batch, offset: {count}")
        j = market.get_markets(limit=500, offset=count, closed=closed).json()
        if not j:
            logger.info(f"No more markets to fetch at offset {count}")
            break
        all_records.extend(j)
        logger.info(f"Accumulated {len(all_records)} records (last batch: {len(j)})")
        count += 500
    if all_records:
        pl.DataFrame(all_records).write_parquet(out)
        logger.info(f"Data written to {out} (parquet) with {len(all_records)} rows")
    else:
        logger.warning("No records fetched to write to parquet")

def clean_data(df: pl.DataFrame) -> pl.DataFrame:
    """
    Clean the data
    Args:
        df: Polars DataFrame
    Returns:
        Polars DataFrame
    """
    df = df.with_columns([
        pl.col('startDate').cast(pl.Datetime),
        pl.col('endDate').cast(pl.Datetime),
        pl.col('volume').cast(pl.Float64),
    ]).drop(
        "sponsorImage", 
        "sentDiscord", 
        "umaResolutionStatuses", 
        "pendingDeployment",
        "categoryMailchimpTag",
        "mailchimpTag",
        "volume24hr",
        "volume1wk",
        "volume1mo",
        "icon"
    ).sort('startDate', descending=True, multithreaded=True, nulls_last=True)
    return df

load_dotenv()
app = FastAPI()
market = MarketAPI()
df: Optional[pl.DataFrame] = None

parquet_path = "./closed-markets-raw.parquet"
if os.path.exists(parquet_path):
    logger.info(f"Parquet file {parquet_path} found, loading DataFrame")
else:
    logger.info(f"Parquet file {parquet_path} not found, creating it")
    write_data(market, parquet_path, closed=True)
    logger.info(f"Data written and loaded from parquet file with {df.height} rows")

df = clean_data(pl.read_parquet(parquet_path))
logger.info(f"Data loaded from parquet into dataframe with {df.height} rows")
logger.info("FastAPI application initialized")


#-----FastAPI endpoints-----

@app.get('/')
async def get_root() -> dict:
    global df
    logger.info("Root endpoint called")
    return df.to_dict(as_series=False)


@app.get('/markets/{condition_id}')
async def get_market_trades(condition_id: str) -> Union[list, dict]:
    logger.info(f"Fetching market trades for condition_id: {condition_id}")
    resp = market.get_trades_for_market(condition_id)
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
