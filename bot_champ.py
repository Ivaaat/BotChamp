import telebot
from telebot import types, formatting
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
import logging
from datetime import datetime
from config import mass_contry
from config import list_name_site, db
from championat import add_db, get_tab, get_logo, get_cal, parent_word
from world_champ import WorldCup, world_playoff
from config import TOKEN, user_id, channel_link
from config import channel_id
from user_mongo import add_user, view_users, get_push
from user_mongo import set_push, get_user, get_list_user
import news_football 
import youtube_parse 
from live import tomorrow
import flask
import socket

WEBHOOK_HOST = socket.gethostbyname(socket.gethostname())
WEBHOOK_PORT = 8443  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = '0.0.0.0'

WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (TOKEN)

app = flask.Flask(__name__)


# Empty webserver index, return nothing, just http 200
@app.route('/', methods=['GET', 'HEAD'])
def index():
    return ''


# Process webhook calls
@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)
bot = telebot.TeleBot(TOKEN,skip_pending=True)  # Токен
bot.set_my_commands(
    commands=[
        telebot.types.BotCommand("start", "start_parse"),
    ],
)


# создание клавиатуры с название чемпионатов
def champ_keyboard():
    markup = types.ReplyKeyboardMarkup()
    back_button(markup)
    for key in mass_contry:
        button = types.KeyboardButton(key)
        markup.add(button)
    return markup


# создание кнопки назад
def back_button(markup):
    button_back = types.KeyboardButton('Назад')
    return markup.add(button_back)


# создание кнопки меню
def menu_button(markup):
    button_menu = types.KeyboardButton('Главное меню')
    return markup.add(button_menu)


def user_verif(message):
#     text = f"Чтобы получить доступ к боту подпишись \
# на канал:\n {channel_link} и нажми /start"
#     try:
#         member = bot.get_chat_member(channel_id, message.chat.id)
#         if member.status == 'left':
#             bot.send_message(message.chat.id, text)
#             return False
#     except telebot.apihelper.ApiTelegramException:
#         bot.send_message(message.chat.id, text)
#         return False
    if not get_user(message.chat.id):
        add_user(f'{message.chat.first_name} {message.chat.username}',
                 message.chat.id, push=False)
        bot.send_message(user_id,
                         "Новый пользователь {} {} {}".format(
                                                    message.chat.id,
                                                    message.chat.first_name,
                                                    message.chat.username))
    return True


# СТАРТУЕМ ОТСЮДА
#@bot.message_handler(content_types='text')
@bot.message_handler(func=lambda message: True, content_types=['text'])
def button_country_news(message):
    if not user_verif(message):
        return
    markup = types.ReplyKeyboardMarkup()
    button_country = types.KeyboardButton('Чемпионаты🏆')
    button_news = types.KeyboardButton('Новости📰')
    button_review = types.KeyboardButton('Обзоры⚽')
    button_live = types.KeyboardButton('Ближайшие матчи')
    markup.add(button_country, button_news)
    markup.add(button_review, button_live)
    if get_push(message.chat.id):
        ne = 'не'
    else:
        ne = ""
    msg = bot.send_message(message.chat.id,
                           f'{message.chat.first_name}! aka \
{message.chat.username}\n\n\
                     ⚽ Тебя приветствует @{bot.user.username} ⚽\n\n\
        Здесь можно узнать самое главное о топ чемпионатаx!\n\n\
                Хочешь узнать результаты команд?\n\
                ✅Жми - Чемпионаты🏆\n\n\
                Хочешь узнать последние новости футбольного мира?\n\
                ✅Жми -  Новости📰\n\n\
                Хочешь посмотреть видеообзоры футбольных матчей?\n\
                ✅Жми -  Обзоры⚽\n\n\n\
                ✅Жми /push и тебе {ne} будут приходить уведомления о новостях!\
\n\n\n✅Выбирай!',
                           reply_markup=markup)

    bot.delete_my_commands()
    bot.set_my_commands(commands=[
        telebot.types.BotCommand("push", f"{ne} push notifications")])
    bot.register_next_step_handler(msg, table_text)


# обработка inline-кнопки главное меню
@bot.callback_query_handler(func=lambda call: call.data == 'back')
def callback_query(call):
    bot.answer_callback_query(call.id, "Главное меню")
    bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
    button_country_news(call.message)


