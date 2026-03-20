import requests
import re
import json
import datetime
import hashlib
import os
import concurrent.futures
from dotenv import load_dotenv

load_dotenv()

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

SNAPCHAT_BASE_URL = "https://www.snapchat.com/add/"
JSON_REGEX = r'<script[^>]+type="application/json"[^>]*>(.*?)</script>'

# Webshare rotating proxy configuration
PROXY_CONFIG = {
    "host": "p.webshare.io",
    "port": "80",
    "username": "jdprtnas-rotate",
    "password": os.getenv("WEBSHARE_PASS", ""),
}


def _get_proxy_url():
    if not PROXY_CONFIG["password"]:
        return None
    return f"http://{PROXY_CONFIG['username']}:{PROXY_CONFIG['password']}@{PROXY_CONFIG['host']}:{PROXY_CONFIG['port']}"


def _get_proxies():
    proxy_url = _get_proxy_url()
    if not proxy_url:
        return None
    return {"http": proxy_url, "https": proxy_url}


def _load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f).get("json_data_paths", {})


def _get_value(json_data, paths, data_name, placeholder=None):
    path = paths.get(data_name)
    if not path:
        return None
    data = json_data
    for key in path.split("."):
        try:
            match = re.match(r"\{(.*?)\}", key)
            if match:
                data = data[placeholder]
            else:
                data = data.get(key, {})
        except (AttributeError, TypeError, IndexError, KeyError):
            return None
    return data if data != {} else None


def _ms_to_duration_str(milliseconds):
    seconds = int(milliseconds) / 1000
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m{secs}s"


def _timestamp_to_str(ts):
    try:
        return datetime.datetime.utcfromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError, OSError):
        return None


