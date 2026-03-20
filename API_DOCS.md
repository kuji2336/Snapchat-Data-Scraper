# SnapIntel REST API Documentation

Comprehensive REST API for SnapIntel — an OSINT tool for investigating Snapchat users. Built with FastAPI.

---

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
  - [Local Setup](#local-setup)
  - [Docker Setup](#docker-setup)
- [Base URL](#base-url)
- [Authentication](#authentication)
- [Common Query Parameters](#common-query-parameters)
- [Error Handling](#error-handling)
- [API Endpoints](#api-endpoints)
  - [Health Check](#1-health-check)
  - [Get User Info](#2-get-user-info)
  - [Get Stories](#3-get-stories)
  - [Get Curated Highlights](#4-get-curated-highlights)
  - [Get Spotlights](#5-get-spotlights)
  - [Get Lenses](#6-get-lenses)
  - [Get Bitmojis](#7-get-bitmojis)
  - [Get Stats](#8-get-stats)
  - [Get Heatmap Data](#9-get-heatmap-data)
  - [Get All Data](#10-get-all-data)
- [Response Models Reference](#response-models-reference)
- [Rate Limiting & Notes](#rate-limiting--notes)
- [Example Workflows](#example-workflows)

---

## Overview

| Property             | Value                              |
| -------------------- | ---------------------------------- |
| **API Version**      | 1.0.0                              |
| **Framework**        | FastAPI (Python)                   |
| **License**          | AGPL-3.0                           |
| **Source**           | https://github.com/Kr0wZ/SnapIntel |
| **Interactive Docs** | `/docs` (Swagger UI)               |
| **ReDoc**            | `/redoc`                           |
| **OpenAPI Spec**     | `/openapi.json`                    |

The API scrapes public Snapchat profile pages and returns structured JSON data. It supports:

- **User profiles** — public and private account metadata
- **Stories** — currently active stories with media URLs
- **Curated Highlights** — grouped highlight stories
- **Spotlights** — spotlight videos with engagement stats and hashtags
- **Lenses** — AR lenses/filters with preview URLs
- **Bitmojis** — unique bitmoji versions for private users
- **Statistics** — aggregated summary data
- **Heatmap** — upload time distribution (day × hour matrix)

---

## Getting Started

### Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/Kr0wZ/SnapIntel/
cd SnapIntel

# 2. Configure environment
cp .env.example .env
# Edit .env and set your WEBSHARE_PASS

# 3. Install API dependencies
pip install -r requirements-api.txt

# 4. Start the API server
uvicorn api.app:app --host 127.0.0.1 --port 8000

# 5. Open interactive docs
open http://127.0.0.1:8000/docs
```

### Docker Setup (Horizontally Scaled)

The Docker Compose setup runs **3 API server instances** behind an **nginx load balancer** for high throughput. Each instance uses Webshare rotating proxies to avoid IP throttling.

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env and set your WEBSHARE_PASS

# 2. Build and run (3 instances + nginx load balancer)
docker-compose up --build -d

# 3. Verify all containers are running
docker-compose ps

# 4. Test load balancing (instance_id will rotate between 1, 2, 3)
curl http://localhost:8000/
curl http://localhost:8000/
curl http://localhost:8000/

# 5. View logs
docker-compose logs -f

# 6. Stop everything
docker-compose down
```

**Architecture:**

```
                    ┌─────────────────┐
   :8000  ────────► │   nginx (LB)    │
                    │  least_conn     │
                    └────┬───┬───┬────┘
                         │   │   │
              ┌──────────┘   │   └──────────┐
              ▼              ▼              ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
     │ API instance 1│ │ API instance 2│ │ API instance 3│
     │  :8000       │ │  :8000       │ │  :8000       │
     └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
            │                │                │
            └────────┬───────┘────────┬───────┘
                     ▼                ▼
            ┌──────────────┐  ┌─────────────┐
            │  Webshare    │  │  Snapchat   │
            │  Proxy Pool  │──│  Servers    │
            └──────────────┘  └─────────────┘
```

**Scaling up/down:** To change the number of instances, edit `docker-compose.yml` — duplicate or remove `snapintel-api-N` services and update the `upstream` block in `nginx.conf`.

**Environment Variables:**

| Variable           | Default | Description                                    |
| ------------------ | ------- | ---------------------------------------------- |
| `WEBSHARE_PASS`    | —       | **Required.** Webshare proxy password          |
| `PYTHONUNBUFFERED` | `1`     | Ensures real-time log output                   |
| `INSTANCE_ID`      | `local` | Server instance identifier (set per container) |

### Proxy Configuration

All outbound requests to Snapchat are routed through **Webshare rotating proxies** to avoid IP-based rate limiting.

| Property     | Value                         |
| ------------ | ----------------------------- |
| **Provider** | Webshare                      |
| **Host**     | `p.webshare.io`               |
| **Port**     | `80`                          |
| **Username** | `jdprtnas-rotate`             |
| **Mode**     | Rotating (new IP per request) |

The proxy password is loaded from the `WEBSHARE_PASS` environment variable (set in `.env`). If `WEBSHARE_PASS` is not set, requests will be made directly without a proxy.

**`.env` file:**

```bash
WEBSHARE_PASS=your_webshare_password_here
```

**`.env.example`** is provided as a template — copy it to `.env` and fill in your credentials.

---

## Base URL

```
http://localhost:8000
```

All API endpoints are prefixed with `/api/v1/user`.

**Full endpoint pattern:**

```
http://localhost:8000/api/v1/user/{username}[/resource]
```

---

## Authentication

**No authentication is required.** The API is open and does not require API keys or tokens.

> ⚠️ If you deploy this publicly, consider adding authentication middleware (e.g., API key header) to prevent abuse.

---

## Common Query Parameters

These query parameters are available on all `/api/v1/user/*` endpoints:

| Parameter | Type | Default | Range | Description                                                        |
| --------- | ---- | ------- | ----- | ------------------------------------------------------------------ |
| `timeout` | int  | `30`    | 1–120 | Request timeout in seconds when fetching data from Snapchat        |
| `threads` | int  | `10`    | 1–50  | Number of concurrent threads (only used by `/bitmojis` and `/all`) |

---

## Error Handling

All errors return a consistent JSON structure:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Meaning         | When It Occurs                                                                  |
| ---- | --------------- | ------------------------------------------------------------------------------- |
| 200  | Success         | Request completed successfully                                                  |
| 400  | Bad Request     | Invalid parameter or endpoint used incorrectly (e.g., bitmojis for public user) |
| 403  | Forbidden       | Trying to access data for a private user (stories, spotlights, etc.)            |
| 404  | Not Found       | User does not exist or no JSON data found on Snapchat                           |
| 502  | Bad Gateway     | Failed to connect to Snapchat servers                                           |
| 504  | Gateway Timeout | Snapchat request timed out                                                      |

### Error Response Examples

**User not found (404):**

```json
{
  "detail": "No JSON data found in Snapchat response for user 'nonexistentuser123'"
}
```

**Private user (403):**

```json
{
  "detail": "User is private. Stories are not available."
}
```

**Timeout (504):**

```json
{
  "detail": "Request timed out after 30s for user 'realmadrid'"
}
```

---

## API Endpoints

---

### 1. Health Check

Returns API status and version.

| Property   | Value |
| ---------- | ----- |
| **Method** | `GET` |
| **URL**    | `/`   |

#### Request

```bash
curl http://localhost:8000/
```

#### Response `200 OK`

```json
{
  "status": "ok",
  "api": "SnapIntel API",
  "version": "1.0.0",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

| Field     | Type   | Description         |
| --------- | ------ | ------------------- |
| `status`  | string | API health status   |
| `api`     | string | API name            |
| `version` | string | Current API version |
| `docs`    | string | Path to Swagger UI  |
| `redoc`   | string | Path to ReDoc       |

---

### 2. Get User Info

Fetches public or private profile information for a Snapchat user.

| Property   | Value                     |
| ---------- | ------------------------- |
| **Method** | `GET`                     |
| **URL**    | `/api/v1/user/{username}` |

#### Path Parameters

| Parameter  | Type   | Required | Description       |
| ---------- | ------ | -------- | ----------------- |
| `username` | string | Yes      | Snapchat username |

#### Query Parameters

| Parameter | Type | Default | Description              |
| --------- | ---- | ------- | ------------------------ |
| `timeout` | int  | `30`    | Request timeout (1–120s) |

#### Request

```bash
curl "http://localhost:8000/api/v1/user/realmadrid"
```

#### Response `200 OK` — Public Profile

```json
{
  "username": "realmadrid",
  "user_info": {
    "page_title": "Real Madrid (@realmadrid) | Snapchat Stories, Spotlight & Lenses",
    "page_description": "Real Madrid is on Snapchat! (@realmadrid) | 4.6m Subscribers | ⚽ Official profile of Real Madrid C.F. | 🏆 15 times European Champions | 🌍 FIFA Best Club of the 20th Century | Madrid, España | Last updated: 01/29/2026",
    "is_private": false,
    "username": "realmadrid",
    "badge": "Creator",
    "profile_picture_url": "https://cf-st.sc-cdn.net/aps/bolt/..._RS0,640_FMjpeg",
    "background_picture_url": "https://cf-st.sc-cdn.net/aps/bolt/..._RS0,1080_FMjpeg",
    "subscriber_count": "4627300",
    "bio": "⚽ Official profile of Real Madrid C.F. | 🏆 15 times European Champions | 🌍 FIFA Best Club of the 20th Century",
    "website_url": "https://www.snapchat.com/discover/Real_Madrid/6314412811",
    "snapcode_image_url": "https://app.snapchat.com/web/deeplink/snapcode?username=realmadrid&type=SVG&bitmoji=enable",
    "display_name": null,
    "avatar_image_url": null,
    "background_image_url": null,
    "error": null
  }
}
```

#### Response Fields — `user_info`

| Field                    | Type    | Description                                             |
| ------------------------ | ------- | ------------------------------------------------------- |
| `page_title`             | string  | Snapchat page title                                     |
| `page_description`       | string  | Meta description from profile page                      |
| `is_private`             | boolean | `true` if account is private, `false` if public         |
| `username`               | string  | Snapchat username                                       |
| `badge`                  | string  | Badge type: `"Creator"`, `"Public Figure"`, or `"None"` |
| `profile_picture_url`    | string  | Profile picture URL (640px, public only)                |
| `background_picture_url` | string  | Hero/background image URL (public only)                 |
| `subscriber_count`       | string  | Subscriber count as string (public only)                |
| `bio`                    | string  | User bio text (public only)                             |
| `website_url`            | string  | Website URL if set (public only)                        |
| `snapcode_image_url`     | string  | Snapcode image URL                                      |
| `display_name`           | string  | Display name (private profiles only)                    |
| `avatar_image_url`       | string  | Current bitmoji/avatar URL (private profiles only)      |
| `background_image_url`   | string  | Background image URL (private profiles only)            |

---

### 3. Get Stories

Fetches current active stories for a public Snapchat user.

| Property   | Value                             |
| ---------- | --------------------------------- |
| **Method** | `GET`                             |
| **URL**    | `/api/v1/user/{username}/stories` |

#### Request

```bash
curl "http://localhost:8000/api/v1/user/realmadrid/stories"
```

#### Response `200 OK`

```json
{
  "username": "realmadrid",
  "total_stories": 54,
  "stories": [
    {
      "snap_index": 0,
      "media_url": "https://cf-st.sc-cdn.net/d/Fz2ILj743LejU8LquHvOa.1023.IRZXSOY?mo=...&uc=75",
      "preview_url": "https://cf-st.sc-cdn.net/d/Fz2ILj743LejU8LquHvOa.256.IRZXSOY?mo=...&uc=75",
      "upload_date": "2026-03-13 12:26:33",
      "media_type": "image"
    },
    {
      "snap_index": 1,
      "media_url": "https://cf-st.sc-cdn.net/d/DKtL3vYkFDCPuiVWk9a2U.1023.IRZXSOY?mo=...&uc=75",
      "preview_url": "https://cf-st.sc-cdn.net/d/DKtL3vYkFDCPuiVWk9a2U.256.IRZXSOY?mo=...&uc=75",
      "upload_date": "2026-03-13 12:26:36",
      "media_type": "image"
    }
  ]
}
```

#### Response Fields — `stories[]`

| Field         | Type   | Description                                              |
| ------------- | ------ | -------------------------------------------------------- |
| `snap_index`  | int    | Sequential index of the snap in the story                |
| `media_url`   | string | Direct URL to the full-resolution media (image or video) |
| `preview_url` | string | Thumbnail/preview URL (256px)                            |
| `upload_date` | string | Upload timestamp in `YYYY-MM-DD HH:MM:SS` format (UTC)   |
| `media_type`  | string | `"image"` (JPG) or `"video"` (MP4)                       |

---

### 4. Get Curated Highlights

Fetches curated highlight stories grouped by title.

| Property   | Value                                |
| ---------- | ------------------------------------ |
| **Method** | `GET`                                |
| **URL**    | `/api/v1/user/{username}/highlights` |

#### Request

```bash
curl "http://localhost:8000/api/v1/user/realmadrid/highlights"
```

#### Response `200 OK`

```json
{
  "username": "realmadrid",
  "total_highlights": 2,
  "highlights": [
    {
      "title": "Match Day",
      "snap_count": 5,
      "snaps": [
        {
          "snap_index": 0,
          "media_url": "https://cf-st.sc-cdn.net/d/...",
          "upload_date": "2026-03-10 19:45:00"
        },
        {
          "snap_index": 1,
          "media_url": "https://cf-st.sc-cdn.net/d/...",
          "upload_date": "2026-03-10 20:30:00"
        }
      ]
    }
  ]
}
```

#### Response Fields — `highlights[]`

| Field        | Type   | Description                             |
| ------------ | ------ | --------------------------------------- |
| `title`      | string | Highlight group title                   |
| `snap_count` | int    | Number of snaps in this highlight group |
| `snaps`      | array  | Array of snap objects                   |

#### Response Fields — `highlights[].snaps[]`

| Field         | Type   | Description                                     |
| ------------- | ------ | ----------------------------------------------- |
| `snap_index`  | int    | Sequential index of the snap                    |
| `media_url`   | string | Direct URL to the media                         |
| `upload_date` | string | Upload timestamp in `YYYY-MM-DD HH:MM:SS` (UTC) |

---

### 5. Get Spotlights

Fetches spotlight videos with engagement data, hashtags, and media URLs.

| Property   | Value                                |
| ---------- | ------------------------------------ |
| **Method** | `GET`                                |
| **URL**    | `/api/v1/user/{username}/spotlights` |

#### Request

```bash
curl "http://localhost:8000/api/v1/user/realmadrid/spotlights"
```

#### Response `200 OK`

```json
{
  "username": "realmadrid",
  "total_spotlights": 30,
  "total_engagement": 1163896,
  "hashtag_rankings": [
    { "tag": "#RealMadrid", "count": 15 },
    { "tag": "#UCL", "count": 9 },
    { "tag": "#ViniJr", "count": 5 },
    { "tag": "#ucl", "count": 5 },
    { "tag": "#goals", "count": 3 }
  ],
  "spotlights": [
    {
      "name": "Spotlight Snap",
      "thumbnail_url": "https://bolt-gcdn.sc-cdn.net/bp/...",
      "duration": "0m46s",
      "duration_ms": 46000,
      "upload_date": "2026-03-07 15:28:15",
      "engagement_views": 15691,
      "hashtags": [],
      "snaps": [
        {
          "snap_index": 0,
          "media_url": "https://bolt-gcdn.sc-cdn.net/bp/..."
        }
      ]
    },
    {
      "name": "Spotlight Snap",
      "thumbnail_url": "https://bolt-gcdn.sc-cdn.net/bp/...",
      "duration": "1m27s",
      "duration_ms": 87000,
      "upload_date": "2026-03-07 13:40:34",
      "engagement_views": 12340,
      "hashtags": ["#CeltaRealMadrid", "#RealMadrid"],
      "snaps": [
        {
          "snap_index": 0,
          "media_url": "https://bolt-gcdn.sc-cdn.net/bp/..."
        }
      ]
    }
  ]
}
```

#### Response Fields — Top Level

| Field              | Type  | Description                         |
| ------------------ | ----- | ----------------------------------- |
| `total_spotlights` | int   | Total number of spotlight videos    |
| `total_engagement` | int   | Sum of all spotlight view counts    |
| `hashtag_rankings` | array | Top 10 hashtags sorted by frequency |

#### Response Fields — `hashtag_rankings[]`

| Field   | Type   | Description                |
| ------- | ------ | -------------------------- |
| `tag`   | string | Hashtag text (e.g. `#UCL`) |
| `count` | int    | Number of occurrences      |

#### Response Fields — `spotlights[]`

| Field              | Type   | Description                                  |
| ------------------ | ------ | -------------------------------------------- |
| `name`             | string | Spotlight name/title                         |
| `thumbnail_url`    | string | Thumbnail image URL                          |
| `duration`         | string | Human-readable duration (e.g. `"1m27s"`)     |
| `duration_ms`      | int    | Duration in milliseconds                     |
| `upload_date`      | string | Upload timestamp `YYYY-MM-DD HH:MM:SS` (UTC) |
| `engagement_views` | int    | View count / engagement stats                |
| `hashtags`         | array  | List of hashtag strings for this spotlight   |
| `snaps`            | array  | Media snaps within this spotlight            |

#### Response Fields — `spotlights[].snaps[]`

| Field        | Type   | Description       |
| ------------ | ------ | ----------------- |
| `snap_index` | int    | Index of the snap |
| `media_url`  | string | Direct media URL  |

---

### 6. Get Lenses

Fetches Snapchat lenses/AR filters associated with a user.

| Property   | Value                            |
| ---------- | -------------------------------- |
| **Method** | `GET`                            |
| **URL**    | `/api/v1/user/{username}/lenses` |

#### Request

```bash
curl "http://localhost:8000/api/v1/user/realmadrid/lenses"
```

#### Response `200 OK`

```json
{
  "username": "realmadrid",
  "total_lenses": 2,
  "lenses": [
    {
      "name": "Real Madrid Jersey",
      "is_official": false,
      "preview_video_url": "https://lens-storage.storage.googleapis.com/previewvideo/87d9be6d-eb98-4061-b15d-cc4dc3982cdb"
    },
    {
      "name": "Real Madrid CF",
      "is_official": false,
      "preview_video_url": "https://lens-storage.storage.googleapis.com/previewvideo/835b4b69-4b3d-4271-8202-bd2a49ff43fa"
    }
  ]
}
```

#### Response Fields — `lenses[]`

| Field               | Type    | Description                               |
| ------------------- | ------- | ----------------------------------------- |
| `name`              | string  | Lens name/title                           |
| `is_official`       | boolean | Whether this is an official Snapchat lens |
| `preview_video_url` | string  | URL to the lens preview video             |

---

### 7. Get Bitmojis

Fetches unique bitmoji versions for **private** Snapchat users only.

| Property   | Value                              |
| ---------- | ---------------------------------- |
| **Method** | `GET`                              |
| **URL**    | `/api/v1/user/{username}/bitmojis` |

#### Query Parameters

| Parameter | Type | Default | Description                                    |
| --------- | ---- | ------- | ---------------------------------------------- |
| `timeout` | int  | `30`    | Request timeout (1–120s)                       |
| `threads` | int  | `10`    | Concurrent threads for bitmoji fetching (1–50) |

#### Request

```bash
curl "http://localhost:8000/api/v1/user/someprivateuser/bitmojis?threads=20"
```

#### Response `200 OK`

```json
{
  "username": "someprivateuser",
  "total_bitmojis": 12,
  "bitmoji_hashes": [
    "a1b2c3d4e5f6789012345678abcdef01",
    "f0e1d2c3b4a5968778695a4b3c2d1e0f",
    "..."
  ]
}
```

#### Response Fields

| Field            | Type  | Description                             |
| ---------------- | ----- | --------------------------------------- |
| `total_bitmojis` | int   | Number of unique bitmoji versions found |
| `bitmoji_hashes` | array | MD5 hashes of each unique bitmoji image |

#### Error Response `400 Bad Request`

Returned if you call this endpoint for a **public** user:

```json
{
  "detail": "Bitmoji endpoint is only available for private users."
}
```

---

### 8. Get Stats

Fetches aggregated summary statistics for a user's content.

| Property   | Value                           |
| ---------- | ------------------------------- |
| **Method** | `GET`                           |
| **URL**    | `/api/v1/user/{username}/stats` |

#### Request

```bash
curl "http://localhost:8000/api/v1/user/realmadrid/stats"
```

#### Response `200 OK`

```json
{
  "username": "realmadrid",
  "stats": {
    "total_stories": 54,
    "total_curated_highlights": 0,
    "total_highlight_snaps": 0,
    "total_spotlights": 30,
    "total_spotlight_snaps": 30,
    "total_spotlight_duration": "13m57s",
    "total_spotlight_duration_ms": 837639,
    "total_spotlight_engagement": 1163896,
    "total_lenses": 2,
    "top_hashtags": [
      { "tag": "#RealMadrid", "count": 15 },
      { "tag": "#UCL", "count": 9 },
      { "tag": "#ViniJr", "count": 5 },
      { "tag": "#ucl", "count": 5 },
      { "tag": "#goals", "count": 3 },
      { "tag": "#RealMadridElche", "count": 2 },
      { "tag": "#RMCity", "count": 2 },
      { "tag": "#LouisVuitton", "count": 1 },
      { "tag": "#Bale", "count": 1 },
      { "tag": "#CeltaRealMadrid", "count": 1 }
    ]
  }
}
```

#### Response Fields — `stats`

| Field                         | Type   | Description                                     |
| ----------------------------- | ------ | ----------------------------------------------- |
| `total_stories`               | int    | Number of current active stories                |
| `total_curated_highlights`    | int    | Number of curated highlight groups              |
| `total_highlight_snaps`       | int    | Total snaps across all highlight groups         |
| `total_spotlights`            | int    | Number of spotlight videos                      |
| `total_spotlight_snaps`       | int    | Total snaps across all spotlights               |
| `total_spotlight_duration`    | string | Total duration human-readable (e.g. `"13m57s"`) |
| `total_spotlight_duration_ms` | int    | Total duration in milliseconds                  |
| `total_spotlight_engagement`  | int    | Sum of all spotlight view counts                |
| `total_lenses`                | int    | Number of lenses                                |
| `top_hashtags`                | array  | Top 10 hashtags by frequency (tag + count)      |

---

### 9. Get Heatmap Data

Returns upload time distribution as a day-of-week × hour matrix. Data is derived from story and spotlight upload timestamps.

| Property   | Value                             |
| ---------- | --------------------------------- |
| **Method** | `GET`                             |
| **URL**    | `/api/v1/user/{username}/heatmap` |

#### Request

```bash
curl "http://localhost:8000/api/v1/user/realmadrid/heatmap"
```

#### Response `200 OK`

```json
{
  "username": "realmadrid",
  "heatmap_data": {
    "total_data_points": 84,
    "heatmap": {
      "Monday": {
        "0": 0,
        "1": 0,
        "2": 0,
        "3": 0,
        "4": 0,
        "5": 0,
        "6": 0,
        "7": 0,
        "8": 0,
        "9": 1,
        "10": 4,
        "11": 0,
        "12": 0,
        "13": 3,
        "14": 0,
        "15": 0,
        "16": 0,
        "17": 1,
        "18": 0,
        "19": 0,
        "20": 2,
        "21": 0,
        "22": 4,
        "23": 0
      },
      "Tuesday": { "0": 4, "1": 0, "...": "..." },
      "Wednesday": { "...": "..." },
      "Thursday": { "...": "..." },
      "Friday": { "...": "..." },
      "Saturday": { "...": "..." },
      "Sunday": { "...": "..." }
    }
  }
}
```

#### Response Fields — `heatmap_data`

| Field               | Type   | Description                                  |
| ------------------- | ------ | -------------------------------------------- |
| `total_data_points` | int    | Total number of upload timestamps analyzed   |
| `heatmap`           | object | Nested object: `day_name` → `hour` → `count` |

**`heatmap` structure:**

- Top-level keys: `"Monday"` through `"Sunday"`
- Each day contains keys `"0"` through `"23"` (hours in UTC)
- Values are integers representing the number of uploads in that hour/day slot

---

### 10. Get All Data

Fetches all available data for a user in a single request. For public profiles, this returns everything. For private profiles, only user info and bitmojis.

| Property   | Value                         |
| ---------- | ----------------------------- |
| **Method** | `GET`                         |
| **URL**    | `/api/v1/user/{username}/all` |

#### Query Parameters

| Parameter | Type | Default | Description                            |
| --------- | ---- | ------- | -------------------------------------- |
| `timeout` | int  | `30`    | Request timeout (1–120s)               |
| `threads` | int  | `10`    | Concurrent threads for bitmojis (1–50) |

#### Request

```bash
curl "http://localhost:8000/api/v1/user/realmadrid/all"
```

#### Response `200 OK` — Public Profile

```json
{
  "username": "realmadrid",
  "fetched_at": "2026-03-20T12:30:25.571832Z",
  "user_info": { "..." },
  "stories": [ "..." ],
  "curated_highlights": [ "..." ],
  "spotlights": {
    "username": "realmadrid",
    "total_spotlights": 30,
    "total_engagement": 1163896,
    "hashtag_rankings": [ "..." ],
    "spotlights": [ "..." ]
  },
  "lenses": [ "..." ],
  "stats": { "..." },
  "heatmap": { "..." },
  "bitmojis": null,
  "note": null
}
```

#### Response `200 OK` — Private Profile

```json
{
  "username": "someprivateuser",
  "fetched_at": "2026-03-20T12:30:25.571832Z",
  "user_info": {
    "page_title": "...",
    "is_private": true,
    "username": "someprivateuser",
    "display_name": "Some User",
    "avatar_image_url": "https://...",
    "background_image_url": "https://...",
    "snapcode_image_url": "https://..."
  },
  "stories": null,
  "curated_highlights": null,
  "spotlights": null,
  "lenses": null,
  "stats": null,
  "heatmap": null,
  "bitmojis": ["a1b2c3d4...", "f0e1d2c3..."],
  "note": "User is private. Only bitmoji data is available."
}
```

#### Response Fields — Top Level

| Field                | Type   | Description                                               |
| -------------------- | ------ | --------------------------------------------------------- |
| `username`           | string | Queried username                                          |
| `fetched_at`         | string | ISO 8601 timestamp of when data was fetched (UTC)         |
| `user_info`          | object | User profile data (see [Get User Info](#2-get-user-info)) |
| `stories`            | array  | Stories array or `null` (private users)                   |
| `curated_highlights` | array  | Highlights array or `null`                                |
| `spotlights`         | object | Spotlights data or `null`                                 |
| `lenses`             | array  | Lenses array or `null`                                    |
| `stats`              | object | Statistics or `null`                                      |
| `heatmap`            | object | Heatmap data or `null`                                    |
| `bitmojis`           | array  | Bitmoji hashes or `null` (public users)                   |
| `note`               | string | Additional note (e.g. private user warning)               |

---

## Response Models Reference

All response models are defined as Pydantic schemas and are available in the auto-generated OpenAPI spec.

| Model                | Used By                      | Description                  |
| -------------------- | ---------------------------- | ---------------------------- |
| `UserInfoResponse`   | `GET /{username}`            | User profile wrapper         |
| `StoriesResponse`    | `GET /{username}/stories`    | Stories list with count      |
| `HighlightsResponse` | `GET /{username}/highlights` | Highlight groups with snaps  |
| `SpotlightsResponse` | `GET /{username}/spotlights` | Spotlights with engagement   |
| `LensesResponse`     | `GET /{username}/lenses`     | Lens list                    |
| `BitmojisResponse`   | `GET /{username}/bitmojis`   | Bitmoji hash list            |
| `StatsResponse`      | `GET /{username}/stats`      | Summary statistics           |
| `HeatmapResponse`    | `GET /{username}/heatmap`    | Day×hour upload distribution |
| `AllDataResponse`    | `GET /{username}/all`        | Everything combined          |
| `ErrorResponse`      | All (error cases)            | Error detail                 |

For full schema definitions with all fields and types, visit:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

## Rate Limiting & Notes

### Snapchat Upstream Throttling

This API scrapes public Snapchat profile pages. Snapchat may throttle or block excessive requests from the same IP.

**Built-in mitigation:**

- All requests are routed through **Webshare rotating proxies** — each request gets a different IP
- The Docker setup runs **3 parallel API instances** behind nginx for high throughput

**Additional recommendations:**

- **Add delays** between requests when querying many users in batch
- **Cache responses** on your end if you need to query the same user repeatedly
- **Use reasonable timeouts** (default 30s is usually sufficient)

### Data Freshness

- Stories are typically available for **24 hours** after posting
- Spotlight and highlight data reflects what is currently on the user's profile
- Data is fetched **live** on each request — there is no server-side caching

### Private vs Public Users

| Feature            | Public | Private      |
| ------------------ | ------ | ------------ |
| User Info          | ✅     | ✅ (limited) |
| Stories            | ✅     | ❌           |
| Curated Highlights | ✅     | ❌           |
| Spotlights         | ✅     | ❌           |
| Lenses             | ✅     | ❌           |
| Bitmojis           | ❌     | ✅           |
| Stats              | ✅     | ❌           |
| Heatmap            | ✅     | ❌           |

---

## Example Workflows

### 1. Quick Profile Overview

Get user info and stats in two parallel requests:

```bash
# User info
curl "http://localhost:8000/api/v1/user/realmadrid"

# Stats
curl "http://localhost:8000/api/v1/user/realmadrid/stats"
```

### 2. Get Everything at Once

Use the `/all` endpoint for a single comprehensive request:

```bash
curl "http://localhost:8000/api/v1/user/realmadrid/all" | python3 -m json.tool > realmadrid_full.json
```

### 3. Analyze Posting Patterns

Get heatmap data to understand when a user posts:

```bash
curl "http://localhost:8000/api/v1/user/realmadrid/heatmap" | python3 -m json.tool
```

### 4. Find Top Hashtags & Engagement

Query spotlights for hashtag rankings and view counts:

```bash
curl "http://localhost:8000/api/v1/user/realmadrid/spotlights" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Total views: {data[\"total_engagement\"]:,}')
for h in data['hashtag_rankings']:
    print(f'  {h[\"tag\"]}: {h[\"count\"]}x')
"
```

### 5. Monitor Stories with Custom Timeout

Use a longer timeout for unreliable connections:

```bash
curl "http://localhost:8000/api/v1/user/realmadrid/stories?timeout=60"
```

### 6. Investigate Private User Bitmojis

```bash
curl "http://localhost:8000/api/v1/user/someprivateuser/bitmojis?threads=20"
```

---

## Project Structure

```
SnapIntel/
├── api/
│   ├── __init__.py
│   ├── app.py                          # FastAPI application entry point
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py                  # Pydantic response models
│   ├── routers/
│   │   ├── __init__.py
│   │   └── snapchat.py                 # API endpoint definitions
│   └── services/
│       ├── __init__.py
│       └── snapchat_service.py         # Core scraping/parsing logic
├── config.json                         # Snapchat JSON path configuration
├── display.py                          # CLI display (unchanged)
├── heatmap.py                          # CLI heatmap (unchanged)
├── main.py                             # CLI entry point (unchanged)
├── snap_parser.py                      # CLI argument parser (unchanged)
├── ssd.py                              # CLI scraper (unchanged)
├── requirements.txt                    # CLI dependencies
├── requirements-api.txt                # API dependencies
├── Dockerfile                          # Docker image definition
├── docker-compose.yml                  # Docker Compose (3 instances + nginx LB)
├── nginx.conf                          # Nginx load balancer configuration
├── .env                                # Environment variables (git-ignored)
├── .env.example                        # Environment template
└── API_DOCS.md                         # This documentation
```
