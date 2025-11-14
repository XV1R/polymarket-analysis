import requests
import logging
from typing import Optional

# Configure logger for market API
logger = logging.getLogger("polymarket.market")

class MarketAPI():
    '''
    Wrapper around the polymarket gamma and data api endpoints 
    '''
    def __init__(self):
        self.gamma_api_url ="https://gamma-api.polymarket.com"
        self.data_api_url ="https://data-api.polymarket.com"
        self.logger = logger
        logger.info("MarketAPI initialized")

    def get_markets(self, limit: int = 20, 
                   offset: Optional[int] = None, 
                   order: Optional[str] = None,
                   ascending: Optional[bool] = None,
                   closed: Optional[bool] = None,
                   **kwargs) -> requests.Response:
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
                              limit: int = 500, 
                              offset: int = 0, 
                              takerOnly:bool = False, 
                              side: Optional[str] = None) -> Optional[dict]:
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
            response.raise_for_status()  # Raise exception for bad status codes
            data = response.json()
            trade_count = len(data) if isinstance(data, list) else 1
            self.logger.info(f"Successfully fetched {trade_count} trades for market {market}")
            return data
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout getting trades for market {market}")
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