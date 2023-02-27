
from pytube import Playlist, YouTube
import requests
import googleapiclient.discovery
from constants import mass_review
from bs4 import BeautifulSoup
import re
import time

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
    })


def bs4_youtube(query):
    base_video_url = f'https://www.youtube.com/playlist?list={query}'
    req = requests.get(base_video_url)
    send = BeautifulSoup(req.text, 'html.parser')
    search = send.find_all('script')
    key = '"watchEndpoint":{"videoId":"'
    title = ']},"title":{"runs":\[{"text":'
    asd = {}
    data = re.findall(key + r"([^*]{12})", str(search))
    data1 = re.findall(title + r"([^*]{150})" , str(search))
    if mass_review['Чемпионат НН 22-23. Городская лига'] == query:
        data1 = data1[:len(data1)-1]
        data1 = data1[::-1]
        data = data[:len(data1)] 
        data = data[::-1]
    i = 0
    for clear_title in data1[:60]:
        asd[clear_title[1:clear_title.find('}')-1]] = 'https://www.youtube.com/watch?v=' + data[i][:len(data[i])-1]
        i+=1
    return asd 

def youtube_video(channel, query='highlights'):
    req = requests.get(f'https://www.youtube.com/{channel}/videos')
    send = BeautifulSoup(req.text, 'html.parser')
    search = send.find_all('script')
    key = '"watchEndpoint":{"videoId":"'
    title = ']},"title":{"runs":\[{"text":'
    asd = {}
    data = re.findall(key + r"([^*]{12})", str(search))
    data1 = re.findall(title + r"([^*]{150})" , str(search))
    i = 0
    for clear_title in data1:
        if query in clear_title.lower():
            asd[clear_title[1:clear_title.find('}')-1]] = 'https://www.youtube.com/watch?v=' + data[i][:len(data[i])-1]
        i+=1
        continue
    return asd 


def rutube_video(channel="255003",query='обзор'):
    req = requests.get(f'https://rutube.ru/metainfo/tv/{channel}')
    send = BeautifulSoup(req.text, 'html.parser')
    search = send.find_all('script')
    key = '"video_url":"https://rutube.ru/video/'
    title = '"title":"'
    asd = {}
    time.sleep(1)
    data = re.findall(key + r"([^*]{32})", str(search))
    data1 = re.findall(title + r"([^*]{150})" , str(search))
    i = 0
    for clear_title in data1:
        if query in clear_title.lower():
            try:
                asd[clear_title[:clear_title.find('"')]] = 'https://rutube.ru/video/' + data[i]
            except IndexError:
                break
            i+=1
        continue
    return asd 
