from fastapi import APIRouter, HTTPException, Query
from api.services import snapchat_service
from api.models.schemas import (
    UserInfoResponse,
    StoriesResponse,
    HighlightsResponse,
    SpotlightsResponse,
    LensesResponse,
    BitmojisResponse,
    StatsResponse,
    HeatmapResponse,
    AllDataResponse,
    ErrorResponse,
)

router = APIRouter(prefix="/api/v1/user", tags=["Snapchat OSINT"])


def _fetch_data(username: str, timeout: int):
    try:
        return snapchat_service.fetch_raw_data(username, timeout)
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{username}",
    response_model=UserInfoResponse,
    responses={404: {"model": ErrorResponse}, 502: {"model": ErrorResponse}, 504: {"model": ErrorResponse}},
    summary="Get user profile information",
    description="Fetches public or private profile information for a Snapchat user including username, badge, subscriber count, bio, profile picture, and more.",
)
def get_user_info(
    username: str,
    timeout: int = Query(30, ge=1, le=120, description="Request timeout in seconds"),
):
    json_data = _fetch_data(username, timeout)
    user_info = snapchat_service.get_user_info(json_data)
    if user_info.get("error"):
        raise HTTPException(status_code=404, detail=user_info["error"])
    return {"username": username, "user_info": user_info}


@router.get(
    "/{username}/stories",
    response_model=StoriesResponse,
    responses={404: {"model": ErrorResponse}, 502: {"model": ErrorResponse}, 504: {"model": ErrorResponse}},
    summary="Get user stories",
    description="Fetches current active stories for a Snapchat user. Each story includes media URL, preview URL, upload date, and media type (image/video). Only available for public profiles.",
)
def get_stories(
    username: str,
    timeout: int = Query(30, ge=1, le=120, description="Request timeout in seconds"),
):
    json_data = _fetch_data(username, timeout)
    user_info = snapchat_service.get_user_info(json_data)
    if user_info.get("is_private"):
        raise HTTPException(status_code=403, detail="User is private. Stories are not available.")
    stories = snapchat_service.get_stories(json_data)
    return {"username": username, "user_info": user_info, "total_stories": len(stories), "stories": stories}


@router.get(
    "/{username}/highlights",
    response_model=HighlightsResponse,
    responses={404: {"model": ErrorResponse}, 502: {"model": ErrorResponse}, 504: {"model": ErrorResponse}},
    summary="Get curated highlights",
    description="Fetches curated highlight stories for a Snapchat user. Each highlight group has a title and contains multiple snaps with media URLs and upload dates.",
)
def get_highlights(
    username: str,
    timeout: int = Query(30, ge=1, le=120, description="Request timeout in seconds"),
):
    json_data = _fetch_data(username, timeout)
    user_info = snapchat_service.get_user_info(json_data)
    if user_info.get("is_private"):
        raise HTTPException(status_code=403, detail="User is private. Highlights are not available.")
    highlights = snapchat_service.get_curated_highlights(json_data)
    return {"username": username, "user_info": user_info, "total_highlights": len(highlights), "highlights": highlights}


@router.get(
    "/{username}/spotlights",
    response_model=SpotlightsResponse,
    responses={404: {"model": ErrorResponse}, 502: {"model": ErrorResponse}, 504: {"model": ErrorResponse}},
    summary="Get spotlights",
    description="Fetches spotlight videos for a Snapchat user. Includes name, thumbnail, duration, upload date, engagement stats (view count), hashtags, and snap media URLs. Also returns total engagement and top 10 hashtag rankings.",
)
def get_spotlights(
    username: str,
    timeout: int = Query(30, ge=1, le=120, description="Request timeout in seconds"),
):
    json_data = _fetch_data(username, timeout)
    user_info = snapchat_service.get_user_info(json_data)
    if user_info.get("is_private"):
        raise HTTPException(status_code=403, detail="User is private. Spotlights are not available.")
    spotlight_data = snapchat_service.get_spotlights(json_data)
    return {
        "username": username,
        "user_info": user_info,
        "total_spotlights": len(spotlight_data["spotlights"]),
        "total_engagement": spotlight_data["total_engagement"],
        "hashtag_rankings": spotlight_data["hashtag_rankings"],
        "spotlights": spotlight_data["spotlights"],
    }


