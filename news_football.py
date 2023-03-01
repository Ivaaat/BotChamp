import requests
from lxml import html
import xmltodict
# import textwrap
from config import parse_site, User_agent


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


def get_one_news(link, query):
    string_news = ""
    sess = requests.Session()
    sess.headers.update(User_agent)
    response = sess.get('{}{}'.format(parse_site, link))
    list_photo_ref = []
    tree1 = html.fromstring(response.text)
    text_site = tree1.xpath('//*[@data-type = "news"]/p//text()')
    ref_photo = tree1.xpath('//div [@class = "article-head__photo"]//@src')
    ref_photo1 = tree1.xpath('//div [@class = "content-photo"]//@data-src')
    list_black = ['Полностью интервью', 'Новость по теме', 'Видеоролик:']
    clear_text = text_site
    for srt in text_site:
        for word in list_black:
            if word in srt:
                i = text_site.index(srt)
                clear_text = text_site[:i]
                break
    # list_text = textwrap.wrap(' '.join(clear_text).strip(),width=40)
    string_news = ' '.join(clear_text)
    if len(ref_photo) != 0:
        list_photo_ref.append(ref_photo[0])
    elif len(ref_photo1) != 0:
        list_photo_ref.append(ref_photo1[0])
    else:
        list_photo_ref.append(
            "https://img.championat.com/s/735x490/news/big/f/i/\
                v-uefa-planirujut-sozdat-letnjuju-ligu-\
                    chempionov_1583405978161575552.jpg")
    list_photo_ref.append(string_news)
    return list_photo_ref


def rss_news(response):
    asd = xmltodict.parse(response.text)
    title = ""
    for news_list in asd['rss']['channel']['item']:
        for news in news_list['category']:
            try:
                if news['@domain'] == 'content_importance':
                    link = news_list['link']
                    title = news_list["title"]
                    try:
                        logo = news_list['enclosure']['@url']
                    except KeyError:
                        logo = "https://img.championat.com/\
                            s/735x490/news/big/f/i/v-uefa-\
                                planirujut-sozdat-letnjuju-\
                                    ligu-chempionov_1583405978161575552.jpg"
            except TypeError:
                continue
        if title != "":
            break
    return title, link.replace('https://', ""), logo


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
