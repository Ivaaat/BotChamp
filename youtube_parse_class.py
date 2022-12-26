"""
import requests, json

api_key = 'AIzaSyA4HqKqfNFbKXcm7xUVg1PdC2DKwxd8DwY'

channelid = 'c/trg'

base_video_url = 'https://www.youtube.com/'

base_search_url = 'https://www.googleapis.com/youtube/v3/search?'

first_url = base_search_url + 'key=' + api_key + "&channeid=" + channelid + '&part=snippet,id&order=date&maxResults=25'

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
    })

response = sess.get(first_url)
resp = json.load(response.text)
print(response.text)

"""
from pytube import Playlist, YouTube
import requests
import googleapiclient.discovery
from constants_class import mass_review
from bs4 import BeautifulSoup
import re

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
    })



# API information
def parse_youtube_ref(query):
    base_video_url = 'https://www.youtube.com/watch?v='
    api_service_name = "youtube"
    api_version = "v3"
    DEVELOPER_KEY = "AIzaSyCZWDIf-Ng27QBeR9bNo8XyPzPm9Ciig4Q"
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey = DEVELOPER_KEY)
    asd = {}
    request = youtube.playlistItems().list(
        part = 'snippet,contentDetails',
        playlistId = query,
        maxResults = 50,
        )
    '''
    request = youtube.search().list(
            part = 'snippet',
            #order="date",
            maxResults = 10,
            #channelId = 'UCC8ehCq2MShQF6IRuwReiuQ',
            q = query,
            fields="items(id(videoId),snippet(title))"
        )
    '''
    response = request.execute()
    
    if mass_review['Чемпионат НН 22-23. Городская лига'] == query:
        for  value in range(len(response['items']) - 1, 0, -1):
            asd[response['items'][value]['snippet']['title']] = base_video_url + response['items'][value]['contentDetails']['videoId']
    #return asd
    else:
        for  value in range(len(response['items'])):
            asd[response['items'][value]['snippet']['title']] = base_video_url + response['items'][value]['contentDetails']['videoId']
    return asd
    '''
    for value in mass_review.values():
        request = youtube.search().list(
            part = 'snippet',
            maxResults = 1,
            #channelId = 'UCC8ehCq2MShQF6IRuwReiuQ',
            q = value,
            fields="items(id(videoId),snippet(title))"
        )
        response = request.execute()
        #asd.append(base_video_url + response['items'][0]['id']['videoId'])
        asd[response['items'][0]['snippet']['title']] = base_video_url + response['items'][0]['id']['videoId']
    '''
    #return asd
        #response = request.execute()
    #return base_video_url + response['items'][0]['id']['videoId']
    #response1 = request1.execute()
    # Print the results
    #print(response)
#print(parse_youtube_ref('Обзор матча чемпионата Италии'))
    #print(base_video_url + response['items'][0]['id']['videoId'])

def you_pytube(query):
    try:
        base_video_url = f'https://www.youtube.com/playlist?list={query}'
        playlist = Playlist(base_video_url)
        asd = {}
        # for video in playlist.videos:
        #     asd[video.title] = video.watch_url
        #     asd.append(video.title)
        #     print ("")
        i = 0
        for url in playlist.video_urls:
            #asd.append(url)
            yt = YouTube(url)
            print(yt.title + url)
            asd[yt.title] = url
            #print(url + playlist.videos[i].title)
            i+=1
            # if i == 20:
            #     break
        
        return asd
    except :
        print('Че за хуйня')

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
        # if "accessibility" not in clear_title:
        #     continue
        asd[clear_title[1:clear_title.find('}')-1]] = 'https://www.youtube.com/watch?v=' + data[i][:len(data[i])-1]
        #asd[re.findall('[а-яА-ЯёЁ]',clear_title)] = 'https://www.youtube.com/watch?v=' + data[::3][i][1:len(data[::3][i])]
        i+=1

    return asd 

#bs4_youtube(mass_review['Чемпионат НН 22-23. Городская лига'])
#bs4_youtube(mass_review['Россия🇷🇺'])

    
