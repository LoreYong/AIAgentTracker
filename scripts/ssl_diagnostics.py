import os
import sys
import ssl
import socket
import requests
import platform
import datetime
import urllib3
import subprocess
from urllib.parse import urlparse

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.logger import setup_logger

logger = setup_logger("ssl_diagnostics", level=20)  # INFO level

def check_system_time():
    """Check if system time is accurate"""
    logger.info("=== 系统时间检查 ===")
    system_time = datetime.datetime.now()
    logger.info(f"系统时间: {system_time}")
    
    # 尝试获取一个标准时间服务器的时间
    try:
        response = requests.get("https://worldtimeapi.org/api/ip", timeout=10)
        if response.status_code == 200:
            network_time = datetime.datetime.fromisoformat(response.json().get("datetime").replace("Z", "+00:00"))
            time_diff = abs((network_time - system_time.astimezone()).total_seconds())
            logger.info(f"网络时间: {network_time}")
            logger.info(f"时间差异: {time_diff:.2f} 秒")
            
            if time_diff > 300:  # 5分钟
                logger.warning("⚠️ 系统时间与网络时间相差较大，可能导致SSL证书验证问题")
    except Exception as e:
        logger.warning(f"无法检查网络时间: {str(e)}")

def print_ssl_info():
    """Print SSL/TLS library information"""
    logger.info("=== SSL/TLS 信息 ===")
    logger.info(f"OpenSSL 版本: {ssl.OPENSSL_VERSION}")
    
    # 获取默认 HTTPS 协议（兼容不同 Python 版本）
    try:
        # 尝试创建默认上下文并获取其协议
        context = ssl.create_default_context()
        protocol = context.protocol
        logger.info(f"默认 SSL 协议: {protocol}")
    except Exception as e:
        logger.info(f"无法确定默认 SSL 协议: {str(e)}")
    
    # 显示证书路径
    try:
        cert_paths = ssl.get_default_verify_paths()
        logger.info(f"证书文件路径: {cert_paths.cafile}")
        logger.info(f"证书目录路径: {cert_paths.capath}")
    except Exception as e:
        logger.info(f"无法获取证书路径: {str(e)}")
    
    # 列出所有可用的TLS版本
    logger.info(f"支持的 TLS 方法:")
    tls_versions = [
        "TLSv1", "TLSv1_1", "TLSv1_2", "TLSv1_3", 
        "PROTOCOL_SSLv23", "PROTOCOL_TLS", "PROTOCOL_TLS_CLIENT", 
        "PROTOCOL_TLS_SERVER"
    ]
    
    for ver in tls_versions:
        if hasattr(ssl, ver):
            logger.info(f"  - {ver}: 支持")
        else:
            logger.info(f"  - {ver}: 不支持")

def test_ssl_connection(hostname="api.github.com", port=443):
    """Test direct SSL connection to the server"""
    logger.info(f"\n=== 直接 SSL 连接测试 ({hostname}:{port}) ===")
    
    # 使用默认 SSL 上下文
    try:
        context = ssl.create_default_context()
        logger.info(f"使用默认 SSL 上下文")
    except Exception as e:
        logger.error(f"创建 SSL 上下文失败: {str(e)}")
        return False
    
    try:
        with socket.create_connection((hostname, port), timeout=10) as sock:
            logger.info(f"TCP 连接成功")
            
            try:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    logger.info(f"SSL 握手成功!")
                    cert = ssock.getpeercert()
                    subject = dict(x[0] for x in cert['subject'])
                    issuer = dict(x[0] for x in cert['issuer'])
                    logger.info(f"证书有效期: {cert['notBefore']} 到 {cert['notAfter']}")
                    logger.info(f"证书主体: {subject.get('commonName')}")
                    logger.info(f"证书颁发者: {issuer.get('commonName')}")
                    logger.info(f"使用的密码套件: {ssock.cipher()}")
                    return True
            except ssl.SSLError as e:
                logger.error(f"SSL 握手失败: {str(e)}")
                return False
            except Exception as e:
                logger.error(f"SSL 握手过程中发生错误: {str(e)}")
                return False
    except socket.timeout:
        logger.error("TCP 连接超时")
        return False
    except ConnectionRefusedError:
        logger.error("TCP 连接被拒绝")
        return False
    except Exception as e:
        logger.error(f"TCP 连接失败: {str(e)}")
        return False