# Создаем три кнопки "Чемпионаты🏆" и "Новости📰  'Обзоры⚽' после вызова старта"
def table_text(message, back=""):
    markup = types.ReplyKeyboardMarkup()
    if message.text == '/push':
        if get_push(message.chat.id) is False:
            set_push(message.chat.id, True)
            bot.send_message(message.chat.id, 'Жди уведомлений!')
        else:
            set_push(message.chat.id, False)
            bot.send_message(message.chat.id, 'Уведомлений не будет!')
        button_country_news(message)
    elif 'Чемпионаты🏆' in [message.text, back]:
        msg = bot.send_message(message.chat.id, 'Выбери чемпионат',
                               reply_markup=champ_keyboard())
        bot.register_next_step_handler(msg, calendar_and_table)
    elif 'Новости📰' in [message.text, back]:
        back_button(markup)
        news_coll = db['news']
        dict_news = {}
        for news in news_coll.find().limit(50).sort('date',-1):
            date = news['date'].strftime("%H:%M")
            title = '{} {}'.format(date, news['title']) 
            markup.add(types.KeyboardButton(title))
            dict_news[title] = [news['logo'], news['text']]
        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
        msg = bot.send_message(message.chat.id,
                               'Новости', reply_markup=markup)
        bot.register_next_step_handler(msg, get_news, dict_news)
    elif 'Обзоры⚽' in [message.text, back]:
        back_button(markup)
        for key in list_name_site:
            if message.chat.id != user_id and (
                                key == 'Чемпионат НН 22-23. \
                                Городская лига' or key.startswith('Кубок')):
                continue
            button_champ_rev = types.KeyboardButton(key)
            markup.add(button_champ_rev)
        msg = bot.send_message(message.chat.id, 'Выбери чемпионат',
                               reply_markup=markup)
        bot.register_next_step_handler(msg, get_dict_review)
    elif message.text == "update" and user_id == message.chat.id:
        for name in mass_contry.values():
            add_db(name, '2022/2023')
            bot.send_message(message.chat.id, f'Обновил {name}')
            time.sleep(5)
        bot.send_message(message.chat.id, 'Обновил таблицы')
        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
        button_country_news(message)
    elif 'Ближайшие матчи' in [message.text, back]:
        back_button(markup)
        #markup.add(types.KeyboardButton('Live'))
        buttons = ['Live','Вчера', 'Сегодня', 'Завтра']
        markup.add(buttons[0])
        markup.add(*[x for x in buttons[1:]])
        msg = bot.send_message(message.chat.id, 'Матчи',
                               reply_markup=markup)
        bot.register_next_step_handler(msg, button_days, buttons)
    elif message.text == 'users' and user_id == message.chat.id:
        bot.send_message(user_id, view_users())
    elif message.text == 'send' and user_id == message.chat.id:
        user_list = get_list_user()
        for id in user_list:
            bot.send_message(id, "Вышло обновление. Жми /start")
    else:
        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
        button_country_news(message)


def button_days(message, buttons):
    #bot.delete_message(message.chat.id,message_id= message.message_id)
    if message.text in buttons:
        markup = types.ReplyKeyboardMarkup()
        back_button(markup)
        matches = tomorrow(message.text)
        if matches is None:
            msg = bot.send_message(message.chat.id, 'Нет матчей')
            return bot.register_next_step_handler(msg, button_days, buttons)
        for match in matches:
            markup.add(types.KeyboardButton(match))
        msg = bot.send_message(message.chat.id, message.text,
                                reply_markup=markup)
        bot.register_next_step_handler(msg, match_res)
    else:
        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
        button_country_news(message)
    

def match_res(message):
    table_text(message,back='Ближайшие матчи')


# Создаем две кнопки "Календарь" и "Таблица "
def calendar_and_table(message, back=""):
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
            msg = bot.send_message(message.chat.id, message.text,
                                   reply_markup=markup)
            bot.register_next_step_handler(msg, get_def, message.text)
        elif message.text == 'Назад':
            button_country_news(message)
        else:
            raise KeyError
    except Exception:
        table_text(message, back='Чемпионаты🏆')


# Нажатие кнопок обозначенных выше
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
        msg = bot.send_message(message.chat.id,
                               f'{message.chat.first_name}!✅Выбери!\n\n\
                                  🔙Назад\n\n\
            🗓Календарь          📊Таблица\
            ')
        bot.register_next_step_handler(msg, get_def, text)


