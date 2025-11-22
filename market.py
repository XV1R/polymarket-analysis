from typing import Optional, Union
from trades import MarketStorage
import polars as pl
import requests
import logging

logger = logging.getLogger("polymarket.market")

class MarketAPI():
    '''
    Wrapper around the polymarket gamma and data api endpoints 
    '''
    def __init__(self):
        self.gamma_api_url ="https://gamma-api.polymarket.com"
        self.data_api_url ="https://data-api.polymarket.com"
        self.mstorage: MarketStorage = MarketStorage()
        self.logger = logger
        logger.info("MarketAPI initialized")
    
    #Endpoint handler
    def fetch_market_trades(self, condition_id: str, refresh: bool) -> pl.DataFrame:
        trades: pl.DataFrame = self.mstorage.get_trades_lf(condition_id).collect()
        if not trades.is_empty() and not refresh:
            self.logger.info(f"Returning {trades.height} cached trades for {condition_id}")
            return trades

        # Fetch from API
        self.logger.info(f"No cached trades, fetching from API for {condition_id}")
        trades_data = self.get_trades_for_market(condition_id, limit=1000)

        if trades_data is None:
            self.logger.warning(f"API returned None for {condition_id} - market may not exist or have no trades")
            return pl.DataFrame() 
        
        if isinstance(trades_data, list) and len(trades_data) == 0:
            self.logger.warning(f"API returned empty list for {condition_id}")
            return pl.DataFrame()

        self.mstorage.insert_markets(trades_data)
        
        if isinstance(trades_data, list):
            return pl.DataFrame(trades_data)
        elif isinstance(trades_data, dict):
            return pl.DataFrame([trades_data])
        else:
            return pl.DataFrame()

    def get_markets(self, limit: int = 20, 
                   offset: Optional[int] = None, 
                   order: Optional[str] = None,
                   ascending: Optional[bool] = None,
                   closed: Optional[bool] = None,
                   **kwargs) -> Optional[requests.Response]:
        """
        Retrieves a list of markets from the Polymarket gamma API.

        Parameters:
            limit (int): The maximum number of markets to retrieve. Default is 20.
            offset (Optional[int]): The offset for paginated results.
            order (Optional[str]): The field by which to order results.
            ascending (Optional[bool]): Whether to order results in ascending order.
            closed (Optional[bool]): Whether to filter for closed markets.
            **kwargs: Additional parameters supported by the API.

        Returns:
            requests.Response: The HTTP response object containing the list of markets.

        Example:
            >>> api = marketAPI()
            >>> response = api.get_markets(limit=100, closed=True)
            >>> markets = response.json()
        """
        query = {"limit": limit}
        if offset is not None:
            query["offset"] = offset
        if order is not None:
            query["order"] = order
        if ascending is not None:
            query["ascending"] = ascending
        if closed is not None:
            query["closed"] = closed
        # Add any additional query parameters
        query.update(kwargs)
        self.logger.debug(f"Fetching markets with params: {query}")
        try:
            response = requests.get(f"{self.gamma_api_url}/markets", params=query)
            if response.ok:
                self.logger.debug(f"Successfully fetched markets (status: {response.status_code})")
            else:
                self.logger.warning(f"Failed to fetch markets (status: {response.status_code})")
            return response
        except Exception as e:
            self.logger.error(f"Error getting markets: {e}")
            return None

    def get_market_by_slug(self, slug: str) -> Optional[dict]: 
        self.logger.info(f"Fetching market by slug: {slug}")
        try:
            response = requests.get(f"{self.gamma_api_url}/markets/slug/{slug}")
            if response.ok:
                self.logger.debug(f"Successfully fetched market for slug: {slug}")
            return response
        except Exception as e:
            self.logger.error(f"Error getting market by slug {slug}: {e}")
            return None

    def get_trades_for_market(self, market: str, 
                              limit: int = 100, 
                              offset: int = 0, 
                              takerOnly:bool = False, 
                              side: Optional[str] = None) -> Optional[Union[list, dict]]:
        # API expects string values for parameters
        query = {
            "market": market,
            "limit": str(limit),
            "offset": str(offset)
        }
        if takerOnly:
            query["takerOnly"] = "true"
        if side is not None:
            query["side"] = side
        self.logger.debug(f"Fetching trades for market {market} with params: {query}")
        try:
            response = requests.get(
                f"{self.data_api_url}/trades", 
                params=query,
                timeout=30  # 30 second timeout
            )
            
            # Handle 404 specifically - market doesn't exist or has no trades
            if response.status_code == 404:
                self.logger.warning(f"Market {market} not found or has no trades (404)")
                return None
            
            response.raise_for_status()  # Raise exception for other bad status codes
            data = response.json()
            
            # Check if data is empty
            if isinstance(data, list) and len(data) == 0:
                self.logger.info(f"Market {market} exists but has no trades")
                return []
            
            trade_count = len(data) if isinstance(data, list) else 1
            self.logger.info(f"Successfully fetched {trade_count} trades for market {market}")
            return data
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout getting trades for market {market}")
            return None
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error getting trades for market {market}: {e.response.status_code if hasattr(e, 'response') else 'unknown'}")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error getting trades for market {market}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting trades for market {market}: {e}")
            return None

    def get_trades_for_user(self, user: str, limit: int = 500, offset: int = 0, takerOnly:bool = False) -> Optional[dict]:
        self.logger.info(f"Fetching trades for user: {user}")
        query = {
            "user": user,
            "limit": limit,
            "offset": offset,
            "takerOnly": takerOnly
        }
        self.logger.debug(f"Fetching trades with params: {query}")
        try:
            response = requests.get(f"{self.data_api_url}/trades", params=query)
            response.raise_for_status()
            data = response.json()
            trade_count = len(data) if isinstance(data, list) else 1
            self.logger.info(f"Successfully fetched {trade_count} trades for user {user}")
            return data
        except Exception as e:
            self.logger.error(f"Error getting trades for user {user}: {e}")
            return None
