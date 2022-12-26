import requests
from lxml import html

def news_parse():
    sess = requests.Session()
    sess.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.5304.63 Safari/537.36'
        })
    #parse_site = 'https://www.championat.com/football'
    parse_site = 'https://www.championat.com/news/football/1.html'

    response = sess.get(parse_site)
    tree = html.fromstring(response.text)
    news_text = tree.xpath('//div [@class="news _all"]//a[starts-with(@class,"news-item__title")]/text()')
    #news_text = tree.xpath('//ul/li/div[2]/a[1]/text()') 
    news_time =tree.xpath('//div  [@class="news _all"]//div[@class="news-item__time"]/text()') 
    #news_time = tree.xpath('//ul/li/div[@class="news-item__time"]/text()')
    #news_ref = tree.xpath('//div  [@class="news-item__content"]/a[1]/@href') 
    news_ref = tree.xpath('//div  [@class="news _all"]//a[1]/@href') 
    #news_ref = tree.xpath('//ul/li/div[2]/a[1]/@href') 
    #/html/body/div[7]/div[4]/div[2]/div/div[5]/ul/li[2]/div[2]/a[1]
    #news = []
    mass_ref = []
    news = {}

    for i in range(len(news_ref)):
        news_str = f'{news_time[i]} {news_text[i]}'
        news[news_str] = news_ref[i]
    return news

def descrp_news(news):
    sess = requests.Session()
    sess.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.5304.63 Safari/537.36'
        })
    j = 0
    for key,value in news.items():
        string_news = ""
        for cxx, stroka in value.items():    
            response = sess.get('https://www.championat.com'+cxx)
            tree1 = html.fromstring(response.text)
            #text_site = tree1.xpath('//[contains(@data-type, "news")]')
            text_site = tree1.xpath('//*[@data-type = "news"]//text()')
            for text in text_site:
                string_news += text.strip() + ' '
            #mass_ref.append(string_news)
            #news[key] = string_news
            news[j] = {stroka:string_news}
            j+=1
    return news

def get_one_news(cxx):
    string_news = ""
    sess = requests.Session()
    sess.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.5304.63 Safari/537.36'
        })
    response = sess.get('https://www.championat.com'+cxx)
    list_photo_ref = []
    tree1 = html.fromstring(response.text)
    #text_site = tree1.xpath('//[contains(@data-type, "news")]')
    text_site = tree1.xpath('//*[@data-type = "news"]//text()')
    #ref_photo = tree1.xpath('//img [@class = "lazyload"]/@data-src')
    ref_photo = tree1.xpath('//div [@class = "article-head__photo"]//@src')
    #ref_video = tree1.xpath('//div [@class="video js-social-embed-iframe _matchtv"]//@src')
    if len(ref_photo) != 0 :
        list_photo_ref.append(ref_photo[0])
    #elif len(ref_video) != 0 :
        #list_photo_ref.append(ref_video[0])
    else:
        list_photo_ref.append("http://2016.goldensite.ru/upload/iblock/814/814eaedad168e8d22c0ed40247c46f9d.jpg")
    j = 0
    for text in text_site:
        if text.startswith('\n'):
            j+=1
            if j >= 3:
                break
            else:
                continue
        j = 0
        string_news += text
            #string_news.strip()
    list_photo_ref.append(string_news)
    return list_photo_ref
#print(descrp_news(news_parse()))
        #news.reverse()
    #news.reverse()
 #   news_set =  ""
  #  for j in range(len(news)):
  #      news_set +=f'{news[j]}\n\n'
   # return news_set

#news_parse()