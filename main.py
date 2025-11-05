import requests
from typing import Optional, List
import json

class GammaAPI():
    def __init__(self):
        self.api_url ="https://gamma-api.polymarket.com"

    def get_events(self, limit: int = 20, 
                   offset: Optional[int] = None, 
                   order: Optional[List[str]] = None,
                   ascending: Optional[bool] = None,
                   ):

        query = {"limit": limit}
        return 
    def get_event_by_slug(self, slug:str) -> Optional[dict]: 
        return requests.get(f"{self.api_url}/events/slug/{slug}")
    def get_event_by_id(): 
        return None

if __name__ == "__main__":
    gamma = GammaAPI()
    print(gamma.get_events().json())
