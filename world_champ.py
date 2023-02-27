import requests
from lxml import html
sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
    })
#country = 'worldcup'
class WorldCup:
    def __init__(self, country) -> None:
        self.country = country
        self.ref_country = ""
        self.list_table = []
        self.url = 'https://www.championat.com'
        
    def worldcup_calendar(self):
        text_button = ""
        url_championat = f'{self.url}/football/_{self.country}.html'
        response = sess.get(url_championat)
        tree = html.fromstring(response.text)
        parse_calendar = tree.xpath('//div  [@class="entity-header__menu js-entity-header-menu"]//@href')
        url_calendar = f'{self.url}{parse_calendar[0]}calendar'
        response = sess.get(url_calendar)
        tree = html.fromstring(response.text)
        pars_title = tree.xpath('//td [@class="stat-results__link"]/a/@title')
        parse_time_match = tree.xpath('//td [@class="stat-results__date-time _hidden-td"]/text()')
        parse_name_group = tree.xpath('//td [@class="stat-results__group _hidden-td"]/text()')
        parse_score = tree.xpath("//span [@class='stat-results__count-main']/text()")
        for i in range(len(parse_score)):
            text_button += '{} | {} | {} | {}\n\n'.format(parse_name_group[i],
                                                    " ".join(parse_time_match[i].split()),
                                                    pars_title[i][:pars_title[i].find(',')],
                                                    parse_score[i].strip())        
        return text_button

    def worldcup_table(self):  
        url_championat = f'{self.url}/football/_{self.country}.html'
        response = sess.get(url_championat)
        tree = html.fromstring(response.text)
        list_teams = tree.xpath('//span[@class="table-item__name"]/text()')
        list_games = tree.xpath('//tr/td[3]/text()')
        list_points = tree.xpath('//tr/td[4]/text()')
        list_ref = tree.xpath('//td[@class="_nowrap _w-64"]/a/@href')
        self.ref_country = list_ref
        str_table = []
        alpabet  = 'ABCDEFGH'
        self.list_table = [f'{list_teams[i]} Игры: {list_games[i]} Очки: {list_points[i].strip()}' for i in range(len(list_teams))]
        j = 0
        for i in range(0,len(list_games)):
            if i % 4 == 0:
                name_group = f'Группа {alpabet[j]}'
                str_table.append(name_group)
                j+=1
            str_table.append(self.list_table[i])

        return str_table
        
    def worldcup_results(self, message, dict_name_ref, bot, calendar_and_table, button_country_news):
        try:
            if message.text == 'Главное меню':
                raise Exception(button_country_news(message))   
            elif message.text == 'Назад':
                raise Exception(calendar_and_table(message, back = 'Чемпионат мира'))
            elif message.text.startswith("Группа") or message.text not in dict_name_ref:
                msg = bot.send_message(message.chat.id, "Выбери команду")
                return bot.register_next_step_handler(msg, self.worldcup_results, dict_name_ref, bot, calendar_and_table, button_country_news)
            else:
                response = sess.get(self.url + dict_name_ref[message.text])
                tree = html.fromstring(response.text)
                sadc = ""
                list_data = tree.xpath('//div[@class="stat-results__title-date _hidden-dt"]//text()')
                list_match = tree.xpath('//span [@class="table-item__name"]/text()')
                #list_relust = tree.xpath('//span [@class="stat-results__count-main"]/text()')
                list_relust = tree.xpath('//span[starts-with(@class,"stat-results__count-main")]/text()')
                ref_logo = tree.xpath('//div [@class="entity-header__img"]//img/@src')
                j = 0
                for i in range(0,len(list_data),2):
                    sadc += f'{list_data[i].strip()} \
 {list_data[i+1].strip()} \
 {list_match[i]} - {list_match[i+1]}  {list_relust[j].strip()}\n'
                    j+=1
                #msg = bot.send_message(message.chat.id, sadc)
                msg = bot.send_photo(message.chat.id, ref_logo[0] , caption = sadc)
                bot.register_next_step_handler(msg, self.worldcup_results, dict_name_ref, bot, calendar_and_table, button_country_news)
        except Exception as main_menu_or_step_back:
            main_menu_or_step_back

def world_playoff():
    parse_site = "https://www.championat.com/football/_worldcup/tournament/4949/calendar/"
    response = sess.get(parse_site)
    tree = html.fromstring(response.text)
    #news_ref = tree.xpath('//span[@class = "table-item__name"]/text()') 
    news_ref = tree.xpath('//td[@class="stat-results__link"]/a/@title') 
    res_match = tree.xpath('//span[@class ="stat-results__count-main"]/text()') 
    tournam_stage = tree.xpath('//td[@class="stat-results__group _hidden-td"]/text()') 
    result_match = tree.xpath('//span[@class="stat-results__count-main"]/text()') 
    res_penalty = tree.xpath('//span[@class="stat-results__count-ext"]/text()') 
    date_match = tree.xpath('//td[@class="stat-results__date-time _hidden-td"]/text()') 
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
        asd.append('                    {} \n| {}|\n| {} | {} {} '.format(tournam_stage[i].strip(),
                                                date_match[i].strip(), 
                                                news_ref[i][:news_ref[i].find(',')].strip(), 
                                                result_match[i].strip(),
                                                penalty))                                            

    #print(return_string)
    return ('\n\n'.join(asd))





         
    

    '''
    list_teams = []
    for i in range(len(parse_table)):
        if parse_table[i] not in list_teams:
            list_teams.append(parse_table[i])
    '''

    print("")
                
#worldcup_table('worldcup')
'''
for i in range(len(parse_score)):
    kalendar_world_cup[pars_title[i][:pars_title[i].find(',')]] = {"Группа":parse_name_group[i],
                                                "Дата": parse_time_match[i].strip(),
                                                "Счет": parse_score[i].strip()}
print("")
for key,value in kalendar_world_cup.items():
    print(value["Группа"] + key +  value["Дата"] + value["Счет"]) 
'''
