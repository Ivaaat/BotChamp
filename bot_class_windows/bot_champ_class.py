import requests
from lxml import html
import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
import logging
from telebot import formatting
from news_football_class import news_parse, get_one_news
from youtube_parse_class import parse_youtube_ref, you_pytube, bs4_youtube
from xpath_ref_class import *
from constants_class import mass_contry, mass_review, parse_site, mass_youtube
from championat_class import Calendar, Table, Team
from world_champ import WorldCup, world_playoff
import threading
from config import TOKEN, user_id, User_agent
from MyDataBase import MyBaseDB
import re
from test import json_championat
#from bot_class_windows.user_mongo import add_user, view_users, get_push
from user_mongo import add_user, view_users, get_push, get_user, get_list_user

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
bot = telebot.TeleBot(TOKEN)#Токен 
bot.set_my_commands(
    commands=[
        telebot.types.BotCommand("start", "start_parse"),
    ],
)

base = MyBaseDB()

# #with open(base.filename, "r", encoding = 'utf-8') as file:
#             content = file.readlines()
#             for i in range(1,len(content)):
#                 send_user = re.findall(r'\d+', content[i])
#                 bot.send_message(send_user[len(send_user)-1],"Вышло обновление. Жми /start")

user_list = get_list_user()
for i in range(len(user_list)):
                #send_user = re.findall(r'\d+', user_list[i])
                bot.send_message(int(user_list[i]),"Вышло обновление. Жми /start")


sess = requests.Session()
sess.headers.update(User_agent)

#создание клавиатуры с название чемпионатов
def champ_keyboard():
    markup = types.ReplyKeyboardMarkup()
    back_button(markup)
    for key in mass_contry:
        button = types.KeyboardButton(key)
        markup.add(button)
    return markup

#создание кнопки назад
def back_button(markup):
    button_back = types.KeyboardButton('Назад')
    return markup.add(button_back)

#создание кнопки меню
def menu_button(markup):
    button_menu = types.KeyboardButton('Главное меню')
    return markup.add(button_menu)
   

def push(message, push_notif, old_news, old_video):
    try:
        #list_photo_text = "new"
        #old_news = "old"
        new_video = []
        while True:
            timer = 20
            if push_notif:
                parse_site1 = f'{parse_site}/news/football/1.html'
                response = sess.get(parse_site1)
                tree = html.fromstring(response.text)
                news_ref = tree.xpath('//div  [@class="news _all"]//a[1]/@href') 
                list_photo_text = get_one_news(news_ref[0])
                if list_photo_text[1][:20] != old_news[1][:20]:
                    old_news = list_photo_text[1] 
                    if len(list_photo_text[1]) >= 1024:
                        num_symb =list_photo_text[1][:1024].rfind('.') + 1
                        bot.send_photo(message.chat.id, 
                            list_photo_text[0],
                            caption=list_photo_text[1][:num_symb])
                        for x in range(num_symb, len(list_photo_text[1]), 1024):
                            bot.send_message(message.chat.id, list_photo_text[1][x:x+1024])
                            list_photo_text[1][:20] == old_news[1][:20]
                    else:
                        bot.send_photo(user_id, 
                            list_photo_text[0],
                            caption=list_photo_text[1],
                        )
                        list_photo_text[1][:20] == old_news[1][:20]
                for query in mass_youtube:
                    new_video_dict = bs4_youtube(query)
                    for desc_video, ref in new_video_dict.items():
                        if desc_video not in old_video:
                            new_video.append(desc_video)
                            bot.send_message(message.chat.id, ref)
                        break
                    old_video.extend(new_video)
            time.sleep(timer)
    except Exception:
        time.sleep(timer)
        threading.Timer(10,push(message)).start()

def user(message):
    bot.send_message(user_id,base.open())

