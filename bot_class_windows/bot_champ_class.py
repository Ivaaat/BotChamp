import requests
from lxml import html
import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
import logging
from telebot import formatting
from news_football_class import news_parse, get_one_news, rss_news
from youtube_parse_class import parse_youtube_ref, you_pytube, bs4_youtube, youtube_video, rutube_video
from xpath_ref_class import *
from constants_class import mass_contry, mass_review, parse_site, dict_youtube, dict_site, list_name_site, dict_matchtv, rss_link
from championat_class import add_db, get_tab, get_logo, get_next_date, get_cal, get_start_end_tour, news_pic
from world_champ import WorldCup, world_playoff
import threading
from config import TOKEN, user_id, User_agent
from MyDataBase import MyBaseDB
from pymongo import MongoClient
import re
#from testd import json_championat
from user_mongo import add_user, view_users, get_push, get_user, get_list_user, set_push, add_field, delete_field, get_live
#from googletrans import Translator
from datetime import datetime, timedelta
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 



client = MongoClient()
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
bot = telebot.TeleBot(TOKEN)#Токен
bot.set_my_commands(
    commands=[
        telebot.types.BotCommand("start", "start_parse"),
    ],
)

bot.send_message(user_id,"Вышло обновление. Жми /start")
@bot.message_handler(regexp='send')
def userlist(message):
    user_list = get_list_user()
    for user_id in user_list:
        bot.send_message(user_id,"Вышло обновление. Жми /start")


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

# def live():
#     old_result = get_live()
#     new_result = {}
#     while True:
#         for id, list_live in old_result.items():
#             new_result[id] = json_championat('push', list_live)
#             for i, match_live in enumerate(list_live):

#                 if old_result[id][i] != match_live:
#                     bot.send_message(id, json_championat('push', match_live))
#threading.Thread(target=live).start()

def parse_for_push(url):
    response = sess.get(url)
    tree = html.fromstring(response.text)
    review_list_lxml_href = tree.xpath(review_xpath_href)
    review_list_lxml_title = tree.xpath(review_xpath_title)
    review_list_lxml_date= tree.xpath(review_xpath_date)
    asd = []
    if len(review_list_lxml_href) == 0:
            review_list_lxml_href = tree_ref.xpath(review_xpath_match_France_href)
    for i, url_ref in enumerate(review_list_lxml_href):
        response_ref = sess.get(url_ref)
        tree_ref = html.fromstring(response_ref.text)
        review_href_list = tree_ref.xpath(review_xpath_match_href)
        if len(review_href_list) == 0:
            review_href_list = tree_ref.xpath(review_xpath_match_France_href)
        review_ref = review_href_list[0][review_href_list[0].find('https'):len(review_href_list[0])]
        asd.append([(review_list_lxml_title[i].replace('видео обзор матча'," | ") + review_list_lxml_date[i]), review_ref])
    return dict(asd)


def news():
    response = sess.get(rss_link)
    _, old_link, _ = rss_news(response)
    while True:
        try:
            timer = 120
            list_user_push_true = [user_id for user_id in get_list_user() if get_push(user_id)]
            if len(list_user_push_true) > 0:
                response = sess.get(rss_link)
                new_news, new_link, logo = rss_news(response)
                #if new_news != old_news:
                if new_link != old_link:
                    pic = news_pic(logo, new_news)
                    inst_view = f'https://t.me/iv?url=https%3A%2F%2F{new_link}&rhash=f610f320a497f8'
                    markup = InlineKeyboardMarkup()
                    markup.add(InlineKeyboardButton(new_news, url=inst_view))
                    old_link = new_link
                    for id in list_user_push_true:
                        bot.send_photo(id,pic,reply_markup = markup)
        except Exception as e:
            bot.send_message(user_id, str('def news\n'))
            time.sleep(timer)
        time.sleep(timer)
threading.Thread(target=news).start()

def video_matchtv():
    old_video_dict = rutube_video()
    while True:
        ### Тут код парсинга
        timer = 1800
        list_user_push_true = [user_id for user_id in get_list_user() if get_push(user_id)]
        try:
            new_video_dict = rutube_video()
            for desc_video, ref in new_video_dict.items():
                if desc_video in old_video_dict:
                    break
                for id in list_user_push_true:
                    bot.send_message(user_id, str(f'Вышел обзор\n'))
                    message = bot.send_message(id, f"{desc_video}\n{ref}")
                    if id < 0:
                        bot.pin_chat_message(id, message.message_id)
                old_video_dict[desc_video] = ref
        except Exception:
            bot.send_message(user_id, str(f'except video_matchtv\n'))
            time.sleep(timer)
        time.sleep(timer)


