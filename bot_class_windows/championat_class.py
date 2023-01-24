from xpath_ref_class import *
import requests
from lxml import html
from constants_class import mass_contry, mass_review, parse_site
import time
from pymongo import MongoClient
from datetime import datetime, timedelta
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
    })


client = MongoClient()
db = client['json_champ']
users_col = db['users']


class Championat:
    def __init__(self,country = "") :
        self.country = country
        self.url = parse_site
        self.url_calendar = ""
        self.response_text = ""
        self.tree = ""
        self.calendar = {}
        #self.dict_table = {}
        self.tour = 1
        self.num_tour = []
        self.list_match = []
        self.list_datematch = []
        self.list_result = []
        self.list_games = []
        self.list_teams = []
        self.list_points = []
        self.list_result_six_matches = []
        self.list_ref_logo = []
        
        if self.country == "":
            self.country = "germany"
            
        self.url_championat = f'{self.url}/football/_{self.country}.html'

        response = sess.get(self.url_championat)
        self.response_text = response.text
        self.tree = html.fromstring(self.response_text)
    '''
    def get_response_championat(self):
        response = sess.get(self.url_championat)
        self.response_text = response.text
        self.tree = html.fromstring(self.response_text)
    '''
    



    def get_response_calendar(self):
        #response = sess.get(self.url_championat)
        #tree = html.fromstring(response.text)
        #parse_text = tree.xpath(parse_xpath_text)
        parse_calendar = self.tree.xpath(parse_xpath_text)
        self.url_calendar = f'{parse_site}{parse_calendar[0]}calendar'
        response = sess.get(self.url_calendar)  
        self.response_text = response.text
        self.tree = html.fromstring(self.response_text)

    def get_match(self):
        list_match = self.tree.xpath(parse_xpath_match)
        for i in range(0,len(list_match),2):
            self.list_match.append(' - '.join(list_match[i:i + 2]))
        return self.list_match
    
    def get_result(self):
        list_result = self.tree.xpath(parse_xpath_result)
        for i in range(0,len(list_result)):
            self.list_result.append(list_result[i].strip())
    
    def get_date(self):
        list_datematch = self.tree.xpath(date_xpath_match)
        for i in range(0,len(list_datematch)):
            self.list_datematch.append (" ".join(list_datematch[i].split()))
        return self.list_datematch

    def get_tour(self):
        list_tour = self.tree.xpath(num_xpath_tour)
        self.num_tour = list_tour
        self.tour = int(((len(set(list_tour))/2) + 1)/2)
        
    
    def request_calendar(self):
        tree = html.fromstring(self.response)
        parse_text = tree.xpath(parse_xpath_text)
        url = f'{parse_site}{parse_text[0]}calendar'
        response = sess.get(url)
        return response.text

    def get_teams(self):
        self.list_teams = self.tree.xpath(teams_xpath)

    def get_games(self):
         self.list_games = self.tree.xpath(games_xpath)

    def get_points(self):
        self.list_points = self.tree.xpath(points_xpath)

    def get_result_six_matches(self):
        self.list_result_six_matches = self.tree.xpath(results_xpath)

    def get_logo(self):
        self.list_ref_logo = self.tree.xpath(logo_ref_xpath)

        

    def get_keyboard():
        pass


            
class Calendar(Championat):
    def get_calendar(self):
        self.get_response_calendar()
        self.get_date()
        self.get_match()
        self.get_result()
        self.get_tour()
        for i in range(0,len(self.num_tour),self.tour):
            name_date = self.list_datematch[i:self.tour+i][0][:10] + '-' + self.list_datematch[i:self.tour+i][self.tour-1][:10]
            if '– : –' not in self.list_result[i:self.tour+i][self.tour-1]  :
                self.calendar['Тур ' + str(self.num_tour[i]) +' | '+ name_date +'| закончен'] =[
                                                            self.list_datematch[i:self.tour+i],
                                                            self.list_match[i:self.tour+i],
                                                            self.list_result[i:self.tour+i]
                                                            ]
            else:
                self.calendar['Тур ' + str(self.num_tour[i]) +' | '+ name_date] =[
                                                            self.list_datematch[i:self.tour+i],
                                                            self.list_match[i:self.tour+i],
                                                            self.list_result[i:self.tour+i]
                                                            ]
        return self.calendar