def user_verif(message):
    word_verif = "Спартак"
    if message.text != word_verif:
        msg = bot.send_message(message.chat.id, "Напиши админу: https://t.me/vaneuser")
        return bot.register_next_step_handler(msg, user_verif)
    #base.create(f'{message.chat.first_name} {message.chat.username}', message.chat.id, unique_strings=True )
    add_user(f'{message.chat.first_name} {message.chat.username}', message.chat.id, push=False)
    #bot.send_message(user_id,base.open())
    bot.send_message(user_id,view_users())
    bot.send_message(user_id,"Новый пользователь {} {} {}".format(message.chat.id, message.chat.first_name, message.chat.username))
    return button_country_news(message)


#СТАРТУЕМ ОТСЮДА
@bot.message_handler(commands='start')
def button_country_news(message):
    #if str(message.chat.id) not in base.open():
    if not get_user(message.chat.id):
        msg = bot.send_message(message.chat.id, "Введи проверочное слово")
        return bot.register_next_step_handler(msg, user_verif)
    markup = types.ReplyKeyboardMarkup()
    button_country = types.KeyboardButton('Чемпионаты🏆')
    button_news = types.KeyboardButton('Новости📰')
    button_review = types.KeyboardButton('Обзоры⚽')
    button_live = types.KeyboardButton('Live')
    markup.add(button_country, button_news)
    markup.add(button_review, button_live)
    msg = bot.send_message(message.chat.id, f'{message.chat.first_name}! aka {message.chat.username}\n\n\
                     ⚽ Тебя приветствует @{bot.user.username} ⚽\n\n\
        Здесь можно узнать самое главное о топ чемпионатаx!\n\n\
                Хочешь узнать результаты команд?\n\
                ✅Жми - Чемпионаты🏆\n\n\
                Хочешь узнать последние новости футбольного мира?\n\
                ✅Жми -  Новости📰\n\n\
                Хочешь посмотреть видеообзоры футбольных матчей?\n\
                ✅Жми -  Обзоры⚽\n\n\n\
                ✅Жми /push будут приходить уведомления о новостях!\n\n\n✅Выбирай!', reply_markup= markup)
    bot.delete_my_commands()
    bot.set_my_commands(
    commands=[
        telebot.types.BotCommand("push", "push notifications")
    ],
)
    bot.register_next_step_handler(msg, table_text)

#обработка inline-кнопки главное меню
@bot.callback_query_handler(func=lambda call: call.data == 'back')
def callback_query(call):
        bot.answer_callback_query(call.id, "Главное меню")
        bot.clear_step_handler_by_chat_id(chat_id = call.message.chat.id)
        button_country_news(call.message)

#Создаем три кнопки "Чемпионаты🏆" и "Новости📰  'Обзоры⚽' после вызова старта" 
def table_text(message, back = "" ): 
    markup = types.ReplyKeyboardMarkup()
    if message.text == '/push':
        if get_push(message.chat.id) == False:
            push_notif = True
        else:
            push_notif = False
        time.sleep(1)
        parse_site1 = f'{parse_site}/news/football/1.html'
        response = sess.get(parse_site1)
        tree = html.fromstring(response.text)
        news_ref = tree.xpath('//div  [@class="news _all"]//a[1]/@href') 
        old_news = get_one_news(news_ref[0])
        old_video = []
        for query in mass_youtube:
            new_video_dict = bs4_youtube(query)
            for desc_video, ref in new_video_dict.items():
                old_video.append(desc_video)
                break
        button_country_news(message)
        return threading.Timer(10,push(message, push_notif, old_news, old_video)).start()
    elif message.text == '/user':
        user(message)
        return button_country_news(message)
    elif 'Чемпионаты🏆' in [message.text, back]:
        msg = bot.send_message(message.chat.id, 'Выбери чемпионат', reply_markup=champ_keyboard())
        bot.register_next_step_handler(msg, calendar_and_table)
    elif message.text == 'Новости📰':
        back_button(markup)
        dict_news = news_parse()
        for news in dict_news:
                    markup.add(types.KeyboardButton(news))
        bot.clear_step_handler_by_chat_id(chat_id = message.chat.id)
        msg = bot.send_message(message.chat.id,
                        'Новости', 
                        reply_markup = markup)
        bot.register_next_step_handler(msg, get_news,dict_news)
    elif 'Обзоры⚽' in [message.text, back]:
        back_button(markup)
        for key in mass_review:
            button_champ_rev = types.KeyboardButton(key)
            markup.add(button_champ_rev)
        msg = bot.send_message(message.chat.id, 'Выбери чемпионат', reply_markup=markup)
        bot.register_next_step_handler(msg, get_dict_review)
    elif 'Live' in [message.text, back]:
        markup = types.ReplyKeyboardMarkup()
        button_today = types.KeyboardButton('Сегодня')
        button_live = types.KeyboardButton('Live')
        back_button(markup)
        markup.add(button_today, button_live)
        msg = bot.send_message(message.chat.id, 'Матчи', reply_markup=markup)
        bot.register_next_step_handler(msg, today_or_live)
    else:
        bot.clear_step_handler_by_chat_id(chat_id = message.chat.id)
        button_country_news(message)