def video(name="", channel="", query = "highlights"):
    if channel.startswith("@"):
        old_video_dict = youtube_video(channel, query = query )
    elif name == "":
        old_video_dict = rutube_video()
    else:
        old_video_dict = parse_for_push(dict_site[name])
    while True:
        ### Тут код парсинга
        timer = 1800
        list_user_push_true = [user_id for user_id in get_list_user() if get_push(user_id)]
        try:
            if channel.startswith("@"):
                new_video_dict = youtube_video(name, query = query )
            elif name == "":
                new_video_dict = rutube_video()
            else:
                new_video_dict = parse_for_push(dict_site[name])
            for desc_video, ref in new_video_dict.items():
                if desc_video in old_video_dict:
                    break
                for id in list_user_push_true:
                    bot.send_message(user_id, str(f'{name}\nВышел обзор\n'))
                    message = bot.send_message(id, f"{desc_video}\n{ref}")
                    if id < 0:
                        bot.pin_chat_message(id, message.message_id)
                old_video_dict[desc_video] = ref
        except Exception:
            bot.send_message(user_id, str(f'{name}\nexcept parse youtube\n'))
            time.sleep(timer)
        time.sleep(timer)


            
# for name in dict_youtube:
#     #threading.Thread(target=video, args=(name,)).start()
#     threading.Timer(1,video, [name]).start()
# for name in dict_site:
#     threading.Timer(1,video, [name]).start()
# for name in dict_matchtv:
#     threading.Timer(1,video, [name]).start()
# for name in mass_contry.values():
#      threading.Timer(1,video, [name]).start()


threading.Timer(1, video).start()
threading.Timer(1, video, ['spain',"@okkosport", 'ла лига.']).start()
threading.Timer(1, video, ['france',"@Ligue1official"]).start()
# threading.Timer(1, video, ['france']).start()
threading.Timer(1, video, ['england']).start()
#threading.Timer(1, video, ['germany']).start()
#threading.Timer(1, video, ['russiapl']).start()
#threading.Timer(1, video, ['spain']).start()

# def push_live():
#     while True:
#         list_user_push_true = [user_id for user_id in get_list_user() if get_push(user_id, name_field = "123")]
#         if len(list_user_push_true) == 0:
#             continue
#         get_user()
#         if get_push(user_id, name_field = message.text) is str:
#             add_field(message.chat.id, message.text, True)
#         else:
#             if get_push(message.chat.id, name_field = message.text):
#                 bool_push = False
#             else:
#                 bool_push = True
#             set_push(message.chat.id, bool_push)


#         push = json_championat("push", message.text)

# threading.Thread(target=push_live).start()

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
    markup.add(button_country, button_news)
    markup.add(button_review)
    if get_push(message.chat.id):
        ne = 'не'
    else:
        ne = ""
    msg = bot.send_message(message.chat.id, f'{message.chat.first_name}! aka {message.chat.username}\n\n\
                     ⚽ Тебя приветствует @{bot.user.username} ⚽\n\n\
        Здесь можно узнать самое главное о топ чемпионатаx!\n\n\
                Хочешь узнать результаты команд?\n\
                ✅Жми - Чемпионаты🏆\n\n\
                Хочешь узнать последние новости футбольного мира?\n\
                ✅Жми -  Новости📰\n\n\
                Хочешь посмотреть видеообзоры футбольных матчей?\n\
                ✅Жми -  Обзоры⚽\n\n\n\
                ✅Жми /push и тебе {ne} будут приходить уведомления о новостях!\n\n\n✅Выбирай!', reply_markup= markup)
    bot.delete_my_commands()
    bot.set_my_commands(
    commands=[
        telebot.types.BotCommand("push", f"{ne} push notifications")
    ],
)
    bot.register_next_step_handler(msg, table_text)

#обработка inline-кнопки главное меню
@bot.callback_query_handler(func=lambda call: call.data == 'back')
def callback_query(call):
        bot.answer_callback_query(call.id, "Главное меню")
        bot.clear_step_handler_by_chat_id(chat_id = call.message.chat.id)
        button_country_news(call.message)