def test_curl_connection(url="https://api.github.com/rate_limit"):
    """Test connection using curl command line tool"""
    logger.info(f"\n=== 使用 curl 测试连接 ({url}) ===")
    
    parsed_url = urlparse(url)
    hostname = parsed_url.netloc
    
    try:
        # First test with verbose output
        logger.info("使用 curl 执行 SSL 握手 (详细模式)...")
        result = subprocess.run(
            ["curl", "-v", "-s", "-o", "NUL", url],
            capture_output=True, 
            text=True
        )
        
        # Print the verbose output for SSL diagnosis
        stderr_lines = result.stderr.split('\n')
        ssl_info_lines = [line for line in stderr_lines if "SSL" in line or "TLS" in line]
        for line in ssl_info_lines:
            logger.info(f"curl: {line.strip()}")
            
        # Now try to get actual data
        logger.info("\n尝试使用 curl 获取数据:")
        result = subprocess.run(
            ["curl", "-s", url],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout:
            logger.info("curl 成功获取数据!")
            data_preview = result.stdout[:100] + "..." if len(result.stdout) > 100 else result.stdout
            logger.info(f"数据预览: {data_preview}")
            return True
        else:
            logger.error(f"curl 请求失败, 退出码: {result.returncode}")
            if result.stderr:
                logger.error(f"错误: {result.stderr}")
            return False
            
    except FileNotFoundError:
        logger.warning("curl 命令未找到。请确保 curl 已安装并在 PATH 中")
        return False
    except Exception as e:
        logger.error(f"执行 curl 时出错: {str(e)}")
        return False

def test_different_requests_configs():
    """Test different requests configurations"""
    logger.info("\n=== 不同的请求配置测试 ===")
    url = "https://api.github.com/zen"
    
    # 测试配置选项
    configs = [
        {
            "name": "默认设置",
            "options": {}
        },
        {
            "name": "自定义超时设置",
            "options": {
                "timeout": 30
            }
        },
        {
            "name": "自定义连接适配器",
            "options": {
                "session": True,
                "mount": True
            }
        },
        {
            "name": "绕过主机验证 (仅测试)",
            "options": {
                "verify": False
            }
        }
    ]
    
    for config in configs:
        logger.info(f"\n测试配置: {config['name']}")
        options = config['options']
        
        try:
            if options.get("session", False):
                session = requests.Session()
                
                if options.get("mount", False):
                    adapter = requests.adapters.HTTPAdapter(
                        pool_connections=1,
                        pool_maxsize=1,
                        max_retries=3
                    )
                    session.mount("https://", adapter)
                    response = session.get(url, timeout=options.get("timeout", 10))
                else:
                    response = session.get(url, timeout=options.get("timeout", 10))
            else:
                verify = options.get("verify", True)
                if not verify:
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                
                response = requests.get(
                    url, 
                    timeout=options.get("timeout", 10),
                    verify=verify
                )
                
            logger.info(f"成功! 状态码: {response.status_code}")
            logger.info(f"响应: {response.text}")
            return True
            
        except Exception as e:
            logger.error(f"失败: {type(e).__name__}: {str(e)}")
    
    return False

def print_network_interfaces():
    """Print information about network interfaces"""
    logger.info("\n=== 网络接口信息 ===")
    
    try:
        # 仅适用于Windows
        if platform.system() == "Windows":
            result = subprocess.run(
                ["ipconfig", "/all"], 
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                interfaces = result.stdout.split("\n\n")
                for interface in interfaces:
                    if "IPv4" in interface or "IPv6" in interface:
                        logger.info(interface.strip())
        # 仅适用于Linux/Mac
        else:
            result = subprocess.run(
                ["ifconfig"], 
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                interfaces = result.stdout.split("\n\n")
                for interface in interfaces:
                    if "inet " in interface:
                        logger.info(interface.strip())
    except Exception as e:
        logger.warning(f"获取网络接口信息失败: {str(e)}")

def check_dns_resolution(hostname="api.github.com"):
    """Check DNS resolution for a hostname"""
    logger.info(f"\n=== DNS 解析测试 ({hostname}) ===")
    
    try:
        # Get address info
        addr_info = socket.getaddrinfo(hostname, 443)
        ips = set()
        for info in addr_info:
            family, socktype, proto, canonname, sockaddr = info
            if family in (socket.AF_INET, socket.AF_INET6):
                ips.add(sockaddr[0])
        
        if ips:
            logger.info(f"DNS 解析成功，IP地址: {', '.join(ips)}")
            return True
        else:
            logger.warning("DNS 解析成功，但未返回有效IP地址")
            return False
    except socket.gaierror as e:
        logger.error(f"DNS 解析失败: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"检查DNS解析时出错: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("开始 SSL 诊断...\n")
    
    # 打印系统和环境信息
    logger.info("=== 系统信息 ===")
    logger.info(f"操作系统: {platform.system()} {platform.release()} ({platform.platform()})")
    logger.info(f"Python 版本: {platform.python_version()}")
    logger.info(f"requests 版本: {requests.__version__}")
    logger.info(f"urllib3 版本: {urllib3.__version__}")
    
    # 检查代理环境变量
    logger.info("\n=== 网络代理环境变量 ===")
    http_proxy = os.environ.get("HTTP_PROXY")
    https_proxy = os.environ.get("HTTPS_PROXY")
    no_proxy = os.environ.get("NO_PROXY")
    logger.info(f"HTTP_PROXY: {http_proxy or '未设置'}")
    logger.info(f"HTTPS_PROXY: {https_proxy or '未设置'}")
    logger.info(f"NO_PROXY: {no_proxy or '未设置'}")
    
    # 检查系统时间
    check_system_time()
    
    # 检查DNS解析
    check_dns_resolution()
    
    # 打印网络接口信息
    print_network_interfaces()
    
    # 打印SSL库信息
    print_ssl_info()
    
    # 测试直接SSL连接
    logger.info("\n开始测试连接...")
    test_ssl_connection()
    
    # 使用curl尝试连接
    test_curl_connection()
    
    # 测试不同的请求配置
    test_different_requests_configs()
    
    logger.info("\n诊断完成! 请查看上面的输出以确定问题所在。")
    
    # 提供可能的解决方案
    logger.info("\n=== 可能的解决方案 ===")
    logger.info("1. 检查防火墙是否阻止了 HTTPS 连接")
    logger.info("2. 确保系统时间是准确的")
    logger.info("3. 尝试更新 OpenSSL 或 Python")
    logger.info("4. 如果在企业网络中，配置正确的代理设置")
    logger.info("5. 临时解决方案: 使用 --no-ssl-verify 选项 (不推荐用于生产环境)")
    logger.info("   python -m scripts.test_proxy --enable --http 'http://你的代理:端口' --https 'http://你的代理:端口' --no-ssl-verify")