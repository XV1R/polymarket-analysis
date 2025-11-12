from typing import Optional, List
import polars as pl
import numpy as np
import requests
import json
import logging
import os


#TODO: error handling, data structuring
class GammaAPI():
    
    '''
    Wrapper around the polymarket gamma api endpoints 
    '''
    def __init__(self):
        self.api_url ="https://gamma-api.polymarket.com"
        self.logger = logging.getLogger("gamma-api")

    def get_markets(self, limit: int = 20, 
                   offset: Optional[int] = None, 
                   order: Optional[str] = None,
                   ascending: Optional[bool] = None,
                   closed: Optional[bool] = None,
                   **kwargs) -> requests.Response:
        """
        Retrieves a list of markets from the Polymarket Gamma API.

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
            >>> api = GammaAPI()
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
            return requests.get(f"{self.api_url}/markets", params=query)
        except Exception as e:
            self.logger.error(f"Error getting markets: {e}")
            return None

    def get_market_by_slug(self, slug: str) -> Optional[dict]: 
        try:
            return requests.get(f"{self.api_url}/markets/slug/{slug}")
        except Exception as e:
            self.logger.error(f"Error getting market by slug {slug}: {e}")
            return None



def write_data(gamma: GammaAPI, out: str, cap: int = 10_000, closed: bool = False) -> None:
    count = 0
    while count < cap:
        j = gamma.get_markets(limit=500, offset=count, closed=closed).json()
        with open(out, "a") as f:
            for record in j:
                f.write(json.dumps(record) + '\n')
        print(f"Dumped count {count}")
        count += 500

def main():
    gamma = GammaAPI()
    data_path = "closed-markets.json"
    if not os.path.exists(data_path):
        write_data(gamma, data_path,cap=500,closed=True)
        print(f"Data written to {data_path}")
    else:
        print(f"Data already exists at {data_path}")

if __name__ == "__main__":
    main()

