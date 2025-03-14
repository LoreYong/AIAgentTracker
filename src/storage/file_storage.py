import os
import json
import csv
from datetime import datetime
from ..utils.logger import setup_logger

logger = setup_logger("file_storage")

class FileStorage:
    """Store repository data in JSON or CSV files"""
    
    def __init__(self, data_dir="data"):
        """Initialize file storage with target directory"""
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def save_json(self, data, filename=None):
        """
        Save data as JSON file
        
        Args:
            data (list): List of repositories to save
            filename (str): Optional filename, defaults to current date
            
        Returns:
            str: Path to the saved file
        """
        if filename is None:
            filename = f"{datetime.now().strftime('%Y-%m-%d')}.json"
        
        file_path = os.path.join(self.data_dir, filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(data)} repositories to {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error saving JSON data: {str(e)}")
            return None
    
    def save_csv(self, data, filename=None):
        """
        Save data as CSV file
        
        Args:
            data (list): List of repositories to save
            filename (str): Optional filename, defaults to current date
            
        Returns:
            str: Path to the saved file
        """
        if filename is None:
            filename = f"{datetime.now().strftime('%Y-%m-%d')}.csv"
        
        file_path = os.path.join(self.data_dir, filename)
        
        try:
            # Determine fieldnames from the first item or use default fields
            if data and len(data) > 0:
                fieldnames = list(data[0].keys())
            else:
                fieldnames = ["name", "full_name", "description", "stars", "forks", 
                            "last_updated", "url", "language", "collection_timestamp"]
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"Saved {len(data)} repositories to {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error saving CSV data: {str(e)}")
            return None
    
    def load_json(self, filename):
        """
        Load data from JSON file
        
        Args:
            filename (str): Name of file to load
            
        Returns:
            list: Repository data loaded from file
        """
        file_path = os.path.join(self.data_dir, filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} repositories from {file_path}")
            return data
        except Exception as e:
            logger.error(f"Error loading JSON data: {str(e)}")
            return []
    
    def load_latest(self, file_format="json"):
        """
        Load the latest data file
        
        Args:
            file_format (str): File format to look for (json or csv)
            
        Returns:
            list: Repository data from the latest file
        """
        try:
            # List all files with the specified extension
            files = [f for f in os.listdir(self.data_dir) 
                    if f.endswith(f".{file_format}") and 
                    f[0:10].replace('-', '').isdigit()]  # Filter by date format YYYY-MM-DD
            
            if not files:
                logger.warning(f"No {file_format} files found in {self.data_dir}")
                return []
            
            # Sort by filename (which contains the date)
            latest_file = sorted(files)[-1]
            
            if file_format == "json":
                return self.load_json(latest_file)
            else:
                logger.warning("CSV loading not implemented yet")
                return []
                
        except Exception as e:
            logger.error(f"Error loading latest data: {str(e)}")
            return []