from xpath_ref import logo_ref_xpath, parse_xpath_text, num_xpath_tour
from xpath_ref import parse_xpath_result, date_xpath_match, logo_xpath
import requests
from lxml import html
from config import parse_site, client_champ
from pymongo import MongoClient
from datetime import datetime, timedelta
import locale
from config import User_agent
import time
import threading

locale.setlocale(locale.LC_ALL, "")
db = client_champ['json_champ']

def parent_word(month):
    if month.split()[1].endswith("ь"):
        month = month.replace('ь', 'я', 1)
    elif month.split()[1].endswith("й"):
        month = month.replace('й', 'я', 1)
    else:
        month = month.replace('т', 'та', 1)
    return month


class Championat:
    def __init__(self, country=""):
        self.country = country
        self.url = parse_site
        self.url_calendar = ""
        self.response_text = ""
        self.tree = ""
        self.calendar = {}
        self.list_ref_logo = []
        if self.country == "":
            self.country = "germany"
        self.url_championat = f'{self.url}/football/_{self.country}.html'
        self.sess = requests.Session()
        self.sess.headers.update(User_agent)
        response = self.sess.get(self.url_championat)
        self.response_text = response.text
        self.tree = html.fromstring(self.response_text)

    def get_logo(self):
        self.list_ref_logo = self.tree.xpath(logo_ref_xpath)


class Calendar(Championat):
    def __init__(self, country=""):
        super().__init__(country)
        parse_calendar = self.tree.xpath(parse_xpath_text)
        self.url_calendar = '{}{}'.format(parse_site, parse_calendar[2])
        response = self.sess.get(self.url_calendar)
        self.response_text = response.text
        self.tree = html.fromstring(self.response_text)
        self.tour = self.tree.xpath(num_xpath_tour)

    def get_date(self):
        return [" ".join(date.replace('.', '-').split()) for date in
                self.tree.xpath(date_xpath_match)]

    def get_tour(self):
        return self.tree.xpath(num_xpath_tour)

    def get_matches(self):
        return [match.split(",")[0] for match in self.tree.xpath(
            '//td [@class="stat-results__link"]//@title')]

    def get_result(self):
        return [result.replace('– : –','').strip() for result in
                self.tree.xpath(parse_xpath_result)]

    def get_calendar(self):
        for i in range(0, len(self.num_tour), self.tour):
            name_date = f"{self.list_datematch[i:self.tour+i][0][:10]}-\
            {self.list_datematch[i:self.tour+i][self.tour-1][:10]}"
            if '– : –' not in self.list_result[i:self.tour+i][self.tour-1]:
                self.calendar[
                    f'Тур {str(self.num_tour[i])} | {name_date} | закончен'
                    ] = [
                        self.list_datematch[i:self.tour+i],
                        self.list_match[i:self.tour+i],
                        self.list_result[i:self.tour+i]
                        ]
            else:
                self.calendar[
                    f'Тур str(self.num_tour[i])  | {name_date}'
                              ] = [
                                    self.list_datematch[i:self.tour+i],
                                    self.list_match[i:self.tour+i],
                                    self.list_result[i:self.tour+i]
                                    ]
        return self.calendar


