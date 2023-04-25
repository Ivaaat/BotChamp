from datetime import datetime, timedelta
from config import User_agent, update_champ
import time
from championat import Calendar, Table, parent_word
import threading
from config import parse_site, update_champ, db, dbs, bot
from config import user_id, dict_match, season
import requests
import pymongo


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


def get_logo(team):
    country = db[f'table_{season}']
    logo = country.find_one({'team':team})
    return logo["logo"]


def get_cal(name):
    country_calendar = db[f'calendar_{season}']
    match_calendar = {}
    for i in range(1,len(country_calendar.find({"country": name}).distinct('tour')) + 1):
        end_match = []
        date = []
        matches = []
        calendar = country_calendar.find({"country": name, 'tour':str(i)} )
        for match in calendar:
            end_match.append(match['ends'])
            date.append(match['date'])
            matches.append(' | '.join((match['date'], 
                                        match['match'], 
                                        match['result'])))
        match_calendar[f'Тур {str(i)}'] = {'Матчи': matches,
                                        'start':date[0] ,
                                        'end':date[-1],
                                        'Закончен': not False in end_match}
    return match_calendar


def sortByAlphabet(inputStr):
    return int(inputStr[:2])


def sort_date(date):
    if len(date.split("|")[0].split()) == 1:
        date = date.split("|")[0].replace('.', '-') + " 23:59"
        return date.strip()
    return date.split('|')[0].replace('.', '-').strip()


def get_tab(name):
    country = db[f'table_{season}']
    calendar = {}
    country_calendar = db[f"calendar_{season}"]
    for team in country.find({"country": name}):
        six_match = country_calendar.find({'match':{"$regex":team['team']}, 'ends': True}).sort("$natural",1)
        calendar[team['team']] = team['games'], \
                                team['points'], \
                                team['balls'],\
                                [' | '.join([match['date'], 
                                             match['match'], 
                                             match['result']]) for match in six_match][-6:]
    return calendar


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
            wait_time : dict = {}
            dict_now = response['matches']['football']['tournaments']
            for id_champ, country in update_champ.items():
                try:
                    for matches in dict_now[id_champ]['matches']:
                        time_delta = datetime.strptime(matches['time_str'],'%d.%m.%Y %H:%M') + \
                            timedelta(hours=2, minutes=15)
                        if matches['status']['name'] == 'Перенесён':
                            continue
                        if time_delta not in wait_time:
                            wait_time[time_delta] = [country]
                        else:
                            if country not in wait_time[time_delta]:
                                wait_time[time_delta].append(country)
                except KeyError:
                    continue
            sorted_dict = dict(sorted(wait_time.items()))
            for date_update, champions_names in sorted_dict.items():
                seconds_sleep = (date_update - datetime.now()).total_seconds()
                time.sleep(seconds_sleep)
                for name_champ in champions_names:
                    add_calendar(name_champ,'2022/2023') 
                    add_table(name_champ,'2022/2023')
                bot.send_message(user_id,'обновил {}'.format('\n'.join(champions_names)))
            i+=1
        except:
            time.sleep(120)

#threading.Thread(target=update_base).start()
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

