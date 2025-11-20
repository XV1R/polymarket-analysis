from typing import Union, List, TypeVar
import polars as pl
import os
import logging
from utils import clean_market_frame, clean_trade_frame

class InsertError(Exception):
    pass


class MarketStorage:
    def __init__(self):
        self.path = "data.parquet"
        self.logger = logging.getLogger("polymarket.trades")
        self.market_df = clean_market_frame(pl.LazyFrame("data.parquet"))
        #self.trades_df = clean_trade_frame(pl.LazyFrame("trades.parquet"))
        self.logger.info(self.market_df.columns)
        self.logger.info(self.trades_df.columns)
    def insert_markets(self, markets: Union[dict, List[dict]]) -> bool:
        if isinstance(markets, dict):
            markets = [markets]
        new_markets_df = clean_market_frame(pl.LazyFrame(markets))
        self.market_df = pl.concat(self.market_df, new_markets_df, how="vertical")
        return True


    def insert_trades(self, trades: Union[dict, List[dict]]) -> bool:
        if isinstance(trades, dict):
            trades = [trades]
        new_trades_df = clean_trade_frame(pl.DataFrame(trades).lazy())
        self.trades_df = pl.concat(self.trades_df, new_trades_df, how='vertical')

    def get_trades_lf(self, condition_ids: Union[str, list[str]]) -> pl.LazyFrame:
        """Get trades for a condition_id or list of condition_ids as Polars DataFrame"""
        if isinstance(condition_ids, str):
            condition_ids = [condition_ids]
        result: pl.LazyFrame = self.market_df.filter(pl.col("condition_id").is_in(condition_ids))
        if result.collect().is_empty():
            self.logger.warning(f"No trades found for markets {condition_ids}")
        self.logger.info(f"Returning result {result}")
        return result.lazy()

