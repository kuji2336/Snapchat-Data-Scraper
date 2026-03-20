from pydantic import BaseModel, Field
from typing import Optional, List, Dict


class UserInfo(BaseModel):
    page_title: Optional[str] = Field(None, description="Page title from Snapchat profile")
    page_description: Optional[str] = Field(None, description="Page meta description")
    is_private: bool = Field(..., description="Whether the profile is private")
    username: Optional[str] = Field(None, description="Snapchat username")
    badge: Optional[str] = Field(None, description="Badge type: Creator, Public Figure, or None")
    profile_picture_url: Optional[str] = Field(None, description="Profile picture URL (640px)")
    background_picture_url: Optional[str] = Field(None, description="Background/hero image URL")
    subscriber_count: Optional[str] = Field(None, description="Subscriber count as string")
    bio: Optional[str] = Field(None, description="User bio text")
    website_url: Optional[str] = Field(None, description="User's website URL")
    snapcode_image_url: Optional[str] = Field(None, description="Snapcode image URL")
    display_name: Optional[str] = Field(None, description="Display name (private profiles only)")
    avatar_image_url: Optional[str] = Field(None, description="Avatar/bitmoji URL (private profiles only)")
    background_image_url: Optional[str] = Field(None, description="Background image (private profiles only)")
    error: Optional[str] = Field(None, description="Error message if user not found")


class UserInfoResponse(BaseModel):
    username: str
    user_info: UserInfo


class Story(BaseModel):
    snap_index: Optional[int] = Field(None, description="Index of the snap in the story")
    media_url: Optional[str] = Field(None, description="Direct media URL")
    preview_url: Optional[str] = Field(None, description="Preview/thumbnail URL")
    upload_date: Optional[str] = Field(None, description="Upload date in YYYY-MM-DD HH:MM:SS format (UTC)")
    media_type: Optional[str] = Field(None, description="Media type: 'image' or 'video'")


class StoriesResponse(BaseModel):
    username: str
    total_stories: int
    stories: List[Story]


class HighlightSnap(BaseModel):
    snap_index: Optional[int] = Field(None, description="Index of the snap")
    media_url: Optional[str] = Field(None, description="Direct media URL")
    upload_date: Optional[str] = Field(None, description="Upload date (UTC)")


class CuratedHighlight(BaseModel):
    title: str = Field(..., description="Highlight story title")
    snap_count: int = Field(..., description="Number of snaps in this highlight")
    snaps: List[HighlightSnap]


class HighlightsResponse(BaseModel):
    username: str
    total_highlights: int
    highlights: List[CuratedHighlight]


class SpotlightSnap(BaseModel):
    snap_index: Optional[int] = Field(None, description="Index of the snap")
    media_url: Optional[str] = Field(None, description="Direct media URL")


class HashtagRanking(BaseModel):
    tag: str = Field(..., description="Hashtag text")
    count: int = Field(..., description="Number of occurrences")


class Spotlight(BaseModel):
    name: Optional[str] = Field(None, description="Spotlight name/title")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail image URL")
    duration: Optional[str] = Field(None, description="Duration as human-readable string (e.g. '1m30s')")
    duration_ms: Optional[int] = Field(None, description="Duration in milliseconds")
    upload_date: Optional[str] = Field(None, description="Upload date (UTC)")
    engagement_views: int = Field(0, description="View count / engagement stats")
    hashtags: List[str] = Field(default_factory=list, description="Associated hashtags")
    snaps: List[SpotlightSnap] = Field(default_factory=list, description="Snap media within this spotlight")


class SpotlightsResponse(BaseModel):
    username: str
    total_spotlights: int
    total_engagement: int
    hashtag_rankings: List[HashtagRanking]
    spotlights: List[Spotlight]


class Lens(BaseModel):
    name: Optional[str] = Field(None, description="Lens name/title")
    is_official: bool = Field(False, description="Whether this is an official Snap lens")
    preview_video_url: Optional[str] = Field(None, description="Preview video URL")


class LensesResponse(BaseModel):
    username: str
    total_lenses: int
    lenses: List[Lens]


class BitmojisResponse(BaseModel):
    username: str
    total_bitmojis: int
    bitmoji_hashes: List[str] = Field(default_factory=list, description="MD5 hashes of unique bitmoji versions")


class Stats(BaseModel):
    total_stories: int = Field(0, description="Number of current stories")
    total_curated_highlights: int = Field(0, description="Number of curated highlight groups")
    total_highlight_snaps: int = Field(0, description="Total snaps across all highlights")
    total_spotlights: int = Field(0, description="Number of spotlight videos")
    total_spotlight_snaps: int = Field(0, description="Total snaps across all spotlights")
    total_spotlight_duration: str = Field("0m0s", description="Total spotlight duration (human-readable)")
    total_spotlight_duration_ms: int = Field(0, description="Total spotlight duration in milliseconds")
    total_spotlight_engagement: int = Field(0, description="Total spotlight view count")
    total_lenses: int = Field(0, description="Number of lenses")
    top_hashtags: List[HashtagRanking] = Field(default_factory=list, description="Top 10 hashtags by frequency")


class StatsResponse(BaseModel):
    username: str
    stats: Stats


class HeatmapData(BaseModel):
    total_data_points: int = Field(0, description="Total number of upload timestamps analyzed")
    heatmap: Dict[str, Dict[str, int]] = Field(
        default_factory=dict,
        description="Matrix of day_of_week -> hour -> count"
    )


class HeatmapResponse(BaseModel):
    username: str
    heatmap_data: HeatmapData


class AllDataResponse(BaseModel):
    username: str
    fetched_at: str
    user_info: UserInfo
    stories: Optional[List[Story]] = None
    curated_highlights: Optional[List[CuratedHighlight]] = None
    spotlights: Optional[SpotlightsResponse] = None
    lenses: Optional[List[Lens]] = None
    stats: Optional[Stats] = None
    heatmap: Optional[HeatmapData] = None
    bitmojis: Optional[List[str]] = None
    note: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
