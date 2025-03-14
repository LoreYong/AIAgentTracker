import time
import requests
from datetime import datetime
from ..utils.logger import setup_logger

logger = setup_logger("github_search")

class GitHubSearcher:
    """Search GitHub repositories based on keywords and filters"""
    
    def __init__(self, token=None):
        """Initialize the GitHub searcher with authentication token"""
        self.token = token
        self.headers = {}
        if token:
            self.headers["Authorization"] = f"token {token}"
        self.base_url = "https://api.github.com"
        self.search_url = f"{self.base_url}/search/repositories"
        
    def search_repositories(self, query, sort="stars", order="desc", per_page=100, max_pages=10):
        """
        Search for repositories based on query string
        
        Args:
            query (str): GitHub search query
            sort (str): Sorting criteria (stars, forks, updated)
            order (str): Sort order (asc, desc)
            per_page (int): Results per page (max 100)
            max_pages (int): Maximum number of pages to retrieve
            
        Returns:
            list: List of repository data dictionaries
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
                response = requests.get(self.search_url, headers=self.headers, params=params)
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
                
                # Add a small delay between requests to be nice to GitHub API
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error searching repositories: {str(e)}")
                break
        
        logger.info(f"Found {len(all_repos)} repositories matching the query")
        return all_repos
    
    def search_ai_agent_repos(self, additional_keywords=None, min_stars=10):
        """
        Search specifically for AI Agent related repositories
        
        Args:
            additional_keywords (list): Additional keywords to include in search
            min_stars (int): Minimum stars for repositories
            
        Returns:
            list: List of AI Agent repositories
        """
        # Base query for AI Agent repositories
        query = f"topic:ai-agent OR topic:ai-agents OR topic:aiagent OR topic:aiagents OR \"AI agent\" in:name,description,readme stars:>={min_stars}"
        
        # Add additional keywords if provided
        if additional_keywords and isinstance(additional_keywords, list):
            for keyword in additional_keywords:
                query += f" OR \"{keyword}\" in:name,description,readme"
        
        return self.search_repositories(query)