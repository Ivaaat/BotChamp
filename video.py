import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import aiohttp
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
import telebot
from telebot.async_telebot import AsyncTeleBot
import config
import xpath
from datetime import datetime
from lxml import etree, html
import pymongo
import re
import time

DB_URI = 'mongodb://localhost:27017/'
DB_NAME = 'championat'
COLLECTION_NAME = 'videos'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

RETRY_DELAY = 60  # Задержка перед повторной попыткой в секундах
MAX_RETRIES = 3  # Максимальное количество попыток

PROXY_URL = 'http://proxy.example.com:8080'  # URL прокси-сервера

TELEGRAM_TOKEN = config.TOKEN
TELEGRAM_CHAT_ID = config.channel_id

class Observer(ABC):
    @abstractmethod
    def update(self, event: str, data: dict):
        pass

class TelegramObserver(Observer):
    def __init__(self, token: str, chat_id: str):
        #self.bot = telebot.TeleBot(token)
        self.bot = AsyncTeleBot(token)
        self.chat_id = chat_id

    async def update(self, event: str, data: dict):
        if event == 'new_video' and config.IS_SEND:
            message = '{}\n{}'.format(data['title'], data['link'])
            try:
                await self.bot.send_message(self.chat_id, message)
            except telebot.asyncio_helper.ApiTelegramException:
                await asyncio.sleep(10)
                await self.bot.send_message(self.chat_id, message)


class AsyncVideoParser(ABC):
    def __init__(self):
        self.observers = []

    def add_observer(self, observer: Observer):
        self.observers.append(observer)

    async def notify_observers(self, event: str, data: dict):
        for observer in self.observers:
            await observer.update(event, data)

    @abstractmethod
    async def get_videos(self, urls: list):
        pass

    async def fetch_html(self, url: str):
        retries = 0
        use_proxy = False
        while retries < MAX_RETRIES:
            try:
                async with aiohttp.ClientSession(headers=HEADERS) as self.session:
                    if use_proxy:
                        async with self.session.get(url, proxy=PROXY_URL) as response:
                            return await response.text()
                    else:
                        async with self.session.get(url) as response:
                            return await response.text()
            except Exception as e:
                print(f'Error fetching HTML: {e}')
                retries += 1
                #use_proxy = True
                await asyncio.sleep(RETRY_DELAY)
        return None

class AsyncYouTubeVideoParser(AsyncVideoParser):
    async def get_videos(self, urls: list):
        videos = []
        for url in urls:
            try:
                search_query, link = url.split('_')
                full_url = 'https://www.youtube.com/{}/videos'.format(link)
                country_dict = config.dict_youtube
            except ValueError:
                full_url = 'https://www.youtube.com/playlist?list={}'.format(url)
                country_dict = config.mass_review
            html = await self.fetch_html(full_url)
            if html:
                send = BeautifulSoup(html, 'html.parser')
                search = send.find_all('script')
                link_re = r'"watchEndpoint":{"videoId":"'
                title_re = r']},"title":{"runs":\[{"text":'
                data_link = re.findall(link_re + r"([^*]{12})", str(search))
                data_title = re.findall(title_re + r"([^*]{150})", str(search))
                for i, clear_title in enumerate(data_title):
                    try:
                        cond = search_query in clear_title
                    except UnboundLocalError:
                        cond = True
                    if cond:
                        title = clear_title[1:clear_title.find('}')-1]
                        date = title.split()[-1]
                        b = i
                        while '.' not in date:
                            title = data_title[b-1][1:data_title[b-1].find('}')-1]
                            date = title.split()[-1]
                            b-=1
                        try:
                            clear_date = datetime.strptime(date,"%d.%m.%Y")
                        except ValueError:
                            clear_date = datetime.strptime(date,"%d.%m.%y")
                        for country in country_dict:
                            if url == country_dict[country]:
                                break
                            country = ""
                        videos.append({'title':title, 
                                'link': 'https://www.youtube.com/watch?v=' + data_link[i][:-1], 
                                'date': clear_date,
                                'champ':country})
        return videos

