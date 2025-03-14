import time
import requests
from datetime import datetime
from ..utils.logger import setup_logger
from ..utils.network import create_session

logger = setup_logger("github_collector")

class GitHubCollector:
    """Collect detailed information about GitHub repositories"""
    
    def __init__(self, token=None):
        """Initialize the GitHub collector with authentication token"""
        self.token = token
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
        self.base_url = "https://api.github.com"
        
        # 创建会话并加载代理配置
        self.session, self.proxies = create_session()
    
    def get_additional_repo_info(self, owner, repo):
        """
        Get additional repository information that may not be included in search results
        
        Args:
            owner (str): Repository owner/organization
            repo (str): Repository name
            
        Returns:
            dict: Additional repository information or None if failed
        """
        url = f"{self.base_url}/repos/{owner}/{repo}"
        
        try:
            response = self.session.get(
                url, 
                headers=self.headers,
                proxies=self.proxies,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting additional info for {owner}/{repo}: {str(e)}")
            return None
            
    # 保持其他方法不变
        
    def get_repository_details(self, repo_data):
        """
        Extract relevant details from repository data
        
        Args:
            repo_data (dict): Repository data from GitHub API
            
        Returns:
            dict: Cleaned repository details
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return {
            "name": repo_data.get("name", ""),
            "full_name": repo_data.get("full_name", ""),
            "owner": repo_data.get("owner", {}).get("login", ""),
            "description": repo_data.get("description", ""),
            "stars": repo_data.get("stargazers_count", 0),
            "forks": repo_data.get("forks_count", 0),
            "last_updated": repo_data.get("updated_at", ""),
            "created_at": repo_data.get("created_at", ""),
            "url": repo_data.get("html_url", ""),
            "language": repo_data.get("language", ""),
            "topics": repo_data.get("topics", []),
            "open_issues": repo_data.get("open_issues_count", 0),
            "collection_timestamp": timestamp
        }
    
  
    
    def process_repo_list(self, repo_list):
        """
        Process a list of repositories to extract and enrich data
        
        Args:
            repo_list (list): List of repositories from search results
            
        Returns:
            list: List of processed repository details
        """
        processed_repos = []
        
        for repo in repo_list:
            try:
                # Extract basic details from search result
                repo_details = self.get_repository_details(repo)
                
                # Optionally get additional information if needed
                # If search results already contain all needed info, skip this step
                # additional_info = self.get_additional_repo_info(repo_details["owner"], repo_details["name"])
                # if additional_info:
                #     # Update with any additional fields needed
                #     pass
                
                processed_repos.append(repo_details)
                
                # Be nice to the GitHub API
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Error processing repository {repo.get('full_name', 'unknown')}: {str(e)}")
        
        # Sort by stars (descending)
        processed_repos.sort(key=lambda x: x.get("stars", 0), reverse=True)
        
        return processed_repos