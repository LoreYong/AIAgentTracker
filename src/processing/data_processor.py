from datetime import datetime
from ..utils.logger import setup_logger

logger = setup_logger("data_processor")

class DataProcessor:
    """Process and transform repository data"""
    
    def __init__(self):
        """Initialize the data processor"""
        pass
    
    def sort_by_stars(self, repos):
        """
        Sort repositories by star count (descending)
        
        Args:
            repos (list): List of repository dictionaries
            
        Returns:
            list: Sorted list of repositories
        """
        return sorted(repos, key=lambda x: x.get("stars", 0), reverse=True)
    
    def filter_duplicate_repos(self, repos):
        """
        Remove duplicate repositories based on full_name
        
        Args:
            repos (list): List of repository dictionaries
            
        Returns:
            list: List with duplicates removed
        """
        unique_repos = {}
        for repo in repos:
            full_name = repo.get("full_name")
            if full_name and full_name not in unique_repos:
                unique_repos[full_name] = repo
        
        return list(unique_repos.values())
    
    def enrich_repos(self, repos):
        """
        Add additional calculated fields to repository data
        
        Args:
            repos (list): List of repository dictionaries
            
        Returns:
            list: List with enriched repository data
        """
        enriched_repos = []
        timestamp = datetime.now().strftime("%Y-%m-%d")
        
        for repo in repos:
            # Clone the repo dictionary to avoid modifying original
            enriched_repo = repo.copy()
            
            # Add any calculated fields here
            # For example, a star-to-fork ratio
            stars = enriched_repo.get("stars", 0)
            forks = enriched_repo.get("forks", 0)
            if forks > 0:
                enriched_repo["star_fork_ratio"] = round(stars / forks, 2)
            else:
                enriched_repo["star_fork_ratio"] = stars
            
            # Calculate days since last update
            try:
                last_updated = datetime.fromisoformat(enriched_repo.get("last_updated", "").replace("Z", "+00:00"))
                now = datetime.now().astimezone()
                days_since_update = (now - last_updated).days
                enriched_repo["days_since_update"] = days_since_update
            except (ValueError, TypeError):
                enriched_repo["days_since_update"] = None
            
            enriched_repo["collection_date"] = timestamp
            enriched_repos.append(enriched_repo)
        
        return enriched_repos
    
    def process_repositories(self, repos):
        """
        Complete processing pipeline for repository data
        
        Args:
            repos (list): List of repository dictionaries
            
        Returns:
            list: Fully processed repositories
        """
        if not repos:
            logger.warning("No repositories to process")
            return []
        
        logger.info(f"Processing {len(repos)} repositories")
        
        # Remove duplicates first
        unique_repos = self.filter_duplicate_repos(repos)
        logger.info(f"After removing duplicates: {len(unique_repos)} repositories")
        
        # Enrich the data
        enriched_repos = self.enrich_repos(unique_repos)
        
        # Sort by stars
        sorted_repos = self.sort_by_stars(enriched_repos)
        
        return sorted_repos