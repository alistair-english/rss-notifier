from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import feedparser
from slugify import slugify
import datetime as dt
import time
import os
import smtplib
from email.mime.text import MIMEText

from typing import Optional

FEED_URLS: list[str] = [
    "https://www.ozbargain.com.au/product/sony-wh-1000xm4/feed",
    "https://www.ozbargain.com.au/product/sony-wh-1000xm5/feed"
]

@dataclass
class FeedUpdate:
    title: str
    published: dt.datetime
    link: str

url_updates: dict[str, list[FeedUpdate]] = defaultdict(list)

for url in FEED_URLS:
    print(url)
    last_opened: Optional[dt.datetime] = None
    last_opened_path = Path("./_data") / Path(slugify(url))
    if last_opened_path.exists():
        with open(last_opened_path, 'r') as f:
            last_opened = dt.datetime.fromisoformat(f.read())
    else:
        last_opened_path.parent.mkdir(parents=True, exist_ok=True)
        last_opened_path.touch()

    feed = feedparser.parse(url)

    if last_opened is None:
        if len(feed["entries"]) < 1:
            print("Haven't got any history and no entries to update history with!")
            continue

        print("Haven't got any history!")
        last_published = dt.datetime.fromtimestamp(time.mktime(feed["entries"][0]["published_parsed"]))
        with open(last_opened_path, 'w') as f:
            f.write(last_published.isoformat())
            continue
    
    last_published = None
    for entry in reversed(feed["entries"]):
        entry_published = dt.datetime.fromtimestamp(time.mktime(entry["published_parsed"]))
        if entry_published > last_opened:
            url_updates[url].append(
                FeedUpdate(
                    entry["title"],
                    entry_published,
                    entry["link"],
                )
            )
            last_published = entry_published

    if last_published is not None:
        with open(last_opened_path, 'w') as f:
            f.write(last_published.isoformat())

print(url_updates)

if len(url_updates) < 1:
    exit(1)

SENDER = os.getenv("RSS_NOTIFIER_SENDER")
PASSWORD = os.getenv("RSS_NOTIFIER_PASSWORD")
RECIPENTS = [s.strip() for s in os.getenv("RSS_NOTIFIER_RECIPENTS").split(";")]

body = "The following feeds have updates.\n\n"

for url, updates in url_updates.items():
    body += f"{'='*80}\n"
    body += f"{url}\n"
    body += f"{'='*80}\n"
    for update in sorted(updates, key=lambda x: x.published, reverse=True):
        body += f"{update.published.strftime('%c')}\n{update.title} \n \t - {update.link}\n\n"

print(body)

msg = MIMEText(body)
msg["Subject"] = "RSS Updates"
msg["From"] = SENDER
msg["To"] = ', '.join(RECIPENTS)
with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
    smtp_server.login(SENDER, PASSWORD)
    smtp_server.sendmail(SENDER, RECIPENTS, msg.as_string())

print("email sent")
