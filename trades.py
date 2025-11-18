from typing import Optional, Union
from market import MarketAPI
from dotenv import load_dotenv
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
    def __init__(self, path:str = os.getenv("PARQUET_FILE")):
        self.conn = duckdb.connect(path)
        self.logger = logging.getLogger("polymarket.trades")
        self.create_table()

    def create_table(self) -> None:
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id BIGINT PRIMARY KEY,
                condition_id VARCHAR,
                user VARCHAR,
                size DECIMAL,
                price DECIMAL,
                side VARCHAR,
                timestamp TIMESTAMP,
                hash VARCHAR,
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
                pl.col("conditionId").alias("condition_id"),
                pl.col("name").alias("user"),
                pl.col("size").alias("size"),
                pl.col("price").alias("price"),
                pl.col("side").alias("side"),
                pl.col("timestamp").alias("timestamp"),
                pl.col("transactionHash").alias("hash"),
            )
            self.conn.register("trades_temp", df)
            self.conn.execute("INSERT INTO trades SELECT * FROM trades_temp")
            # Unregister the temporary view
            self.conn.unregister("trades_temp")
            self.logger.info(f"Successfully inserted {len(df)} trades")
        except Exception as e:
            self.logger.error(f"Error inserting trades: {e}")
            # Clean up view if it exists
            try:
                self.conn.unregister("trades_temp")
            except:
                pass
            raise InsertError(f"Error inserting trades: {e}")