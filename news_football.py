import requests
from lxml import html
import xmltodict
# import textwrap
from config import parse_site, User_agent, client_champ,rss_link, user_id, TOKEN
from datetime import datetime
import time
from pymongo import MongoClient, errors
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pict import news_pic
import telebot
import locale

bot = telebot.TeleBot(TOKEN)
sess = requests.Session()
sess.headers.update(User_agent)


def news():
    db = client_champ['users-table']
    users_col = db['users']
    timer = 120
    while True:
        try:
            if users_col.count_documents({'Push':True}) > 0:
                response = sess.get(rss_link)
                list_news = rss_news(response)
                if list_news is None:
                    time.sleep(timer)
                    continue
                else:
                    for news in list_news:
                        pic = news_pic(news['logo'], news['title'])
                        inst_view = f'https://t.me/iv?url=https%3A%2F%2F\
{news["link"]}&rhash=f610f320a497f8'
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
    sess = requests.Session()
    sess.headers.update(User_agent)
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
    sess = requests.Session()
    sess.headers.update(User_agent)
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
    client = MongoClient()
    dbc = client['json_champ']
    news_coll = dbc['news']
    asd = xmltodict.parse(response.text)
    list_news = []
    for news_list in asd['rss']['channel']['item']:
        link = news_list['link']
        title = news_list["title"].replace('&#039;','\'')
        locale.setlocale(locale.LC_TIME, ('en_US', 'UTF-8'))
        date = datetime.strptime(news_list['pubDate'].replace('+0300',"").strip(),'%a, %d %b %Y %H:%M:%S')
        locale.setlocale(locale.LC_TIME, ('ru_RU', 'UTF-8'))
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
                except TypeError:
                    continue
        dict_news = {
            'title':title,
            'link':link.replace('https://', ""), 
            'date':date,
            'logo':logo,
            'text': text,
            'content_importance':content_importance}
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
    sess = requests.Session()
    sess.headers.update(User_agent)
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