def fetch_raw_data(username: str, timeout: int = 30) -> dict:
    """Fetch and parse the raw JSON data from a Snapchat profile page."""
    url = SNAPCHAT_BASE_URL + username
    proxies = _get_proxies()
    try:
        response = requests.get(url, timeout=timeout, headers=HEADERS, proxies=proxies).text
    except requests.exceptions.Timeout:
        raise TimeoutError(f"Request timed out after {timeout}s for user '{username}'")
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Failed to fetch data for user '{username}': {str(e)}")

    match = re.search(JSON_REGEX, response, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON data found in Snapchat response for user '{username}'")

    try:
        json_data = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON data: {str(e)}")

    return json_data


def get_user_info(json_data: dict) -> dict:
    """Extract user profile information from raw data."""
    paths = _load_config()

    page_type = _get_value(json_data, paths, "pageType")
    page_title = _get_value(json_data, paths, "pageTitle")

    if not page_title:
        return {"error": "User does not exist"}

    is_private = page_type != 18

    result = {
        "page_title": page_title,
        "page_description": _get_value(json_data, paths, "pageDescription"),
        "is_private": is_private,
    }

    if not is_private:
        username = _get_value(json_data, paths, "username")
        badge_val = _get_value(json_data, paths, "badge")
        badge_map = {1: "Creator", 3: "Public Figure"}
        badge = badge_map.get(badge_val, "None")

        profile_pic = _get_value(json_data, paths, "profilePictureUrl") or ""
        profile_pic = re.sub(r'90(?=_FM(png|jpeg|gif)$)', "640", profile_pic)

        result.update({
            "username": username,
            "badge": badge,
            "profile_picture_url": profile_pic,
            "background_picture_url": _get_value(json_data, paths, "squareHeroImageUrl"),
            "subscriber_count": _get_value(json_data, paths, "subscriberCount"),
            "bio": _get_value(json_data, paths, "bio"),
            "website_url": _get_value(json_data, paths, "websiteUrl") or None,
            "snapcode_image_url": _get_value(json_data, paths, "snapcodeImageUrl"),
        })
    else:
        result.update({
            "username": _get_value(json_data, paths, "private_username"),
            "display_name": _get_value(json_data, paths, "displayName"),
            "avatar_image_url": _get_value(json_data, paths, "avatarImageUrl"),
            "background_image_url": _get_value(json_data, paths, "backgroundImageUrl"),
            "snapcode_image_url": _get_value(json_data, paths, "private_snapcodeImageUrl"),
        })

    return result


def get_stories(json_data: dict) -> list:
    """Extract stories from raw data."""
    paths = _load_config()
    story = _get_value(json_data, paths, "story")

    if not story or not isinstance(story, list):
        return []

    MEDIA_TYPES = {0: "image", 1: "video"}
    results = []

    for snap in story:
        try:
            results.append({
                "snap_index": snap.get("snapIndex"),
                "media_url": snap.get("snapUrls", {}).get("mediaUrl"),
                "preview_url": (snap.get("snapUrls", {}).get("mediaPreviewUrl") or {}).get("value"),
                "upload_date": _timestamp_to_str(snap.get("timestampInSec", {}).get("value")),
                "media_type": MEDIA_TYPES.get(snap.get("snapMediaType"), "unknown"),
            })
        except (AttributeError, TypeError):
            continue

    return results


def get_curated_highlights(json_data: dict) -> list:
    """Extract curated highlights from raw data."""
    paths = _load_config()

    has_highlights = _get_value(json_data, paths, "hasCuratedHighlights")
    if has_highlights is False:
        return []

    highlights = _get_value(json_data, paths, "curatedHighlights")
    if not highlights or not isinstance(highlights, list):
        return []

    results = []
    for highlight in highlights:
        try:
            title = highlight.get("storyTitle", {}).get("value", "Untitled")
            snaps = []
            for story in highlight.get("snapList", []):
                snap_data = {
                    "snap_index": story.get("snapIndex"),
                    "media_url": story.get("snapUrls", {}).get("mediaUrl"),
                    "upload_date": _timestamp_to_str(
                        story.get("timestampInSec", {}).get("value")
                    ),
                }
                snaps.append(snap_data)

            results.append({
                "title": title,
                "snap_count": len(snaps),
                "snaps": snaps,
            })
        except (AttributeError, TypeError):
            continue

    return results


def get_spotlights(json_data: dict) -> dict:
    """Extract spotlights from raw data."""
    paths = _load_config()

    has_spotlights = _get_value(json_data, paths, "spotlightHighlights")
    if not has_spotlights:
        return {"spotlights": [], "total_engagement": 0, "hashtag_rankings": []}

    spotlight_highlights = has_spotlights
    if not isinstance(spotlight_highlights, list):
        return {"spotlights": [], "total_engagement": 0, "hashtag_rankings": []}

    results = []
    total_engagement = 0
    hashtag_counts = {}

    for count, spotlight in enumerate(spotlight_highlights):
        try:
            name = _get_value(json_data, paths, "spotlightName", count)
            duration_ms = _get_value(json_data, paths, "spotlightDuration", count)
            upload_date_ms = _get_value(json_data, paths, "spotlightUploadDate", count)
            engagement = _get_value(json_data, paths, "spotlightEngagementStats", count)
            hashtags_raw = _get_value(json_data, paths, "spotlightHashtags", count) or []

            if engagement:
                total_engagement += int(engagement)

            hashtags = []
            for tag in hashtags_raw:
                hashtags.append(tag)
                hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1

            snaps = []
            for story in spotlight.get("snapList", []):
                snaps.append({
                    "snap_index": story.get("snapIndex"),
                    "media_url": story.get("snapUrls", {}).get("mediaUrl"),
                })

            results.append({
                "name": name,
                "thumbnail_url": (spotlight.get("thumbnailUrl") or {}).get("value"),
                "duration": _ms_to_duration_str(duration_ms) if duration_ms else None,
                "duration_ms": int(duration_ms) if duration_ms else None,
                "upload_date": _timestamp_to_str(int(upload_date_ms) / 1000) if upload_date_ms else None,
                "engagement_views": int(engagement) if engagement else 0,
                "hashtags": hashtags,
                "snaps": snaps,
            })
        except (TypeError, ValueError, AttributeError):
            continue

    top_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "spotlights": results,
        "total_engagement": total_engagement,
        "hashtag_rankings": [{"tag": tag, "count": cnt} for tag, cnt in top_hashtags],
    }


def get_lenses(json_data: dict) -> list:
    """Extract lenses from raw data."""
    paths = _load_config()
    lenses = _get_value(json_data, paths, "lenses")

    if not lenses or not isinstance(lenses, list):
        return []

    results = []
    for lens in lenses:
        try:
            results.append({
                "name": lens.get("lensName"),
                "is_official": lens.get("isOfficialSnapLens", False),
                "preview_video_url": lens.get("lensPreviewVideoUrl"),
            })
        except (AttributeError, TypeError):
            continue

    return results


