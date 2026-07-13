# Bing 每日壁纸

[![Docker](https://img.shields.io/badge/Docker-✓-blue)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

[English Documentation](./README.md)

一款自托管的 Bing 每日壁纸抓取服务，可自动获取 Bing 首页每日高清壁纸，持久化存储图片与元数据，并以 Cover Flow 风格的网页画廊提供历史壁纸浏览功能。

## ✨ 特性

- **每日自动抓取** — 通过 Bing 官方 API 定时获取最新每日壁纸。
- **Cover Flow 网页画廊** — 优雅的响应式 Cover Flow 轮播界面，支持缩略图网格、键盘导航与触控滑动。
- **全分辨率归档** — 下载 UHD 原图并在本地保留，同时写入 EXIF 元数据。
- **定时调度** — 内建 crontab 支持，可通过环境变量灵活配置抓取周期。
- **通知推送集成** — 可选接入 [Bark](https://github.com/Finb/Bark)（iOS）和 [Synology Chat](https://www.synology.com/zh-cn/dsm/feature/chat) 进行消息推送。
- **容器化部署** — 通过 `docker compose up` 一键启动，所有配置项均由环境变量驱动。
- **轻量级设计** — 基于 `python:3.11-slim` 镜像，资源占用极低。

## 🚀 快速开始

### 环境要求

- Docker 与 Docker Compose

### 1. 克隆项目

```bash
git clone https://github.com/Ericality/bing-wallpaper.git
cd bing-wallpaper
```

### 2. 配置环境变量

复制示例环境变量文件并根据需要进行修改：

```bash
cp env.example.txt .env
```

主要环境变量：

| 变量 | 说明 | 默认值 |
|---|---|---|
| `BING_AUTO_FETCH` | 是否在容器启动时立即执行一次抓取 | `false` |
| `BING_CRON` | 定时抓取的 crontab 表达式（如 `0 3 * * *`） | （空） |
| `BARK_DEVICE_KEY` | Bark 设备密钥，用于 iOS 推送通知 | （空） |
| `SYNOLOGY_CHAT_WEBHOOK` | Synology Chat 传入 Webhook 地址 | （空） |
| `TZ` | 时区设置 | `Asia/Shanghai` |

### 3. 启动服务

```bash
docker compose up -d
```

### 4. 访问画廊

在浏览器中打开：

```
http://localhost:8080
```

## 📁 目录结构

```
bing-wallpaper/
├── bing_docker.py        # 核心脚本：抓取、下载、归档、通知
├── Dockerfile             # Docker 多阶段构建文件
├── docker-compose.yml     # Docker Compose 编排文件
├── entrypoint.sh          # 容器入口脚本（含 cron 配置）
├── env.example.txt        # 环境变量模板
├── requirements.txt       # Python 依赖清单
├── Dispaly.html           # Cover Flow 网页界面
├── data/                  # 持久化数据目录
│   ├── web/               # Web 可访问文件
│   │   ├── images/        # 壁纸图片（YYYYMMDD.jpg / YYYYMMDD_1080p.jpg）
│   │   ├── wallpapers.json# 元数据索引
│   │   ├── today.jpg      # 今日壁纸
│   │   ├── note.txt       # 今日描述
│   │   └── index.html     # 画廊页面
│   └── backup/            # 归档备份（按年/月组织）
```

## 🖼️ 网页画廊

Cover Flow 画廊由 `data/web/` 目录直接提供服务，支持以下功能：

- **Cover Flow 轮播** — 左右拖拽/滑动即可翻阅壁纸。
- **缩略图网格** — 点击 ☰ 菜单按钮可一览所有历史壁纸。
- **全屏浏览** — 点击中间壁纸可查看 UHD 原图全屏效果。
- **键盘快捷键** — `←` / `→` 切换壁纸，`F` 全屏浏览，`G` 打开缩略图网格，`Esc` 关闭。

## 🔧 运维操作

### 手动抓取

在容器中直接执行抓取脚本：

```bash
docker exec bing-wallpaper python3 /app/bing_docker.py
```

### 配置定时任务

在 `.env` 文件中设置 `BING_CRON` 环境变量即可。以下示例为每天凌晨 3:00 执行抓取：

```env
BING_CRON=0 3 * * *
```

### 完整环境变量参考

| 变量 | 说明 | 默认值 |
|---|---|---|
| `BING_WEB_PATH` | Web 文档根目录 | `/data/web` |
| `BING_IMAGES_PATH` | 壁纸图片存储目录 | `/data/web/images` |
| `BING_METADATA_FILE` | 元数据 JSON 文件路径 | `/data/web/wallpapers.json` |
| `BING_BACKUP_PATH` | 归档备份目录 | `/data/backup` |
| `BING_IDX` | Bing API 偏移量（0 = 今天，-1 = 昨天） | `0` |
| `BARK_API_URL` | Bark API 端点 | `https://api.day.app/push` |

## 📄 许可证

[MIT](LICENSE)