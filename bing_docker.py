import requests
import re
from pyexiv2 import Image
import os
import datetime
import pytz
import json
from bs4 import BeautifulSoup
import urllib.parse

# ==================== 常量配置（通过环境变量注入）====================
SYNOLOGY_CHAT_WEBHOOK = os.environ.get('SYNOLOGY_CHAT_WEBHOOK', '')
BARK_DEVICE_KEY = os.environ.get('BARK_DEVICE_KEY', '')
BARK_API_URL = os.environ.get('BARK_API_URL', 'https://api.day.app/push')

# 路径配置（全部通过环境变量覆盖，适配 Docker / 任意服务器部署）
path = os.environ.get('BING_BACKUP_PATH', '/data/backup')                     # 备份路径
web_path = os.environ.get('BING_WEB_PATH', '/data/web')                       # 网页服务根目录
images_subdir = os.environ.get('BING_IMAGES_PATH',
                               os.path.join(web_path, 'images'))            # 图片子目录
metadata_file = os.environ.get('BING_METADATA_FILE',
                                os.path.join(web_path, 'wallpapers.json'))  # 元数据文件

# 请求头
header = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"
}

# ==================== 工具函数 ====================

def ensure_dir(directory):
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"创建目录: {directory}")

def set_file_time_to_midnight(file_path):
    """将文件的访问和修改时间设置为当天北京时间零点"""
    try:
        beijing_tz = pytz.timezone('Asia/Shanghai')
        now_beijing = datetime.datetime.now(beijing_tz)
        midnight_beijing = now_beijing.replace(hour=0, minute=0, second=0, microsecond=0)
        timestamp = midnight_beijing.timestamp()
        os.utime(file_path, (timestamp, timestamp))
        print(f"已设置文件时间为当天零点: {midnight_beijing.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"设置文件时间失败: {str(e)}")

def sanitize_filename(filename):
    """清理文件名中的非法字符"""
    invalid_chars = ['<', '>', ':', '"', '/', '\\\\', '|', '?', '*']
    for char in invalid_chars:
        filename = filename.replace(char, ' ')
    filename = re.sub(r'[\x00-\x1F\x7F\u200B-\u200D\u2060\uFEFF]', '', filename)
    return re.sub(r'\s+', ' ', filename).strip()

def parse_copyright(copyright_str):
    """解析版权字符串，分离标题和版权信息"""
    match = re.search(r'\((.*?)\)', copyright_str)
    if match:
        title = copyright_str[:match.start()].strip()
        copyright_info = match.group(1).strip()
    else:
        title = copyright_str.strip()
        copyright_info = "© Bing"
    return title, copyright_info

def extract_description(homepage_html):
    """从Bing主页HTML中提取详细描述（多种备选方法）"""
    try:
        # 方法1: 从 _model JSON 提取完整描述
        json_pattern = r'var _model\s*=\s*({.*?});'
        json_match = re.search(json_pattern, homepage_html, re.DOTALL)
        if json_match:
            try:
                model_data = json.loads(json_match.group(1))
                if model_data.get('MediaContents') and model_data['MediaContents']:
                    image_content = model_data['MediaContents'][0].get('ImageContent', {})
                    full_description = image_content.get('Description', '')
                    if full_description:
                        result = full_description.replace('\\"', '"').replace('\\\\', '\\')
                        print(f"从 _model JSON 提取成功 ({len(result)} 字符)")
                        return result
            except (json.JSONDecodeError, KeyError) as e:
                print(f"_model JSON 解析失败: {e}")

        # 方法2: 直接搜索 Description 字段
        desc_pattern = r'"Description":"((?:[^"\\]|\\.)*)"'
        desc_match = re.search(desc_pattern, homepage_html, re.DOTALL)
        if desc_match:
            result = desc_match.group(1).replace('\\"', '"').replace('\\\\', '\\')
            print(f"从 Description 字段提取成功 ({len(result)} 字符)")
            return result

        # 方法3: 从 meta 标签提取
        meta_pattern = r'<meta property="og:description" content="([^"]+)"'
        meta_match = re.search(meta_pattern, homepage_html)
        if meta_match:
            result = meta_match.group(1)
            print(f"从 meta 标签提取成功 (可能截断, {len(result)} 字符)")
            return result

        # 方法4: 使用 BeautifulSoup 查找 script 标签中的描述
        soup = BeautifulSoup(homepage_html, 'html.parser')
        for script in soup.find_all('script'):
            if script.string and '"Description":' in script.string:
                desc_match = re.search(r'"Description":"([^"]+)"', script.string)
                if desc_match:
                    result = desc_match.group(1).replace('\\"', '"')
                    print(f"从 script 标签提取成功 ({len(result)} 字符)")
                    return result

        print("所有提取方法均失败，使用默认描述")
        return "今日Bing壁纸"
    except Exception as e:
        print(f"描述提取异常: {e}")
        return "无法获取详细描述"

def load_metadata():
    """加载元数据文件，返回列表"""
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                else:
                    print("警告: 元数据格式错误，将重新创建")
                    return []
        except Exception as e:
            print(f"读取元数据失败: {e}，将重新创建")
            return []
    return []

def save_metadata(metadata):
    """保存元数据到 JSON 文件"""
    try:
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        print(f"元数据已保存: {metadata_file}")
    except Exception as e:
        print(f"保存元数据失败: {e}")

def update_metadata(new_entry):
    """更新元数据：去重、排序、保留最近30天"""
    metadata = load_metadata()
    metadata = [entry for entry in metadata if entry['date'] != new_entry['date']]
    metadata.append(new_entry)
    metadata.sort(key=lambda x: x['date'], reverse=True)
    if len(metadata) > 30:
        metadata = metadata[:30]
    save_metadata(metadata)
    return metadata

def cleanup_old_images():
    """清理 images/ 目录中超过30天的旧图片"""
    ensure_dir(images_subdir)
    beijing_tz = pytz.timezone('Asia/Shanghai')
    now = datetime.datetime.now(beijing_tz)
    cutoff = now - datetime.timedelta(days=30)
    cutoff_str = cutoff.strftime('%Y%m%d')

    for filename in os.listdir(images_subdir):
        filepath = os.path.join(images_subdir, filename)
        if not os.path.isfile(filepath):
            continue
        # 匹配原图 YYYYMMDD.jpg
        match = re.match(r'^(\d{8})\.jpg$', filename)
        if match and match.group(1) < cutoff_str:
            try:
                os.remove(filepath)
                print(f"已删除旧原图: {filename}")
            except Exception as e:
                print(f"删除 {filename} 失败: {e}")
            continue
        # 匹配预览图 YYYYMMDD_1080p.jpg
        match = re.match(r'^(\d{8})_1080p\.jpg$', filename)
        if match and match.group(1) < cutoff_str:
            try:
                os.remove(filepath)
                print(f"已删除旧预览图: {filename}")
            except Exception as e:
                print(f"删除 {filename} 失败: {e}")

# ==================== 通知发送函数 ====================

def send_synology_notification(title, description, image_url=None):
    """发送消息到 Synology Chat"""
    try:
        message = f"**{title}**\n\n{description}"
        if image_url:
            message += f"\n\n🔗{image_url}"
        payload_json = {"text": message}
        payload_str = json.dumps(payload_json, ensure_ascii=False)
        data = {"payload": payload_str}
        print(f"正在发送 Synology Chat: {title}")
        response = requests.post(
            SYNOLOGY_CHAT_WEBHOOK,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
            verify=False
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            try:
                resp_json = response.json()
                if resp_json.get("success"):
                    print("✓ Synology Chat 发送成功")
                    return True
                else:
                    error = resp_json.get('error', {})
                    print(f"✗ Synology Chat 返回错误: {error}")
                    return False
            except json.JSONDecodeError:
                print("✓ Synology Chat 响应非JSON，但状态码200")
                return True
        else:
            print(f"✗ Synology Chat 发送失败，状态码 {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Synology Chat 异常: {e}")
        return False

def send_bark_notification(title, body, group="BingWallpaper", level="active", icon=None):
    """发送通知到 Bark (iOS)"""
    try:
        payload = {
            "device_key": BARK_DEVICE_KEY,
            "title": title,
            "body": body,
            "group": group,
            "level": level,
        }
        if icon:
            payload["icon"] = icon
        else:
            payload["icon"] = "https://daily.ericality.com"  # 默认图标

        headers = {"Content-Type": "application/json; charset=utf-8"}
        response = requests.post(BARK_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        resp_json = response.json()
        if resp_json.get("code") == 200:
            print(f"✓ Bark 通知发送成功: {title}")
        else:
            print(f"✗ Bark 通知失败: {resp_json.get('message')}")
    except Exception as e:
        print(f"✗ Bark 通知异常: {e}")

# ==================== 核心业务函数 ====================

def fetch_bing_data():
    """从 Bing 获取今日壁纸数据，返回所需信息"""
    print("正在获取 Bing API 数据...")
    api_url = f'https://www.bing.com/HPImageArchive.aspx?format=js&idx={os.environ.get("BING_IDX", "0")}&n=1&mkt=zh-CN'
    resp = requests.get(api_url, headers=header)
    resp.raise_for_status()
    data = resp.json()
    if not data.get('images'):
        raise ValueError("API 响应中未找到图片数据")

    image_data = data['images'][0]
    print(f"图片数据: {image_data.get('copyright', 'Unknown')[:50]}...")

    # 构造图片 URL
    base_url = 'https://www.bing.com' + image_data['url']
    uhd_url = base_url.replace('1920x1080', 'UHD').replace('.webp', '.jpg')
    std_url = base_url.replace('.webp', '.jpg') if '.webp' in base_url else base_url

    # 获取详细描述
    bing_homepage_url = 'https://www.bing.com/?mkt=zh-CN'
    homepage_resp = requests.get(bing_homepage_url, headers=header)
    homepage_html = homepage_resp.text
    description = extract_description(homepage_html)

    # 解析标题和版权
    copyright_full = image_data['copyright']
    title, copyright_info = parse_copyright(copyright_full)
    full_detail = f"{copyright_full}\n{description}"

    print("完整描述信息:")
    print("-" * 50)
    print(full_detail)
    print("-" * 50)

    # 生成时间相关字符串
    beijing_tz = pytz.timezone('Asia/Shanghai')
    now_beijing = datetime.datetime.now(beijing_tz)
    time_str = now_beijing.strftime("%Y.%m.%d")
    image_date_str = now_beijing.strftime("%Y%m%d")
    safe_title = sanitize_filename(title)
    name = f"{time_str}-{safe_title}"

    return {
        'uhd_url': uhd_url,
        'std_url': std_url,
        'full_detail': full_detail,
        'title': title,
        'copyright_info': copyright_info,
        'description': description,
        'time_str': time_str,
        'image_date_str': image_date_str,
        'safe_title': safe_title,
        'name': name,
    }

def download_images(uhd_url, std_url):
    """下载原图和预览图，返回图片二进制内容"""
    print("正在下载 UHD 原图...")
    img_uhd = requests.get(uhd_url)
    img_uhd.raise_for_status()
    print("正在下载 1080p 预览图...")
    img_std = requests.get(std_url)
    img_std.raise_for_status()
    return img_uhd.content, img_std.content

def save_to_backup(image_uhd_content, name, full_detail):
    """保存原图和描述文件到备份目录（按年月归档）"""
    ensure_dir(path)

    beijing_tz = pytz.timezone('Asia/Shanghai')
    now = datetime.datetime.now(beijing_tz)
    year = now.strftime("%Y")
    month = now.strftime("%m")
    month_folder = f"{year}-{month}"

    target_dir = os.path.join(path, year, month_folder)
    ensure_dir(target_dir)

    local_img_path = os.path.join(target_dir, name + '.jpg')
    with open(local_img_path, 'wb') as f:
        f.write(image_uhd_content)
    print(f'原图备份至: {local_img_path}')

    with Image(local_img_path) as img_file:
        img_file.modify_exif({'Exif.Photo.UserComment': full_detail})
    print("EXIF 数据添加成功")
    set_file_time_to_midnight(local_img_path)

    local_txt_path = os.path.join(target_dir, name + '.txt')
    with open(local_txt_path, 'w', encoding='utf-8') as f:
        f.write(full_detail)
    print(f'描述文件备份至: {local_txt_path}')
    set_file_time_to_midnight(local_txt_path)

def save_to_web(image_uhd_content, full_detail):
    """保存 today.jpg 和 note.txt 到网页根目录"""
    ensure_dir(web_path)

    web_img_path = os.path.join(web_path, 'today.jpg')
    with open(web_img_path, 'wb') as f:
        f.write(image_uhd_content)
    print(f'今日壁纸保存至: {web_img_path}')
    with Image(web_img_path) as web_img:
        web_img.modify_exif({'Exif.Photo.UserComment': full_detail})
    set_file_time_to_midnight(web_img_path)

    web_txt_path = os.path.join(web_path, 'note.txt')
    with open(web_txt_path, 'w', encoding='utf-8') as f:
        f.write(full_detail)
    print(f'描述文件保存至: {web_txt_path}')
    set_file_time_to_midnight(web_txt_path)

def save_to_images_subdir(image_uhd_content, image_std_content, image_date_str):
    """保存原图和预览图到 images 子目录，文件名使用日期"""
    ensure_dir(images_subdir)

    uhd_filename = f"{image_date_str}.jpg"
    uhd_subpath = os.path.join(images_subdir, uhd_filename)
    with open(uhd_subpath, 'wb') as f:
        f.write(image_uhd_content)
    print(f'原图存档至: {uhd_subpath}')
    set_file_time_to_midnight(uhd_subpath)

    preview_filename = f"{image_date_str}_1080p.jpg"
    preview_subpath = os.path.join(images_subdir, preview_filename)
    with open(preview_subpath, 'wb') as f:
        f.write(image_std_content)
    print(f'预览图存档至: {preview_subpath}')
    set_file_time_to_midnight(preview_subpath)

    return uhd_filename, preview_filename

def update_metadata_and_cleanup(metadata_entry):
    """更新元数据 JSON 并清理过期图片"""
    update_metadata(metadata_entry)
    cleanup_old_images()

def send_notifications(title, safe_title, description, time_str, std_url):
    """发送 Synology Chat 和 Bark 通知"""
    chat_title = f"📸Bing壁纸 - {time_str}"
    short_desc = description[:500] + "..." if len(description) > 500 else description
    send_synology_notification(
        title=chat_title,
        description=short_desc,
        image_url="https://daily.ericality.com/today.jpg"
    )

    send_bark_notification(
        title=f'Bing:{safe_title}',
        body=description,
        icon=std_url
    )

# ==================== 主函数 ====================

def main():
    try:
        print("========== 开始 Bing 壁纸获取流程 ==========")
        print(f"  📁 网页目录: {web_path}")
        print(f"  🖼️  图片目录: {images_subdir}")
        print(f"  💾 备份目录: {path}")
        print(f"  📋 元数据:   {metadata_file}")

        # 1. 获取数据
        data = fetch_bing_data()

        # 2. 下载图片
        img_uhd_content, img_std_content = download_images(data['uhd_url'], data['std_url'])

        # 3. 保存到备份目录
        save_to_backup(img_uhd_content, data['name'], data['full_detail'])

        # 4. 保存到网页根目录
        save_to_web(img_uhd_content, data['full_detail'])

        # 5. 保存到 images 子目录
        uhd_filename, preview_filename = save_to_images_subdir(
            img_uhd_content, img_std_content, data['image_date_str']
        )

        # 6. 构建元数据条目
        metadata_entry = {
            "date": data['time_str'].replace('.', '-'),
            "image_uhd": uhd_filename,
            "image_preview": preview_filename,
            "title": data['title'],
            "copyright": data['copyright_info'],
            "description": data['description'].strip()
        }

        # 7. 更新元数据并清理旧文件
        update_metadata_and_cleanup(metadata_entry)

        # 8. 发送通知
        send_notifications(
            data['title'], data['safe_title'],
            data['description'], data['time_str'], data['std_url']
        )

        print("========== 脚本执行成功 ==========")
    except Exception as e:
        error_message = f'脚本运行出错: {str(e)}'
        print(error_message)
        send_bark_notification('Bing:运行出错', error_message, level='timeSensitive')
        send_synology_notification('Bing 壁纸获取失败', error_message)

if __name__ == '__main__':
    main()
