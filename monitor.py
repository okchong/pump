import os
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta

# 配置（从环境变量读取）
TOKEN = os.environ.get("7879193494:AAHWupFI6UYYQeeNPktpiK0nCkxi0FHQ3sI")
CHAT_ID = os.environ.get("6347325342")
URL = "https://t.me/s/YHone_PUMP"

def send_notification(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, json=payload)

def scrape_channel():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    proxies = {  # 可选，添加代理IP
        "http": "http://你的代理IP:端口",
        "https": "https://你的代理IP:端口"
    }
    max_retries = 3  # 最大重试次数
    retry_delay = 5  # 每次重试间隔（秒）
    
    for attempt in range(max_retries):
        try:
            response = requests.get(URL, headers=headers, timeout=15, proxies=proxies)
            if response.status_code == 200:
                return response.text
            print(f"尝试 {attempt + 1}/{max_retries} 失败，状态码: {response.status_code}")
        except requests.exceptions.ConnectTimeout:
            print(f"连接超时，尝试 {attempt + 1}/{max_retries}")
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
    print("抓取失败，所有重试均超时")
    return None

def parse_message_time(message_div):
    # 提取消息时间（假设时间在 <time> 标签或类名中）
    time_elem = message_div.find("time", class_="tgme_widget_message_date")
    if time_elem and 'datetime' in time_elem.attrs:
        time_str = time_elem['datetime']  # 格式如 "2025-03-02T14:30:00Z"
        try:
            # 转换为本地时间
            message_time = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
            return message_time
        except ValueError:
            print(f"无法解析时间: {time_str}")
            return None
    return None

def parse_message(message_div):
    text_div = message_div.find("div", class_="tgme_widget_message_text")
    if not text_div:
        return None, None
    
    text = text_div.get_text(strip=True)
    conditions = {
        "naReply": 0,
        "smart_money": 0,
        "ca_posts": 0,
        "tg_calls": 0
    }
    
    # 提取字段
    reply_match = re.search(r"Reply评论:\s*(\d+)", text)
    if reply_match:
        conditions["naReply"] = int(reply_match.group(1))
    smart_money_match = re.search(r"总计聪明钱：\s*(\d+)", text)
    if smart_money_match:
        conditions["smart_money"] = int(smart_money_match.group(1))
    ca_posts_match = re.search(r"CA关联推文：\s*(\d+)", text)
    if ca_posts_match:
        conditions["ca_posts"] = int(ca_posts_match.group(1))
    tg_calls_match = re.search(r"TGCall：\s*(\d+)", text)
    if tg_calls_match:
        conditions["tg_calls"] = int(tg_calls_match.group(1))

    matched_conditions = []
    if conditions["naReply"] > 10:
        matched_conditions.append(f"回复数: {conditions['naReply']} (>10)")
    if conditions["smart_money"] > 0:
        matched_conditions.append(f"聪明钱: {conditions['smart_money']} (>0)")
    if conditions["ca_posts"] > 1:
        matched_conditions.append(f"CA关联推文: {conditions['ca_posts']} (>1)")
    if conditions["tg_calls"] > 1:
        matched_conditions.append(f"TGCall: {conditions['tg_calls']} (>1)")
    
    if matched_conditions:
        return conditions, "\n".join(matched_conditions)
    return conditions, None

def is_within_10_minutes(message_time):
    if not message_time:
        return False
    now = datetime.utcnow()
    ten_minutes_ago = now - timedelta(minutes=10)
    return ten_minutes_ago <= message_time <= now

def monitor_channel():
    html = scrape_channel()
    if html:
        soup = BeautifulSoup(html, "html.parser")
        message_divs = soup.find_all("div", class_="tgme_widget_message")
        if message_divs:
            for message_div in reversed(message_divs):  # 从最新到最旧检查
                message_time = parse_message_time(message_div)
                if is_within_10_minutes(message_time):
                    conditions, matched = parse_message(message_div)
                    if matched:
                        text_div = message_div.find("div", class_="tgme_widget_message_text")
                        if text_div:
                            message_text = text_div.get_text(strip=True)
                            send_notification(
                                f"检测到符合条件的消息:\n"
                                f"内容: {message_text}\n"
                                f"满足的条件:\n{matched}"
                            )
                else:
                    break  # 如果超出10分钟，停止检查更旧的消息

if __name__ == "__main__":
    monitor_channel()