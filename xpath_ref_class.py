#файл с ключами xpath парсинга сайта

#xpath сайта https://football-video.org/
review_xpath_href = '//div  [@class="figure-wrap1"]/a[1]/@href'
review_xpath_title = '//div  [@class="figure-wrap1"]/a[1]/@title'
review_xpath_date = '//span  [@class="datespan1"]//text()'


#xpath конкретной ссылки на обзор матч сайта  https://football-video.org/
review_xpath_match_href ='//div  [@class="embed-responsive embed-responsive-16by9"]/iframe/@src'
#xpath конкретной ссылки на обзор матча чемпионата Франции сайта  https://football-video.org/
review_xpath_match_France_href = '//div  [@class="embed-responsive embed-responsive-16by9"]/img/@onclick'


#xpath конкретной ссылки на чемпионат https://www.championat.com/football/_{country}.html
#команд teams
teams_xpath = '//td[@class = "_nowrap _w-64"]/a/span[2]/text()'
#кол-во игр games
#games_xpath = '//td[@class = "results-table__games _right"]/text()'
games_xpath = '//tbody//td[3]/text()'
#кол-во очков points
#points_xpath = '//td[@class = "results-table__points _right"]/text()'
points_xpath = '//tbody//td[4]/text()'
#послед 6 результатов results
results_xpath = '//td [@class="results-table__outcome _center _hidden-td"]//@title'
#ссылка на информацию о команде 
logo_ref_xpath = '//td [@class="_nowrap _w-64"]//@href'
#картинки эмблем команд 'https://www.championat.com' + ссылка на информацию о команде (см.выше)
logo_xpath = '//div  [@class="entity-header__img"]//@src'


#Создание календаря dict_command()
#парсинг https://www.championat.com/football/_{country}.html
#вычисляем необходимую подстанову id пример(tournament/4987)берем [0] элемент- это calendar 
parse_xpath_text = '//div  [@class="entity-header__menu js-entity-header-menu"]//@href'
#теперь парсим ссылку на календарь https://www.championat.com/football/{country}/tournament/{у всех свой}/calendar/
#вытаскиваем номер тура
num_xpath_tour = '//tr/@data-tour'
#вытаскиваем название матча
parse_xpath_match = '//span  [@class="table-item__name"]/text()'
#вытаскиваем результат
parse_xpath_result = '//span  [@class="stat-results__count-main"]//text()'
#вытаскиваем дату
date_xpath_match = '//td [@class="stat-results__date-time _hidden-td"]/text()'

