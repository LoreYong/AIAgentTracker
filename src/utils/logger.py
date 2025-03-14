import os
import logging
from datetime import datetime

def setup_logger(name, log_dir="logs", level=logging.INFO):
    """设置带有文件和控制台处理程序的logger"""
    # 确保日志目录存在
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 清理现有处理程序
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # 创建文件处理程序
    log_filename = f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(os.path.join(log_dir, log_filename))
    file_handler.setLevel(level)
    
    # 创建控制台处理程序
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # 创建格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理程序到logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger