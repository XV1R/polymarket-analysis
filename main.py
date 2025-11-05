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

    def get_events(self, limit: int = 20, 
                   offset: Optional[int] = None, 
                   order: Optional[List[str]] = None,
                   ascending: Optional[bool] = None,
                   ):

        query = {"limit": limit}
        return requests.get(f"{self.api_url}/events", params=query)

    def get_event_by_slug(self, slug:str) -> Optional[dict]: 
        return requests.get(f"{self.api_url}/events/slug/{slug}")

    def get_event_by_id(): 
        return NotImplementedError

def write_data(gamma: GammaAPI, out: str, cap: int = 10_000):
    count = 0
    while count < cap:
        j = gamma.get_events(limit=500, offset=count).json()
        with open(out, "a") as f:
            for record in j:
                f.write(json.dumps(record) + '\n')
        print(f"Dumped count {count}")
        count += 500

def main():
    gamma = GammaAPI()
    data_path = "open-events.json"
    if not os.path.exists(data_path):
        write_data(gamma, data_path)
    df: pl.DataFrame = pl.read_ndjson(data_path)
    print(df)

if __name__ == "__main__":
    main()