def upcoming_matches():
    i = 0
    calendar = db[f"calendar_{season}"]
    table = db[f"table_{season}"]
    if calendar.count_documents({}) == 0:
        add_calendar(f"calendar_{season}")
    if table.count_documents({}) == 0:
        for country in update_champ.values():
            add_table(country)
    while True:
        try:
            sess = requests.Session()
            sess.headers.update(User_agent) 
            today_date = (datetime.now() + timedelta(i)).strftime("%Y-%m-%d")
            parse_link = f"{parse_site}/stat/{today_date}.json"
            response = sess.get(parse_link).json()
            live = []
            end = []
            future = []
            dict_now = response['matches']['football']['tournaments']
            for id_champ in update_champ:
                try:
                    for matches in dict_now[id_champ]['matches']:
                        if matches['flags']['live'] == 1:
                            live.append(matches)
                        elif matches['flags']['is_played'] == 1:
                            end.append(matches)
                        else:
                            future.append(matches)
                except KeyError:
                     continue  
            if len(live) > 0:
                for live_match in live:
                    match ='{} - {}'.format(live_match['teams'][0]['name'], 
                                                    live_match['teams'][1]['name']) 
                    results ='{} : {}'.format(live_match['result']['detailed']['goal1'], 
                                                live_match['result']['detailed']['goal2']) 
                    calendar.update_one({'match':match},
                                                    {
                                                    '$set':{
                                                    'result':results,+
                                                    'live':True,
                                                    'time' : live_match['status']['name']
                                                    }
                                                    })
                time.sleep(30)
                if len(end) == 0:
                    upcoming_matches()
            if ends := len(end) > 0:
                for match_end in end:
                    match ='{} - {}'.format(match_end['teams'][0]['name'], 
                                                    match_end['teams'][1]['name']) 
                    if calendar.find_one({'match':match,'ends':True}) is None:
                        results ='{} : {}'.format(match_end['result']['detailed']['goal1'], 
                                                match_end['result']['detailed']['goal2']) 
                        date = match_end['date'].split('-')
                        dates = '-'.join([date[2],date[1],date[0]])
                        calendar.update_one({'match':match},
                                                    {
                                                    '$set':{
                                                    'date':' '.join([dates, match_end['time']]),
                                                    'result':results,
                                                    'tour':match_end['roundForLTAndMC'].split('-')[0],
                                                    'ends': ends,
                                                    'live':False,
                                                    'country' : match_end['section'],
                                                    'champ': match_end['link_title'].split('.')[3].strip()
                                                    }
                                                    }
                                                )  
                        add_table(match_end['section'])
                    if len(live) > 0:
                        upcoming_matches()
            if ends := len(future) > 0:
                time_list = []
                for future_match in future:
                    match ='{} - {}'.format(future_match['teams'][0]['name'], 
                                                future_match['teams'][1]['name']) 
                    if calendar.find_one({'match':match}) is not None:
                        time_match = datetime.strptime(future_match['time_str'],'%d.%m.%Y %H:%M')
                        if future_match['status']['name'] == 'Перенесён':
                            continue
                        if time_match not in time_list:
                            time_list.append(time_match)
                        time_list.sort()
                        for date_update in time_list:
                            seconds_sleep = (date_update - datetime.now()).total_seconds()
                            time.sleep(seconds_sleep) 
                            upcoming_matches()  
                    else:
                        date = future_match['date'].split('-')
                        dates = '-'.join([date[2],date[1],date[0]])
                        calendar.insert_one({'match':match,
                                                        'date':' '.join([dates, future_match['time']]),
                                                        'result':'',
                                                        'tour':future_match['roundForLTAndMC'].split('-')[0],
                                                        'ends': not ends,
                                                        'country' : future_match['section'],
                                                        'champ': future_match['link_title'].split('.')[3].strip()
                                                        }
                                                    )  
            i+=1
        except Exception as e:
            bot.send_message(user_id, e)
            continue  
        
            
                

threading.Thread(target=upcoming_matches).start()           

#db.auth('user_id', '12345')
users_col = dbs['users']


def add_user(employee_name, id, push=False):
    users = {"_id": str(id),
             "Name": employee_name,
             "Push": push
             }
    try:
        users_col.insert_one(users)
        return True
    except Exception():
        return False
    

def get_list_user():
    list_user = []
    for user_view in users_col.find():
        for key, value in user_view.items():
            if key == "_id":
                list_user.append(int(value))
    return list_user


def get_live():
    dict_live = {}
    list_live = []
    for live_view in users_col.find():
        try:
            for key, value in live_view['live'].items():
                if value:
                    list_live.append(key)
            dict_live[live_view['_id']] = list_live
        except KeyError:
            continue
    return dict_live


def view_users():
    user = ''
    for user_view in users_col.find():
        for key, value in user_view.items():
            user += f'{key}: {value}\n'
        user += '\n'
    return user


def set_push(id, bool_push):
    users_col.update_one({"_id": str(id)},
                         {"$set": {"Push": bool_push}})


def add_field(id, num_field, bool_push):
    users_col.update_one({"_id": str(id)},
                         {"$set": {'live': {num_field: bool_push}}})


def delete_field(id, name_field):
    users_col.update_one({"_id": str(id)},
                         {"$unset": {f"{name_field}": 1}})


def get_push(id, name_field=""):
    push_dict = users_col.find_one({"_id": str(id)})
    try:
        if name_field != "":
            return push_dict[name_field]
        else:
            return push_dict['Push']
    except KeyError:
        return ""


def get_user(id):
    user_dict = users_col.find_one({"_id": str(id)})
    if user_dict is None:
        return False
    else:
        return True