@bot.callback_query_handler(func=lambda call: call.data == 'Матч ТВ')
def callback_query(call):
        bot.answer_callback_query(call.id, "Главное меню")
        bot.clear_step_handler_by_chat_id(chat_id = call.message.chat.id)
        button_country_news(call.message)

#Создаем три кнопки "Чемпионаты🏆" и "Новости📰  'Обзоры⚽' после вызова старта"
def table_text(message, back = "" ):
    markup = types.ReplyKeyboardMarkup()
    if message.text == '/push':
        if get_push(message.chat.id) == False:
            set_push(message.chat.id, True)
            bot.send_message(message.chat.id,'Жди уведомлений!')
        else:
            set_push(message.chat.id, False)
            bot.send_message(message.chat.id,'Уведомлений не будет!')
        button_country_news(message)
    elif 'Чемпионаты🏆' in [message.text, back]:
        msg = bot.send_message(message.chat.id, 'Выбери чемпионат', reply_markup=champ_keyboard())
        bot.register_next_step_handler(msg, calendar_and_table)
    elif 'Новости📰' in [message.text, back]:
        back_button(markup)
        dict_news = news_parse()
        for news in dict_news:
                    markup.add(types.KeyboardButton(news))
        bot.clear_step_handler_by_chat_id(chat_id = message.chat.id)
        msg = bot.send_message(message.chat.id,
                        'Новости',
                        reply_markup = markup)
        bot.register_next_step_handler(msg, get_news, dict_news)
    elif 'Обзоры⚽' in [message.text, back]:
        back_button(markup)
        for key in mass_review:
            if message.chat.id != user_id and (key == 'Чемпионат НН 22-23. Городская лига' or key.startswith('Кубок')) :
                continue
            button_champ_rev = types.KeyboardButton(key)
            markup.add(button_champ_rev)
        msg = bot.send_message(message.chat.id, 'Выбери чемпионат', reply_markup=markup)
        bot.register_next_step_handler(msg, get_dict_review)
    # elif 'Live' in [message.text, back]:
    #     markup = types.ReplyKeyboardMarkup()
    #     button_today = types.KeyboardButton('Сегодня')
    #     button_live = types.KeyboardButton('Live')
    #     back_button(markup)
    #     markup.add(button_today, button_live)
    #     msg = bot.send_message(message.chat.id, 'Матчи', reply_markup=markup)
    #     bot.register_next_step_handler(msg, today_or_live)
    elif message.text == "update" and user_id == message.chat.id:
        for name in mass_contry.values():
            add_db(name, '2022/2023')
            bot.send_message(message.chat.id, f'Обновил {name}')
            time.sleep(5)
        bot.send_message(message.chat.id, 'Обновил таблицы')
        bot.clear_step_handler_by_chat_id(chat_id = message.chat.id)
        button_country_news(message)
    else:
        bot.clear_step_handler_by_chat_id(chat_id = message.chat.id)
        button_country_news(message)

# def today_or_live(message, back = ""):
#     try:
#         markup = types.ReplyKeyboardMarkup()
#         menu_button(markup)
#         back_button(markup)
#         prop_match = json_championat(message.text)
#         if message.text == 'Назад':
#             return button_country_news(message)
#         elif prop_match == "Нет матчей":
#             button_name = types.KeyboardButton(prop_match)
#             markup.add(button_name)
#         elif message.text in  ['Live', "Сегодня"] or back in ['Live', "Сегодня"]:
#             if message.text not in ['Live', "Сегодня"]:
#                 text = back
#             text = message.text
#             prop_match = json_championat(text)
#             for name_match in prop_match:
#                 button_name = types.KeyboardButton(name_match)
#                 markup.add(button_name)
#         else:
#             raise KeyError
#         msg = bot.send_message(message.chat.id, message.text, reply_markup=markup)
#         bot.register_next_step_handler(msg, property_match)
#     except Exception:
#         table_text(message, back = 'Live')

