import requests
from lxml import html
from config import TOKEN, user_id, User_agent
import time
import datetime


def world_play():
    sess = requests.Session()
    sess.headers.update(User_agent)
    parse_site = "https://www.championat.com/football/_worldcup/tournament/4949/calendar/"
    response = sess.get(parse_site)
    tree = html.fromstring(response.text)
    #news_ref = tree.xpath('//span[@class = "table-item__name"]/text()') 
    news_ref = tree.xpath('//td[@class="stat-results__link"]/a/@title') 
    res_match = tree.xpath('//span[@class ="stat-results__count-main"]/text()') 
    tournam_stage = tree.xpath('//td[@class="stat-results__group _hidden-td"]/text()') 
    result_match = tree.xpath('//span[@class="stat-results__count-main"]/text()') 
    res_penalty = tree.xpath('//span[@class="stat-results__count-ext"]/text()') 
    return_string = ""
    asd = []
    a = 0
    for i in range(len(news_ref)-16, len(news_ref)):
        penalty = ""
        name_macth = ('Япония - Хорватия', 'Марокко - Испания', 'Хорватия - Бразилия', "Нидерланды - Аргентина" )
        if news_ref[i][:news_ref[i].find(',')].strip().startswith(name_macth[a]):
            penalty = "| пен: " + res_penalty[a]
            a+=1
            if a == len(name_macth):
                a = 0
        # return_string+='{} | {} | {} {} \n'.format(tournam_stage[i].strip(), 
        #                                         news_ref[i][:news_ref[i].find(',')].strip(), 
        #                                         result_match[i].strip(),
        #                                         penalty)
        asd.append('{} | {} | {} {} '.format(tournam_stage[i].strip(), 
                                                news_ref[i][:news_ref[i].find(',')].strip(), 
                                                result_match[i].strip(),
                                                penalty))                                            

    #print(return_string)
    print('\n'.join(asd[::-1]))

def json_championat(query, name_team = ""):
    today_date = datetime.datetime.now().strftime("%Y-%m-%d")
    sess = requests.Session()
    sess.headers.update(User_agent)
    parse_site = f"https://www.championat.com/stat/{today_date}.json"
    #parse_site = f"https://www.championat.com/stat/2022-12-06.json"
    response = sess.get(parse_site).json()
    asd = []
    match query:
        case 'Live':
            for value_dict in response['matches']['football']['tournaments'].values():
                for i in range(len(value_dict['matches'])):
                    if value_dict['matches'][i]['flags']['live'] == 1:
                        asd.append(value_dict['name'])
                        team_res1 = value_dict['matches'][i]['result']['detailed']['goal1']
                        team_res2 = value_dict['matches'][i]['result']['detailed']['goal2']
                        live_time_match = value_dict['matches'][i]['status']['name']
                        result_match = f'| {team_res1}:{team_res2} |'
                        team_name1 = value_dict['matches'][i]['teams'][0]['name']
                        team_name2 = value_dict['matches'][i]['teams'][1]['name']
                        date_match = value_dict['matches'][i]['date']
                        time_match = value_dict['matches'][i]['time']
                        asd.append(f'{team_name1} - {team_name2} | {live_time_match}  {result_match}')
            if len(asd) == 0:
                return "Нет матчей" 
            else:
                return asd 
        case 'Сегодня':
            for value_dict in response['matches']['football']['tournaments'].values():
                asd.append(value_dict['name'])
                for i in range(len(value_dict['matches'])):
                    try:
                        extra_result = value_dict['matches'][i]['result']['detailed']['extra']
                    except KeyError:
                        extra_result = ""
                    if value_dict['matches'][i]['status']['name'] == 'Не начался':                        
                        result_match = ""
                    elif value_dict['matches'][i]['flags']['live'] == 1:
                        team_res1 = value_dict['matches'][i]['result']['detailed']['goal1']
                        team_res2 = value_dict['matches'][i]['result']['detailed']['goal2']
                        result_match = f'"Live" | {team_res1}:{team_res2} |'
                    else:
                        team_res1 = value_dict['matches'][i]['result']['detailed']['goal1']
                        team_res2 = value_dict['matches'][i]['result']['detailed']['goal2']
                        result_match = f'| {team_res1}:{team_res2} |'
                    if extra_result != "":
                        extra_result = ('Пен: {}').format(value_dict['matches'][i]['result']['detailed']['extra'] )
                    else:
                        extra_result = ""
                    team_name1 = value_dict['matches'][i]['teams'][0]['name']
                    team_name2 = value_dict['matches'][i]['teams'][1]['name']
                    date_match = value_dict['matches'][i]['date']
                    time_match = value_dict['matches'][i]['time']
                    asd.append(f'{date_match} {time_match} | {team_name1} - {team_name2}\n {result_match} {extra_result}')
            return asd 
        case 'КФ':
            for value_dict in response['matches']['football']['tournaments'].values():
                for i in range(len(value_dict['matches'])):
                    try:
                        if value_dict['matches'][i]['status']['name'] !=  "Окончен" and value_dict['matches'][i]['teams'][0]['name'] in name_team:
                            team_coeff1 = value_dict['matches'][i]['coeffs']['RU']['f']
                            team_coeff2 = value_dict['matches'][i]['coeffs']['RU']['s']
                            team_coeff_drow = value_dict['matches'][i]['coeffs']['RU']['d']
                            all_coef = f'Коэффициенты: {team_coeff1} - {team_coeff_drow} - {team_coeff2}'
                            asd.append(team_coeff1)
                            asd.append(team_coeff_drow)
                            asd.append(team_coeff2)
                            break
                    except KeyError:
                        asd.append("Нет коэффициентов")
                        return asd
            return asd

    def coeff():
        if value_dict['matches'][i]['status']['name'] !=  "Окончен":
            team_coeff1 = value_dict['matches'][i]['coeffs']['RU']['f']
            team_coeff2 = value_dict['matches'][i]['coeffs']['RU']['s']
            team_coeff_drow = value_dict['matches'][i]['coeffs']['RU']['d']
            all_coef = f'Коэффициенты: {team_coeff1} - {team_coeff_drow} - {team_coeff2}'
            asd.append(team_coeff1,team_coeff_drow,team_coeff2)

            



            


                    

    
                    
            
    #         asd.append(f'{date_match} {time_match} | {team_name1} - {team_name2} | {live_time_match} {result_match}\n\n \
    #   {all_coef}\n{separator1}\n')   
#             asd.append(f'{date_match} {time_match} | {team_name1} - {team_name2} | {live_time_match} {result_match}\n\n \
#    {all_coef}\n') 
            asd.append(f'{date_match} {time_match} | {team_name1} - {team_name2} |')   
        #asd.append(f'{separator}\n\n')
    #print('\n'.join(asd))
    #return ('\n'.join(asd))
# while True:    
#     json_championat()
#     time.sleep(1)

#json_championat('Live')
#json_championat('КФ', "Бирмингем Сити")
#json_championat('Сегодня')
