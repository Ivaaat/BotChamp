import requests
from bs4 import BeautifulSoup
import re
from config import User_agent, dict_rutube, dict_youtube, dict_footbal_video, mass_review, TOKEN
from xpath_ref import review_xpath_href, review_xpath_title
from xpath_ref import review_xpath_date, review_xpath_match_href, review_xpath_France_href
from lxml import etree, html
import time
from pymongo import MongoClient
import telebot
import threading
bot = telebot.TeleBot(TOKEN) 

client = MongoClient()
db = client['json_champ']
video_coll = db['video']


def bs4_youtube(query):
    base_video_url = f'https://www.youtube.com/playlist?list={query}'
    req = requests.get(base_video_url)
    send = BeautifulSoup(req.text, 'html.parser')
    search = send.find_all('script')
    key = r'"watchEndpoint":{"videoId":"'
    title = r']},"title":{"runs":\[{"text":'
    asd = {}
    data = re.findall(key + r"([^*]{12})", str(search))
    data1 = re.findall(title + r"([^*]{150})", str(search))
    i = 0
    for clear_title in data1[:60]:
        asd[clear_title[1:clear_title.find('}')-1]] = '\
https://www.youtube.com/watch?v=' + data[i][:len(data[i])-1]
        i += 1
    return asd


def youtube_video(query):
    search_query, link = query.split('_')
    req = requests.get(f'https://www.youtube.com/{link}/videos')
    send = BeautifulSoup(req.text, 'html.parser')
    search = send.find_all('script')
    key = r'"watchEndpoint":{"videoId":"'
    title = r']},"title":{"runs":\[{"text":'
    asd = {}
    data = re.findall(key + r"([^*]{12})", str(search))
    data1 = re.findall(title + r"([^*]{150})", str(search))
    i = 0
    for clear_title in data1:
        if search_query in clear_title:
            asd[clear_title[1:clear_title.find('}')-1]] = '\
https://www.youtube.com/watch?v=' + data[i][:len(data[i])-1]
        i += 1
        continue
    return asd


def rutube_video(query="обзор"):
    video_dict = {}
    #for j in range(1,21):
    #    time.sleep(1)
    req = requests.get(f'https://rutube.ru/metainfo/tv/255003/')#page-{j}')
    send = BeautifulSoup(req.text, 'html.parser')
    video_title = etree.HTML(str(send))
    title = video_title.xpath('//section/a/div/img/@alt')
    video = video_title.xpath('//div/section/a/@href')
    for i in range(len(video)):
        if query.upper() in title[i].upper():
            video_dict[title[i]] = video[i]
    return video_dict



def football_video(link):
    dict_review = {}
    sess = requests.Session()
    sess.headers.update(User_agent)
    response = sess.get(link)
    tree = html.fromstring(response.text)
    review_list_href = tree.xpath(review_xpath_href)
    review_list_title = tree.xpath(review_xpath_title)
    review_list_date = tree.xpath(review_xpath_date)
    for i in range(len(review_list_href)):
        review_title = review_list_title[i].replace(
            'видео обзор матча', " ")
        response = sess.get(review_list_href[i])
        tree = html.fromstring(response.text)
        list_href = tree.xpath(review_xpath_match_href)
        ends = None
        if len(list_href) == 0:
            list_href = tree.xpath(review_xpath_France_href)
        try:
            review_ref = list_href[0].split('\'')[1]
        except IndexError:
            review_ref = list_href[0].split('=')[1]
        title = '{} {}'.format(review_title.strip(), 
                               review_list_date[i].strip())
        dict_review[title] = review_ref
    return dict_review
        

def send_and_bd(func, dict_query):
    try:
        while True:
            for key, query in dict_query.items():
                video_dict = func(query)
                for desc_video, link in video_dict.items():
                    try:
                        video_coll.insert_one({"desc": desc_video, 
                                        "link": link, 
                                        "country":key})
                        bot.send_message(377190896, f"{desc_video}\n{link}")
                    except Exception:
                        break
                time.sleep(120)
            time.sleep(1800)
    except Exception as e:
        bot.send_message(377190896, f"пиздарики{key}\n {e}")
                
# send_and_bd(rutube_video,dict_rutube)
#send_and_bd(youtube_video,dict_youtube)
#send_and_bd(football_video,dict_footbal_video)
threading.Timer(1, send_and_bd, [rutube_video, dict_rutube]).start()
threading.Timer(2, send_and_bd, [youtube_video, dict_youtube]).start()
threading.Timer(3, send_and_bd, [football_video, dict_footbal_video]).start()

def add_video(func, dict_query):
    for key, query in dict_query.items():
        video_dict = func(query)
        list_video = [{f:a} for f,a in video_dict.items()]
        list_video.reverse()
        for video_dicts in list_video:
            for desc, link in video_dicts.items():
                try:
                    #time.sleep(0.1)
                    video_coll.insert_one({"desc": desc, "link": link, "country":key})
                except Exception:
                    continue
        time.sleep(10)
def delete_video():
    video_coll.delete_many({})
#delete_video()

# add_video(bs4_youtube, mass_review)
# add_video(rutube_video,dict_rutube)
# add_video(youtube_video,dict_youtube)
# add_video(football_video, dict_footbal_video)


