import requests
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
import time
import datetime
from bs4 import BeautifulSoup


options = Options()
#options.headless = True
options.add_argument('--headless')
today_date = datetime.datetime.now().strftime("%Y-%m-%d")
EXE_PATH = 'chromedriver.exe' # EXE_PATH это путь до ранее загруженного нами файла chromedriver.exe
driver = webdriver.Chrome(executable_path=EXE_PATH, chrome_options = options)
driver.implicitly_wait(10)
#driver = webdriver.Remote(
   #command_executor='http://127.0.0.1:4444/wd/hub',
   #desired_capabilities=DesiredCapabilities.CHROME)
#driver.set_window_size(1440, 900)

class Live:
    def __init__(self) -> None:
        driver.get(f'https://www.championat.com/stat/football/#{str(today_date)}')
        self.start_time = time.time()
        self.elemets_result = driver.find_elements(By.XPATH,'//div[@class = "results-item__result"]')
        self.elemets_status = driver.find_elements(By.XPATH,'//div[@class = "results-item__status"]')
        self.elemets_time = driver.find_elements(By.XPATH,'//div[@class = "results-item__title-date"]')   
        # self.element_result = [elemets_result[i].text for i in range(len(elemets_result))]
        # self.elemets_status = [elemets_status[i].text for i in range(len(elemets_status))]
        # self.elemets_time = [elemets_time[i].text for i in range(len(elemets_time))]

        self.site = f'https://www.championat.com/stat/football/#{str(today_date)}'
        self.sess = requests.Session()
        self.sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
    })  
        self.response = self.sess.get(self.site)
        self.tree = html.fromstring(self.response.text)
        #self.today_match = '//li  [@class="seo-results__item"]//text()'
        #self.all_today = '//* [starts-with(@class,"seo-results__")]//text()'
        self.all_today = '//* [@class = "seo-results__item" or @class = "seo-results__tournament"] /a/text()'
        self.today_match = '//* [@class = "seo-results__item"]//text()'
        self.today_name = '//* [@class = "seo-results__tournament"]/a/text()'

    
    def view_live(self):
        self.today = self.tree.xpath(self.today_match)
        self.name_tournam = self.tree.xpath(self.today_name)
        self.all_match  = self.tree.xpath(self.all_today)
        list_live = []
        a = 0 
        separator = ""
        for j in range(len(self.name_tournam)):
            if j == (len(self.name_tournam) - 1):
                end_num = len(self.all_match)
            else:
                end_num = self.all_match.index(self.name_tournam[j+1])
            list_live.append(separator + self.name_tournam[j])
            start_num  = self.all_match.index(self.name_tournam[j]) + 1
            asdv = self.all_match[start_num:end_num]
            for i in range(len(asdv)):
                list_live.append('{} | {} | {} | {}'.format(self.elemets_time[a].text,
                                                            asdv[i],
                                                            self.elemets_status[a].text,
                                                            self.elemets_result[a].text))
                a += 1
            separator = "\n"
        #return list_live
        self.time_code = (time.time()- self.start_time)
        return ('\n'.join(list_live)) 





#live = Live()
#casxc  = live.bs4_live()

#print()
'''
time_code1 = (time.time()- start_time)
start_time = time.time()
asdc  = live.view_live()
time_code2 = (time.time()- start_time)

print()
'''


        