def today_or_live(message):
    try:
        markup = types.ReplyKeyboardMarkup()
        prop_match =  json_championat(message.text)
        menu_button(markup)
        back_button(markup)
        if message.text == 'Назад':
            raise Exception(button_country_news(message))
        elif prop_match == "Нет матчей":
            button_name = types.KeyboardButton(prop_match)
            markup.add(button_name)
        elif message.text in  ['Live', "Сегодня"]: 
            for name_match in prop_match:
                button_name = types.KeyboardButton(name_match)
                markup.add(button_name)
        else:
            raise Exception(table_text(message, back = 'Live'))
        msg = bot.send_message(message.chat.id, message.text, reply_markup=markup)
        bot.register_next_step_handler(msg, property_match)
    except Exception as main_menu_or_step_back:
        main_menu_or_step_back

def property_match(message):
    try:
        if message.text == 'Главное меню':
            raise Exception(button_country_news(message))
        elif message.text == 'Назад':
            raise Exception(table_text(message, back = 'Live'))
        else:
            list_coeff = json_championat("КФ", message.text)
            if len(list_coeff) == 0:
                msg = bot.send_message(message.chat.id, "Матч окончен!")
                return bot.register_next_step_handler(msg, table_text, 'Live')
            elif len(list_coeff) == 1:
                msg = bot.send_message(message.chat.id, list_coeff[0])
                return bot.register_next_step_handler(msg, table_text, 'Live')
            markup = types.ReplyKeyboardMarkup()
            button_team1 = types.KeyboardButton(f'П1: {list_coeff[0]}')
            button_drow = types.KeyboardButton(f'Н: {list_coeff[1]}')
            button_team2 = types.KeyboardButton(f'П2: {list_coeff[2]}')
            markup.add(button_team1, button_drow, button_team2)
            msg = bot.send_message(message.chat.id, "КФ", reply_markup= markup)
            bot.register_next_step_handler(msg, table_text, 'Live')
    except Exception as main_menu_or_step_back:
        main_menu_or_step_back

def button_coeff(message, list_coeff):
    try:
        if len(list_coeff) == 0:
            msg = bot.send_message(message.chat.id, "Матч окончен!")
            return bot.register_next_step_handler(msg, table_text, 'Live')
        elif len(list_coeff) == 1:
            msg = bot.send_message(message.chat.id, list_coeff[0])
            return bot.register_next_step_handler(msg, table_text, 'Live')
        markup = types.ReplyKeyboardMarkup()
        button_team1 = types.KeyboardButton(f'П1: {list_coeff[0]}')
        button_drow = types.KeyboardButton(f'Н: {list_coeff[1]}')
        button_team2 = types.KeyboardButton(f'П2: {list_coeff[2]}')
        markup.add(button_team1, button_drow, button_team2)
        if message.text == 'Главное меню':
            raise Exception(button_country_news(message))
        elif message.text == 'Назад':
            raise Exception(table_text(message, back = 'Live'))
        else:
            msg = bot.send_message(message.chat.id, "КФ", reply_markup= markup)
            bot.register_next_step_handler(msg, table_text, 'Live')
    except Exception as main_menu_or_step_back:
        main_menu_or_step_back



