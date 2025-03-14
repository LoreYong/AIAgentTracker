import time
import requests
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from ..utils.logger import setup_logger

logger = setup_logger("github_search")

class GitHubSearcher:
    """Search GitHub repositories based on keywords and filters"""
    
    def __init__(self, token=None):
        """Initialize the GitHub searcher with authentication token"""
        self.token = token
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
        
        self.base_url = "https://api.github.com"
        self.search_url = f"{self.base_url}/search/repositories"
        
        # Create session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=5,  # Total number of retries
            backoff_factor=1,  # Backoff factor for sleep between retries
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
            allowed_methods=["GET"]  # Only retry for GET requests
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        
    def search_repositories(self, query, sort="stars", order="desc", per_page=100, max_pages=10):
        """
        Search for repositories based on query string
        """
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": per_page,
            "page": 1
        }
        
        all_repos = []
        for page in range(1, max_pages + 1):
            params["page"] = page
            logger.info(f"Searching repositories: {query} (page {page}/{max_pages})")
            
            try:

                
                # Use session with retry logic
                response = self.session.get(
                    self.search_url, 
                    headers=self.headers, 
                    params=params,
                    timeout=30  # Add a timeout
                )
                response.raise_for_status()
                
                data = response.json()
                repos = data.get("items", [])
                
                # Break if no more results
                if not repos:
                    break
                
                all_repos.extend(repos)
                
                # Check for rate limiting
                remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
                if remaining < 5:
                    reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                    sleep_time = reset_time - time.time() + 5  # Add 5 seconds buffer
                    if sleep_time > 0:
                        logger.warning(f"Rate limit almost reached. Sleeping for {sleep_time:.2f} seconds")
                        time.sleep(sleep_time)
                
                # Longer delay between requests
                time.sleep(2)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error searching repositories (page {page}): {str(e)}")
                # Continue with next page instead of breaking
                time.sleep(5)  # Wait a bit longer after an error
                continue
        
        logger.info(f"Found {len(all_repos)} repositories matching the query")
        return all_repos