import pymongo
import time
from abc import ABC, abstractmethod
from datetime import date, timedelta, datetime
from datetime import time as tm
import requests
from pymongo import MongoClient
import config
import query_mongo


class Match:
    def __init__(self, is_live, is_finished, data, notifier=''):
        self.is_live = is_live
        self.is_finished = is_finished
        self.notifier = notifier
        self.data = data

    def set_live(self, is_live):
        self.is_live = is_live
        self.notifier.notify_observers(self)

    def set_finished(self, is_finished):
        self.is_finished = is_finished
        self.notifier.notify_observers(self)

    def set_home_goals(self, is_goal):
        self.is_goal = is_goal
        self.notifier.notify_observers(self)

    def set_away_goals(self, is_goal):
        self.is_goal = is_goal
        self.notifier.notify_observers(self)


class MatchProvider(ABC):
    @abstractmethod
    def get_matches(self, current_date):
        pass

class FootballMatchProvider(MatchProvider):
    def get_matches(self, current_date):
        url = f"https://www.championat.com/stat/{current_date}.json"
        sess = requests.Session()
        sess.headers.update(config.User_agent) 
        response = sess.get(url).json()
        try:
            data = response['matches']['football']['tournaments']
        except KeyError:
            data = {}
        self.next_date = response['nav']['next']['date']
        matches = []
        for match_champ in data.values():
            for match_data in match_champ['matches']:
                is_live = match_data["flags"]['live'] == 1
                is_finished = match_data['flags']['is_played'] == 1
                match_data.pop('_id')
                match_data['id_champ'] = match_champ['id']
                try:
                    match_data['name_champ'] = match_champ['name_tournament']
                except KeyError:
                    match_data['name_champ'] = match_data['link_title'].split('.')[3].strip()
                match = Match(is_live, is_finished, match_data)
                matches.append(match)
        return matches

class MatchParser(ABC):
    @abstractmethod
    def update_results(self, finished_matches):
        pass

    @abstractmethod
    def sleep_until_next_match(self, future_matches):
        pass

