import time
from abc import ABC, abstractmethod
from datetime import date, timedelta, datetime
from datetime import time as tm
import requests
from pymongo import MongoClient
import config


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
        self.db = self.client["champ"]
        self.collection = self.db["foot"]
        self.sess = requests.Session()
        self.sess.headers.update(config.User_agent) 
        self.initial_link = 'https://www.championat.com/stat/'


    def update_results(self, data):
        for match_data in data:
            match_id = match_data.data["id"]
            match = self.collection.find_one({"id": match_id})
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

    def single_match_request(self, id, date):
        url = "{}{}.json".format(self.initial_link, date)
        response = self.sess.get(url)
        data = response.json()['matches']['football']['tournaments']
        for match_champ in data.values():
            for match_data in match_champ['matches']:
                if match_data['id'] == id:
                    match_data.pop('_id')
                    match_data['id_champ'] = match_champ['id']
                    try:
                        match_data['name_champ'] = match_champ['name_tournament']
                    except KeyError:
                        match_data['name_champ'] = match_data['link_title'].split('.')[3].strip()
                    return match_data

    def update_previous_result(self):
        now_timestamp = datetime.now().timestamp()
        for matches_not_end in self.collection.find({'$and':[{'pub_date':{'$lt':now_timestamp}},
                                                    {'status.label':{'$nin':['post', "cans",'delay','dns', 'ntl','fin']}}]}):
            updated_match = self.single_match_request(matches_not_end['id'], matches_not_end['date'])
            self.collection.replace_one({'id': matches_not_end['id']}, updated_match)

    def update_database_to_date(self, to_date):
        current_date = date.today()
        delta = 1
        if current_date > datetime.strptime(to_date, "%Y-%m-%d").date():
                delta = - 1
        while str(current_date) != to_date:
            url = "{}{}.json".format(self.initial_link, current_date)
            response = self.sess.get(url)
            try:
                resp_json = response.json()
                data = resp_json['matches']['football']['tournaments']
            except (KeyError,TypeError):
                data = {}
            for match_champ in data.values():
                for match_data in match_champ['matches']:
                    match = self.collection.find_one({"id": match_data["id"]})
                    match_data.pop('_id')
                    match_data['id_champ'] = match_champ['id']
                    try:
                        match_data['name_champ'] = match_champ['name_tournament']
                    except KeyError:
                        match_data['name_champ'] = match_data['link_title'].split('.')[3].strip()
                    if not match:
                        self.collection.insert_one(match_data)
                    else:
                        self.collection.replace_one({'id': match_data['id']}, match_data)
            try:
                current_date = resp_json['nav']['next']['date'] if delta == 1 else resp_json['nav']['prev']['date']
            except (KeyError,TypeError):
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
        current_date = date.today()
        prev_live_matches_count = 0
        self.parser.update_previous_result()
        while True:
            matches = self.provider.get_matches(current_date)
            live_matches = []
            finished_matches = []
            future_matches = []
            for match in matches:
                if match.is_live:
                    live_matches.append(match)
                elif match.is_finished:
                    finished_matches.append(match)
                else:
                    future_matches.append(match)
            live_matches_count = len(live_matches)
            if finished_matches and live_matches_count != prev_live_matches_count:
                self.parser.update_results(finished_matches)
            if live_matches:
                self.parser.update_results(live_matches)
                time.sleep(30)
                prev_live_matches_count = live_matches_count
            else:
                if future_matches:
                    try:
                        self.parser.update_results(future_matches)
                        self.parser.sleep_until_next_match(future_matches)
                    except ValueError:
                        current_date = self.provider.next_date
                else:
                    self.parser.update_results(finished_matches)
                    current_date = self.provider.next_date
                    self.parser.update_previous_result()

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


# if __name__ == "__main__":
#     #facade = MatchParserFacade()
#     #facade.run()
#     update = FootballMatchParser()
#     update.update_database_to_date('2024-05-26')
