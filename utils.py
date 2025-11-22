import polars as pl
from typing import TypeVar

FrameType = TypeVar("FrameType", pl.DataFrame, pl.LazyFrame)

def clean_market_frame(frame: FrameType) -> FrameType:
    df = frame.select([
        pl.col('startDate').cast(pl.Datetime).alias('start_date'),
        pl.col('endDate').cast(pl.Datetime).alias('end_date'),
        pl.col('volume').cast(pl.Float64).alias('volume'),
        pl.col('conditionId').alias('condition_id')
    ])
    return df.select([
        pl.exclude(
        "sponsorImage", 
        "sentDiscord", 
        "umaResolutionStatuses", 
        "pendingDeployment",
        "categoryMailchimpTag",
        "mailchimpTag",
        "volume24hr",
        "volume1wk",
        "volume1mo",
        "icon",
        "startDateIso",
        )
    ]).sort('start_date', 
           descending=True, 
           multithreaded=True,
           nulls_last=True)    

def clean_trade_frame(frame: FrameType) -> FrameType:
    return frame.drop(
        "profileImage",
        "profileImageOptimized",
        "icon"
        ).sort("timestamp",
               descending=True,
               multithreaded=True,
               nulls_last=True)