# def property_match(message):
#     try:
#         if message.text == 'Главное меню':
#             button_country_news(message)
#         elif message.text == 'Назад':
#             table_text(message, back = 'Live')
#         else:
#             push = json_championat("push", message.text)
#             if type(push) == bool:
#                 bot.send_message(message.chat.id, "Матч не Live")
#                 return table_text(message, back = 'Live')
#             if get_push(message.chat.id, name_field = message.text) == "":
#                 add_field(message.chat.id, message.text, True)
#                 bot.send_message(message.chat.id, "Ты подписался на матч\n" + message.text)
#             else:
#                 delete_field(message.chat.id, message.text)
#                 bot.send_message(message.chat.id, "Ты отписался от матча\n" + message.text)
                # if get_push(message.chat.id, name_field = message.text):
                #     bool_push = False
                # else:
                #     bool_push = True
                # set_push(message.chat.id, bool_push)

            #msg = bot.send_message(message.chat.id, "КФ", reply_markup= markup)
            #bot.register_next_step_handler(msg, table_text, 'Live')
    #         today_or_live(message, back = "Live")
    # except Exception:
    #     table_text(message, back = 'Live')


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
            button_country_news(message)
        else:
            raise KeyError
    except Exception:
        table_text(message, back='Чемпионаты🏆')



#Нажатие кнопок обозначенных выше
def get_def(message, text):
    try:
        if message.text == 'Календарь🗓':
            create_calendar(message, text)
        elif message.text == 'Таблица⚽':
            create_table(message, text)
        elif message.text == 'Назад':
            table_text(message, back='Чемпионаты🏆')
        else:
             raise KeyError
    except Exception:
        msg = bot.send_message(message.chat.id, f'{message.chat.first_name}!✅Выбери!\n\n\
                                  🔙Назад\n\n\
            🗓Календарь          📊Таблица\
            ')
        bot.register_next_step_handler(msg, get_def, text)


#Создание таблицы с командами
def create_table(message, country_button):
    #Создаю массив с командами из парсинга
    if country_button == 'Чемпионат мира🌍':
        bot.send_message(message.chat.id, f'{country_button}. Плей-офф! \n\n{world_playoff()}')
        return calendar_and_table(message, back = country_button)
    else:
        mass = get_tab(mass_contry[country_button])
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
            bot.delete_message(message.chat.id, message.message_id)
            msg = bot.send_photo(message.chat.id,
                get_logo(mass_contry[country_button], text),
                caption = formatting.mbold('\n\n'.join(dict_team[text]['Последние результаты\n'])),
                parse_mode='MarkdownV2',
                reply_markup = markup
                )
            bot.register_next_step_handler(msg, result_team, dict_team, country_button)
        elif message.text == 'Главное меню':
            button_country_news(message)
        elif message.text == 'Назад':
            calendar_and_table(message, back = country_button)
        else:
            raise KeyError("Выбери команду:")
    except Exception as e:
        msg = bot.send_message(message.chat.id, e)
        bot.register_next_step_handler(msg, result_team, dict_team, country_button)

#Создание календаря
def create_calendar(message, country_button):
    if country_button == "Чемпионат мира🌍":
        worldcup = WorldCup(mass_contry[country_button])
        bot.send_message(message.chat.id, worldcup.worldcup_calendar())
        return calendar_and_table(message, back = country_button)
    elif country_button in mass_contry:
        country = mass_contry.get(country_button)
        dict_calendar = get_cal(country,'2022/2023')
        markup = types.ReplyKeyboardMarkup()
        menu_button(markup)
        back_button(markup)
        for key in dict_calendar:
            start = str(dict_calendar[key]['start'])
            end = str(dict_calendar[key]['end'])
            the_end =""
            if dict_calendar[key]['Закончен']:
                the_end = '| Закончен'
            button = types.KeyboardButton(('{} | {} - {} {}').format(key, start[:10], end[:10], the_end))
            markup.add(button)
        msg = bot.send_message(message.chat.id,
                            f'{country_button} Выбери тур, чтобы узнать результаты:',
                            reply_markup=markup
                            )
        bot.register_next_step_handler(msg, view_tour, dict_calendar, country_button)
    else:
        msg = bot.send_message(message.chat.id, 'Выбери чемпионат:[eq')
        bot.register_next_step_handler(msg, create_calendar)

