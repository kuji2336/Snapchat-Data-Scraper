import requests
import re
import json
import datetime

def get_snapchat_data(username):
    """Fetch and parse Snapchat user data"""
    url = f"https://www.snapchat.com/add/{username}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    json_regex = r'<script[^>]+type="application/json"[^>]*>(.*?)</script>'
    
    try:
        response = requests.get(url, timeout=30, headers=headers).text
        
        # Extract JSON data from the page
        json_matches = re.findall(json_regex, response, re.DOTALL)
        
        if json_matches:
            json_data = json.loads(json_matches[0])
            
            # Load config paths
            with open("config.json", "r") as config_file:
                config_data = json.load(config_file)
            json_data_paths = config_data.get("json_data_paths", {})
            
            # Extract relevant data
            extracted_data = {
                "username": username,
                "fetched_at": datetime.datetime.now().isoformat(),
                "user_info": {},
                "stories": [],
                "curated_highlights": [],
                "spotlights": [],
                "lenses": [],
                "statistics": {}
            }
            
            # Helper function to get nested values
            def get_value(data, path):
                try:
                    for key in path.split('.'):
                        data = data.get(key, {})
                    return data
                except:
                    return None
            
            # Extract user info
            user_paths = {
                "pageType": "pageType",
                "pageTitle": "pageTitle",
                "pageDescription": "pageDescription",
                "username": "username",
                "displayName": "displayName",
                "subscriberCount": "subscriberCount",
                "bio": "bio",
                "websiteUrl": "websiteUrl"
            }
            
            for key, path_key in user_paths.items():
                if path_key in json_data_paths:
                    value = get_value(json_data, json_data_paths[path_key])
                    if value:
                        extracted_data["user_info"][key] = value
            
            # Extract stories
            story_path = json_data_paths.get("story")
            if story_path:
                stories = get_value(json_data, story_path)
                if stories and isinstance(stories, list):
                    extracted_data["stories"] = stories
            
            # Extract curated highlights
            highlights_path = json_data_paths.get("curatedHighlights")
            if highlights_path:
                highlights = get_value(json_data, highlights_path)
                if highlights:
                    extracted_data["curated_highlights"] = highlights
            
            # Extract spotlights
            spotlights_path = json_data_paths.get("spotlightHighlights")
            if spotlights_path:
                spotlights = get_value(json_data, spotlights_path)
                if spotlights:
                    extracted_data["spotlights"] = spotlights
            
            # Extract lenses
            lenses_path = json_data_paths.get("lenses")
            if lenses_path:
                lenses = get_value(json_data, lenses_path)
                if lenses:
                    extracted_data["lenses"] = lenses
            
            # Calculate statistics
            extracted_data["statistics"] = {
                "total_stories": len(extracted_data["stories"]),
                "total_curated_highlights": len(extracted_data["curated_highlights"]) if isinstance(extracted_data["curated_highlights"], list) else 0,
                "total_spotlights": len(extracted_data["spotlights"]) if isinstance(extracted_data["spotlights"], list) else 0,
                "total_lenses": len(extracted_data["lenses"]) if isinstance(extracted_data["lenses"], list) else 0
            }
            
            return extracted_data
        else:
            return {"error": "No JSON data found in response"}
            
    except Exception as e:
        return {"error": str(e)}

def save_to_json(data, filename):
    """Save data to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Data saved to {filename}")

if __name__ == "__main__":
    import sys
    
    username = sys.argv[1] if len(sys.argv) > 1 else "realmadrid"
    output_file = sys.argv[2] if len(sys.argv) > 2 else f"{username}_data.json"
    
    print(f"🔍 Fetching data for @{username}...")
    data = get_snapchat_data(username)
    
    if "error" not in data:
        save_to_json(data, output_file)
        print(f"\n📊 Summary:")
        print(f"   - Stories: {data['statistics']['total_stories']}")
        print(f"   - Curated Highlights: {data['statistics']['total_curated_highlights']}")
        print(f"   - Spotlights: {data['statistics']['total_spotlights']}")
        print(f"   - Lenses: {data['statistics']['total_lenses']}")
    else:
        print(f"❌ Error: {data['error']}")
