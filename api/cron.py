import feedparser
import requests
import datetime
import os
import smtplib
from email.mime.text import MIMEText

SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
TO_EMAIL = os.environ.get("TO_EMAIL")

RSS_SOURCES = [
    "http://www.xinhuanet.com/politics/xhll.xml",
    "http://www.most.gov.cn/rss.xml",
    "https://rsshub.app/gov/pbc/goutongjiaoliu",
    "https://rsshub.app/gov/miit/zcjd",
    "https://rsshub.app/gov/stats/xxgk",
]

def fetch_news():
    news_list = []
    for url in RSS_SOURCES:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                news_list.append({
                    "title": entry.title,
                    "link": entry.link,
                    "source": feed.feed.get("title", "未知来源")
                })
        except:
            continue
    return news_list

def generate_briefing(news_list, today):
    news_text = ""
    for i, news in enumerate(news_list):
        news_text += f"{i+1}. 【{news['source']}】{news['title']}\n"
    
    prompt = f"""你是晨报编辑。今天是{today}，根据下面的要闻生成晨报。

要求：
1. 筛选最重要的5条，用大白话翻译
2. 写一段"串联分析"，说明这些事之间的关系
3. 写一段"对普通人的影响和建议"

新闻列表：
{news_text}
"""
    
    response = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.environ.get('DEEPSEEK_API_KEY')}",
            "Content-Type": "application/json"
        },
        json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
    )
    
    result = response.json()
    return result["choices"][0]["message"]["content"]

def send_email(content, today):
    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = f"每日晨报 - {today}"
    msg["From"] = SMTP_USER
    msg["To"] = TO_EMAIL
    
    server = smtplib.SMTP_SSL("smtp.qq.com", 465)
    server.login(SMTP_USER, SMTP_PASS)
    server.sendmail(SMTP_USER, [TO_EMAIL], msg.as_string())
    server.quit()

def handler(event, context):
    today = datetime.date.today().strftime("%Y-%m-%d")
    news = fetch_news()
    report = generate_briefing(news, today)
    send_email(report, today)
    return {"statusCode": 200, "body": "晨报已发送！"}
