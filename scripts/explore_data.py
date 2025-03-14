import json
import sys
import argparse

def explore_data(file_path):
    """Explore a JSON data file and print summary information"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"File: {file_path}")
    print(f"Number of repositories: {len(data)}")
    
    if not data:
        print("No data found in file.")
        return
    
    print("\nData structure sample (first item):")
    first_item = data[0]
    for key, value in first_item.items():
        if isinstance(value, str) and len(value) > 100:
            value = value[:100] + "..."
        print(f"  {key}: {value}")
    
    # Get some statistics if stars field exists
    if "stars" in first_item or "stargazers_count" in first_item:
        star_key = "stars" if "stars" in first_item else "stargazers_count"
        stars = [repo.get(star_key, 0) for repo in data]
        print("\nStar statistics:")
        print(f"  Total stars: {sum(stars)}")
        print(f"  Average stars: {sum(stars)/len(stars):.2f}")
        print(f"  Min stars: {min(stars)}")
        print(f"  Max stars: {max(stars)}")
        
        print("\nTop 10 repositories by stars:")
        sorted_data = sorted(data, key=lambda x: x.get(star_key, 0), reverse=True)
        for i, repo in enumerate(sorted_data[:10]):
            name = repo.get("full_name", repo.get("name", "Unknown"))
            stars = repo.get(star_key, 0)
            print(f"  {i+1}. {name} - ⭐ {stars}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Explore a JSON data file")
    parser.add_argument("file", help="Path to JSON data file to explore")
    
    args = parser.parse_args()
    explore_data(args.file)