class Table(Championat):
    def __init__(self,country):
        super().__init__(country)
        self.dict_table = {}
    def get_table(self):
        self.get_teams()
        self.get_games()
        self.get_points()
        self.get_result_six_matches()
        self.get_logo()
        results = []
        num_match = 6
        for i in range(0, len(self.list_result_six_matches), num_match):
            results.append(self.list_result_six_matches[i : i + num_match])
        #картинки эмблем команд
        for i in range(len(self.list_teams)):
            self.dict_table[self.list_teams[i]] = {
            'Игры':int(self.list_games[i]),
            'Очки':int(self.list_points[i].strip()),
            'Последние результаты\n': '\n\n'.join(results[i]), 
            'Лого': self.list_ref_logo[i]
            }
        return self.dict_table
    

class Team(Championat):
    def __init__(self, name_team, dict_table_team):
        self.name_team = name_team
        self.dict_table_team = dict_table_team
        self.result_title = ""
        self.logo_list = []
        self.logo_ref_team = ""
    def get_logo(self):
        url1 = f'{parse_site}' + self.dict_table_team[self.name_team]['Лого']
        response1 = sess.get(url1)
        tree = html.fromstring(response1.text)
        self.logo_list = tree.xpath(logo_xpath)
        self.logo_ref_team = self.logo_list[0]
        self.result_title +=  '\n' + 'Последние результаты:\n' + self.dict_table_team[self.name_team]['Последние результаты\n']
        
    def get_calendar():
        pass
    def get_table():
        pass



def add_db(name, name_champ):
    country =  db[name]
    calendar = Calendar(name)
    calendar.get_response_calendar()
    calendar.get_date()
    calendar.get_match()
    calendar.get_result()
    calendar.get_tour()
    table = Table(name)
    table.get_table()
    dac = [calendar.num_tour[i] + " " + calendar.list_datematch[i] + " | " + calendar.list_match[i] + " | " + calendar.list_result[i]  for i in range(len(calendar.num_tour))]
    dac.sort(key = sortByAlphabet)
    dict_champ = {}
    #logo = {}
    dict_champ['Чемпионат'] = name_champ
    for i, name_team in enumerate(table.list_teams):
        games = [dac[i][2:].strip() for i in range(len(dac)) if name_team in dac[i]]
        # url = f'{parse_site}' + table.list_ref_logo[i]
        # response = sess.get(url)
        # tree = html.fromstring(response.text)
        # logo_list = tree.xpath(logo_xpath)
        dict_champ[name_team]={
                            'Таблица':{
                                        "Очки" : table.list_points[i],
                                        "Игры": table.list_games[i]
                                    },

                            'Календарь': games,
        }
        #logo[name_team] = logo_list[0]
        #country.update_one({"Чемпионат": '2022/2023'}, {'$set':{'Лого':{name_team:logo_list[0]}}})
        #country.update_one({"Чемпионат": '2022/2023'}, {'$set':{dict_champ[name_team]['Таблица']["Очки"]:table.list_points[i]}})
    #country.update_one({"Чемпионат": '2022/2023'}, {'$set':dict_champ,'$set':{'Лого':logo}})
    country.update_one({"Чемпионат": '2022/2023'}, {'$set':dict_champ})
    get_cal(name, name_champ)

def get_logo(db_name, name):
    country =  db[db_name]
    logo = country.find_one({"Чемпионат": '2022/2023'})
    return logo["Лого"][name]