#Создаем две кнопки "Календарь" и "Таблица " 
def calendar_and_table(message, back = ""):
    try:
        bot.delete_message(message.chat.id, message.message_id)
        markup = types.ReplyKeyboardMarkup()
        button_calendar = types.KeyboardButton('Календарь🗓')
        button_table = types.KeyboardButton('Таблица⚽')
        back_button(markup)
        markup.add(button_calendar, button_table)
        if back in mass_contry:
            msg = bot.send_message(message.chat.id, back, reply_markup=markup)
            bot.register_next_step_handler(msg, get_def, back)
        elif message.text in mass_contry:
            msg = bot.send_message(message.chat.id, message.text, reply_markup=markup)
            bot.register_next_step_handler(msg, get_def, message.text)
        elif message.text == 'Назад':
            raise Exception(button_country_news(message))
        else:
            raise Exception(table_text(message, back='Чемпионаты🏆'))
    except Exception as main_menu:
        main_menu
    
#Нажатие кнопок обозначенных выше
def get_def(message, text):
    try:
        if message.text == 'Календарь🗓':
            create_calendar(message, text)
        elif message.text == 'Таблица⚽':
            create_table(message, text)
        elif message.text == 'Назад':
            raise Exception(table_text(message, back='Чемпионаты🏆'))
        else:
            msg = bot.send_message(message.chat.id, f'{message.chat.first_name}!✅Выбери!\n\n\
                                  🔙Назад\n\n\
            🗓Календарь          📊Таблица\
            ')
            bot.register_next_step_handler(msg, get_def, text)
    except Exception as step_back:
        step_back

#Создание таблицы с командами
def create_table(message, country_button):
    #Создаю массив с командами из парсинга
    if country_button == 'Чемпионат мира🌍':
        bot.send_message(message.chat.id, f'{country_button}. Плей-офф! \n\n{world_playoff()}')
        return calendar_and_table(message, back = country_button)
    else:
        table = Table(mass_contry.get(country_button))                    
        mass = table.get_table()
        markup = types.ReplyKeyboardMarkup()
        menu_button(markup)
        back_button(markup)
        i = 1
        for key, value in mass.items():
            button = types.KeyboardButton(f'{str(i)}.  {key}' + 
            '   Очки: ' + str(value['Очки']) + 
            '   Игры: ' + str(value['Игры'])
            )
            markup.add(button)
            i+=1
        msg = bot.send_message(message.chat.id, 
        f'{country_button}.Таблица чемпионата!\n\
    Выбери команду, чтобы узнать последние результаты', 
                                        reply_markup=markup
        )
        bot.register_next_step_handler(msg, result_team, mass, country_button)

#Нажатие на кнопку с названием команды
def result_team(message, dict_team, country_button):
    try:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Главное меню", callback_data="back")) 
        text = message.text[4:message.text.find('О', 5)].strip() 
        if text in dict_team:
            team = Team(text, dict_team)
            team.get_logo()
            bot.delete_message(message.chat.id, message.message_id)
            msg = bot.send_photo(message.chat.id, 
                team.logo_ref_team,
                caption = formatting.mbold(team.result_title),
                parse_mode='MarkdownV2', 
                reply_markup = markup
                )
            bot.register_next_step_handler(msg, result_team, dict_team, country_button)
        elif message.text == 'Главное меню':
            raise Exception(button_country_news(message))
        elif message.text == 'Назад':
            raise Exception(calendar_and_table(message, back = country_button))
        else:
            msg = bot.send_message(message.chat.id, 'Выбери команду:')
            bot.register_next_step_handler(msg, result_team, dict_team, country_button)
    except Exception as main_menu_or_step_back:
        main_menu_or_step_back
    
