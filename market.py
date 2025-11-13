import requests
import logging
from typing import Optional
class MarketAPI():
    '''
    Wrapper around the polymarket gamma and data api endpoints 
    '''
    def __init__(self):
        self.gamma_api_url ="https://gamma-api.polymarket.com"
        self.data_api_url ="https://data-api.polymarket.com"
        self.logger = logging.getLogger("market-api")

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
        try:
            return requests.get(f"{self.gamma_api_url}/markets", params=query)
        except Exception as e:
            self.logger.error(f"Error getting markets: {e}")
            return None

    def get_market_by_slug(self, slug: str) -> Optional[dict]: 
        try:
            return requests.get(f"{self.gamma_api_url}/markets/slug/{slug}")
        except Exception as e:
            self.logger.error(f"Error getting market by slug {slug}: {e}")
            return None

    #TODO: fix request time out? 
    def get_trades_for_market(self, market: str, 
                              limit: int = 500, 
                              offset: int = 0, 
                              takerOnly:bool = False, 
                              side: Optional[str] = None) -> Optional[dict]:
        query = {
            "market": [market],
            "limit": limit,
            "offset": offset,
            "takerOnly": takerOnly,
            "side": side if side is not None else None
        }
        print(query)
        try:
            return requests.get(f"{self.data_api_url}/trades", params=query).json()
        except Exception as e:
            self.logger.error(f"Error getting trades for market {market}: {e}")
            return None

    def get_trades_for_user(self, user: str, limit: int = 500, offset: int = 0, takerOnly:bool = False) -> Optional[dict]:
        query = {
            "user": user,
            "limit": limit,
            "offset": offset,
            "takerOnly": takerOnly
        }
        try:
            return requests.get(f"{self.data_api_url}/trades", params=query).json()
        except Exception as e:
            self.logger.error(f"Error getting trades for user {user}: {e}")
            return None