def get_cal(name, name_champ):
    country =  db[name]
    calendar = country.find_one({"Чемпионат": name_champ})
    i = 0
    asd = {}
    for j in range(40):
        try:
            list_table = []
            for team, stat in calendar.items():
                if team not in ['_id','Чемпионат','Календарь','Лого']:
                        table_str = '{}'.format(stat['Календарь'][j])
                        if table_str in list_table:
                            continue
                        list_table.append(table_str)
            i+=1
            list_table.sort(key = lambda date: datetime.strptime(sort_date(date), '%d-%m-%Y %H:%M'))
            for fdf in list_table:
                if fdf.endswith('– : –'):
                    ends = False
                    break
                ends = True
            asd[f'Тур {i}'] = {'Матчи':list_table,
                                'start':datetime.strptime(sort_date(list_table[0].split('|')[0].replace('.','-').strip()), '%d-%m-%Y %H:%M'),
                                'end': datetime.strptime(sort_date(list_table[len(list_table) - 1].split('|')[0].replace('.','-').strip()), '%d-%m-%Y %H:%M'),
                                'Закончен':ends,
                                            }
        except IndexError:
            break
    country.update_one({"Чемпионат": '2022/2023'}, {'$set':{'Календарь':asd}})
    return asd


def sortByAlphabet(inputStr):
    return int(inputStr[:2])

def sort_date(date):
    if len(date.split("|")[0].split()) == 1:
        date = date.split("|")[0].replace('.','-') + " 23:59"
        return date.strip()
    return date.split('|')[0].replace('.','-').strip()

def get_tab(name):
    country =  db[name]
    table = country.find_one({"Чемпионат": '2022/2023'})
    i = 1
    dict_table = {}
    try:
        for team, stat in table.items():
            if team not in ['_id','Чемпионат','Календарь','Лого']:
                i+=1
                asd =[teams for teams in stat['Календарь'] if not teams.endswith("– : –")]
                dict_table[team] = {
                'Игры':stat['Таблица']['Игры'],
                'Очки':stat['Таблица']['Очки'],
                'Последние результаты\n': asd[len(asd) - 6:], 
                'Лого': table['Лого'][team]
                }
        return dict_table
    except Exception as e:
            print(e)
            print(e)

def get_next_date(name):
    country =  db[name]
    calendar = country.find_one({"Чемпионат": '2022/2023'})
    now = datetime.now()
    date_min = []
    for tour in calendar['Календарь'].values():
        if tour['Закончен']:
            continue
        for date in tour['Матчи']:
            try:
                date_match = datetime.strptime(date.split('|')[0].replace('.', '-').strip(), '%d-%m-%Y %H:%M')
            except Exception:
                date_match = datetime.strptime(date.split()[0].replace('.', '-').strip() + ' 23:59', '%d-%m-%Y %H:%M')
            if date.endswith('– : –') and now < date_match:
                if date_match not in date_min:
                    date_min.append(date_match)
    date_min.sort()
    return date_min[0]

def get_start_end_tour(name, next_date):
    country =  db[name]
    calendar = country.find_one({"Чемпионат": '2022/2023'})
    for name_tour, tour in calendar['Календарь'].items():
        if tour['Закончен']:
            continue
        if next_date == tour['start']:
            text = 'В этом туре\n\n' + ('\n\n').join(tour['Матчи'])
        elif datetime.now() > tour['end']:
            text = 'Тур закончен\n\n' + ('\n\n').join(tour['Матчи'])
        else:
            break
        #img = Image.open("football-soccer1.png")
        img = Image.open(f"{name}.png")
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("arkhip_font.ttf", 200)
        _, _, w, _ = draw.textbbox((0, 0), f"{name_tour} \n\n", font=font)
        draw.text(((img.width-w)/2, 40), f"{name_tour} \n\n",(0,0,0),font=font, align = "center")
        font = ImageFont.truetype("arkhip_font.ttf", 100)
        _, _, w, _ = draw.textbbox((0, 0),text, font=font)
        #draw.text(((img.width-w)/2, 130),text,(20,34,69),font=font, align = "center")
        draw.text(((img.width-w)/2, 400),text,(0,0,0),font=font, align = "center")
        img.save(f'{name}1.png')
        img.show()
        return img
        
#get_start_end_tour('italy', get_next_date('italy'))
get_start_end_tour('germany', get_next_date('germany'))
#get_start_end_tour('england', get_next_date('england'))