import os
import sys
import argparse
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.step1_search import search_repositories
from scripts.step2_collect import collect_repository_details
from scripts.step3_process import process_repositories
from scripts.step4_store import store_repositories
from src.utils.logger import setup_logger

logger = setup_logger("run_all")

def run_all_steps(config_path=None, output_format=None, keep_temp=False):
    """Run all steps of the AIAgentTracker pipeline"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Step 1: Search repositories
    logger.info("STEP 1: SEARCHING REPOSITORIES")
    step1_output = os.path.join(temp_dir, f"step1_search_{timestamp}.json")
    step1_output = search_repositories(config_path, step1_output)
    if not step1_output:
        logger.error("Step 1 (Search) failed. Aborting pipeline.")
        return False
    
    # Step 2: Collect repository details
    logger.info("STEP 2: COLLECTING REPOSITORY DETAILS")
    step2_output = os.path.join(temp_dir, f"step2_details_{timestamp}.json")
    step2_output = collect_repository_details(step1_output, step2_output)
    if not step2_output:
        logger.error("Step 2 (Collection) failed. Aborting pipeline.")
        return False
    
    # Step 3: Process repositories
    logger.info("STEP 3: PROCESSING REPOSITORIES")
    step3_output = os.path.join(temp_dir, f"step3_processed_{timestamp}.json")
    step3_output = process_repositories(step2_output, step3_output)
    if not step3_output:
        logger.error("Step 3 (Processing) failed. Aborting pipeline.")
        return False
    
    # Step 4: Store repositories
    logger.info("STEP 4: STORING REPOSITORIES")
    final_output = store_repositories(step3_output, output_format, config_path)
    if not final_output:
        logger.error("Step 4 (Storage) failed.")
        return False
    
    logger.info(f"All steps completed successfully!")
    logger.info(f"Final output: {final_output}")
    
    # Clean up temporary files if not keeping them
    if not keep_temp:
        logger.info("Cleaning up temporary files...")
        try:
            os.remove(step1_output)
            os.remove(step2_output)
            os.remove(step3_output)
            logger.info("Temporary files removed.")
        except Exception as e:
            logger.warning(f"Error removing temporary files: {str(e)}")
    else:
        logger.info("Keeping temporary files for inspection.")
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run all steps of the AIAgentTracker pipeline")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--format", choices=["json", "csv"], help="Output format")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary files")
    
    args = parser.parse_args()
    success = run_all_steps(args.config, args.format, args.keep_temp)
    
    if not success:
        logger.error("Pipeline execution failed")
        sys.exit(1)