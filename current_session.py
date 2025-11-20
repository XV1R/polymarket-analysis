# coding: utf-8
import polars as pl
df = pl.scan_parquet("data.parquet")
from utils import *
print(df.columns)
c = clean_market_frame(df)
print(c.columns)
