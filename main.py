from pathlib import Path
import feedparser
from slugify import slugify
import datetime as dt
import time

from typing import Optional


FEED_URLS: list[str] = [
    "https://www.ozbargain.com.au/product/sony-wh-1000xm4/feed",
    "https://www.ozbargain.com.au/product/sony-wh-1000xm5/feed"
]

for url in FEED_URLS:
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
            print("havent got any history and no entries to update history with!")
            continue

        print("havent got any history!")
        last_published = dt.datetime.fromtimestamp(time.mktime(feed["entries"][0]["published_parsed"]))
        with open(last_opened_path, 'w') as f:
            f.write(last_published.isoformat())
            continue
    
    last_published = None
    for entry in reversed(feed["entries"]):
        entry_published = dt.datetime.fromtimestamp(time.mktime(entry["published_parsed"]))
        if entry_published > last_opened:
            print(entry_published)
            last_published = entry_published
    
    if last_published is not None:
        with open(last_opened_path, 'w') as f:
            f.write(last_published.isoformat())
            break
