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

# 在现有main.py基础上添加/修改以下内容

def generate_readme(data_path=None):
    """
    生成项目README.md，展示项目数据
    
    Args:
        data_path (str): 数据文件路径
        
    Returns:
        bool: 是否成功生成
    """
    logger.info("生成项目展示页面")
    
    # 使用FileStorage加载最新数据
    storage = FileStorage(data_dir="data")
    repos = storage.load_latest() if not data_path else storage.load_json(os.path.basename(data_path))
    
    if not repos:
        logger.error("无数据可用于生成README")
        return False
    
    # 准备README内容
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    readme_content = f"""# AI Agent 项目追踪器

> 最后更新于: {timestamp}

此仓库自动追踪GitHub上与AI Agent相关的开源项目，并按照星标数量排序展示。

## 热门项目排行榜

| # | 项目名称 | 描述 | 星标 ⭐ | 最后更新 |
|---|---------|------|--------|---------|
"""
    
    # 添加前20个项目
    for i, repo in enumerate(repos[:20], 1):
        name = repo.get("full_name", "")
        description = repo.get("description", "").replace("|", "/")
        if len(description) > 80:
            description = description[:77] + "..."
        
        stars = repo.get("stars", 0)
        last_updated = repo.get("last_updated", "").split("T")[0]
        
        readme_content += f"| {i} | [{name}]({repo.get('url', '')}) | {description} | {stars} | {last_updated} |\n"
    
    # 添加项目统计信息
    total_repos = len(repos)
    total_stars = sum(repo.get("stars", 0) for repo in repos)
    
    readme_content += f"""
## 项目统计

- 跟踪的项目总数: **{total_repos}**
- 总星标数: **{total_stars}**
- 平均每个项目星标数: **{total_stars / total_repos:.1f}**

## 关于本项目

AIAgentTracker 是一个自动化工具，每天从GitHub获取与AI Agent相关的开源项目信息，并按照流行度进行排序。

项目会每日自动更新。如果想要添加您的项目到追踪列表中，请确保它包含"ai-agent"、"AI agent"等相关标签或描述。
"""
    
    # 写入README.md文件
    try:
        with open("README.md", 'w', encoding='utf-8') as f:
            f.write(readme_content)
        logger.info("已成功生成 README.md")
        return True
    except Exception as e:
        logger.error(f"生成README.md时出错: {str(e)}")
        return False

def run_tracker(config_path=None, save_format=None, update_readme=True):
    """Run the AI Agent tracking process"""
    # 现有代码保持不变
    # [...]
    
    # 在函数末尾添加:
    if file_path and update_readme:
        # 生成README
        if generate_readme(file_path):
            logger.info("已更新项目展示页面")
    
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Track AI Agent repositories on GitHub")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--format", choices=["json", "csv"], help="Output file format")
    
    args = parser.parse_args()
    success = run_tracker(args.config, args.format)
    
    if not success:
        exit(1)