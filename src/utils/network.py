import os
import yaml
import requests
import socket
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .logger import setup_logger

logger = setup_logger("network")

def load_proxy_config(config_path="config/proxy_config.yaml"):
    """
    加载代理和SSL配置
    
    Args:
        config_path (str): 代理配置文件路径
        
    Returns:
        dict: 包含 'proxies' 和 'verify' 键的字典
    """
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        proxy_settings = config.get("proxy", {})
        ssl_settings = config.get("ssl", {})
        
        # 如果启用，配置代理
        proxies = None
        if proxy_settings.get("enabled", False):
            proxies = {
                "http": proxy_settings.get("http", None),
                "https": proxy_settings.get("https", None)
            }
            no_proxy = proxy_settings.get("no_proxy")
            if no_proxy:
                # 注意：这会设置环境变量并影响所有请求
                os.environ["NO_PROXY"] = no_proxy
            
            logger.info(f"代理已启用，设置为: {proxies}")
        
        # 配置SSL验证
        verify = ssl_settings.get("verify", True)
        if not verify:
            # 如果禁用了验证，禁止警告
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            logger.warning("SSL验证已禁用。这是不安全的！")
        
        # 如果提供了证书路径，使用它
        cert_path = ssl_settings.get("cert_path")
        if cert_path and verify:
            verify = cert_path
            logger.info(f"使用自定义证书路径: {cert_path}")
        
        return {
            "proxies": proxies,
            "verify": verify
        }
    except FileNotFoundError:
        logger.warning(f"未找到代理配置文件: {config_path}。使用默认设置。")
        return {
            "proxies": None,
            "verify": True
        }
    except Exception as e:
        logger.warning(f"加载代理配置时出错: {str(e)}")
        return {
            "proxies": None,
            "verify": True
        }

def create_session():
    """
    创建带有重试逻辑和代理设置的 requests Session
    
    Returns:
        tuple: (session, proxies) 配置好的session对象和代理设置
    """
    # 加载网络配置
    network_config = load_proxy_config()
    
    # 创建带有重试逻辑的会话
    session = requests.Session()
    retry_strategy = Retry(
        total=5,  # 总重试次数
        backoff_factor=1,  # 重试之间的睡眠时间因子
        status_forcelist=[429, 500, 502, 503, 504],  # 这些状态码触发重试
        allowed_methods=["GET"]  # 只对GET请求进行重试
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    # 应用代理和SSL设置
    session.verify = network_config["verify"]
    
    return session, network_config["proxies"]

def test_connectivity(url="https://api.github.com", timeout=10):
    """
    测试与指定URL的连接
    
    Args:
        url (str): 要测试的URL
        timeout (int): 连接超时时间（秒）
        
    Returns:
        bool: 连接是否成功
    """
    session, proxies = create_session()
    
    try:
        logger.info(f"测试连接到 {url}")
        response = session.get(url, timeout=timeout, proxies=proxies)
        response.raise_for_status()
        logger.info(f"连接成功！状态码: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"连接失败: {str(e)}")
        return False

def check_proxy_status():
    """
    检查代理配置状态并尝试连接
    
    Returns:
        dict: 代理状态信息
    """
    config = load_proxy_config()
    proxies = config["proxies"]
    
    status = {
        "proxy_enabled": proxies is not None,
        "proxy_settings": proxies,
        "ssl_verify": config["verify"],
        "connectivity_test": False
    }
    
    if proxies:
        # 测试代理连接
        try:
            session = requests.Session()
            session.verify = config["verify"]
            
            logger.info("测试代理连接...")
            response = session.get(
                "https://api.github.com", 
                proxies=proxies,
                timeout=15
            )
            response.raise_for_status()
            status["connectivity_test"] = True
            status["server_time"] = response.headers.get("Date")
            logger.info("代理连接测试成功")
        except Exception as e:
            logger.error(f"代理连接测试失败: {str(e)}")
    
    return status