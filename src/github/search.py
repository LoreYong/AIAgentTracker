import time
import requests
from datetime import datetime
from ..utils.logger import setup_logger
from ..utils.network import create_session, load_proxy_config

logger = setup_logger("github_search")

class GitHubSearcher:
    """Search GitHub repositories based on keywords and filters"""
    
    def __init__(self, token=None):
        """Initialize the GitHub searcher with authentication token"""
        self.token = token
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
        
        self.base_url = "https://api.github.com"
        self.search_url = f"{self.base_url}/search/repositories"
        
        # 创建会话并加载代理配置
        self.session, self.proxies = create_session()
        
        # 如果使用代理，记录信息
        if self.proxies:
            logger.info(f"使用代理配置: {self.proxies}")
    
    def search_repositories(self, query, sort="stars", order="desc", per_page=100, max_pages=10):
        """
        Search for repositories based on query string
        
        Args:
            query (str): GitHub search query
            sort (str): Sorting criteria (stars, forks, updated)
            order (str): Sort order (asc, desc)
            per_page (int): Results per page (max 100)
            max_pages (int): Maximum number of pages to retrieve
            
        Returns:
            list: List of repository data dictionaries
        """
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": per_page,
            "page": 1
        }
        
        all_repos = []
        for page in range(1, max_pages + 1):
            params["page"] = page
            logger.info(f"Searching repositories: {query} (page {page}/{max_pages})")
            
            try:
                response = self.session.get(
                    self.search_url, 
                    headers=self.headers, 
                    params=params,
                    proxies=self.proxies,
                    timeout=30  # 30秒超时
                )
                response.raise_for_status()
                
                data = response.json()
                repos = data.get("items", [])
                
                # Break if no more results
                if not repos:
                    break
                
                all_repos.extend(repos)
                
                # Check for rate limiting
                remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
                if remaining < 5:
                    reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                    sleep_time = reset_time - time.time() + 5  # Add 5 seconds buffer
                    if sleep_time > 0:
                        logger.warning(f"Rate limit almost reached. Sleeping for {sleep_time:.2f} seconds")
                        time.sleep(sleep_time)
                
                # Add a small delay between requests to be nice to GitHub API
                time.sleep(2)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error searching repositories: {str(e)}")
                logger.info("Waiting 5 seconds before continuing...")
                time.sleep(5)  # 错误后等待时间增加
                continue  # 继续尝试下一页，而不是中断
        
        logger.info(f"Found {len(all_repos)} repositories matching the query")
        return all_repos
    
    def search_ai_agent_repos(self, additional_keywords=None, min_stars=10, max_pages=10, exclude_keywords=None):
        """
        Search specifically for AI Agent related repositories
        
        Args:
            additional_keywords (list): Additional keywords to include in search
            min_stars (int): Minimum stars for repositories
            max_pages (int): Maximum number of pages to search
            exclude_keywords (list): Keywords to exclude from search
            
        Returns:
            list: List of AI Agent repositories
        """
        all_repos = []
        found_repo_ids = set()  # 用于去重
        
        # 构建几个更小的查询
        queries = []
        
        # 查询1: 使用主题标签搜索
        queries.append(f"topic:ai-agent stars:>={min_stars}")
        queries.append(f"topic:ai-agents stars:>={min_stars}")
        queries.append(f"topic:aiagent stars:>={min_stars}")
        
        # 查询2: 使用名称和描述搜索核心术语
        queries.append(f"\"AI agent\" in:name,description stars:>={min_stars}")
        
        # 查询3: 使用 README 搜索核心术语
        queries.append(f"\"AI agent\" in:readme stars:>={min_stars}")
        
        # 添加额外关键词查询
        if additional_keywords and isinstance(additional_keywords, list):
            for keyword in additional_keywords:
                if keyword.lower() != "ai agent":  # 避免重复
                    queries.append(f"\"{keyword}\" in:name,description stars:>={min_stars}")
        
        # 执行多个查询并合并结果
        logger.info(f"将执行 {len(queries)} 个单独的查询以获取完整结果")
        
        for i, query in enumerate(queries):
            logger.info(f"执行查询 {i+1}/{len(queries)}: {query}")
            
            # 处理排除关键词
            exclude_query = query
            if exclude_keywords and isinstance(exclude_keywords, list):
                for keyword in exclude_keywords:
                    exclude_query += f" NOT \"{keyword}\""
            
            # 执行搜索
            page_limit = max(1, max_pages // len(queries))  # 分配页数给每个查询
            repos = self.search_repositories(exclude_query, max_pages=page_limit)
            
            # 合并结果并去重
            for repo in repos:
                if repo.get('id') not in found_repo_ids:
                    all_repos.append(repo)
                    found_repo_ids.add(repo.get('id'))
        
        # 按星标数排序
        all_repos.sort(key=lambda x: x.get('stargazers_count', 0), reverse=True)
        
        logger.info(f"所有查询完成，共找到 {len(all_repos)} 个唯一仓库")
        return all_repos
    
    def get_trending_ai_agents(self, days=7, min_stars=5, max_results=50):
        """
        Get trending AI Agent repositories created or updated recently
        
        Args:
            days (int): Look for repos updated within this many days
            min_stars (int): Minimum stars
            max_results (int): Maximum results to return
            
        Returns:
            list: List of trending AI Agent repositories
        """
        date_cutoff = (datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        
        query = f"(topic:ai-agent OR \"AI agent\" in:name,description,readme) stars:>={min_stars} created:>={date_cutoff}"
        
        # Calculate how many pages to retrieve
        pages_needed = max(1, min(10, max_results // 100 + 1))
        
        repos = self.search_repositories(query, sort="stars", max_pages=pages_needed)
        
        # Limit to max_results
        return repos[:max_results]
    
    def get_rate_limit_status(self):
        """
        Get current GitHub API rate limit status
        
        Returns:
            dict: Rate limit information or None if request fails
        """
        try:
            response = self.session.get(
                f"{self.base_url}/rate_limit",
                headers=self.headers,
                proxies=self.proxies,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            return None