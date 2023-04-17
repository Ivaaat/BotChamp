#файл с ключами xpath парсинга сайта

#xpath сайта https://football-video.org/
review_xpath_href = '//div  [@class="figure-wrap1"]/a[1]/@href'
review_xpath_title = '//div  [@class="figure-wrap1"]/a[1]/@title'
review_xpath_date = '//span  [@class="datespan1"]//text()'


#xpath конкретной ссылки на обзор матч сайта  https://football-video.org/
review_xpath_match_href ='//div  [@class="embed-responsive embed-responsive-16by9"]/iframe/@src'
#xpath конкретной ссылки на обзор матча чемпионата Франции сайта  https://football-video.org/
review_xpath_France_href = '//div  [@class="embed-responsive embed-responsive-16by9"]/img/@onclick'

#вычисляем необходимую подстанову id пример(tournament/4987)берем [0] элемент- это calendar 
parse_text = '//div  [@class="entity-header__menu js-entity-header-menu"]//@href'


#xpath для class Calendar:
#даты 
date_match = '//td [@class="stat-results__date-time _hidden-td"]/text()'
#номер тура
num_tour = '//tr/@data-tour'
#кол-во игр games
games = '//td [@class="stat-results__link"]//@title'
#вытаскиваем результат
result = '//span  [@class="stat-results__count-main"]//text()'


#xpath для class Table:
#названия клубов
name_xpath = '//span[@class="table-item__name"]/text()'
#очки
points = '//td[8]/strong/text()'
#игры
game_table = '//td[3]/strong/text()'
#победы
wins = '//td[4]//text()'
#ничья
draws = '//td[5]//text()'
#поражения
loses = '//td[6]//text()'
#мячи
balls = '//td[7]//text()'
#лого
logo_ref = '//td [@class="_nowrap _w-64"]//@data-src'



