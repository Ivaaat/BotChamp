from datetime import datetime, timedelta
from config import User_agent, update_champ
import time
from championat import Calendar, Table
import threading
from config import parse_site, update_champ, db, bot
from config import user_id, dict_match, season
import requests
import pymongo
from pymongo import errors


def add_calendar(name_champ):
    for id, country in update_champ.items():
        country_calendar = db[name_champ]
        indexes = [name_index['name'] for name_index in country_calendar.list_indexes()] 
        if 'match_1' not in indexes:
            country_calendar.create_index([("match", pymongo.ASCENDING)], unique=True)
        calendar = Calendar(country)
        tours = calendar.get_tour()
        dates = calendar.get_date()
        matches = calendar.get_matches()
        results = calendar.get_result()
        for i in range(len(matches)):
            try:
                country_calendar.insert_one({'match':matches[i],
                                'date':dates[i],
                                'result':results[i],
                                'tour':tours[i],
                                'ends': results[i] != "",
                                'country': country,
                                'champ': dict_match[id],
                                'live':False
                                })
            except pymongo.errors.DuplicateKeyError:
                country_calendar.update_one({'match':matches[i]},
                                {'$set':{
                                        'date':dates[i],
                                        'result':results[i],
                                        'tour':tours[i],
                                        'ends': results[i] != "",
                                        'country': country,
                                        'champ': dict_match[id],
                                        'live':False}}
                                )
            

def add_table(name):
    country_table = db[f"table_{season}"]
    indexes = [name_index['name'] for name_index in country_table.list_indexes()] 
    if 'team_1' not in indexes:
        country_table.create_index([("team", pymongo.ASCENDING)], unique=True)
    table = Table(name)
    logo_60x60 =  table.get_logo()
    names = table.get_name()
    points_stat = table.get_points()
    games_stat = table.get_games()
    wins_stat = table.get_wins()
    loses_stat = table.get_loss()
    draw_stat = table.get_draw()
    balls_stat = table.get_balls()
    logo = [link.replace('60x60', '300x300') for link in logo_60x60]
    for i in range(len(points_stat)):
        try:
            country_table.insert_one(
                                    {"team": names[i],
                                    "points": points_stat[i],
                                    "games": games_stat[i],
                                    "win": wins_stat[i],
                                    "lose": loses_stat[i],
                                    "draw": draw_stat[i],
                                    "balls": balls_stat[i],
                                    "logo": logo[i],
                                    "country": name})
        except pymongo.errors.DuplicateKeyError:
            country_table.update_one({"team": names[i]},
                                        {'$set':{"points": points_stat[i],
                                                "games": games_stat[i],
                                                "win": wins_stat[i],
                                                "lose": loses_stat[i],
                                                "draw": draw_stat[i],
                                                "balls": balls_stat[i],
                                                "logo": logo[i],
                                                "country": name}
                                    })



def update():
    calendar = db[f"calendar_{season}"]
    i = 0
    today_date = (datetime.now() - timedelta(1)).strftime("%d-%m-%Y")
    date_last = datetime(2022,12,31).strftime("%d-%m-%Y")
    while date_last != today_date:
        date_last = (datetime(2022,12,31) + timedelta(i)).strftime("%d-%m-%Y")
        for _ in calendar.find({'ends':False , 'date':{'$regex':date_last}}):
            add_calendar(f"calendar_{season}")
            for country in update_champ.values():
                add_table(country)
            date_last = today_date
        i+=1

        
