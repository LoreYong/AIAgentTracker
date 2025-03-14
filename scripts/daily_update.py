import os
import sys
import time
import schedule
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.main import run_tracker
from src.utils.logger import setup_logger

logger = setup_logger("daily_update")

def daily_job():
    """Run the daily update job"""
    logger.info(f"Starting daily update job at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    success = run_tracker()
    
    if success:
        logger.info("Daily update completed successfully")
    else:
        logger.error("Daily update failed")
    
    return success

def schedule_daily_job(hour=2, minute=0):
    """Schedule the daily job to run at the specified time"""
    logger.info(f"Scheduling daily job to run at {hour:02d}:{minute:02d}")
    schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(daily_job)
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run daily AI Agent tracker update")
    parser.add_argument("--now", action="store_true", help="Run update immediately")
    parser.add_argument("--hour", type=int, default=2, help="Hour to run daily update (24h format)")
    parser.add_argument("--minute", type=int, default=0, help="Minute to run daily update")
    
    args = parser.parse_args()
    
    if args.now:
        daily_job()
    else:
        try:
            schedule_daily_job(args.hour, args.minute)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")