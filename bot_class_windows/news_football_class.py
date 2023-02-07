import requests, re
from lxml import html
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import xmltodict

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

def get_one_news(cxx, query):
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
    ref_photo1 = tree1.xpath('//div [@class = "content-photo"]//@data-src')
    #ref_video = tree1.xpath('//div [@class="video js-social-embed-iframe _matchtv"]//@src')
    list_srt =['Видеоролик:','ПОЛНОСТЬЮ ИНТЕРВЬЮ ЧИТАЙТЕ НА «ЧЕМПИОНАТЕ».']

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
    if len(ref_photo) != 0 :
        list_photo_ref.append(ref_photo[0])
    elif len(ref_photo1) != 0 :
        list_photo_ref.append(ref_photo1[0])
    else:
        # try:
        #     list_photo_ref.append(req_yandex(query))
        # except Exception:
            #list_photo_ref.append("http://2016.goldensite.ru/upload/iblock/814/814eaedad168e8d22c0ed40247c46f9d.jpg")
            #list_photo_ref.append("https://catherineasquithgallery.com/uploads/posts/2021-02/1613259700_23-p-sinii-futbolnii-fon-28.jpg")
            list_photo_ref.append("https://img.championat.com/s/735x490/news/big/f/i/v-uefa-planirujut-sozdat-letnjuju-ligu-chempionov_1583405978161575552.jpg")
    for srt in list_srt:
        string_news = string_news.replace(srt,'')
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
                        logo = "https://img.championat.com/s/735x490/news/big/f/i/v-uefa-planirujut-sozdat-letnjuju-ligu-chempionov_1583405978161575552.jpg"
            except TypeError:
                continue
        if title != "":
            break
    return title, link.replace('https://',""), logo
    

def req_yandex(text):
    sess = requests.Session()
    sess.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.5304.63 Safari/537.36',
        })
    zxc = [czs for czs in text.split() if not czs.islower()]
    if len(zxc) < 3:
        text = '{} футбол'.format(' '.join(zxc))
    text = '%20'.join([req_text for req_text in text.split()])
    response = sess.get(f'https://yandex.ru/images/search?text={text}')#, params={'text':f'{text}'})
    #response = sess.get(f'https://www.google.ru/search', params={'q':f'{text}','tbm':'isch'})
    tree = html.fromstring(response.text)
    news_ref = tree.xpath('//img[@class="serp-item__thumb justifier__thumb"]/@src') 
    #news_ref = tree.xpath('//div[@class="bRMDJf islir"]/img/@src') youtube

    #soup = BeautifulSoup(response.text, 'lxml')
    #soup = BeautifulSoup(response.text, 'html.parser') 
    #script_img_tags = soup.find_all('script')
    #img_matches = re.findall(r"s='data:image/jpeg;base64,(.*?)';", str(script_img_tags))
    #for result in soup.select('div[jsname=r5xl4]'):
        #link = f"https://www.google.com{result.a['href']}"
    #print(news_ref[0])
    ref_pic = f'https:{news_ref[0]}'
    return ref_pic


def pil_pic(text):
    img = Image.open('champ.png')
 
    # Call draw Method to add 2D graphics in an image
    I1 = ImageDraw.Draw(img)
    
    # Custom font style and font size
    myFont = ImageFont.truetype('arkhip_font.ttf', 10)
    
    # Add Text to an image
    I1.text((10, 10), text, font=myFont, fill =(255, 0, 0))
    
    # Display edited image
    #img.show()
    
    # Save the edited image
    img.save("champ.png")
#pil_pic("«Зенит» получит больше 50% от будущей продажи Мантуана")
#req_yandex("«Тулуза» 14 футбол")
#print(descrp_news(news_parse()))
        #news.reverse()
    #news.reverse()
 #   news_set =  ""
  #  for j in range(len(news)):
  #      news_set +=f'{news[j]}\n\n'
   # return news_set

#news_parse()