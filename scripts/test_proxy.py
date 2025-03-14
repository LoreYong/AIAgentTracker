import os
import sys
import yaml
import argparse

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.network import load_proxy_config, create_session
from src.utils.logger import setup_logger

logger = setup_logger("proxy_test")

def test_github_connection():
    """Test GitHub API connection with current proxy settings"""
    # 加载代理配置
    network_config = load_proxy_config()
    session, proxies = create_session()
    
    logger.info("Testing GitHub API connection with current settings...")
    logger.info(f"Proxy enabled: {proxies is not None}")
    if proxies:
        logger.info(f"Proxy settings: {proxies}")
    logger.info(f"SSL verification: {session.verify}")
    
    try:
        response = session.get(
            "https://api.github.com/rate_limit", 
            proxies=proxies,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"Connection successful! Status code: {response.status_code}")
        logger.info(f"Rate limit - Core: {data['resources']['core']['remaining']}/{data['resources']['core']['limit']}")
        logger.info(f"Rate limit - Search: {data['resources']['search']['remaining']}/{data['resources']['search']['limit']}")
        return True
    except Exception as e:
        logger.error(f"Connection error: {type(e).__name__}: {str(e)}")
        return False

def update_proxy_config(enable=None, http_proxy=None, https_proxy=None, verify_ssl=None):
    """Update proxy configuration file"""
    config_path = "config/proxy_config.yaml"
    
    # 确保配置目录存在
    os.makedirs("config", exist_ok=True)
    
    # 读取现有配置或创建新配置
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            if config is None:
                config = {}
    except FileNotFoundError:
        config = {}
    
    # 初始化代理部分（如果不存在）
    if "proxy" not in config:
        config["proxy"] = {}
    
    # 初始化SSL部分（如果不存在）
    if "ssl" not in config:
        config["ssl"] = {}
    
    # 更新配置
    if enable is not None:
        config["proxy"]["enabled"] = enable
    
    if http_proxy is not None:
        config["proxy"]["http"] = http_proxy
    
    if https_proxy is not None:
        config["proxy"]["https"] = https_proxy
    
    if verify_ssl is not None:
        config["ssl"]["verify"] = verify_ssl
    
    # 写入配置文件
    with open(config_path, 'w') as file:
        yaml.dump(config, file, default_flow_style=False)
    
    logger.info(f"Updated proxy configuration in {config_path}")
    logger.info(f"Current settings: Proxy enabled: {config['proxy'].get('enabled', False)}")
    if config["proxy"].get("enabled", False):
        logger.info(f"HTTP proxy: {config['proxy'].get('http', 'not set')}")
        logger.info(f"HTTPS proxy: {config['proxy'].get('https', 'not set')}")
    logger.info(f"SSL verification: {config['ssl'].get('verify', True)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test and configure proxy settings")
    parser.add_argument("--enable", action="store_true", help="Enable proxy")
    parser.add_argument("--disable", action="store_true", help="Disable proxy")
    parser.add_argument("--http", help="HTTP proxy URL (e.g., http://proxy:port)")
    parser.add_argument("--https", help="HTTPS proxy URL (e.g., http://proxy:port)")
    parser.add_argument("--no-ssl-verify", action="store_true", help="Disable SSL verification")
    parser.add_argument("--test", action="store_true", help="Test connection with current settings")
    
    args = parser.parse_args()
    
    # 检查是否需要更新代理配置
    if args.enable or args.disable or args.http or args.https or args.no_ssl_verify:
        enable = None
        if args.enable:
            enable = True
        elif args.disable:
            enable = False
        
        verify_ssl = None
        if args.no_ssl_verify:
            verify_ssl = False
            
        update_proxy_config(enable, args.http, args.https, verify_ssl)
    
    # 测试连接
    if args.test or not (args.enable or args.disable or args.http or args.https or args.no_ssl_verify):
        success = test_github_connection()
        if not success:
            sys.exit(1)