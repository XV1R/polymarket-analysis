from fastapi import FastAPI, HTTPException
from market import MarketAPI
from dotenv import load_dotenv
from typing import Optional, List
from contextlib import asynccontextmanager
import logging
import polars as pl
import os

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
        write_market_data(market, out="data.parquet", cap=100_000, closed=True)
    logger.info("FastAPI application initialized")
    yield
    # Shutdown (if needed)
    logger.info("FastAPI application shutting down...")

app = FastAPI(lifespan=lifespan)
market = MarketAPI()

@app.get("/")
async def root():
    logger.debug("Root endpoint accessed")
    return {"message": "Hello World"}

@app.get("/markets/search")
async def search_markets(
    q: Optional[str] = None,
    limit: int = 20,
    closed: Optional[bool] = None
) -> List[dict]:
    """Search markets for autocomplete suggestions"""
    logger.info(f"Searching markets with query: {q}, limit: {limit}")
    try:
        response = market.get_markets(limit=limit, closed=closed)
        if response is None:
            return []
        
        markets = response.json()
        if not isinstance(markets, list):
            markets = markets if isinstance(markets, list) else []
        
        # Filter by query if provided
        if q:
            q_lower = q.lower()
            markets = [
                m for m in markets
                if q_lower in str(m.get("question", "")).lower()
                or q_lower in str(m.get("slug", "")).lower()
                or q_lower in str(m.get("conditionId", "")).lower()
            ]
        
        # Return simplified format for autocomplete
        result = []
        for m in markets[:limit]:
            result.append({
                "conditionId": m.get("conditionId"),
                "question": m.get("question", ""),
                "slug": m.get("slug", ""),
                "volume": m.get("volume", 0),
                "liquidity": m.get("liquidity", 0),
            })
        
        return result
    except Exception as e:
        logger.error(f"Error searching markets: {e}")
        return []

@app.get('/markets/{condition_id}')
async def get_market_trades(condition_id: str) -> List[dict]:
    logger.info(f"Fetching market trades for condition_id: {condition_id}")
    try:
        trades: pl.DataFrame = market.fetch_market_trades(condition_id, True)
        if trades.is_empty():
            logger.warning(f"No trades found for condition_id: {condition_id}")
            raise HTTPException(
                status_code=404, 
                detail=f"No trades found for condition_id: {condition_id}. The market may not exist or have no trades yet."
            )
        logger.info(f"Successfully fetched {trades.height} trades for {condition_id}")
        return trades.to_dicts()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching trades for {condition_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching trades: {str(e)}"
        )

    
def write_market_data(market: MarketAPI, out: str, cap: int = 10_000, closed: bool = False) -> None:
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
