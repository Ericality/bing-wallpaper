#!/bin/bash
set -e

echo "=========================================="
echo "  🌄 Bing 每日壁纸 · Cover Flow 浏览器"
echo "=========================================="

# 确保数据目录存在
mkdir -p "$BING_WEB_PATH" "$BING_IMAGES_PATH" "$BING_BACKUP_PATH"

echo ""
echo "📁 网页目录:   $BING_WEB_PATH"
echo "🖼️  图片目录:   $BING_IMAGES_PATH"
echo "💾 备份目录:   $BING_BACKUP_PATH"
echo "📋 元数据文件: $BING_METADATA_FILE"
echo ""

# 如果设置了自动抓取，先执行一次
if [ "${BING_AUTO_FETCH}" = "true" ]; then
    echo "📸 执行首次壁纸抓取..."
    python /app/bing_docker.py || echo "⚠️  首次抓取失败，服务继续运行"
    echo ""
fi

# ----- 定时任务配置 (crontab) -----
if [ -n "${BING_CRON}" ]; then
    # 创建 cron wrapper 脚本，注入环境变量
    cat > /app/cron_run.sh << EOF
#!/bin/bash
export SYNOLOGY_CHAT_WEBHOOK="${SYNOLOGY_CHAT_WEBHOOK}"
export BARK_DEVICE_KEY="${BARK_DEVICE_KEY}"
export BARK_API_URL="${BARK_API_URL:-https://api.day.app/push}"
export BING_WEB_PATH="${BING_WEB_PATH}"
export BING_IMAGES_PATH="${BING_IMAGES_PATH}"
export BING_METADATA_FILE="${BING_METADATA_FILE}"
export BING_BACKUP_PATH="${BING_BACKUP_PATH}"
export TZ="${TZ}"
cd /app && /usr/local/bin/python /app/bing_docker.py
EOF
    chmod +x /app/cron_run.sh
    echo "${BING_CRON} /app/cron_run.sh >> /var/log/bing_cron.log 2>&1" | crontab -
    echo "⏰ 已配置定时抓取: ${BING_CRON}"
    cron -f &
else
    echo "ℹ️  未设置 BING_CRON，不启用定时抓取"
fi

# 将前端页面复制到网页目录
echo "📄 复制前端页面..."
cp /app/Dispaly.html "$BING_WEB_PATH/index.html"

echo "🚀 启动 HTTP 静态文件服务器 (端口 8080)..."
cd "$BING_WEB_PATH"

# 使用 Python http.server 提供静态文件服务
exec python -m http.server 8080 --bind 0.0.0.0