# test_github_connection.py
import requests

def test_github_connection():
    print("Testing GitHub API connection...")
    try:
        proxies = {
            "http": "http://localhost:7890",
            "https": "http://localhost:7890"
        }
        response = requests.get("https://api.github.com/rate_limit", timeout=10,proxies =proxies)
        response.raise_for_status()
        print(f"Connection successful! Status code: {response.status_code}")
        data = response.json()
        print(f"Rate limit remaining: {data['resources']['core']['remaining']}")
        return True
    except Exception as e:
        print(f"Connection error: {str(e)}")
        return False

if __name__ == "__main__":
    test_github_connection()