#Обработка нажатия на кнопку с туром
def view_tour (message, dict_calendar, country_button):
    try:
        text = message.text[:6].strip()
        if text in dict_calendar:
            start = str(dict_calendar[text]['start'])
            end = str(dict_calendar[text]['end'])
            bot.delete_message(message.chat.id, message.message_id)
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Главное меню", callback_data="back"))
            #markup.add(InlineKeyboardButton("Матч ТВ", url = 'https://www.youtube.com/@MatchTV/videos'))
            asd = f'{text} | {start} - {end} | \n\n' + '\n\n'.join(dict_calendar[text]['Матчи'])
            msg = bot.send_message(message.chat.id,
                            formatting.format_text(formatting.mbold(asd)),
                            parse_mode = 'MarkdownV2',
                            reply_markup = markup)
            bot.register_next_step_handler(msg, view_tour, dict_calendar, country_button)
        elif message.text == 'Назад':
            bot.clear_step_handler_by_chat_id(chat_id = message.chat.id)
            calendar_and_table(message, back = country_button)
        elif message.text == 'Главное меню':
            bot.clear_step_handler_by_chat_id(chat_id = message.chat.id)
            button_country_news(message)
        else:
            raise KeyError
    except Exception:
        msg = bot.send_message(message.chat.id, f'Дорогой, {message.chat.first_name}. ✅Выбери тур!\n\n\
    ✅Или нажми назад, чтобы выбрать чемпионат\n\
    ✅Или нажми главное меню, чтобы выбрать другую категорию\n ')
        bot.register_next_step_handler(msg, view_tour, dict_calendar, country_button)

#получаем новости из чемпионата
def get_news(message, ref_dict):
    try:
        if message.text in ref_dict :
            axzc = ref_dict.get(message.text)
            list_photo_text = get_one_news(axzc, message.text[5:])
            #pic = news_pic(list_photo_text[0], message.text)
            if len(list_photo_text[1]) >= 1024:
                num_symb =list_photo_text[1][:1024].rfind('.') + 1
                bot.send_photo(message.chat.id,
                    #pic,
                    list_photo_text[0],
                    caption=list_photo_text[1][:num_symb])
                for x in range(num_symb, len(list_photo_text[1]), 1024):
                    msg = bot.send_message(message.chat.id, list_photo_text[1][x:x+1024])
            else:
                msg = bot.send_photo(message.chat.id,
                    list_photo_text[0],#pic,#list_photo_text[0],
                    caption=list_photo_text[1],
                )
            bot.register_next_step_handler(msg, get_news,ref_dict)
        elif message.text == 'Назад':
            bot.clear_step_handler_by_chat_id(chat_id = message.chat.id)
            button_country_news(message)
        else:
            raise KeyError
    except Exception:
         table_text(message, back = 'Новости📰')


#получение ссылки на обрзор из api youtube
def get_dict_review(message, back = ""):
    dict_review = {}
    markup = types.ReplyKeyboardMarkup()
    menu_button(markup)
    back_button(markup)
    try:
        #if 'Англия🏴󠁧󠁢󠁥󠁮󠁧󠁿' in [message.text, back] or 'Франция🇫🇷' in [message.text, back] or:
        if message.text in list_name_site or back in list_name_site:
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
            button_country_news(message)
        else:
            raise KeyError
    except Exception:
        table_text(message, back = 'Обзоры⚽')


def get_ref_review(message, dict_review, text):
    try:
        if message.text in dict_review and text in list_name_site:
            url = f'{dict_review[message.text]}'
            response = sess.get(url)
            tree = html.fromstring(response.text)
            review_list_lxml_href = tree.xpath(review_xpath_match_href)
            if len(review_list_lxml_href) == 0:
                review_list_lxml_href = tree.xpath(review_xpath_match_France_href)
            review_ref = review_list_lxml_href[0][review_list_lxml_href[0].find('https'):len(review_list_lxml_href[0])]
            msg = bot.send_message(message.chat.id, f"{message.text}\n{review_ref}")
            return bot.register_next_step_handler(msg, get_ref_review,dict_review,text)
        elif message.text in dict_review and text in mass_review:
            msg = bot.send_message(message.chat.id, dict_review[message.text])
            return bot.register_next_step_handler(msg, get_ref_review, dict_review, text)
        elif message.text == 'Главное меню':
            button_country_news(message)
        elif message.text == 'Назад':
            table_text(message, back = 'Обзоры⚽')
        else:
            raise KeyError
    except Exception:
        table_text(message, back = 'Обзоры⚽')

if __name__ == '__main__':
    while True:
        try:#добавляем try для бесперебойной работы
            #bot.polling(none_stop=True)#запуск бота
            bot.infinity_polling()
        except:
            time.sleep(10)#в случае падения