# Создание таблицы с командами
def create_table(message, country_button):
    # Создаю массив с командами из парсинга
    if country_button == 'Чемпионат мира🌍':
        bot.send_message(message.chat.id,
                         f'{country_button}. Плей-офф! \n\n{world_playoff()}')
        return calendar_and_table(message, back=country_button)
    else:
        mass = get_tab(mass_contry[country_button])
        markup = types.ReplyKeyboardMarkup()
        menu_button(markup)
        back_button(markup)
        j = 1
        for name_team, stat in mass.items():
            button = types.KeyboardButton(
                                    "{}. | {} |  И: {}  О: {}  M: {}".format(
                                        j,
                                        name_team,
                                        stat[0],
                                        stat[1],
                                        stat[2]
                                        )
                                    )
            markup.add(button)
            j += 1
        msg = bot.send_message(message.chat.id,
                               f'{country_button}.Таблица чемпионата!\n\
    Выбери команду, чтобы узнать последние результаты',
                               reply_markup=markup
                               )
        bot.register_next_step_handler(msg, result_team, mass, country_button)


# Нажатие на кнопку с названием команды
def result_team(message, dict_team, country_button):
    try:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Главное меню", callback_data="back"))
        try:
            text = message.text.split("|")[1].strip()
        except IndexError:
            text = message.text
        if text in dict_team:
            list_date = []
            for date in dict_team[text][3]:
                true_date = datetime.strptime(date.split("|")[0].split()[0],
                                      '%d-%m-%Y').strftime('%d %B')
                list_date.append(
                    formatting.mbold('{} {} | {} | {}\
                                     '.format(true_date,
                                              date.split("|")[0],
                                              date.split('|')[1],
                                              date.split('|')[2]),escape=True))
            bot.delete_message(message.chat.id, message.message_id)
            msg = bot.send_photo(message.chat.id,
                                 get_logo(mass_contry[country_button], text),
                                 caption='\n\n'.join(list_date),
                                 reply_markup=markup,
                                 parse_mode="MarkdownV2"
                                 )
            bot.register_next_step_handler(msg, result_team, dict_team,
                                           country_button)
        elif message.text == 'Главное меню':
            button_country_news(message)
        elif message.text == 'Назад':
            calendar_and_table(message, back=country_button)
        else:
            raise KeyError
    except Exception:
        msg = bot.send_message(message.chat.id,
                               f'Дорогой, {message.chat.first_name}. \
✅Выбери команду!\n\n\
    ✅Или нажми назад, чтобы выбрать чемпионат\n\
    ✅Или нажми главное меню, чтобы выбрать другую категорию')
        bot.register_next_step_handler(msg, result_team, dict_team,
                                       country_button)


# Создание календаря
def create_calendar(message, country_button):
    if country_button == "Чемпионат мира🌍":
        worldcup = WorldCup(mass_contry[country_button])
        bot.send_message(message.chat.id, worldcup.worldcup_calendar())
        return calendar_and_table(message, back=country_button)
    elif country_button in mass_contry:
        dict_calendar = get_cal(mass_contry[country_button], '2022/2023')
        markup = types.ReplyKeyboardMarkup()
        menu_button(markup)
        back_button(markup)
        for key in dict_calendar:
            start = datetime.strptime(
                str(dict_calendar[key]['start']).split()[0],
                '%Y-%m-%d').strftime('%d %B')
            #print(date_start + '\n')
            #start = parent_word(date_start)
            #print(start)
            end = datetime.strptime(
                str(dict_calendar[key]['end']).split()[0],
                '%Y-%m-%d').strftime('%d %B')
            #end = parent_word(date_end)
            the_end = ""
            if dict_calendar[key]['Закончен']:
                the_end = 'Закончен'
            button = types.KeyboardButton(('{} | {} - {} | {}').format(
                key, start, end, the_end))
            markup.add(button)
        msg = bot.send_message(message.chat.id,
                               f'{country_button} Выбери тур, \
чтобы узнать результаты:',
                               reply_markup=markup
                               )
        bot.register_next_step_handler(msg, view_tour, dict_calendar,
                                       country_button)
    else:
        msg = bot.send_message(message.chat.id, 'Выбери чемпионат:[eq')
        bot.register_next_step_handler(msg, create_calendar)


