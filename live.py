import requests
from lxml import html
from datetime import datetime, timedelta
from config import User_agent, parse_site

def tomorrow(button):
    sess = requests.Session()
    sess.headers.update(User_agent)
    if button == 'Live':
        today_date = button.lower()
        live = True
    else:
        if button == 'Сегодня':
            day = 0
        elif button == 'Вчера':
            day = -1
        else:
            day = 1
        live = False
        today_date = (datetime.now() + timedelta(day)).strftime("%Y-%m-%d")
    parse_site = f"{parse_site}/stat/{today_date}.json"
    matches = []
    response = sess.get(parse_site).json()
    try:
        dict_now = response['matches']['football']['tournaments']
    except KeyError:
        return None
    for key, value in dict_now.items():
        name_champ = value['name']
        if key in dict_match:
            if value['name'] not in matches:
                matches.append(name_champ)
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
                if len(matches) == 1:
                    matches.remove(name_champ)
    if len(matches) == 0:
        return None
    return matches
#tomorrow('Live')

        
dict_match = {
'football-5251':'Товарищеские матчи (сборные) - 2023',
'football-5287':'ЧЕ-2024 - квалификация. 2-й тур',
'football-4987': 'МИР Российская Премьер-лига. 18-й тур',
'football-5047': 'Испания - Примера. 24-й тур',
'football-5029': 'Франция - Лига 1. 26-й тур',
'football-5057': 'Италия - Серия А. 25-й тур',
'football-5027': 'Германия - Бундеслига. 23-й тур',
'football-5123': 'Португалия - Примейра. 23-й тур',
'football-5049': 'Бельгия - Лига Жюпиле. 28-й тур',
'football-5059': 'Нидерланды - Эредивизия. 24-й тур',
}