class Table(Championat):
    def __init__(self, country):
        super().__init__(country)
        parse_table = self.tree.xpath(parse_xpath_text)
        url_table = f'{parse_site}{parse_table[3]}'
        response = self.sess.get(url_table)
        self.response_text = response.text
        self.tree = html.fromstring(self.response_text)
        self.dict_table = {}

    def get_name(self):
        names_teams = self.tree.xpath(
            '//span[@class="table-item__name"]/text()')
        return names_teams[:int(len(names_teams)/3)]

    def get_points(self):
        num_points = [ball.strip() for ball in self.tree.xpath(
            '//td[8]/strong/text()')]
        return num_points[:int(len(num_points)/3)]

    def get_games(self):
        num_games = self.tree.xpath('//td[3]/strong/text()')
        return num_games[:int(len(num_games)/3)]

    def get_wins(self):
        num_wins = [win.strip() for win in self.tree.xpath('//td[4]//text()')]
        return num_wins[:int(len(num_wins)/3)]

    def get_draw(self):
        num_draw = [
            draw.strip() for draw in self.tree.xpath('//td[5]//text()')]
        return num_draw[:int(len(num_draw)/3)]

    def get_loss(self):
        num_loss = [
            lose.strip() for lose in self.tree.xpath('//td[6]//text()')]
        return num_loss[:int(len(num_loss)/3)]

    def get_balls(self):
        num_balls = [
            ball.strip() for ball in self.tree.xpath('//td[7]//text()')]
        return num_balls[:int(len(num_balls)/3)]

    def get_six_match(self):
        six_match = self.tree.xpath('//td[10]/a/span/@title')
        return six_match[:int(len(six_match)/3)]

    def get_table(self):
        self.get_teams()
        self.get_games()
        self.get_points()
        self.get_logo()
        results = []
        num_match = 6
        for i in range(0, len(self.list_result_six_matches), num_match):
            results.append(self.list_result_six_matches[i: i + num_match])
        # артинки эмблем команд
        for i in range(len(self.list_teams)):
            self.dict_table[self.list_teams[i]] = {
                            'Игры': int(self.list_games[i]),
                            'Очки': int(self.list_points[i].strip()),
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
        response1 = self.sess.get(url1)
        tree = html.fromstring(response1.text)
        self.logo_list = tree.xpath(logo_xpath)
        self.logo_ref_team = self.logo_list[0]
        self.result_title += '\n' + 'Последние результаты:\n\
            ' + self.dict_table_team[self.name_team]['Последние результаты\n']


def add_db(name, name_champ):
    country = db[name]
    calendar = Calendar(name)
    table = Table(name)
    calendar_all = []
    tours = calendar.get_tour()
    dates = calendar.get_date()
    matches = calendar.get_matches()
    results = calendar.get_result()
    for i in range(len(calendar.tour)):
        calendar_all.append([tours[i], [
                        dates[i],
                        matches[i],
                        results[i]]])
    calendar_all.sort(key=lambda q: (int(q[0])))
    dict_calendar = {}
    num_team = int(len(table.get_games())/2)
    for i, j in enumerate(range(0, len(calendar_all), num_team), 1):
        matches = calendar_all[j:j + num_team]
        for match_end in matches:
            if '' in match_end[1]:
                ends = False
                break
            ends = True
        dict_calendar[f'Тур {i}'] = {
            'Матчи': [' | '.join(match[1]) for match in matches],
            'start':
            datetime.strptime(sort_date(matches[0][1][0]), '%d-%m-%Y %H:%M'),
            'end':
            datetime.strptime(sort_date(matches[num_team - 1][1][0]),
                              '%d-%m-%Y %H:%M'),
            'Закончен': ends,
                        }
    country.update_one({"Чемпионат": '2022/2023'},
                       {'$set': {'Календарь': dict_calendar}})
    points_stat = table.get_points()
    games_stat = table.get_games()
    wins_stat = table.get_wins()
    loses_stat = table.get_loss()
    draw_stat = table.get_draw()
    balls_stat = table.get_balls()
    dict_table = {}
    dict_table['Чемпионат'] = name_champ
    for i, name_team in enumerate(table.get_name()):
        games = [
            " | ".join(namea[1]) for namea in calendar_all if name_team in
            namea[1][1]]
        dict_table[name_team] = {
                            'Таблица': {
                                        "Очки": points_stat[i],
                                        "Игры": games_stat[i],
                                        "В": wins_stat[i],
                                        "П": loses_stat[i],
                                        "Н": draw_stat[i],
                                        "М": balls_stat[i],
                                    },

                            'Календарь': games,
        }
    country.update_one({"Чемпионат": '2022/2023'},
                       {'$set': dict_table})


def get_logo(db_name, name):
    country = db[db_name]
    logo = country.find_one({"Чемпионат": '2022/2023'})
    try:
        return logo["Лого"][name]
    except KeyError:
        return logo["Лого"]['Шальке-04']


def get_cal(name, name_champ):
    country = db[name]
    calendar = country.find_one({"Чемпионат": name_champ})
    return calendar["Календарь"]


def sortByAlphabet(inputStr):
    return int(inputStr[:2])


def sort_date(date):
    if len(date.split("|")[0].split()) == 1:
        date = date.split("|")[0].replace('.', '-') + " 23:59"
        return date.strip()
    return date.split('|')[0].replace('.', '-').strip()


def get_tab(name):
    country = db[name]
    table = country.find_one({"Чемпионат": '2022/2023'})
    clear_table = []
    try:
        for team, stat in table.items():
            if team not in ['_id', 'Чемпионат', 'Календарь', 'Лого']:
                res_six_match = [
                    teams for teams in
                    stat['Календарь'] if not teams.endswith(" ")]
                clear_table.append([team, [
                                    stat['Таблица']['Игры'],
                                    stat['Таблица']['Очки'],
                                    stat['Таблица']['М'],
                                    res_six_match[-6:]]])
        clear_table.sort(key=lambda b: (int(b[1][1]),
                                        int(b[1][2].split("-")[0]) - int(
            b[1][2].split("-")[1])))
        clear_table.reverse()
        return dict(clear_table)
    except Exception as e:
        print(e)


def get_next_date(name):
    country = db[name]
    calendar = country.find_one({"Чемпионат": '2022/2023'})
    now = datetime.now()
    date_min = []
    for tour in calendar['Календарь'].values():
        if tour['Закончен']:
            continue
        for date in tour['Матчи']:
            try:
                date_match = datetime.strptime(
                    date.split('|')[0].replace('.', '-').strip(),
                    '%d-%m-%Y %H:%M')
            except Exception:
                date_match = datetime.strptime(
                    date.split()[0].replace('.', '-').strip() + ' 23:59',
                    '%d-%m-%Y %H:%M')
            if date.endswith('– : –') and now < date_match:
                if date_match not in date_min:
                    date_min.append(date_match)
    date_min.sort()
    return date_min[0]


def get_start_end_tour(name, next_date):
    country = db[name]
    calendar = country.find_one({"Чемпионат": '2022/2023'})
    for name_tour, tour in calendar['Календарь'].items():
        if tour['Закончен']:
            continue
        next_date = tour['end']
        if next_date == tour['start']:
            # if next_date.date() == tour['start'].date():
            dict_match = {}
            for name_match in tour['Матчи']:
                date_match = datetime.strptime(
                    name_match.split('|')[0].split()[0].replace('.', '-'),
                    '%d-%m-%Y').strftime('%d %B, %A').upper()
                time_match = name_match.split('|')[0].split()[1]
                if 'Шальке' in name_match:
                    asdx = name_match.split('|')[1].strip().replace(
                        '-', ' ', 1)
                    # match = asdx.replace('-', time_match)
                    clear_name = asdx.split("-")
                else:
                    # match = name_match.split('|')[1].strip().replace(
                    # '-', time_match)
                    clear_name = name_match.split('|')[1].split("-")
                if date_match not in dict_match:
                    list_match_logo = []
                list_match_logo.append(time_match)
                for name_team in clear_name:
                    list_match_logo.append({name_team.strip(): get_logo(
                        name, name_team.strip())})
                dict_match[date_match] = list_match_logo
        # elif datetime.now() > tour['end']:
        elif next_date == tour['end']:
            dict_match = {}
            for name_match in tour['Матчи']:
                date_match = datetime.strptime(
                    name_match.split('|')[0].split()[0].replace('.', '-'),
                    '%d-%m-%Y').strftime('%d %B, %A').upper()
                date_match = parent_word(date_match)
                results_match = name_match.split('|')[2].strip()
                if 'Шальке' in name_match:
                    asdx = name_match.split('|')[1].strip().replace(
                        '-', ' ', 1)
                    clear_name = asdx.split("-")
                else:
                    clear_name = name_match.split('|')[1].split("-")
                if date_match not in dict_match:
                    list_match_logo = []
                list_match_logo.append(results_match)
                for name_team in clear_name:
                    if name_team == ' Брайтон энд Хоув Альбион ':
                        list_match_logo.append(
                            {'Брайтон': get_logo(name, name_team.strip())})
                        continue
                    list_match_logo.append(
                        {name_team.strip(): get_logo(name, name_team.strip())})
                dict_match[date_match] = list_match_logo
            break
        else:
            continue
    return dict_match, name_tour, len(tour['Матчи'])


def update_base():
    i = 0
    while True:
        try:
            sess = requests.Session()
            sess.headers.update(User_agent) 
            today_date = (datetime.now() + timedelta(i)).strftime("%Y-%m-%d")
            parse_link = f"{parse_site}/stat/{today_date}.json"
            response = sess.get(parse_link).json()
            try:
                dict_now = response['matches']['football']['tournaments']
                clear_time = []
                for key, value in dict_now.items():
                    if key in dict_match:
                        for match in value['matches']:
                            time_match = datetime.strptime(match['time_str'],'%d.%m.%Y %H:%M') + timedelta(hours=2, minutes=30)
                            if [time_match, dict_match[key]] not in clear_time:
                                clear_time.append([time_match, dict_match[key]])
                if len(clear_time) == 0:
                    raise KeyError
                clear_time.sort()
            except KeyError:
                i+=1
                continue
            for date_match in clear_time:
                time_sleep = date_match[0] - datetime.now()
                try:
                    time.sleep(time_sleep.total_seconds())
                except ValueError:
                    continue
                add_db(date_match[1],'2022/2023') 
            i+=1
        except:
            time.sleep(120)
  

dict_match = {
'football-5025':'england',
'football-4987': 'russiapl',
'football-5047': 'spain',
'football-5029': 'france',
'football-5057': 'italy',
'football-5027': 'germany',
}
threading.Thread(target=update_base).start()