class Request:
    start = datetime.strptime('2022-07-10',"%Y-%m-%d")
    end = datetime.strptime('2023-07-10', "%Y-%m-%d")

    def __init__(self) -> None:
        if self.start.date() == self.end.date():
            raise ValueError('Сезон закончен')
        self.important_matches = []
        self.__sess = requests.Session()
        self.__sess.headers.update(User_agent) 
        self.__parse_link = "{}/stat/{}.json".format(parse_site, 
                                                    Request.start.strftime("%Y-%m-%d"))
        self._response = self.__sess.get(self.__parse_link).json()
        try:
            self._dict_now = self._response['matches']['football']['tournaments']
        except TypeError:
            raise ValueError('Сезон закончен')
        for self.value in self._dict_now.values():
            if self.value['data-id'] in dict_match:
                for self.matches in self.value['matches']:
                    self.important_matches.append(self.matches)

    def live(self) -> None:
        self.live_matches : list = []
        for matches in self.important_matches:
            try:
                if matches['flags']['live'] == 1:
                    self.live_matches.append(matches)
            except KeyError:
                    continue
        return len(self.live_matches)

    def past(self) -> None:
        self.complited_matches : list = []
        for matches in self.important_matches:
            try:
                if matches['flags']['is_played'] == 1:
                    self.complited_matches.append(matches)
            except KeyError:
                    continue
        return len(self.complited_matches)

    def future(self) -> None:
        self.sleep_time : list = []
        for matches in self.important_matches:
            try:
                date_match = (datetime.strptime(matches['time_str'], 
                                                '%d.%m.%Y %H:%M'))
                total = (date_match - self.start).total_seconds()
                if total > 0 and total not in self.sleep_time:
                    self.sleep_time.append(total)
            except KeyError:
                    continue
        tomorrow = self.start + timedelta(1)
        midnight = tomorrow.replace(hour=0, minute=5, second=0, microsecond=0)
        total = (midnight - self.start).total_seconds()
        self.sleep_time.append(total)
        self.sleep_time = sorted(self.sleep_time)
        return len(self.sleep_time)


class DB:
    calendar = db[f"calendar_{season}"]
    table = db[f"table_{season}"]

    def __init__(self, matches) -> None:
        self.update = []
        for self.match in matches:
            self.is_over = self.match['flags']['is_played'] == 1
            self.is_live = self.match['flags']['live'] == 1
            try:
                self.result = self.match['score']['direct']['main']
            except KeyError:
                self.result = ""
            try:
                self.tour = self.match['roundForLTAndMC']
            except KeyError:
                continue
            try:
                self.champ = self.match['link_title'].split('.')[3].strip()
            except:
                self.champ = self.match['link_title']
            self.update.append({
                        'title': self.match['link_title'],
                        'date': self.match['date'],
                        'result': self.result,
                        'tour': self.match['roundForLTAndMC'],
                        'is_over': self.is_over,
                        'country':self.match['section'],
                        'is_live': self.is_live,
                        'champ':self.champ,
                        'time':self.match['time'],
                        'datetime':datetime.fromtimestamp(self.match['pub_date']),
                        'status': self.match['status']['name']
            }
            )     

    
    def update_db(self):
        for match in self.update:
            try:
                self.calendar.insert_one(match)
            except errors.DuplicateKeyError:
                self.calendar.update_one({'title':match['title']}, 
                                        {'$set':{
                                            'result':match['result'],
                                            'is_over':match['is_over'],
                                            'is_live':match['is_live'],
                                            'status':match['status']
                                            }
                                        }
                )


def update_today ():
    while True: 
        try:
            Request.start = datetime.now()
            req = Request()
            if req.past() > 0:
                past_update = DB(req.complited_matches)
                past_update.update_db()
            if req.live() > 0:
                count = req.live()
                while req.live() == count:
                    req = Request()
                    req.live()
                    live_update = DB(req.live_matches)
                    live_update.update_db()
                    time.sleep(30)
                continue
            req.future()
            future_update = DB(req.important_matches)
            future_update.update_db()
            for sleep in req.sleep_time:
                bot.send_message(user_id,f'сплю до {sleep}')
                time.sleep(sleep)
                break
        except ValueError:
            break

threading.Thread(target=update_today).start()       

def update_all(i=0):
    Request.start = datetime.now() - timedelta(i)
    Request.end = datetime.now()
    while True:
        try:
            req = Request()
            all_update = DB(req.important_matches)
            all_update.update_db()
            Request.start += timedelta(1)
        except ValueError:
            break

#update_all(i = 20)