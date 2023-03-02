import threading
from xpath_ref import review_xpath_href, review_xpath_title, review_xpath_date
from xpath_ref import review_xpath_France_href, review_xpath_match_href
import requests
from lxml import html
import telebot
from youtube_parse import youtube_video, rutube_video
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
from config import TOKEN, user_id, User_agent, dict_site, rss_link
from user_mongo import get_push, get_list_user
from news_football import rss_news
from pict import news_pic

bot = telebot.TeleBot(TOKEN)
sess = requests.Session()
sess.headers.update(User_agent)


def parse_for_push(name):
    url = dict_site[name[0]]
    response = sess.get(url)
    tree = html.fromstring(response.text)
    review_list_lxml_href = tree.xpath(review_xpath_href)
    review_list_lxml_title = tree.xpath(review_xpath_title)
    review_list_lxml_date = tree.xpath(review_xpath_date)
    asd = []
    if len(review_list_lxml_href) == 0:
        review_list_lxml_href = tree.xpath(review_xpath_France_href)
    for i, url_ref in enumerate(review_list_lxml_href):
        response_ref = sess.get(url_ref)
        tree_ref = html.fromstring(response_ref.text)
        review_href_list = tree_ref.xpath(review_xpath_match_href)
        if len(review_href_list) == 0:
            review_href_list = tree_ref.xpath(review_xpath_France_href)
        review_ref = review_href_list[0][review_href_list[0].find('https'):
                                         len(review_href_list[0])]
        asd.append([(review_list_lxml_title[i].replace(
                    'видео обзор матча', " | ") +
                     review_list_lxml_date[i]), review_ref])
    return dict(asd)


def news():
    response = sess.get(rss_link)
    _, old_link, _ = rss_news(response)
    while True:
        try:
            timer = 120
            list_user_push_true = [
                user_id for user_id in get_list_user() if get_push(user_id)]
            if len(list_user_push_true) > 0:
                response = sess.get(rss_link)
                new_news, new_link, logo = rss_news(response)
                if new_link != old_link:
                    pic = news_pic(logo, new_news)
                    inst_view = f'https://t.me/iv?url=https%3A%2F%2F\
{new_link}&rhash=f610f320a497f8'
                    markup = InlineKeyboardMarkup()
                    markup.add(InlineKeyboardButton(new_news, url=inst_view))
                    old_link = new_link
                    for id in list_user_push_true:
                        bot.send_photo(id, pic, reply_markup=markup)
        except Exception:
            bot.send_message(user_id, str('def news\n'))
            time.sleep(timer)
        time.sleep(timer)


def video(func, *args):
    old_video_dict = func(args)
    while True:
        timer = 1800
        list_user_true = [user_id for user_id in get_list_user()
                          if get_push(user_id)]
        try:
            new_video_dict = func(args)
            for desc_video, ref in new_video_dict.items():
                if desc_video in old_video_dict:
                    break
                for id in list_user_true:
                    bot.send_message(user_id, str(f'{args[0]}\nВышел обзор\n'))
                    message = bot.send_message(id, f"{desc_video}\n{ref}")
                    if id < 0:
                        bot.pin_chat_message(id, message.message_id)
                old_video_dict[desc_video] = ref
        except Exception:
            bot.send_message(user_id,
                             str(f'{args[0]}\nexcept parse youtube\n'))
            time.sleep(timer)
        time.sleep(timer)


def start_push():
    threading.Thread(target=news).start()
    threading.Timer(1, video, [rutube_video, 'рутуб', "255003"]).start()
    threading.Timer(1, video, [youtube_video, 'spain', "@okkosport",
                               'ла лига.']).start()
    # threading.Timer(1, video, [youtube_video,
    #                            'france', "@Ligue1official"]).start()
    threading.Timer(1, video, [parse_for_push, 'england']).start()
    threading.Timer(10, video, [parse_for_push, 'france']).start()
