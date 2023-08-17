from datetime import datetime, timedelta
from config import User_agent, update_champ
import time
from championat import Calendar, Table
import threading
from config import parse_site,  db, bot
from config import user_id, season
import requests
import pymongo
from pymongo import errors, MongoClient


calendar = db['calendar_2022/2023']
calendar.create_index([("title", pymongo.ASCENDING)], unique=True)


class StatChamp:

    def __init__(self, start) -> None:
        self.start = start
        self.__sess = requests.Session()
        self.__sess.headers.update(User_agent) 
        self.__parse_link = "{}/stat/{}.json".format(parse_site, 
                                                    start.strftime("%Y-%m-%d"))
        self.__response = self.__sess.get(self.__parse_link).json()
        try:
            self.next = self.__response['nav']['next']['date']
        except:
            raise ValueError
        try:
            self.dict_now = self.__response['matches']['football']['tournaments']
        except:
            self.dict_now = {}
        

class GetTournaments(StatChamp):
    def __init__(self, start) -> None:
        super().__init__(start)
        self.all_tournaments = []
        for tournaments in self.dict_now.values():
            tournaments.pop('matches')
            self.all_tournaments.append(tournaments)


class GetMatches(StatChamp):

    def __init__(self, start) -> None:
        super().__init__(start)
        self.important_matches = []
        for self.value in self.dict_now.values():
            #if self.value['data-id'] in dict_match:
            #if self.value['is_top']:
            for self.matches in self.value['matches']:
                self.matches.pop('_id')
                self.matches['id_champ'] = self.value['id']
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
        shift = timedelta(seconds=60)
        for matches in self.important_matches:
            try:
                date_match = (datetime.strptime(matches['time_str'], 
                                                '%d.%m.%Y %H:%M'))
                total = (date_match - self.start + shift).total_seconds()
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
                        'id_champ': self.match['id_champ'],
                        'date': self.match['date'],
                        'result': self.result,
                        'tour': self.match['roundForLTAndMC'],
                        'is_over': self.is_over,
                        'country':self.match['section'],
                        'is_live': self.is_live,
                        'champ':self.champ,
                        'time':self.match['time'],
                        'datetime':datetime.fromtimestamp(self.match['pub_date']),
                        'status': self.match['status']['name'],
                        'home':self.match['score']['totalHome'],
                        'away': self.match['score']['totalAway']
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
                                            'status':match['status'],
                                            'datetime':match['datetime'],
                                            'time':match['time'],
                                            'date':match['date']

                                            }
                                        }
                )
                
    @classmethod
    def update_all(cls, request):
        for date_update in cls.calendar.find({'$or':[{'is_live':True}, 
                                                      {'is_over':False}]}
                                                      ).distinct('date'):
            start = datetime.strptime(date_update,"%Y-%m-%d")
            req = GetMatches(start)
            all_update = DB(req.important_matches)
            all_update.update_db()
        bot.send_message(user_id, 'обновил базу')


def update_today ():
    while True: 
        try:
            start = datetime.now()
            req = GetMatches(start)
            if req.past() > 0:
                past_update = DB(req.complited_matches)
                past_update.update_db()
            if req.live() > 0:
                count = req.live()
                while req.live() == count:
                    req = GetMatches(start)
                    req.live()
                    live_update = DB(req.live_matches)
                    live_update.update_db()
                    time.sleep(30)
                continue
            req.future()
            future_update = DB(req.important_matches)
            future_update.update_db()
            for sleep in req.sleep_time:
                bot.send_message(user_id, f'сплю до {sleep} /start')
                time.sleep(sleep)
                bot.send_message(user_id, f'кол-во Live = {req.live()}')
                if len(req.sleep_time) == 1:
                    DB.update_all(GetMatches)
                break
        except ValueError:
            break
#update_today ()
#threading.Thread(target=update_today).start()       


