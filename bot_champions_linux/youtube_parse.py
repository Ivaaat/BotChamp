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
import requests
import googleapiclient.discovery
from constants import mass_review

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