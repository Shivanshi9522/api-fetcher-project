import requests
import pandas as pd
import time
import logging
from typing import Optional, Dict, List
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class APIFetcher:
    def __init__(self, base_url: str, headers: Optional[Dict] = None):
        self.base_url = base_url
        self.headers = headers or {}
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def fetch_with_retry(self, endpoint: str = "", params: Dict = None, max_retries: int = 3) -> Optional[List[Dict]]:
        """Fetch data with exponential backoff retry logic"""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}" if endpoint else self.base_url
        all_data = []

        for attempt in range(max_retries):
            try:
                logging.info(f"Attempt {attempt + 1}: Fetching {url}")
                response = self.session.get(url, params=params, timeout=10)

                # Handle rate limiting
                if response.status_code == 429:
                    wait_time = int(response.headers.get('Retry-After', 2 ** attempt))
                    logging.warning(f"Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                data = response.json()

                # Handle both list response and paginated dict response
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    all_data.extend(data.get('items', data.get('data', [data])))
                    # Check for pagination - GitHub style
                    if 'next' in response.links:
                        url = response.links['next']['url']
                        params = None # next url has params built-in
                        continue
                    return all_data
                return data

            except requests.exceptions.RequestException as e:
                wait_time = 2 ** attempt # Exponential backoff: 1s, 2s, 4s
                logging.error(f"Request failed: {e}. Retrying in {wait_time}s...")
                if attempt == max_retries - 1:
                    logging.error("Max retries reached. Giving up.")
                    return None
                time.sleep(wait_time)
        return None

    def to_csv(self, data: List[Dict], filename: str = "api_data.csv") -> str:
        """Convert JSON to CSV and save"""
        if not data:
            logging.warning("No data to save")
            return ""
        df = pd.json_normalize(data) # Flattens nested JSON
        df.to_csv(filename, index=False)
        logging.info(f"Saved {len(df)} rows to {filename}")
        return filename

# Test it
if __name__ == "__main__":
    # Example: GitHub API - no auth needed for public data
    fetcher = APIFetcher("https://api.github.com")
    repos = fetcher.fetch_with_retry("users/shivanshi/repos", params={"per_page": 5})

    if repos:
        csv_path = fetcher.to_csv(repos, "my_repos.csv")
        df = pd.read_csv(csv_path)
        print(f"\nSuccess! First 3 rows:\n{df.head(3)}")