def find_football():
    #start = datetime.strptime('1992-03-28',"%Y-%m-%d")
    start = datetime.strptime('1996-11-03',"%Y-%m-%d")
    all_client = MongoClient()
    all_db = all_client['all']
    while True:
        try:
            start += timedelta(1)
            req = StatChamp(start)
            for stat in req._dict_now.values():
                stat['date'] = str(start.date())
                try:
                    all_collect = all_db[stat['name_tournament']]
                except KeyError:
                    all_collect = all_db[stat['name']]
                try:
                    all_collect.insert_one(stat)
                except pymongo.errors.DuplicateKeyError:
                    continue
                all_collect.create_index([('date', pymongo.ASCENDING)], unique=True)
                
            print(start)
        except ValueError:
            continue


#find_football()

def new_all():
    all_client = MongoClient()
    all_db = all_client['all']
    all_new_db = all_client['all_new_db']
    for name_collect in all_db.list_collection_names():
        for doc_all_collect in all_db[name_collect].find({}):
            all_new_db['all_new'].insert_one(doc_all_collect)
#new_all()


def find_id_namechamp():
    football_coll = db['football']
    id_champ =  football_coll.find().distinct('id_champ')
    id_tournament = {}
    gen_champ = (match for match in id_champ)
    for _ in range(len(id_champ)):
        id = next(gen_champ)
        doc = list(football_coll.find({'id_champ':id}).sort('pub_date',1))
        name_champ = doc[0]['link_title'].split('.')[-1].strip()
        season_one = doc[0]['date'].split('-')[0]
        season_two = doc[-1]['date'].split('-')[0]
        date = '{} - {}'.format(doc[0]['date'].replace('-', '.'), doc[-1]['date'].replace('-', '.'))
        season = '{}/{}'.format(season_one, season_two) if season_one != season_two else '{}/{}'.format(season_one, str(int(season_one) + 1))
        if season not in id_tournament:
            id_tournament[season] = []
        id_tournament[season].append((name_champ,date, id))
        #id_tournament[id] = {name_champ: (season, date)}

    print()
#find_id_namechamp()

def add_tournaments():
    start = datetime.strptime('1995-09-21',"%Y-%m-%d")
    DB.calendar = db['tournaments']
    DB.calendar.create_index([("id", pymongo.ASCENDING)], unique=True)
    while True:
        try:
            tournaments = GetTournaments(start)
            for champ in tournaments.all_tournaments:
                try:
                    DB.calendar.insert_one(champ)
                except pymongo.errors.DuplicateKeyError:
                    continue
            time.sleep(1)
            start = datetime.strptime(tournaments.next,"%Y-%m-%d")
        except ValueError:
                break
        
#add_tournaments()

def add_all():
    #start = datetime.now()
    #start = datetime.strptime('2023-07-21',"%Y-%m-%d")
    #start = datetime.strptime('2023-07-21',"%Y-%m-%d")
    start = datetime.strptime('1992-03-28',"%Y-%m-%d")
    DB.calendar = db['football_new']
    while True:
        try:
            req = StatChamp(start)
            for match in req.important_matches:
                DB.calendar.insert_one(match)
            time.sleep(1)
            start += timedelta(1)
            #start = datetime.strptime(req.next,"%Y-%m-%d")
        except ValueError:
                break
        
#add_all()

def all():
    client = MongoClient()
    db = client['championat']
    start = '1992-03-28'
    while True:
        #add_value = []
        collection = db[start]
        sess = requests.Session()
        sess.headers.update(User_agent) 
        parse_link = "{}/stat/{}.json".format(parse_site, start)
        try:
            response = sess.get(parse_link).json()
        except:
            time.sleep(30)
            continue
        try:
            start = response['nav']['next']['date']
        except:
            start = str((datetime.strptime(start, '%Y-%m-%d') + timedelta(1)).date())
            continue
        try:
            #add_value.append(response['matches']['football']['tournaments'])
            add_value = [{champ:stat} for champ, stat in response['matches']['football']['tournaments'].items()]
        except:
            continue
        #time.sleep(1)
        collection.insert_many(add_value)

