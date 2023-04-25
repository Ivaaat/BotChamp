import requests
from bs4 import BeautifulSoup
import re
from config import User_agent, dict_rutube, dict_youtube, bot
from config import dict_footbal_video, mass_review, client_champ
from xpath import review_xpath_href, review_xpath_title
from xpath import review_xpath_date, review_xpath_match_href, review_xpath_France_href
from lxml import etree, html
import time
import threading
import pymongo
from pymongo import errors
from datetime import datetime

db = client_champ['json_champ']
video_coll = db['video']


indexes = [name_index['name'] for name_index in video_coll.list_indexes()] 
if 'desc_1' not in indexes:
    video_coll.create_index([("desc", pymongo.ASCENDING)], unique=True)


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
        desc = clear_title[1:clear_title.find('}')-1]
        date = desc.split()[-1]
        b = i
        while '.' not in date:
            desc = data1[b-1][1:data1[b-1].find('}')-1]
            date = desc.split()[-1]
            b-=1
        try:
            clear_date = datetime.strptime(date,"%d.%m.%Y")
        except ValueError:
            try:
                clear_date = datetime.strptime(date,"%d.%m.%y")
            except ValueError:
                continue
        asd[desc] = '\
https://www.youtube.com/watch?v=' + data[i][:len(data[i])-1], clear_date
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
            desc = clear_title[1:clear_title.find('}')-1]
            date = desc.split()[-1]
            b = i
            while '.' not in date:
                desc = data1[b-1][1:data1[b-1].find('}')-1]
                date = desc.split()[-1]
                b-=1
            try:
                clear_date = datetime.strptime(date,"%d.%m.%Y")
            except ValueError:
                clear_date = datetime.strptime(date,"%d.%m.%y")
            asd[desc] = '\
https://www.youtube.com/watch?v=' + data[i][:len(data[i])-1], clear_date
        i += 1
        continue
    return asd


def rutube_video(query="обзор", i=21):
    video_dict = {}
    for j in range(1,i):
        req = requests.get(f'https://rutube.ru/metainfo/tv/255003/page-{j}')
        send = BeautifulSoup(req.text, 'html.parser')
        video_title = etree.HTML(str(send))
        title = video_title.xpath('//section/a/div/img/@alt')
        video = video_title.xpath('//div/section/a/@href')
        for num_list in range(len(video)):
            if query.upper() in title[num_list].upper():
                date = title[num_list].split()[-1]
                b = num_list
                while '.' not in date:
                    date = title[b-1].split()[-1]
                    b-=1
                try:
                    clear_date = datetime.strptime(date,"%d.%m.%Y")
                except ValueError:
                    try:
                        clear_date = datetime.strptime(date,"%d.%m.%y")
                    except ValueError:
                        continue
                video_dict[title[num_list]] = video[num_list], clear_date
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
        dates = review_list_href[i].split('/')
        date = '.'.join([dates[5],dates[4],dates[3]])
        if len(list_href) == 0:
            list_href = tree.xpath(review_xpath_France_href)
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
        dict_review[title] = review_ref, datetime.strptime(date,"%d.%m.%Y")
    return dict_review


def send_and_bd(func, dict_query):
    db = client_champ['users-table']
    users_col = db['users']
    if video_coll.count_documents({}) == 0:
        add_video(func, dict_query)
        print('добавляю все')
    if func == bs4_youtube:
        return
    while True:
        try:
            for key, query in dict_query.items():
                video_dict = func(query)
                for desc_video, link_date in video_dict.items():
                    try:
                        video_coll.insert_one({
                                        "desc": desc_video, 
                                        "link": link_date[0], 
                                        "country":key,
                                        'date':link_date[1]})
                        for id in users_col.find({'Push':True}):
                            int_id = int(id['_id'])
                            msg = bot.send_message(int_id, "{}\n {}".format(desc_video, link_date[0]))
                            if int_id < 0:
                                bot.pin_chat_message(int_id, msg.message_id)
                    except errors.DuplicateKeyError:
                        break
                time.sleep(120)
            time.sleep(1800)
        except Exception as e:
            bot.send_message(377190896, f"пиздарики{key}\n {e}")
            time.sleep(1800)
                

def add_video(func, dict_query):
    for key, query in dict_query.items():
        video_dict = func(query)
        list_video = [{f:a} for f,a in video_dict.items()]
        list_video.reverse()
        for video_dicts in list_video:
            for desc, link_date in video_dicts.items():
                try:
                    video_coll.insert_one({"desc": desc, 
                                           "link": link_date[0], 
                                           "country":key, 
                                           'date':link_date[1]})
                except Exception:
                    continue


def update_rutube():
    j = 2
    if video_coll.count_documents({}) == 0:
        j = 21
        print('добавляю все')
    while True:
        try:
            video_rutube = rutube_video(i = j)
            for title, video_date in video_rutube.items():
                try:
                    for country, query in dict_rutube.items():
                        if query.upper() in title.upper():
                            video_coll.insert_one({
                                                "desc": title, 
                                                "link": video_date[0],
                                                'date':  video_date[1], 
                                                "country":country})
                            break
                except errors.DuplicateKeyError:
                    break
            time.sleep(1800)
        except Exception as e:
            bot.send_message(377190896, f"пиздарики\n {e}")
            time.sleep(1800)


threading.Timer(1, update_rutube).start()
threading.Timer(1, send_and_bd, [youtube_video, dict_youtube]).start()
threading.Timer(1, send_and_bd, [football_video, dict_footbal_video]).start()
threading.Timer(1, send_and_bd, [bs4_youtube, mass_review]).start()

