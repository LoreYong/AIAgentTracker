import os
import yaml
import argparse
from datetime import datetime
from dotenv import load_dotenv

from .github.search import GitHubSearcher
from .github.collector import GitHubCollector
from .processing.data_processor import DataProcessor
from .storage.file_storage import FileStorage
from .utils.logger import setup_logger

# Load environment variables from .env file
load_dotenv()

logger = setup_logger("main")

def load_config(config_path="config/config.yaml"):
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        # Return default configuration
        return {
            "github": {
                "search_keywords": ["AI agent", "AI assistant", "autonomous agent"],
                "min_stars": 10,
                "max_pages": 10
            },
            "storage": {
                "format": "json",
                "data_dir": "data"
            }
        }

def run_tracker(config_path=None, save_format=None):
    """Run the AI Agent tracking process"""
    # Load configuration
    config = load_config(config_path) if config_path else load_config()
    
    # Override save format if specified
    if save_format:
        config["storage"]["format"] = save_format
    
    # Set up GitHub API token
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        logger.warning("No GitHub token found. API rate limits will be restricted.")
    
    # Step 1: Search for repositories
    logger.info("Starting repository search")
    searcher = GitHubSearcher(token=github_token)
    search_config = config.get("github", {})
    additional_keywords = search_config.get("search_keywords", [])
    min_stars = search_config.get("min_stars", 10)
    
    repos = searcher.search_ai_agent_repos(
        additional_keywords=additional_keywords, 
        min_stars=min_stars
    )
    
    if not repos:
        logger.error("No repositories found. Exiting.")
        return False
    
    # Step 2: Collect detailed information
    logger.info(f"Processing {len(repos)} repositories")
    collector = GitHubCollector(token=github_token)
    repo_details = collector.process_repo_list(repos)
    
    # Step 3: Process data
    processor = DataProcessor()
    processed_repos = processor.process_repositories(repo_details)
    
    # Step 4: Store data
    storage_config = config.get("storage", {})
    storage = FileStorage(data_dir=storage_config.get("data_dir", "data"))
    
    # Save in the specified format
    format = storage_config.get("format", "json").lower()
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    if format == "json":
        file_path = storage.save_json(processed_repos)
    elif format == "csv":
        file_path = storage.save_csv(processed_repos)
    else:
        logger.warning(f"Unsupported format: {format}. Defaulting to JSON.")
        file_path = storage.save_json(processed_repos)
    
    if file_path:
        logger.info(f"Successfully saved {len(processed_repos)} repositories to {file_path}")
        return True
    else:
        logger.error("Failed to save repository data")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Track AI Agent repositories on GitHub")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--format", choices=["json", "csv"], help="Output file format")
    
    args = parser.parse_args()
    success = run_tracker(args.config, args.format)
    
    if not success:
        exit(1)