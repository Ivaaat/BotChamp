import requests
from lxml import html
import xmltodict
from config import parse_site, User_agent, rss_link, user_id, TOKEN, db, dbs
from datetime import datetime
import time
from pymongo import MongoClient, errors
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pict import news_pic
import telebot
import pymongo

bot = telebot.TeleBot(TOKEN)
sess = requests.Session()
sess.headers.update(User_agent)
client = MongoClient()


news_coll = db['news']
indexes = [name_index['name'] for name_index in news_coll.list_indexes()] 
if 'link_1' not in indexes:
    news_coll.create_index([("link", pymongo.ASCENDING)], unique=True)

def news():
    users_col = dbs['users']
    timer = 120
    while True:
        try:
            response = sess.get(rss_link)
            list_news = rss_news(response)
            if list_news is None:
                time.sleep(timer)
                continue
            else:
                for news in list_news:
                    pic = news_pic(news['logo'], news['title'])
                    inst_view = f'''https://t.me/iv?url=https%3A%2F%2F\
{news["link"]}&rhash=f610f320a497f8'''
                    markup = InlineKeyboardMarkup()
                    markup.add(InlineKeyboardButton(news['title'], url=inst_view))
                    for id in users_col.find({'Push':True}):
                        bot.send_photo(id['_id'], pic, reply_markup=markup)
            time.sleep(timer)
        except Exception:
            bot.send_message(user_id, str('def news\n'))
            time.sleep(timer)


threading.Thread(target=news).start()


def news_parse():
    response = sess.get(f'{parse_site}/news/football/1.html')
    tree = html.fromstring(response.text)
    news_text = tree.xpath(
        '//div [@class="news _all"]//\
            a[starts-with(@class,"news-item__title")]/text()')
    news_time = tree.xpath(
        '//div  [@class="news _all"]//div[@class="news-item__time"]/text()')
    news_ref = tree.xpath(
        '//div  [@class="news _all"]//a[1]/@href')
    news = {}
    for i in range(len(news_ref)):
        news_str = f'{news_time[i]} {news_text[i]}'
        news[news_str] = news_ref[i]
    return news


def get_one_news(link):
    string_news = ""
    response = sess.get(link)
    tree1 = html.fromstring(response.text)
    text_site = tree1.xpath('//*[@data-type = "news"]/p//text()')
    list_black = ['Полностью интервью', 'Новость по теме', 'Видеоролик:']
    clear_text = text_site
    for srt in text_site:
        for word in list_black:
            if word in srt:
                i = text_site.index(srt)
                clear_text = text_site[:i]
                break
    string_news = ' '.join(clear_text)
    return string_news


def rss_news(response):
    asd = xmltodict.parse(response.text)
    list_news = []
    for news_list in asd['rss']['channel']['item']:
        link = news_list['link']
        title = news_list["title"].replace('&#039;','\'')
        time = news_list['pubDate'].split()[4].split(':')
        date = ' '.join([datetime.now().strftime("%Y-%m-%d"),'{}:{}'.format(time[0],time[1])])
        try:
            logo = news_list['enclosure']['@url']
        except KeyError:
            logo = "https://img.championat.com/\
s/735x490/news/big/f/i/v-uefa-\
planirujut-sozdat-letnjuju-\
ligu-chempionov_1583405978161575552.jpg"
        text = get_one_news(link)
        for news in news_list['category']:
                content_importance = False
                try:
                    if news['@domain'] == 'content_importance':
                        content_importance = True
                        break
                except TypeError:
                    continue
        dict_news = {
            'title':title,
            'link':link.replace('https://', ""), 
            'date':date,
            'logo':logo,
            'text': text,
            'content_importance':content_importance}
        list_news.append(dict_news)
        try:
            news_coll.insert_one(dict_news)
            if dict_news['content_importance']:
                list_news.append(dict_news)
        except errors.DuplicateKeyError:
            if len(list_news) == 0:
                return None
            else:
                return list_news


def req_yandex(text):
    zxc = [czs for czs in text.split() if not czs.islower()]
    if len(zxc) < 3:
        text = '{} футбол'.format(' '.join(zxc))
    text = '%20'.join([req_text for req_text in text.split()])
    response = sess.get(f'https://yandex.ru/images/search?text={text}')
    tree = html.fromstring(response.text)
    news_ref = tree.xpath(
        '//img[@class="serp-item__thumb justifier__thumb"]/@src')
    ref_pic = f'https:{news_ref[0]}'
    return ref_pic
