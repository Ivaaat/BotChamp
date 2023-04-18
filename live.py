import requests
from lxml import html
from datetime import datetime, timedelta
from config import User_agent, parse_site, dict_match

def tomorrow(button):
    sess = requests.Session()
    sess.headers.update(User_agent)
    if button == 'Live':
        today_date = button.lower()
    else:
        if button == 'Сегодня':
            day = 0
        elif button == 'Вчера':
            day = -1
        else:
            day = 1
        today_date = (datetime.now() + timedelta(day)).strftime("%Y-%m-%d")
    parse_link = f"{parse_site}/stat/{today_date}.json"
    matches = []
    response = sess.get(parse_link).json()
    try:
        dict_now = response['matches']['football']['tournaments']
    except KeyError:
        return None
    for key, value in dict_now.items():
        if key in dict_match:
            if value['name'] not in matches:
                matches.append(value['name'])
            for match in value['matches']:
                if button == 'Вчера':
                    time_match = ""
                elif button == 'Live':
                    if match['status']['name'] not in ['Не начался', 'Окончен']:
                        time_match =", " + match['status']['name']
                    else:
                        continue
                else:
                    time_match = ", " + match['time']
                    if match['status']['name'] not in ['Не начался', 'Окончен']:
                        time_match =", {} Live".format(match['status']['name']) 
                try:
                    res_1 = '| ' + str(match['result']['detailed']['goal1'])
                    res_2 = str(match['result']['detailed']['goal2']) +  ' |' 
                    sep = ":"
                except KeyError:
                    res_1 = ""
                    res_2 = ""
                    sep = "-"
                result = '{} {} {} {} {}{}'.format(
                    match['teams'][0]['name'],
                    res_1,
                    sep,
                    res_2,
                    match['teams'][1]['name'],
                    time_match
                        )
                matches.append(result)
            if matches[-1] == value['name']:
                matches.remove(value['name'])
    if len(matches) == 0:
        return None
    return matches

#tomorrow('Live')
