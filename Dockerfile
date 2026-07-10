FROM python:3.11-slim

LABEL maintainer="Ericality"
LABEL description="Bing 每日壁纸 · Cover Flow 浏览器"

ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libexiv2-dev \
      libboost-python-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bing_docker.py .
COPY Dispaly.html .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

RUN mkdir -p /data/web/images /data/backup

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/Dispaly.html')" || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]