# 🌄 Bing 每日壁纸 · Cover Flow 浏览器

自动抓取微软 Bing 每日精选壁纸，通过精美的 **Cover Flow 3D 轮播** 页面展示。支持触摸滑动、键盘快捷键、全屏浏览。提供一键 Docker 部署，可在服务器 / NAS / 树莓派上运行。

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue?logo=python)](https://www.python.org/)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://www.docker.com/)
[![License MIT](https://img.shields.io/badge/License-MIT-green)](./LICENSE)

---

## ✨ 功能特性

### 后端（Python）

| 功能 | 说明 |
|------|------|
| 🔄 **自动抓取** | 调用 Bing API 获取每日壁纸 UHD 原图 + 1080p 预览图 |
| 📝 **描述提取** | 4 种策略（JSON → 正则 → meta 标签 → BeautifulSoup）确保拿到完整文案 |
| 📋 **元数据管理** | JSON 存储标题/版权/描述，自动去重，保留最近 30 天 |
| 🗑️ **自动清理** | 超过 30 天的旧图片自动删除 |
| 💾 **备份归档** | 原图按「年/月」目录结构存档，写入 EXIF 信息 |
| 🔔 **消息推送** | 支持 Bark（iOS 推送）和 Synology Chat 通知 |
| 🐳 **Docker 化** | 所有路径/密钥通过环境变量注入，完全配置驱动 |

### 前端（HTML5 / CSS3 / 原生 JS）

| 功能 | 说明 |
|------|------|
| 🎠 **Cover Flow 轮播** | 三张卡片同时可见，当前居中放大，两侧收缩 + 模糊 |
| 👆 **触摸滑动** | 移动端左右滑动切换，方向锁定（不干扰垂直滚动） |
| 🖱️ **鼠标拖拽** | 桌面端支持拖拽滑动，自动区分拖拽 vs 点击 |
| ⌨️ **键盘快捷键** | `← →` 切换、`F` 全屏、`G` 缩略图网格、`Esc` 关闭 |
| 🖼️ **缩略图面板** | 网格展示所有壁纸，hover 显示标题，点击跳转 |
| 🔍 **全屏浏览** | 点击当前图片进入全屏模式 |
| 🌫️ **模糊背景** | 当前壁纸实时作为模糊背景切换 |
| 📱 **响应式布局** | 7:3 弹性比例，适配手机/平板/桌面 |

---

## 🛠️ 技术栈

- 后端：Python 3.12 + requests + BeautifulSoup4 + pyexiv2 + pytz
- 前端：原生 HTML5 + CSS3 + JavaScript（零框架依赖）
- 部署：Docker + docker-compose
- 存储：本地文件系统 + JSON 元数据

---

## 📁 项目结构

```
.
├── bing.py                # 原始脚本（个人服务器用，路径硬编码）
├── bing_docker.py          # Docker 专用脚本（路径通过环境变量注入）
├── Dispaly.html            # Cover Flow 前端页面
├── requirements.txt        # Python 依赖
├── Dockerfile              # Docker 镜像构建文件
├── docker-compose.yml      # Docker Compose 编排
├── entrypoint.sh           # 容器启动脚本
├── env.example.txt         # 环境变量模板
├── .dockerignore           # Docker 构建忽略
├── images/                 # 示例壁纸（镜像自带，开箱即用）
├── wallpapers.json         # 示例壁纸元数据
├── Example Image/          # 额外备份的示例图片
└── README.md
```

---

## 📸 示例图片

项目中自带了真实抓取的 Bing 壁纸作为示例，来自 `Example Image/2026-06/` 备份数据。Docker 镜像已将这些图片打包在内，启动即可浏览，无需额外配置。你也可以运行脚本抓取最新壁纸来更新。

---

## 🚀 本地运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 抓取今日壁纸
python bing.py

# 3. 启动 HTTP 服务器
python -m http.server 8080

# 4. 浏览器打开
open http://localhost:8080/Dispaly.html
```

---

## 🐳 Docker 部署

### docker-compose（推荐）

```bash
git clone <仓库地址> && cd bing_wallpaper
docker-compose up -d
# 访问 http://localhost:8080/Dispaly.html
```

### 纯 Docker 命令

```bash
docker build -t bing-wallpaper:latest .
docker run -d \
  --name bing-wallpaper \
  -p 8080:8080 \
  -v $(pwd)/data/web:/data/web \
  -e BING_AUTO_FETCH=true \
  bing-wallpaper:latest
```

### 在其他设备上访问

```
http://<宿主机IP>:8080/Dispaly.html
```

> 💡 外网访问建议通过 Nginx 反向代理 + 域名，或使用 Cloudflare Tunnel

---

## ⏰ 定时抓取

```bash
crontab -e
# 每天 8:00 自动抓取
0 8 * * * docker exec bing-wallpaper python /app/bing_docker.py
```

---

## ⚙️ 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `BING_WEB_PATH` | 网页服务根目录 | `/data/web` |
| `BING_IMAGES_PATH` | 图片存储目录 | `/data/web/images` |
| `BING_METADATA_FILE` | 元数据文件路径 | `/data/web/wallpapers.json` |
| `BING_BACKUP_PATH` | 备份目录 | `/data/backup` |
| `BING_AUTO_FETCH` | 启动时自动抓取 | `false` |
| `BARK_DEVICE_KEY` | Bark 推送 Key | （空）|
| `BARK_API_URL` | Bark API 地址 | `https://api.day.app/push` |
| `SYNOLOGY_CHAT_WEBHOOK` | Synology Chat Webhook | （空）|
| `TZ` | 时区 | `Asia/Shanghai` |

---

## 🖥️ 部署到其他平台

### 云服务器

```bash
ssh user@your-server
curl -fsSL https://get.docker.com | sh
git clone <仓库地址> && cd bing_wallpaper
docker-compose up -d
# 防火墙开放 8080 端口
```

### 群晖 NAS

安装 Docker 套件 → 上传项目文件 → `docker-compose up -d`

### 树莓派 / ARM

```bash
docker build -t bing-wallpaper:latest .
docker-compose up -d
```

---

## 📄 许可证

MIT License
