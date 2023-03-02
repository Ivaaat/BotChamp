import requests
from config import mass_review
from bs4 import BeautifulSoup
import re
import time
from lxml import etree


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
    if mass_review['Чемпионат НН 22-23. Городская лига'] == query:
        data1 = data1[:len(data1)-1]
        data1 = data1[::-1]
        data = data[:len(data1)]
        data = data[::-1]
    i = 0
    for clear_title in data1[:60]:
        asd[clear_title[1:clear_title.find('}')-1]] = '\
            https://www.youtube.com/watch?v=' + data[i][:len(data[i])-1]
        i += 1
    return asd


def youtube_video(channel, query='highlights'):
    req = requests.get(f'https://www.youtube.com/{channel}/videos')
    send = BeautifulSoup(req.text, 'html.parser')
    search = send.find_all('script')
    key = r'"watchEndpoint":{"videoId":"'
    title = r']},"title":{"runs":\[{"text":'
    asd = {}
    data = re.findall(key + r"([^*]{12})", str(search))
    data1 = re.findall(title + r"([^*]{150})", str(search))
    i = 0
    for clear_title in data1:
        if query in clear_title.lower():
            asd[clear_title[1:clear_title.find('}')-1]] = '\
https://www.youtube.com/watch?v=' + data[i][:len(data[i])-1]
        i += 1
        continue
    return asd


def rutube_video(channel="255003", query='обзор'):
    req = requests.get(f'https://rutube.ru/metainfo/tv/{channel}')
    send = BeautifulSoup(req.text, 'html.parser')
    asd = {}
    video_title = etree.HTML(str(send))
    title = video_title.xpath('//section/a/div/img/@alt')
    video = video_title.xpath('//div/section/a/@href')
    for i in range(len(video)):
        if query in title[i].lower():
            asd[title[i]] = video[i]
    return asd
