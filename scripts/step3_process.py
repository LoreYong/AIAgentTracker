import os
import sys
import json
import argparse
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.processing.data_processor import DataProcessor
from src.utils.logger import setup_logger

logger = setup_logger("step3_process")

def process_repositories(input_file, output_file=None):
    """Process and transform repository data"""
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
    
    # Create processor
    processor = DataProcessor()
    
    # Process data
    logger.info("Processing repository data...")
    
    # Print summary of input data
    stars_before = sum(repo.get('stars', 0) for repo in repos)
    min_stars = min(repo.get('stars', 0) for repo in repos) if repos else 0
    max_stars = max(repo.get('stars', 0) for repo in repos) if repos else 0
    
    logger.info(f"Input data summary:")
    logger.info(f"- Total repositories: {len(repos)}")
    logger.info(f"- Total stars: {stars_before}")
    logger.info(f"- Star range: {min_stars} to {max_stars}")
    
    # Process the repositories
    processed_repos = processor.process_repositories(repos)
    
    # Generate output file name if not provided
    if not output_file:
        os.makedirs("temp", exist_ok=True)
        output_file = f"temp/step3_processed_repos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Save processed repository information
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_repos, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(processed_repos)} processed repositories to {output_file}")
    except Exception as e:
        logger.error(f"Error saving processed data: {str(e)}")
        return None
    
    # Print summary of output data
    logger.info(f"Output data summary:")
    logger.info(f"- Total repositories after processing: {len(processed_repos)}")
    
    # Print top 5 repositories by stars
    if processed_repos:
        logger.info("Top 5 repositories by stars:")
        for i, repo in enumerate(processed_repos[:5]):
            logger.info(f"{i+1}. {repo.get('full_name')} - ⭐ {repo.get('stars')} - {repo.get('description')[:80]}...")
    
    return output_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process repository data")
    parser.add_argument("--input", required=True, help="Input file with repository details")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    output_file = process_repositories(args.input, args.output)
    
    if not output_file:
        logger.error("Processing operation failed")
        sys.exit(1)
    else:
        logger.info(f"Processing completed successfully. Results saved to: {output_file}")