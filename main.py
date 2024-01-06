import requests
from bs4 import BeautifulSoup
from threading import Thread
from queue import Queue
import time


class NewsAgent:
    def __init__(self, base_url, title_selector, desc_selector=None):
        self.base_url = base_url
        self.title_selector = title_selector
        self.desc_selector = desc_selector

    def fetch_news(self):
        news_items = []
        try:
            response = requests.get(self.base_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                titles = soup.select(self.title_selector)
                descs = soup.select(self.desc_selector) if self.desc_selector else [None] * len(titles)
                for title, desc in zip(titles, descs):
                    news_items.append((title.text.strip(), desc.text.strip() if desc else None))
        except Exception as e:
            print(f"Failed to fetch news from {self.base_url}: {e}")
        return news_items

class NewsFetcher:
    def __init__(self, agents, period):
        self.agents = agents
        self.news_queue = Queue()
        self.period = period

    def start(self):
        for agent in self.agents:
            thread = Thread(target=self.fetch_news_periodically, args=(agent,))
            thread.daemon = True
            thread.start()

    def fetch_news_periodically(self, agent):
        while True:
            news = agent.fetch_news()
            for title in news:
                self.news_queue.put(title)
            time.sleep(self.period)

    def get_news(self):
        while not self.news_queue.empty():
            yield self.news_queue.get()


if __name__ == "__main__":
    agent1 = NewsAgent("https://kazpravda.kz/",
                       "body > div.app > div > main > section:nth-child(1) > div > div > div.col-lg-7.col-xl-8 > div > div:nth-child(1) > article > div.daynews__content > div.daynews__title")
    agent2 = NewsAgent(
        "https://www.thefirstnews.com/",
        "body > div.wrap > main > section.section.section--top5articlescategory > div > div > div:nth-child(1) > div:nth-child(1) > div:nth-child(3) > h3 > a",
        "body > div.wrap > main > section.section.section--top5articlescategory > div > div > div:nth-child(1) > div:nth-child(1) > div:nth-child(3) > a > p"
    )
    agent3 = NewsAgent("https://www.foxnews.com/",
                       "#wrapper > div.page > div.region-content-sidebar > main > div.thumbs-2-7 > article.article.story-1 > div.info > header > h3 > a")

    fetcher = NewsFetcher([agent1, agent2, agent3], period=60)  # Обновление каждую минуту
    fetcher.start()

    try:
        while True:
            while not fetcher.news_queue.empty():
                for title, desc in fetcher.get_news():
                    print(f"Title: {title}")
                    print(f"Description: {desc}\n")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped.")
