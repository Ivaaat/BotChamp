from datetime import  timedelta, date, datetime
from config import db
from pymongo import MongoClient


def upcoming_match(button):
    #client = MongoClient()
    # db = client['champ']
    list_matches = []
    calendar = db['foot']
    today_date = date.today()
    if button == 'Live':
        now_timestamp = datetime.now().timestamp()
        #for matches_not_end in self.collection.find({'$and':[{'pub_date':{'$lt':now_timestamp}},
        mongo_calend = calendar.find({'$and':[{'pub_date':{'$lt':now_timestamp}}, {'flags.live':1, 'date':str(today_date)}]})
    else:
        if button == 'Сегодня':
            day = 0
        elif button == 'Вчера':
            day = -1
        else:
            day = 1
        today_date = date.today() + timedelta(day)
        mongo_calend = calendar.find({'date':str(today_date)})
    for match in mongo_calend:
        if match['flags']['important'] != 1:
            continue
        try:
            round = match['roundForLTAndMC']
        except KeyError:
            round = ""
        try:
            match_result = '{} : {}'.format(match['result']['detailed']['goal1'],
                                            match['result']['detailed']['goal2']) 
        except KeyError:
            match_result = ''
        name_champ_tour = '{}. {}'.format(match['name_champ'], round)
        if match['flags']['live'] == 1:
            time_match =", {} Live".format( match['status']['name']) 
        elif match['flags']['is_played'] :
            time_match = ''
        else:
            time_match =", {} ".format(match['time']) 
        if name_champ_tour not in list_matches:
            list_matches.append(name_champ_tour)
        result = '| {}  {}{} |'.format(
                    match['link_title'].split(',')[0],
                    match_result,
                    time_match)
        list_matches.append(result)
    return list_matches

# upcoming_match('Сегодня')
# upcoming_match('Live')
# upcoming_match('Завтра')
# upcoming_match('Вчера')