#all()       

def update_upcoming():
    update_value = []
    client = MongoClient()
    db = client['matches']
    start = '2023-07-01'
    end = '2023-07-30'
    while start != end:
        #start = str((datetime.strptime(start, '%Y-%m-%d') + timedelta(1)).date())
        collection = db[start]
        sess = requests.Session()
        sess.headers.update(User_agent) 
        parse_link = "{}/stat/{}.json".format(parse_site, start)
        try:
            response = sess.get(parse_link).json()
        except:
            time.sleep(30)
            continue
        try:
            start = response['nav']['next']['date']
        except:
            start = str((datetime.strptime(start, '%Y-%m-%d') + timedelta(1)).date())
            continue
        try:
            update_value.append(response['matches']['football']['tournaments'])
        except:
            continue
        time.sleep(1)
        collection.update_many(update_value)

#update_upcoming()

def create_date_champ():
    client = MongoClient()
    db_get = client['matches']
    db_add = client['my_db']
    names_coll = db_get.list_collection_names()
    names_coll.sort()
    coll_date = db_add['date']
    coll_date.create_index('date', unique =True)
    coll_date_champ = db_add['date_champ']
    coll_champ = db_add['champ']
    coll_champ.create_index('id_old', unique =True)
    coll_matches = db_add['matches']
    coll_matches.create_index('id_old', unique =True)
    coll_teams = db_add['teams']
    coll_teams.create_index('id_old', unique =True)
    coll_champ_teams = db_add['champ_teams']
    for date_get in names_coll:
        coll_get = db_get[date_get]
        
        for doc in coll_get.find({},{'_id':0}):
            for stat in doc.values():
                try:
                    date = coll_date.insert_one({'date': date_get})
                    data_id = date.inserted_id
                except pymongo.errors.DuplicateKeyError:
                    date = coll_date.find_one({'date': date_get})
                    data_id = date['_id']
                try:
                    name_tournament = stat['name_tournament']
                except KeyError:
                    name_tournament = stat['name']
                try:
                    img_tournament = stat['img_tournament']
                except KeyError:
                    img_tournament = stat['img']
                try:
                    champ = coll_champ.insert_one({'name_tournament': name_tournament,
                                            'priority':stat['priority'],
                                            'img':img_tournament,
                                            'id_old': stat['id']})
                    champ_id = champ.inserted_id
                except pymongo.errors.DuplicateKeyError:
                    champ = coll_champ.find_one({'id_old': stat['id']})
                    champ_id = champ['_id']
                # coll_date_champ.insert_one({'id_date':{ "$ref" : "date", "$id" : data_id},
                #                             'id_champ':{ "$ref" : "champ", "$id" : champ_id}})
                for match in stat['matches']:
                    try:
                        home_team = coll_teams.insert_one({'name': match['teams'][0]['name'], 
                                            'id_old': match['teams'][0]['id'],
                                            'img':  match['teams'][0]['icon']})
                        home_team_id = home_team.inserted_id
                    except pymongo.errors.DuplicateKeyError:
                        home_team = coll_teams.find_one({'id_old': match['teams'][0]['id']})  
                        home_team_id = home_team['_id']
                    try:
                        away_team = coll_teams.insert_one({'name': match['teams'][1]['name'], 
                                            'id_old': match['teams'][1]['id'],
                                            'img':  match['teams'][1]['icon']})
                        away_team_id = away_team.inserted_id
                    except pymongo.errors.DuplicateKeyError:
                        away_team = coll_teams.find_one({'id_old': match['teams'][1]['id']})
                        away_team_id = away_team['_id']
                    try:
                        scoreByPeriods = match['scoreByPeriods'] 
                    except KeyError:
                        scoreByPeriods = None
                    try:
                        tour = match['tour']
                    except KeyError:
                        tour = None
                    try:
                        roundForLTAndMC = match['roundForLTAndMC']
                    except KeyError:
                        roundForLTAndMC = '{}-й тур'.format(tour)
                    try:
                        score = match['score']
                        result = match['result']
                    except KeyError:
                        score = None
                        result = None
                    try:
                        coll_matches.insert_one({
                                            'id_date':data_id,
                                            'id_champ': champ_id,
                                            # 'id_date':{ "$ref" : "date", "$id" : data_id},
                                            # 'id_champ':{ "$ref" : "champ", "$id" : champ_id},
                                            'id_old': match['id'],
                                            # 'id_home_team': { "$ref" : "teams", "$id" : home_team_id},
                                            # 'id_away_team': { "$ref" : "teams", "$id" : away_team_id},
                                            'id_home_team': home_team_id,
                                            'id_away_team': away_team_id,
                                            'flags': match['flags'],
                                            'score':score,
                                            'status':match['status'],
                                            'group': match['group'],
                                            'result': result,
                                            'link_title':match['link_title'],
                                            'pub_date':match['pub_date'],
                                            'roundForLTAndMC':roundForLTAndMC,
                                            'tour': tour,
                                            'section':match['section'],
                                            'periods':match['periods'],
                                            'scoreByPeriods':scoreByPeriods
                                             })
                    except pymongo.errors.DuplicateKeyError:
                        continue

                    pipeline = [
                            {
                                '$lookup': {
                                    'from': 'date', 
                                    'localField': 'id_date', 
                                    'foreignField': '_id', 
                                    'as': 'id_date'
                                }
                            }, {
                                '$match': {
                                    'id_date.date': '1992-03-29'
                                }
                            }, {
                                '$lookup': {
                                    'from': 'champ', 
                                    'localField': 'id_champ', 
                                    'foreignField': '_id', 
                                    'as': 'champ'
                                }
                            }, {
                                '$unwind': '$champ'
                            }, {
                                '$lookup': {
                                    'from': 'teams', 
                                    'localField': 'id_home_team', 
                                    'foreignField': '_id', 
                                    'as': 'home_team'
                                }
                            }, {
                                '$unwind': '$home_team'
                            }, {
                                '$lookup': {
                                    'from': 'teams', 
                                    'localField': 'id_away_team', 
                                    'foreignField': '_id', 
                                    'as': 'away_team'
                                }
                            }, {
                                '$unwind': '$away_team'
                            }, {
                                '$project': {
                                    'champ': '$champ.name_tournament', 
                                    'home_team': '$home_team.name', 
                                    'away_team': '$away_team.name'
                                }
                            }
                        ]

            
#create_date_champ()
def get_matches():
    team_name = 'ЦСКА'
    client = MongoClient()
    db_get = client['matches']
    db_add = client['my_db']
    coll_date = db_add['date']
    coll_date_champ = db_add['date_champ']
    coll_champ = db_add['champ']
    coll_matches = db_add['matches']
    coll_teams = db_add['teams']
    #teams = coll_teams.find({'name':{'$regex':team_name}})
    #teams = coll_teams.find({'name':team_name})
    team = coll_teams.find_one({'name':team_name})
    i = 0
    # for team in teams:
    #     all_mathes_team = coll_matches.find({'$or':[{'id_home_team':team['_id']},{'id_away_team':team['_id']}]})
    all_mathes_team = coll_matches.find_one({'$or':[{'id_home_team':team['_id']},{'id_away_team':team['_id']}]})
    #for title in all_mathes_team:
    #i += 1
    champ = coll_champ.find_one({'_id':all_mathes_team['id_champ']})['name_tournament']
    date = coll_date.find_one({'_id':all_mathes_team['id_date']})['date']
    print(i, all_mathes_team['link_title'], date, champ, sep=' ')

#get_matches()

        

