from datetime import datetime, timedelta
from config import db


def upcoming_match(button):
    list_matches = []
    calendar = db['calendar_2022/2023']
    today_date = datetime.strftime(datetime.now(),'%Y-%m-%d')
    if button == 'Live':
        mongo_calend = calendar.find({'is_live':True, 
                                      'date':str(today_date)})
    else:
        if button == 'Сегодня':
            day = 0
        elif button == 'Вчера':
            day = -1
        else:
            day = 1
        today_date = datetime.strftime(datetime.now() + timedelta(day),'%Y-%m-%d')
        mongo_calend = calendar.find({'date':str(today_date)})
    for match in mongo_calend:
        name_champ_tour = '{}. {}'.format(match['champ'], match['tour'])
        if match['is_live']:
            time_match =", {} ".format( match['status']) 
        elif match['is_over'] :
            time_match = ''
        else:
            time_match =", {} ".format(match['time']) 
        if name_champ_tour not in list_matches:
            list_matches.append(name_champ_tour)
        result = '| {}  {}{} |'.format(
                    match['title'].split(',')[0],
                    match['result'],
                    time_match)
        list_matches.append(result)
    return list_matches