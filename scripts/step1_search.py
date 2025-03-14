import os
import sys
import json
import yaml
import argparse
from datetime import datetime

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# 导入日志工具和GitHub搜索类
from src.utils.logger import setup_logger
from src.github.search import GitHubSearcher  # 导入GitHubSearcher类

logger = setup_logger("step1_search")

def load_config(config_path="config/config.yaml"):
    """加载配置文件"""
    config_file = os.path.join(project_root, config_path)
    logger.info(f"尝试加载配置文件: {config_file}")
    
    try:
        if not os.path.exists(config_file):
            logger.warning(f"配置文件不存在: {config_file}")
            # 创建默认配置
            default_config = {
                "github": {
                    "search_keywords": ["AI agent", "AI assistant", "autonomous agent"],
                    "min_stars": 10,
                    "max_pages": 5
                },
                "storage": {
                    "format": "json",
                    "data_dir": "data"
                },
                "proxy": {
                    "enabled": False,
                    "http": None,
                    "https": None
                },
                "ssl": {
                    "verify": True
                }
            }
            
            # 确保目录存在
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            # 写入默认配置
            with open(config_file, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            
            logger.info(f"已创建默认配置文件: {config_file}")
            return default_config
            
        with open(config_file, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        logger.info(f"成功加载配置文件: {config_file}")
        logger.info(f"配置内容: {config}")
        return config
    except Exception as e:
        logger.error(f"加载配置文件时出错: {str(e)}")
        return {
            "github": {
                "search_keywords": ["AI agent"],
                "min_stars": 10,
                "max_pages": 3
            }
        }

def search_ai_agent_repos(token=None, config=None, output_file=None):
    """搜索 AI Agent 相关的 GitHub 仓库"""
    logger.info("开始搜索 AI Agent 相关的 GitHub 仓库")
    
    # 从环境变量获取令牌（如果未提供）
    if not token:
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            logger.info("从环境变量获取到 GitHub 令牌")
        else:
            logger.warning("未提供 GitHub 令牌，API 请求可能会受到速率限制")
    
    # 如果配置为 None，加载默认配置
    if config is None:
        config = load_config()
    
    github_config = config.get("github", {})
    keywords = github_config.get("search_keywords", ["AI agent"])
    min_stars = github_config.get("min_stars", 10)
    max_pages = github_config.get("max_pages", 3)
    exclude_keywords = github_config.get("exclude_keywords", [])
    
    logger.info(f"搜索关键词: {keywords}")
    logger.info(f"最少星标数: {min_stars}")
    logger.info(f"最大页数: {max_pages}")
    if exclude_keywords:
        logger.info(f"排除关键词: {exclude_keywords}")
    
    # 创建 GitHubSearcher 实例
    github_searcher = GitHubSearcher(token)
    
    # 调用 GitHubSearcher 的搜索方法
    all_repos = github_searcher.search_ai_agent_repos(
        additional_keywords=keywords,
        min_stars=min_stars,
        max_pages=max_pages,
        exclude_keywords=exclude_keywords
    )
    
    total_found = len(all_repos) if all_repos else 0
    logger.info(f"搜索完成，总共找到 {total_found} 个仓库")
    
    # 如果没找到仓库，提前返回
    if total_found == 0:
        logger.warning("没有找到匹配的仓库")
        return None
    
    # 生成输出文件名
    if not output_file:
        # 确保 temp 目录存在
        temp_dir = os.path.join(project_root, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(temp_dir, f"ai_agent_repos_{timestamp}.json")
    
    # 打印前 5 个仓库的简要信息
    logger.info("前 5 个仓库预览:")
    for i, repo in enumerate(all_repos[:5]):
        logger.info(f"{i+1}. {repo.get('full_name')} - ⭐ {repo.get('stargazers_count')} - {repo.get('description', '')[:100]}")
    
    # 保存到文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_repos, f, indent=2, ensure_ascii=False)
        logger.info(f"成功将 {total_found} 个仓库数据保存到: {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"保存数据到文件时出错: {str(e)}")
        return None

def main():
    """主函数"""
    logger.info("===== AIAgentTracker: 步骤 1 - 搜索 GitHub 仓库 =====")
    
    parser = argparse.ArgumentParser(description="搜索 GitHub 上的 AI Agent 仓库")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--output", help="输出文件路径")
    parser.add_argument("--token", help="GitHub 令牌")
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config) if args.config else load_config()
    
    # 执行搜索
    output_file = search_ai_agent_repos(
        token=args.token,
        config=config,
        output_file=args.output
    )
    
    if output_file:
        logger.info(f"搜索操作成功完成！结果已保存到: {output_file}")
    else:
        logger.error("搜索操作失败")
        sys.exit(1)

if __name__ == "__main__":
    main()