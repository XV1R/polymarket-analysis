from typing import Optional, Union
from market import MarketAPI
import polars as pl
import duckdb
import logging
import os


class InsertError(Exception):
    """
    Exception raised when an error occurs while inserting trades
    """
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class TradeStorage:
    """
    Storage for trades data in a parquet file to avoid making too many requests to the market API
    """
    #TODO fix this so it can be used in a multi-process environment
    def __init__(self):
        self.path = "data.parquet"
        self.conn = duckdb.connect(self.path)
        self.logger = logging.getLogger("polymarket.trades")
        self.create_table()

    def create_table(self) -> None:
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                hash VARCHAR PRIMARY KEY,
                condition_id VARCHAR,
                user VARCHAR,
                size DECIMAL,
                price DECIMAL,
                side VARCHAR,
                timestamp TIMESTAMP
            )
        """)

    def get_trades_df(self, condition_id: str) -> pl.DataFrame:
        """Get trades for a condition_id as Polars DataFrame"""
        try:
            result = self.conn.execute(
                "SELECT * FROM trades WHERE condition_id = ?",
                [condition_id]
            ).pl()
            return result
        except Exception as e:
            self.logger.error(f"Error fetching trades: {e}")
            return pl.DataFrame()  # Return empty DataFrame on error

    def insert_trades(self, trades: Union[list, dict]) -> None:
        """Insert trades into database"""
        if isinstance(trades, dict):
            trades = [trades]
        if not trades:
            self.logger.warning("No trades to insert")
            return
        try:
            df = pl.DataFrame(trades).select(
                pl.col("transactionHash").alias("hash"),
                pl.col("conditionId").alias("condition_id"),
                pl.col("name").alias("user"),
                pl.col("size"),
                pl.col("price"),
                pl.col("side"),
                pl.col("timestamp").cast(pl.Datetime("ns")).alias("timestamp"),
            )
            self.conn.register("trades_temp", df)
            # Use INSERT OR IGNORE to skip duplicates (based on PRIMARY KEY hash)
            self.conn.execute("INSERT OR IGNORE INTO trades SELECT * FROM trades_temp")
            # Unregister the temporary view
            self.conn.unregister("trades_temp")
            self.logger.info(f"Successfully inserted {len(df)} trades (duplicates skipped)")
        except Exception as e:
            self.logger.error(f"Error inserting trades: {e}")
            # Clean up view if it exists
            try:
                self.conn.unregister("trades_temp")
            except:
                pass
            raise InsertError(f"Error inserting trades: {e}")