#Создание календаря
def create_calendar(message, country_button):
    if country_button == "Чемпионат мира🌍":
        worldcup = WorldCup(mass_contry[country_button])
        bot.send_message(message.chat.id, worldcup.worldcup_calendar())
        return calendar_and_table(message, back = country_button)
    elif country_button in mass_contry:
        country = mass_contry.get(country_button)
        calendar = Calendar(country)
        dict_calendar = calendar.get_calendar()
        markup = types.ReplyKeyboardMarkup()
        menu_button(markup)
        back_button(markup)
        for key in dict_calendar:
            button = types.KeyboardButton(key)
            markup.add(button)
        msg = bot.send_message(message.chat.id, 
                            f'{country_button} Выбери тур, чтобы узнать результаты:', 
                            reply_markup=markup
                            )
        bot.register_next_step_handler(msg, view_tour, dict_calendar, calendar.tour, country_button)
    else:
        msg = bot.send_message(message.chat.id, 'Выбери чемпионат:[eq')
        bot.register_next_step_handler(msg, create_calendar)
    
#Обработка нажатия на кнопку с туром
def view_tour (message, dict_calendar, tour, country_button):
    if message.text in dict_calendar:
        bot.delete_message(message.chat.id, message.message_id)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Главное меню", callback_data="back"))     
        asd = f'{message.text} \n\n'
        for y in range(0, tour):
            asd += '{} |\n| {} | {} \n\n'.format(dict_calendar[message.text][0][y],
                                            dict_calendar[message.text][1][y], 
                                            dict_calendar[message.text][2][y]
                                            )
        msg = bot.send_message(message.chat.id, 
                        formatting.format_text(formatting.mbold(asd)),
                        parse_mode = 'MarkdownV2', 
                        reply_markup = markup)
        bot.register_next_step_handler(msg, view_tour, dict_calendar, tour, country_button)
    elif message.text == 'Назад':
        bot.clear_step_handler_by_chat_id(chat_id = message.chat.id)
        calendar_and_table(message, back = country_button)
    elif message.text == 'Главное меню':
        bot.clear_step_handler_by_chat_id(chat_id = message.chat.id)
        button_country_news(message)
    else:
        msg = bot.send_message(message.chat.id, f'Дорогой, {message.chat.first_name}. ✅Выбери тур!\n\n\
    ✅Или нажми назад, чтобы выбрать чемпионат\n\
    ✅Или нажми главное меню, чтобы выбрать другую категорию\n ')
        bot.register_next_step_handler(msg, view_tour, dict_calendar, tour, country_button)

#получаем новости из чемпионата        
def get_news(message,ref_dict):
    if message.text in ref_dict :
        axzc = ref_dict.get(message.text)
        list_photo_text = get_one_news(axzc)
        if len(list_photo_text[1]) >= 1024:
            num_symb =list_photo_text[1][:1024].rfind('.') + 1
            bot.send_photo(message.chat.id, 
                list_photo_text[0],
                caption=list_photo_text[1][:num_symb])
            for x in range(num_symb, len(list_photo_text[1]), 1024):
                msg = bot.send_message(message.chat.id, list_photo_text[1][x:x+1024])
        else:
            msg = bot.send_photo(message.chat.id, 
                list_photo_text[0],
                caption=list_photo_text[1],
            )
        bot.register_next_step_handler(msg, get_news,ref_dict)
    elif message.text == 'Назад':
        bot.clear_step_handler_by_chat_id(chat_id = message.chat.id)
        button_country_news(message)