class FootballMatchParser(MatchParser):
    def __init__(self):
        self.client = MongoClient()
        self.db = self.client["championat"]
        self.date_coll = self.db["date"]
        self.champ_coll = self.db["champ"]
        self.matches_coll = self.db["matches"]
        self.teams_coll = self.db["teams"]
        self.sess = requests.Session()
        self.sess.headers.update(config.User_agent) 
        self.initial_link = 'https://www.championat.com/stat/'


    def update_results(self, data):
        for match_data in data:
            match_id = match_data.data["id"]
            match = self.matches_coll.find_one({"id": match_id})
            if not match:
                self.collection.insert_one(match_data.data)
                continue
            elif match["flags"]['is_played'] == 1:
                continue
            self.collection.replace_one({'id':match_id}, match_data.data)
            
    def sleep_until_next_match(self, future_matches):
        try:
            next_match_time = future_matches[0].data['pub_date']
            current_time = time.time()
            sleep_time = next_match_time - current_time
            time.sleep(sleep_time)
        except IndexError:
            now = datetime.now() 
            midnight_tomorrow = datetime.combine(now.date() + timedelta(days=1), tm.min)
            sleep_time = (midnight_tomorrow - now).total_seconds()
            time.sleep(sleep_time)

    def single_date_request(self, date):
        url = "{}{}.json".format(self.initial_link, date)
        response = self.sess.get(url)
        self.resp_json = response.json()
        data = self.resp_json['matches']['football']['tournaments']
        try:
            date = self.date_coll.insert_one({'date': date})
            data_id = date.inserted_id
        except pymongo.errors.DuplicateKeyError:
            date = self.date_coll.find_one({'date': date})
            data_id = date['_id']
            for matches in data.values():
                try:
                    name_tournament = matches['name_tournament']
                except KeyError:
                    name_tournament = matches['name']
                try:
                    img_tournament = matches['img_tournament']
                except KeyError:
                    img_tournament = matches['img']
                try:
                    champ = self.champ_coll.insert_one({
                                                'name_tournament': name_tournament,
                                                'priority':matches['priority'],
                                                'img':img_tournament,
                                                'id': matches['id'],
                                                'link': matches['link']})
                    champ_id = champ.inserted_id
                except pymongo.errors.DuplicateKeyError:
                    champ = self.champ_coll.find_one({'id': matches['id']})
                    champ_id = champ['_id']
                for match in matches['matches']:
                    try:
                        home_team = self.teams_coll.insert_one({
                                            'name': match['teams'][0]['name'], 
                                            'id': match['teams'][0]['id'],
                                            'img':  match['teams'][0]['icon']})
                        home_team_id = home_team.inserted_id
                    except pymongo.errors.DuplicateKeyError:
                        home_team = self.teams_coll.find_one({'id': match['teams'][0]['id']})  
                        home_team_id = home_team['_id']
                    try:
                        away_team = self.teams_coll.insert_one({
                                            'name': match['teams'][1]['name'], 
                                            'id': match['teams'][1]['id'],
                                            'img':  match['teams'][1]['icon']})
                        away_team_id = away_team.inserted_id
                    except pymongo.errors.DuplicateKeyError:
                        away_team = self.teams_coll.find_one({'id': match['teams'][1]['id']})
                        away_team_id = away_team['_id']
                    match['id_date'] = data_id
                    match['id_champ'] = champ_id
                    match['id_home_team'] = home_team_id
                    match['id_away_team'] = away_team_id
                    match.pop('_id')
                    match.pop('teams')
                    match.pop('data-id')
                    match.pop('type')
                    match.pop('icons')
                    match.pop('date')
                    self.matches_coll.replace_one({'id':match['id']}, match, upsert=True)

    def update_previous_result(self):
        now_timestamp = datetime.now().timestamp()
        for matches_not_end in self.matches_coll.aggregate(query_mongo.pub_pipl(now_timestamp)):
            self.single_date_request(matches_not_end['date'])

    def update_database_to_date(self, to_date):
        current_date = date.today()
        delta = 1
        if current_date > datetime.strptime(to_date, "%Y-%m-%d").date():
                delta = - 1
        while str(current_date) != to_date:
            self.single_date_request(str(current_date))
            try:
                current_date = self.resp_json['nav']['next']['date'] if delta == 1 else self.resp_json['nav']['prev']['date']
            except (KeyError, TypeError):
                return


class Observer(ABC):
    @abstractmethod
    def update(self, match):
        pass

class MatchNotifier:
    def __init__(self):
        self.observers = []

    def add_observer(self, observer):
        self.observers.append(observer)

    def remove_observer(self, observer):
        self.observers.remove(observer)

    def notify_observers(self, match):
        for observer in self.observers:
            observer.update(match)


class SMSObserver(Observer):
    def update(self, match):
        if match.is_live:
            print(f"Sending SMS: The match has started!")
        elif match.is_finished:
            print(f"Sending SMS: The match has finished!")


class EmailObserver(Observer):
    def update(self, match):
        if match.is_live:
            print(f"Sending Email: The match has started!")
        elif match.is_finished:
            print(f"Sending Email: The match has finished!")


class TelegramObserver(Observer):
    def update(self, match):
        if match.is_live:
            print(f"Sending Email: The match has started!")
        elif match.is_finished:
            print(f"Sending Email: The match has finished!")


class MatchParserContext:
    def __init__(self, parser: MatchParser, provider: MatchProvider):
        self.parser = parser
        self.provider = provider

    def run(self):
        self.parser.update_previous_result()
        while True:
            current_date = str(date.today())
            self.parser.single_date_request(current_date)
            time.sleep(60)

class MatchParserFacade:
    def __init__(self):
        self.parser = FootballMatchParser()
        self.provider = FootballMatchProvider()
        self.context = MatchParserContext(self.parser, self.provider)

    def run(self):
        self.context.run()


def update():
    facade = MatchParserFacade()
    facade.run()

#update()
#update = FootballMatchParser()
#update.update_database_to_date('2024-08-26')


if __name__ == "__main__":
    facade = MatchParserFacade()
    facade.run()
    # update = FootballMatchParser()
    # update.update_database_to_date('2024-05-26')