# Обработка нажатия на кнопку с туром
def view_tour(message, dict_calendar, country_button):
    try:
        text = message.text.split("|")[0].strip()
        if text in dict_calendar:
            bot.delete_message(message.chat.id, message.message_id)
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Главное меню",
                                            callback_data="back"))
            list_date = []
            for date in dict_calendar[text]['Матчи']:
                true_date = formatting.mitalic(
                    datetime.strptime(date.split("|")[0].split()[0],
                                      '%d-%m-%Y').strftime('%d %B'),escape=True)
                if true_date not in list_date:
                    list_date.append(true_date)
                list_date.append(formatting.mbold('{} | {} | {}'.format(
                    date.split("|")[0].split()[1],
                    date.split('|')[1],
                    date.split('|')[2]),escape=True))
            text = formatting.mbold(message.text, escape=True)
            msg = bot.send_message(message.chat.id,
                                   f"{text}\n\n" +
                                   '\n\n'.join(list_date),
                                   reply_markup=markup,
                                   parse_mode='MarkdownV2')
            bot.register_next_step_handler(msg, view_tour, dict_calendar,
                                           country_button)
        elif message.text == 'Назад':
            bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
            calendar_and_table(message, back=country_button)
        elif message.text == 'Главное меню':
            bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
            button_country_news(message)
        else:
            raise KeyError
    except Exception:
        msg = bot.send_message(message.chat.id,
                               f'Дорогой, {message.chat.first_name}. \
✅Выбери тур!\n\n\
    ✅Или нажми назад, чтобы выбрать чемпионат\n\
    ✅Или нажми главное меню, чтобы выбрать другую категорию\n ')
        bot.register_next_step_handler(msg, view_tour, dict_calendar,
                                       country_button)


# получаем новости из чемпионата
def get_news(message, ref_dict):
    try:
        if message.text in ref_dict:
            logo = ref_dict[message.text][0]
            text = ref_dict[message.text][1]
            if len(text) >= 1024:
                num_symb = text[:1024].rfind('.') + 1
                bot.send_photo(message.chat.id,
                               logo,
                               caption=text[:num_symb])
                for x in range(num_symb, len(text), 1024):
                    msg = bot.send_message(message.chat.id,
                                           text[x:x+1024])
            else:
                msg = bot.send_photo(message.chat.id,
                                     logo,
                                     caption=text,
                                     )
            bot.register_next_step_handler(msg, get_news, ref_dict)
        elif message.text == 'Назад':
            bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
            button_country_news(message)
        else:
            raise KeyError
    except Exception:
        table_text(message, back='Новости📰')


# получение ссылки на обрзор из api youtube
def get_dict_review(message, back=""):
    dict_review = {}
    markup = types.ReplyKeyboardMarkup()
    menu_button(markup)
    back_button(markup)
    video_coll = db['video']
    if message.text == list_name_site[0]:
        query = None
    else:
        query = {'country': message.text}
    try:
        if message.text in list_name_site or back in list_name_site:
            for key in video_coll.find(query).sort('_id',-1).limit(50):
                button_champ_rev = types.KeyboardButton(key["desc"])
                dict_review[key["desc"]] = key["link"]
                markup.add(button_champ_rev)
            msg = bot.send_message(message.chat.id, 'Выбери обзор',
                                   reply_markup=markup)
            bot.register_next_step_handler(msg, get_ref_review,
                                           dict_review, message.text)
        elif message.text == 'Назад':
            button_country_news(message)
        else:
            raise KeyError
    except Exception:
        table_text(message, back='Обзоры⚽')


def get_ref_review(message, dict_review, text):
    try:
        if message.text in dict_review:
            msg = bot.send_message(message.chat.id,
                                   f"{message.text}\n\
{dict_review[message.text]}")
            return bot.register_next_step_handler(msg, get_ref_review,
                                                  dict_review, text)
        elif message.text == 'Главное меню':
            button_country_news(message)
        elif message.text == 'Назад':
            table_text(message, back='Обзоры⚽')
        else:
            raise KeyError
    except Exception:
        table_text(message, back='Обзоры⚽')


# if __name__ == '__main__':
   # while True:
   #     try:
   #         bot.infinity_polling()
   #     except Exception:
   #         time.sleep(10)


bot.remove_webhook()

time.sleep(0.1)

bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH ,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))

# Start flask server
app.run(host=WEBHOOK_LISTEN,
        port=WEBHOOK_PORT,
        ssl_context=(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV),
        debug=True)