def _process_bitmoji_version(base_url, end_url, version, timeout):
    try:
        final_url = "-".join(["_".join([base_url, str(version)]), end_url])
        md5_hash = hashlib.md5()
        proxies = _get_proxies()
        response = requests.get(final_url, timeout=timeout, headers=HEADERS, proxies=proxies)
        for data in response.iter_content(8192):
            md5_hash.update(data)
        return md5_hash.hexdigest()
    except requests.exceptions.Timeout:
        return None


def get_bitmojis(json_data: dict, timeout: int = 30, threads: int = 10) -> list:
    """Extract bitmoji versions for private users."""
    paths = _load_config()
    avatar_url = _get_value(json_data, paths, "avatarImageUrl")

    if not avatar_url or not isinstance(avatar_url, str):
        return []

    try:
        base_url = avatar_url.split("_")[0]
        last_version = avatar_url.split("_")[1].split("-")[0]
        end_url = "-".join(avatar_url.split("-")[4:])
    except (IndexError, ValueError):
        return []

    result = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [
            executor.submit(_process_bitmoji_version, base_url, end_url, i, timeout)
            for i in reversed(range(1, int(last_version) + 1))
        ]
        for future in concurrent.futures.as_completed(futures):
            md5_hash = future.result()
            if md5_hash:
                result.add(md5_hash)

    return list(result)


def get_stats(json_data: dict) -> dict:
    """Compute summary statistics from raw data."""
    stories = get_stories(json_data)
    highlights = get_curated_highlights(json_data)
    spotlight_data = get_spotlights(json_data)
    lenses = get_lenses(json_data)

    total_highlight_snaps = sum(h.get("snap_count", 0) for h in highlights)
    total_spotlight_snaps = sum(len(s.get("snaps", [])) for s in spotlight_data["spotlights"])

    total_spotlight_duration_ms = sum(
        s.get("duration_ms", 0) or 0 for s in spotlight_data["spotlights"]
    )
    total_minutes = int(total_spotlight_duration_ms / 1000 // 60)
    total_seconds = int(total_spotlight_duration_ms / 1000 % 60)

    return {
        "total_stories": len(stories),
        "total_curated_highlights": len(highlights),
        "total_highlight_snaps": total_highlight_snaps,
        "total_spotlights": len(spotlight_data["spotlights"]),
        "total_spotlight_snaps": total_spotlight_snaps,
        "total_spotlight_duration": f"{total_minutes}m{total_seconds}s",
        "total_spotlight_duration_ms": total_spotlight_duration_ms,
        "total_spotlight_engagement": spotlight_data["total_engagement"],
        "total_lenses": len(lenses),
        "top_hashtags": spotlight_data["hashtag_rankings"],
    }


def get_heatmap_data(json_data: dict) -> dict:
    """Generate heatmap data (day of week × hour) from upload dates."""
    stories = get_stories(json_data)
    spotlight_data = get_spotlights(json_data)

    dates = []
    for story in stories:
        if story.get("upload_date"):
            dates.append(story["upload_date"])
    for spotlight in spotlight_data["spotlights"]:
        if spotlight.get("upload_date"):
            dates.append(spotlight["upload_date"])

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    matrix = {day: {str(h): 0 for h in range(24)} for day in days}

    for date_str in dates:
        try:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            day_name = days[dt.weekday()]
            hour = str(dt.hour)
            matrix[day_name][hour] += 1
        except (ValueError, IndexError):
            continue

    return {
        "total_data_points": len(dates),
        "heatmap": matrix,
    }


def get_all(username: str, timeout: int = 30, threads: int = 10) -> dict:
    """Fetch everything for a given username in one call."""
    json_data = fetch_raw_data(username, timeout)
    user_info = get_user_info(json_data)

    if user_info.get("error"):
        return {"error": user_info["error"]}

    result = {
        "username": username,
        "fetched_at": datetime.datetime.utcnow().isoformat() + "Z",
        "user_info": user_info,
    }

    if user_info.get("is_private"):
        result["bitmojis"] = get_bitmojis(json_data, timeout, threads)
        result["note"] = "User is private. Only bitmoji data is available."
    else:
        result["stories"] = get_stories(json_data)
        result["curated_highlights"] = get_curated_highlights(json_data)
        result["spotlights"] = get_spotlights(json_data)
        result["lenses"] = get_lenses(json_data)
        result["stats"] = get_stats(json_data)
        result["heatmap"] = get_heatmap_data(json_data)

    return result
