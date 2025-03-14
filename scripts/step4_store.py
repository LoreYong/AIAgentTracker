import os
import sys
import json
import yaml
import argparse
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.storage.file_storage import FileStorage
from src.utils.logger import setup_logger

logger = setup_logger("step4_store")

def load_config(config_path="config/config.yaml"):
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        return {}

def store_repositories(input_file, output_format=None, config_path=None):
    """Store processed repository data to final destination"""
    # Check if input file exists
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        return None
    
    # Load repositories from input file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            repos = json.load(f)
        
        if not repos:
            logger.warning("No repositories found in input file")
            return None
            
        logger.info(f"Loaded {len(repos)} repositories from {input_file}")
    except Exception as e:
        logger.error(f"Error loading repositories from file: {str(e)}")
        return None
    
    # Load configuration
    config = load_config(config_path) if config_path else load_config()
    storage_config = config.get("storage", {})
    
    # Determine storage format
    if output_format:
        format_type = output_format.lower()
    else:
        format_type = storage_config.get("format", "json").lower()
    
    # Create storage handler
    data_dir = storage_config.get("data_dir", "data")
    storage = FileStorage(data_dir=data_dir)
    
    # Generate filename with current date
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}.{format_type}"
    
    # Store data
    logger.info(f"Storing {len(repos)} repositories in {format_type} format")
    
    if format_type == "json":
        output_file = storage.save_json(repos, filename)
    elif format_type == "csv":
        output_file = storage.save_csv(repos, filename)
    else:
        logger.error(f"Unsupported format: {format_type}")
        return None
    
    if output_file:
        logger.info(f"Successfully saved data to: {output_file}")
        
        # Print summary
        logger.info("Data storage summary:")
        logger.info(f"- Date: {date_str}")
        logger.info(f"- Format: {format_type}")
        logger.info(f"- Repositories: {len(repos)}")
        logger.info(f"- Output file: {output_file}")
        
        # Show top 3 repositories
        if repos:
            logger.info("Top 3 repositories by stars:")
            for i, repo in enumerate(repos[:3]):
                logger.info(f"{i+1}. {repo.get('full_name')} - ⭐ {repo.get('stars')}")
    
    return output_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Store processed repositories to final destination")
    parser.add_argument("--input", required=True, help="Input file with processed repositories")
    parser.add_argument("--format", choices=["json", "csv"], help="Output format")
    parser.add_argument("--config", help="Path to configuration file")
    
    args = parser.parse_args()
    output_file = store_repositories(args.input, args.format, args.config)
    
    if not output_file:
        logger.error("Storage operation failed")
        sys.exit(1)
    else:
        logger.info(f"Storage completed successfully. Data saved to: {output_file}")