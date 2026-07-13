# Bing Daily Wallpaper

[![Docker](https://img.shields.io/badge/Docker-✓-blue)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

[中文文档](./README_CN.md)

A self-hosted service that fetches the Bing homepage daily wallpaper, persists the image and metadata, and presents a Cover Flow-style web gallery for browsing historical wallpapers.

## ✨ Features

- **Automatic Daily Fetch** — Retrieves the latest Bing wallpaper from the official API every day.
- **Cover Flow Web Gallery** — An elegant, responsive Cover Flow carousel with thumbnail grid, keyboard navigation, and swipe support.
- **Full-Resolution Archival** — Downloads UHD originals and retains them locally with EXIF metadata.
- **Cron Scheduling** — Built-in crontab support for periodic fetching; specify any schedule via environment variable.
- **Notification Integration** — Optional push notifications via [Bark](https://github.com/Finb/Bark) (iOS) and [Synology Chat](https://www.synology.com/en-global/dsm/feature/chat).
- **Dockerized Deployment** — Single `docker compose up` with fully configurable environment variables.
- **Lightweight** — Based on `python:3.11-slim`, minimal resource footprint.

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose

### 1. Clone and Prepare

```bash
git clone https://github.com/Ericality/bing-wallpaper.git
cd bing-wallpaper
```

### 2. Configure Environment

Copy the example environment file and adjust as needed:

```bash
cp env.example.txt .env
```

Key environment variables:

| Variable | Description | Default |
|---|---|---|
| `BING_AUTO_FETCH` | Whether to fetch on container start | `false` |
| `BING_CRON` | Cron schedule for periodic fetching (e.g. `0 3 * * *`) | (empty) |
| `BARK_DEVICE_KEY` | Bark device key for iOS push notifications | (empty) |
| `SYNOLOGY_CHAT_WEBHOOK` | Synology Chat incoming webhook URL | (empty) |
| `TZ` | Timezone | `Asia/Shanghai` |

### 3. Start the Service

```bash
docker compose up -d
```

### 4. Access the Gallery

Open your browser and navigate to:

```
http://localhost:8080
```

## 📁 Directory Structure

```
bing-wallpaper/
├── bing_docker.py        # Core script: fetch, download, archive, notify
├── Dockerfile             # Multi-stage Docker build
├── docker-compose.yml     # Docker Compose orchestration
├── entrypoint.sh          # Container entrypoint with cron setup
├── env.example.txt        # Environment variable template
├── requirements.txt       # Python dependencies
├── Dispaly.html           # Cover Flow web interface
├── data/                  # Persistent data directory
│   ├── web/               # Web-accessible files
│   │   ├── images/        # Wallpaper images (YYYYMMDD.jpg / YYYYMMDD_1080p.jpg)
│   │   ├── wallpapers.json# Metadata index
│   │   ├── today.jpg      # Today's wallpaper
│   │   ├── note.txt       # Today's description
│   │   └── index.html     # Gallery page
│   └── backup/            # Archive backup (organized by year/month)
```

## 🖼️ Web Gallery

The Cover Flow gallery is served directly from `data/web/`. It supports:

- **Cover Flow Carousel** — Drag/swipe left/right to flip through wallpapers.
- **Thumbnail Grid** — Click the ☰ menu button to browse all wallpapers at a glance.
- **Fullscreen View** — Click the center wallpaper to view the UHD original fullscreen.
- **Keyboard Shortcuts** — `←` / `→` to navigate, `F` for fullscreen, `G` for thumbnail grid, `Esc` to close.

## 🔧 Operation

### Manual Fetch

Execute the fetch script directly inside the container:

```bash
docker exec bing-wallpaper python3 /app/bing_docker.py
```

### Cron Configuration

Set the `BING_CRON` environment variable in your `.env` file. Example for fetching at 3:00 AM daily:

```env
BING_CRON=0 3 * * *
```

### Environment Variables Reference

| Variable | Description | Default |
|---|---|---|
| `BING_WEB_PATH` | Web document root | `/data/web` |
| `BING_IMAGES_PATH` | Wallpaper images directory | `/data/web/images` |
| `BING_METADATA_FILE` | Metadata JSON file path | `/data/web/wallpapers.json` |
| `BING_BACKUP_PATH` | Archive backup directory | `/data/backup` |
| `BING_IDX` | Bing API offset (0 = today, -1 = yesterday) | `0` |
| `BARK_API_URL` | Bark API endpoint | `https://api.day.app/push` |

## 📄 License

[MIT](LICENSE)