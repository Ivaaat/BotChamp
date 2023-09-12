import time
import config 
from pymongo import errors
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import pymongo
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from PIL import Image, ImageEnhance
from PIL import ImageFont
from PIL import ImageDraw
from io import BytesIO
import os
from datetime import datetime


class NewsFetcher(ABC):
    @abstractmethod
    def fetch(self, url):
        pass

class RSSNewsFetcher(NewsFetcher):
    def fetch(self, url):
        response = config.sess.get(url)
        soup = BeautifulSoup(response.content, features='xml')
        articles = soup.findAll('item')
        news = []
        for article in articles:
            pub_date = article.find('pubDate').text
            time = pub_date.split()[4].split(':')
            day = pub_date.split()[1]
            date_pub = str(datetime.now().date())
            date = '{} {}:{}'.format(date_pub.replace(date_pub[-2:], day),
                                                time[0],
                                                time[1])
            try:
                logo = article.find('enclosure').attrs['url']
            except AttributeError:
                logo = ("https://img.championat.com/s/735x490/news/"
"big/f/i/v-uefa-planirujut-sozdat-letnjuju-ligu-chempionov_1583405978161575552.jpg")
            news_item = {
                'title': article.find('title').text,
                'link': article.find('link').text,
                'published': date,
                'img' : logo,
                'content_importance': True if article.find('category', attrs={'domain':'content_importance'}) else False
            }
            news.append(news_item)
        return news

class NewsProcessor(ABC):
    @abstractmethod
    def process(self, news):
        pass

class SimpleNewsProcessor(NewsProcessor):
    def process(self, news):
        for one_news in news:
            response = config.sess.get(one_news['link'])
            soup = BeautifulSoup(response.content, features="lxml")
            one_news['text'] = soup.find('div', {'data-type':"news"}).text.split('\n\n')[0].strip()
        return news 


class NewsSender(ABC):
    @abstractmethod
    def send(self, news):
        pass


class TelegramNewsSender(NewsSender):
    def send(self, news, users_col):
        for one_news in news:
            if config.IS_SEND and one_news['content_importance']:
                markup = InlineKeyboardMarkup()
                one_news['push_pic'] = PictureNews.make_news_pict(one_news['img'], one_news['title'])
                inst_view = f'''https://t.me/iv?url=https%3A%2F%2F{one_news["link"]}&rhash=f610f320a497f8'''
                markup.add(InlineKeyboardButton(one_news['title'], url=inst_view))
                for id in users_col.find({'Push':True}):
                   config.bot.send_photo(id['_id'], one_news['push_pic'], reply_markup=markup)
                config.bot.send_photo(config.channel_id, one_news['push_pic'], reply_markup=markup)


class MongoDBNews:
    def __init__(self):
        self.collection_news = config.db['news']
        self.collection_users = config.db['users']
        self.collection_news.create_index([("link", pymongo.ASCENDING)], unique=True)

    def save(self, news):
        new_news = []
        for one_news in news:
            try:
                self.collection_news.insert_one(one_news)
                new_news.append(one_news)
            except errors.DuplicateKeyError:
                continue
        return new_news
        

class News:
    def __init__(self, fetcher, processor, sender, storage):
        self.fetcher = fetcher
        self.processor = processor
        self.sender = sender
        self.storage = storage

    def run(self, url):
        news = self.fetcher.fetch(url)
        processed_news = self.processor.process(news)
        push_news = self.storage.save(processed_news)
        self.sender.send(push_news, self.storage.collection_users)


class PictureNews:
    

    @staticmethod
    def make_news_pict(logo_news, title):
        response = config.sess.get(logo_news)
        news_picture = Image.open(BytesIO(response.content)).resize((735, 490))
        list_text = title.split()
        logo = Image.open(f"pic{os.sep}1.png").resize((40, 39))
        logo_teleg = Image.open(f"pic{os.sep}tel.png").resize((35, 35))
        enhancer = ImageEnhance.Brightness(news_picture)
        news_picture = enhancer.enhance(0.95)
        draw = ImageDraw.Draw(news_picture)
        font_size = 35
        font = ImageFont.truetype(f"ttf{os.sep}gilroy-black.ttf", font_size)
        lines = []
        current_line = 6 * ' ' + list_text[0]
        for word in list_text[1:]:
            if font.getlength(current_line + ' ' + word) <= news_picture.width - 16:
                current_line += ' ' + word
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
        coord = (0, int(news_picture.height/2) + 50,
                news_picture.width, int(
            news_picture.height/2) + 55 + (len(lines) + 1) * font_size)
        im_crop = news_picture.crop(coord)
        enhancer = ImageEnhance.Brightness(im_crop)
        im_crop = enhancer.enhance(0.4)
        news_picture.paste(im_crop, coord)
        news_picture.paste(logo, (5, int(news_picture.height/2) + 54), logo)
        font_size = 35
        y = 0
        for line in lines:
            draw.text((8, int(news_picture.height/2 + 53 + y) ), line, font=font)
            y += font.getbbox(line)[3]
        font = ImageFont.truetype(f"ttf{os.sep}gilroy-medium.ttf", 20)
        _, _, w, _ = draw.textbbox((0, 0), "Champ_footbaall", font=font)
        coord1 = (0, coord[3] - 3,
                news_picture.width, coord[3] + font.size + 5)
        im_crop1 = news_picture.crop(coord1)
        enhancer = ImageEnhance.Brightness(im_crop1)
        im_crop1 = enhancer.enhance(0.2)
        news_picture.paste(im_crop1, coord1)
        draw.text((news_picture.width/2 - w/2,
                coord[3] + 1),
                "Champ_footbaall", font=font, align="center")
        news_picture.paste(logo_teleg, (int(news_picture.width/2 - w/2 - 35),
                                        coord[3] - 7),
                        logo_teleg)
        return news_picture
    


def news():
    timer = 120
    while True:
        bot = News(RSSNewsFetcher(), SimpleNewsProcessor(), TelegramNewsSender(), MongoDBNews())
        bot.run(config.rss_link)
        time.sleep(timer)


if __name__ == '__main__':
    bot = News(RSSNewsFetcher(), SimpleNewsProcessor(), TelegramNewsSender(), MongoDBNews())
    bot.run(config.rss_link)