#получение ссылки на обрзор из api youtube
def get_dict_review(message, back = ""):
    dict_review = {}
    markup = types.ReplyKeyboardMarkup()
    menu_button(markup)
    back_button(markup)
    try:
        if 'Англия🏴󠁧󠁢󠁥󠁮󠁧󠁿' in [message.text, back] or 'Франция🇫🇷' in [message.text, back]:
            url = f'{mass_review[message.text]}'
            response = sess.get(url)
            tree = html.fromstring(response.text)
            review_list_lxml_href = tree.xpath(review_xpath_href)
            review_list_lxml_title = tree.xpath(review_xpath_title)
            review_list_lxml_date= tree.xpath(review_xpath_date)
            for i in range(len(review_list_lxml_href)):
                review_title = review_list_lxml_title[i].replace('видео обзор матча'," ")
                dict_review[review_title + review_list_lxml_date[i]] = review_list_lxml_href[i]
                button_champ_rev = types.KeyboardButton(review_title + review_list_lxml_date[i])
                markup.add(button_champ_rev)
            msg = bot.send_message(message.chat.id, 'Выбери обзор', reply_markup=markup)
            return bot.register_next_step_handler(msg, get_ref_review, dict_review, message.text)
        elif message.text in mass_review or back in mass_review:
            #dict_review = parse_youtube_ref(mass_review[message.text])
            #dict_review = you_pytube(mass_review[message.text])
            dict_review = bs4_youtube(mass_review[message.text])
            for key in dict_review:
                button_champ_rev = types.KeyboardButton(key)
                markup.add(button_champ_rev)
            msg = bot.send_message(message.chat.id, 'Выбери обзор', reply_markup=markup)
            bot.register_next_step_handler(msg, get_ref_review, dict_review, message.text)
        elif message.text == 'Назад':
            raise Exception(button_country_news(message))
        else:
            raise Exception(table_text(message, back = 'Обзоры⚽'))
    except Exception as step_back:
        step_back

def get_ref_review(message, dict_review, text):
    try:
        if message.text in dict_review and (text == 'Англия🏴󠁧󠁢󠁥󠁮󠁧󠁿' or text == 'Франция🇫🇷'):
            url = f'{dict_review[message.text]}'
            response = sess.get(url)
            tree = html.fromstring(response.text)
            if text == 'Англия🏴󠁧󠁢󠁥󠁮󠁧󠁿':
                review_list_lxml_href = tree.xpath(review_xpath_match_href)
                review_ref = review_list_lxml_href[0][review_list_lxml_href[0].find('https'):len(review_list_lxml_href[0])]
                msg = bot.send_message(message.chat.id, review_ref)
                return bot.register_next_step_handler(msg, get_ref_review,dict_review,text)        
            elif text == 'Франция🇫🇷':
                review_list_lxml_href = tree.xpath(review_xpath_match_France_href)
                if len(review_list_lxml_href) == 0:
                    review_list_lxml_href = tree.xpath(review_xpath_match_href)
                    review_ref = review_list_lxml_href[0][review_list_lxml_href[0].find('https'):len(review_list_lxml_href[0])] 
                    msg = bot.send_message(message.chat.id, review_ref)
                    return bot.register_next_step_handler(msg, get_ref_review,dict_review,text)
                review_ref = review_list_lxml_href[0][review_list_lxml_href[0].find('https'):review_list_lxml_href[0].find(',')-1]
                msg = bot.send_message(message.chat.id, review_ref)
                return bot.register_next_step_handler(msg, get_ref_review, dict_review, text)
        elif message.text == 'Главное меню':
            raise Exception(button_country_news(message))
        elif message.text == 'Назад':
            raise Exception(table_text(message, back = 'Обзоры⚽'))
        elif text in mass_review:
            msg = bot.send_message(message.chat.id, dict_review[message.text])
            return bot.register_next_step_handler(msg, get_ref_review, dict_review, text)
        else:
            msg = bot.send_message(message.chat.id,'Выбери обзор')
            bot.register_next_step_handler(msg, get_ref_review, dict_review, text)
    except Exception as main_menu_or_step_back:
        main_menu_or_step_back

if __name__ == '__main__':
    while True:
        try:#добавляем try для бесперебойной работы
            #bot.polling(none_stop=True)#запуск бота
            bot.infinity_polling()
        except:
            time.sleep(10)#в случае падения