from datetime import datetime, timedelta
from config import db


def upcoming_match(button):
    list_matches = []
    calendar = db['calendar_2022/2023']
    if button == 'Live':
        mongo_calend = calendar.find({'live':True, 
                                      'date':{
            '$regex':datetime.now().strftime("%d-%m-%Y")}})
    else:
        if button == 'Сегодня':
            day = 0
        elif button == 'Вчера':
            day = -1
        else:
            day = 1
        today_date = (datetime.now() + timedelta(day)).strftime("%d-%m-%Y")
        mongo_calend = calendar.find({'date':{'$regex':today_date}})
    for match in mongo_calend:
        name_champ_tour = '{}. {}-й тур'.format(match['champ'], match['tour'])
        if match['live']:
            time_match =" | {}  Live | ".format(match['time']) 
        elif day == -1:
            time_match = ""
        else:
            time_match = " | {} | ".format(match['date'].split()[1]) 
        
        if name_champ_tour not in list_matches:
            list_matches.append(name_champ_tour)
        result = '| {} | {} {}'.format(
                    match['match'],
                    match['result'],
                    time_match)
        list_matches.append(result)
    return list_matches