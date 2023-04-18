from datetime import datetime, timedelta
from config import User_agent, update_champ
import time
from championat import Calendar, Table, parent_word
import threading
from config import parse_site, update_champ, db, dbs
import requests
import pymongo


def add_calendar(name, name_champ):
    country_calendar = db[f"{name}_calendar"]
    indexes = [name_index['name'] for name_index in country_calendar.list_indexes()] 
    if 'match_1' not in indexes:
        country_calendar.create_index([("match", pymongo.ASCENDING)], unique=True)
    calendar = Calendar(name)
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
                            'season' :name_champ
                            })
        except pymongo.errors.DuplicateKeyError:
            country_calendar.update_one({'match':matches[i]},
                            {'$set':{'date':dates[i],
                                     'result':results[i],
                                     'tour':tours[i],
                                     'ends': results[i] != ""}}
                            )
            

def add_table(name, name_champ):
    country_table = db[f"{name}"]
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
                                    "season": name_champ})
        except pymongo.errors.DuplicateKeyError:
            country_table.update_one({"team": names[i]},
                                        {'$set':{"points": points_stat[i],
                                    "games": games_stat[i],
                                    "win": wins_stat[i],
                                    "lose": loses_stat[i],
                                    "draw": draw_stat[i],
                                    "balls": balls_stat[i],
                                    "logo": logo[i],
                                    "season": name_champ}
                                    })


def get_logo(db_name, season, team):
    country = db[db_name]
    logo = country.find_one({'team':team,"season": season})
    return logo["logo"]


def get_cal(name, name_champ):
    country_calendar = db[f"{name}_calendar"]
    match_calendar = {}
    for i in range(1,len(country_calendar.distinct('tour')) + 1):
        end_match = []
        date = []
        matches = []
        calendar = country_calendar.find({"season": name_champ, 'tour':str(i)} )
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


def get_tab(name, name_champ):
    country = db[name]
    table = country.find({"season": name_champ})
    calendar = {}
    country_calendar = db[f"{name}_calendar"]
    for team in table:
        six_match = country_calendar.find({'match':{"$regex":team['team']}, 'ends': True}).sort("$natural",1)
        calendar[team['team']] = team['games'], \
                                team['points'], \
                                team['balls'],\
                                [' | '.join([match['date'], 
                                             match['match'], 
                                             match['result']]) for match in six_match][-6:]
    return calendar
   

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
                    if key in update_champ:
                        for match in value['matches']:
                            time_match = datetime.strptime(match['time_str'],'%d.%m.%Y %H:%M') + timedelta(hours=2, minutes=30)
                            if [time_match, update_champ[key]] not in clear_time:
                                clear_time.append([time_match, update_champ[key]])
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
                add_calendar(date_match[1],'2022/2023') 
                add_table(date_match[1],'2022/2023')
            i+=1
        except:
            time.sleep(120)

threading.Thread(target=update_base).start()


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