class AsyncRuTubeVideoParser(AsyncVideoParser):
    async def get_videos(self, urls: list):
        videos = []
        for url in urls:
            html = await self.fetch_html(url)
            if html:
                send = BeautifulSoup(html, 'html.parser')
                video_title = etree.HTML(str(send))
                title = video_title.xpath('//section/a/div/div/img/@alt')
                link = video_title.xpath('//div/section/a/@href')
                for num_list in range(len(link)):
                    if "обзор".upper() in title[num_list].upper():
                        date = title[num_list].split()[-1]
                        b = num_list
                        while '.' not in date:
                            try:
                                date = title[b+1].split()[-1]
                                b+=1
                            except IndexError:
                                date = title[-2].split()[-1]
                                break
                        try:
                            clear_date = datetime.strptime(date,"%d.%m.%Y")
                        except ValueError:
                            try:
                                clear_date = datetime.strptime(date,"%d.%m.%y")
                            except ValueError:
                                continue
                        for country, query in config.dict_rutube.items():
                            if query.upper() in title[num_list].upper():
                                break
                            else:
                                country = ""
                        videos.append({'title':title[num_list], 
                                       'link': link[num_list], 
                                       'date': clear_date,
                                       'champ':country})
        return videos

class AsyncReviewVideoParser(AsyncVideoParser):
    async def get_videos(self, urls: list):
        videos = []
        for url in urls:
            html_text = await self.fetch_html(url)
            if html_text:
                tree = html.fromstring(html_text)
                review_list_href = tree.xpath(xpath.review_xpath_href)
                review_list_title = tree.xpath(xpath.review_xpath_title)
                review_list_date = tree.xpath(xpath.review_xpath_date)
                for i in range(len(review_list_href)):
                    review_title = review_list_title[i].replace(
                        'видео обзор матча', " ")
                    html_text = await self.fetch_html(review_list_href[i])
                    tree = html.fromstring(html_text)
                    list_href = tree.xpath(xpath.review_xpath_match_href)
                    dates = review_list_href[i].split('/')
                    date = '.'.join([dates[5],dates[4],dates[3]])
                    if len(list_href) == 0:
                        list_href = tree.xpath(xpath.review_xpath_France_href)
                        if len(list_href) == 0:
                            continue
                    try:
                        review_ref = list_href[0].split('\'')[1]
                    except IndexError:
                        try:
                            review_ref = list_href[0].split('=')[1]
                        except IndexError:
                            continue
                    title = '{} {}'.format(review_title.strip(), 
                                        review_list_date[i].strip())
                    for country in config.dict_footbal_video:
                            if url == config.dict_footbal_video[country]:
                                break
                            country = ""
                    videos.append({'title':title, 
                                   'link': review_ref, 
                                   'date': datetime.strptime(date,"%d.%m.%Y"),
                                   'champ': country})
        return videos

class AsyncVideoScraper:
    def __init__(self, parser: AsyncVideoParser):
        self.parser = parser
        self.client = AsyncIOMotorClient(DB_URI)
        self.db = self.client[DB_NAME]
        self.collection = self.db[COLLECTION_NAME]
        self.collection.create_index('title', unique = True)

    async def scrape(self, urls: list):
        videos = await self.parser.get_videos(urls)
        for video in videos:
            try:
                await self.collection.insert_one(video)
                await self.parser.notify_observers('new_video', video)
            except pymongo.errors.DuplicateKeyError:
                continue

async def scrape_site(scraper, urls):
    await scraper.scrape(urls)

async def main():
    telegram_observer = TelegramObserver(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)

    youtube_parser = AsyncYouTubeVideoParser()
    youtube_parser.add_observer(telegram_observer)
    youtube_parser1 = AsyncYouTubeVideoParser()
    youtube_parser1.add_observer(telegram_observer)
    rutube_parser = AsyncRuTubeVideoParser()
    rutube_parser.add_observer(telegram_observer)
    review_parser = AsyncReviewVideoParser()
    review_parser.add_observer(telegram_observer)

    scrapers = [
        AsyncVideoScraper(youtube_parser),
        AsyncVideoScraper(youtube_parser1),
        AsyncVideoScraper(rutube_parser),
        AsyncVideoScraper(review_parser)
    ]
    urls_list = [
        list(config.dict_youtube.values()),
        list(config.mass_review.values()),
        ['https://rutube.ru/metainfo/tv/255003/page-{}'.format(j) for j in range(1,20)],
        list(config.dict_footbal_video.values())
    ]
    interval = 3600  # Интервал в секундах

    while True:
        start = time.time()
        tasks = [scrape_site(scraper, urls) for scraper, urls in zip(scrapers, urls_list)]
        await asyncio.gather(*tasks)
        print('time work:{}'.format(time.time() - start))
        await asyncio.sleep(interval)

def run_async():
    asyncio.run(main())

     
