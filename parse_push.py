import threading
from xpath_ref import review_xpath_href, review_xpath_title, review_xpath_date
from xpath_ref import review_xpath_France_href, review_xpath_match_href
import requests
from lxml import html
import telebot
from youtube_parse import youtube_video, rutube_video
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
from config import TOKEN, user_id, User_agent, dict_site, rss_link, client_champ, mass_review, dict_matchtv
from user_mongo import get_push, get_list_user
from news_football import rss_news
from pict import news_pic
from datetime import datetime
import xmltodict


bot = telebot.TeleBot(TOKEN)
sess = requests.Session()
sess.headers.update(User_agent)