@router.get(
    "/{username}/lenses",
    response_model=LensesResponse,
    responses={404: {"model": ErrorResponse}, 502: {"model": ErrorResponse}, 504: {"model": ErrorResponse}},
    summary="Get lenses",
    description="Fetches Snapchat lenses/filters created by or associated with a user. Includes lens name, whether it is official, and preview video URL.",
)
def get_lenses(
    username: str,
    timeout: int = Query(30, ge=1, le=120, description="Request timeout in seconds"),
):
    json_data = _fetch_data(username, timeout)
    user_info = snapchat_service.get_user_info(json_data)
    if user_info.get("is_private"):
        raise HTTPException(status_code=403, detail="User is private. Lenses are not available.")
    lenses = snapchat_service.get_lenses(json_data)
    return {"username": username, "user_info": user_info, "total_lenses": len(lenses), "lenses": lenses}


@router.get(
    "/{username}/bitmojis",
    response_model=BitmojisResponse,
    responses={404: {"model": ErrorResponse}, 502: {"model": ErrorResponse}, 504: {"model": ErrorResponse}},
    summary="Get bitmoji versions",
    description="Fetches unique bitmoji versions for a private Snapchat user. Returns MD5 hashes of each unique bitmoji image found. Uses multi-threading for faster retrieval.",
)
def get_bitmojis(
    username: str,
    timeout: int = Query(30, ge=1, le=120, description="Request timeout in seconds"),
    threads: int = Query(10, ge=1, le=50, description="Number of concurrent threads for bitmoji fetching"),
):
    json_data = _fetch_data(username, timeout)
    user_info = snapchat_service.get_user_info(json_data)
    if not user_info.get("is_private"):
        raise HTTPException(status_code=400, detail="Bitmoji endpoint is only available for private users.")
    bitmojis = snapchat_service.get_bitmojis(json_data, timeout, threads)
    return {"username": username, "user_info": user_info, "total_bitmojis": len(bitmojis), "bitmoji_hashes": bitmojis}


@router.get(
    "/{username}/stats",
    response_model=StatsResponse,
    responses={404: {"model": ErrorResponse}, 502: {"model": ErrorResponse}, 504: {"model": ErrorResponse}},
    summary="Get account statistics",
    description="Fetches summary statistics for a Snapchat user including total counts for stories, highlights, spotlights, lenses, total engagement, total duration, and top hashtags.",
)
def get_stats(
    username: str,
    timeout: int = Query(30, ge=1, le=120, description="Request timeout in seconds"),
):
    json_data = _fetch_data(username, timeout)
    user_info = snapchat_service.get_user_info(json_data)
    if user_info.get("is_private"):
        raise HTTPException(status_code=403, detail="User is private. Stats are not available.")
    stats = snapchat_service.get_stats(json_data)
    return {"username": username, "user_info": user_info, "stats": stats}


@router.get(
    "/{username}/heatmap",
    response_model=HeatmapResponse,
    responses={404: {"model": ErrorResponse}, 502: {"model": ErrorResponse}, 504: {"model": ErrorResponse}},
    summary="Get upload time heatmap data",
    description="Returns upload time distribution data as a day-of-week × hour matrix. Data is derived from stories and spotlight upload timestamps. Useful for analyzing posting patterns.",
)
def get_heatmap(
    username: str,
    timeout: int = Query(30, ge=1, le=120, description="Request timeout in seconds"),
):
    json_data = _fetch_data(username, timeout)
    user_info = snapchat_service.get_user_info(json_data)
    if user_info.get("is_private"):
        raise HTTPException(status_code=403, detail="User is private. Heatmap data is not available.")
    heatmap_data = snapchat_service.get_heatmap_data(json_data)
    return {"username": username, "user_info": user_info, "heatmap_data": heatmap_data}


@router.get(
    "/{username}/all",
    response_model=AllDataResponse,
    responses={404: {"model": ErrorResponse}, 502: {"model": ErrorResponse}, 504: {"model": ErrorResponse}},
    summary="Get all data",
    description="Fetches all available data for a Snapchat user in a single request. For public profiles: user info, stories, highlights, spotlights, lenses, stats, and heatmap. For private profiles: user info and bitmojis.",
)
def get_all(
    username: str,
    timeout: int = Query(30, ge=1, le=120, description="Request timeout in seconds"),
    threads: int = Query(10, ge=1, le=50, description="Number of concurrent threads for bitmoji fetching"),
):
    try:
        data = snapchat_service.get_all(username, timeout, threads)
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if data.get("error"):
        raise HTTPException(status_code=404, detail=data["error"])

    # Reshape spotlights for response model
    if "spotlights" in data and isinstance(data["spotlights"], dict):
        spotlight_raw = data["spotlights"]
        data["spotlights"] = {
            "username": username,
            "total_spotlights": len(spotlight_raw["spotlights"]),
            "total_engagement": spotlight_raw["total_engagement"],
            "hashtag_rankings": spotlight_raw["hashtag_rankings"],
            "spotlights": spotlight_raw["spotlights"],
        }

    return data
