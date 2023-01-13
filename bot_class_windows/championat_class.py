from xpath_ref_class import *
import requests
from lxml import html
from constants_class import mass_contry, mass_review, parse_site
import time
sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
    })


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

  
    '''
    def get_calendar(self):
        list_match = self.tree.xpath(parse_xpath_match)
        list_result = self.tree.xpath(parse_xpath_result)
        list_datematch = self.tree.xpath(date_xpath_match)
        j = 0
        for i in range(0,len(list_match),2):
            self.list_match.append(' - '.join(list_match[i:i + 2]))
            self.list_datematch.append (" ".join(list_datematch[j].split()))
            self.list_result.append(list_result[j].strip())
            j+=1
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
          '''
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