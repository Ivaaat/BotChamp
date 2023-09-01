from abc import ABC, abstractmethod
from telebot import types, formatting
import config
from datetime import datetime
import locale
import sys
import live
import news 
import video 
import time
import config
import matches
import threading
import telebot
import query_mongo


bot = telebot.TeleBot(config.TOKEN)
db = config.db
news_coll = db['news']
date_coll = db["date"]
champ_coll = db["champ"]
matches_coll = db["matches"]
teams_coll = db["teams"]
users = db['users']
videos_coll = db['videos']


def set_russian_locale():
    try:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'Russian_Russia')
        except locale.Error:
            print('Не удалось установить русскую локаль', file=sys.stderr)


class UserState:
    def __init__(self, user_id):
        self.user_id = user_id

    def get_state(self):
        user = users.find_one({'user_id': self.user_id})
        if user:
            return user['state']
        else:
            return None

    def set_state(self, state):
        users.update_one({'user_id': self.user_id}, {'$set': {'state': state}}, upsert=True)

    def get_history(self):
        user = users.find_one({'user_id': self.user_id})
        if user:
            return user['history']
        else:
            return []

    def push_history(self, state):
        users.update_one({'user_id': self.user_id}, {'$addToSet': {'history': state}}, upsert=True)

    def pop_history(self):
        history = self.get_history()
        if history:
            users.update_one({'user_id': self.user_id}, {'$pop': {'history': 1}})
            return history[-1]
        else:
            return None
    
    def clear_history(self):
        users.update_one({'user_id': self.user_id}, {'$set': {'history': []}})


class MenuItem(ABC):
    def __init__(self, chat_id, user_state):
        self.chat_id = chat_id
        self.user_state = user_state
        self.items = []
        self.width = 1
    
    def add_item(self, item):
        self.items.append(item)

    def send(self, message):
        markup = types.ReplyKeyboardMarkup(row_width=self.width)
        markup.add(*self.items)
        bot.send_message(message.chat.id, message.text, reply_markup=markup)
        i = 0
        while True:
            i += 1
            try:
                bot.delete_message(message.chat.id, message.message_id - i)
            except:
                break

    @abstractmethod
    def execute(self, message):
        pass
   
class MainMenuItem(MenuItem):
    def execute(self, message):
        self.user_state.clear_history()
        self.width = 2
        self.user_state.set_state('Главное меню')
        self.items.extend([
                        'Чемпионаты🏆', 
                        'Новости📰',
                        'Обзоры⚽',
                        'Ближайшие матчи'
                        ])
        self.send(message)

class ChampionshipsMenuItem(MenuItem):
    def execute(self, message):
        self.user_state.push_history('Главное меню')
        self.user_state.set_state('Чемпионаты🏆')
        self.items.extend([
                        'Назад', 
                        'Германия - Бундеслига 🇩🇪',
                        'Англия - Премьер-лига 🏴󠁧󠁢󠁥󠁮󠁧󠁿',
                        'МИР Российская Премьер-лига 🇷🇺',
                        'Испания - Примера 🇪🇸',
                        'Франция - Лига 1 🇫🇷',])
        self.send(message)

class CountryMenuItem(MenuItem):
    def execute(self, message):
        self.user_state.push_history('Чемпионаты🏆')
        self.user_state.set_state(message.text)
        self.items.extend([
                        'Главное меню',
                        'Назад',
                        'Таблица',
                        'Календарь',   ])
        self.send(message)

class TableMenuItem(MenuItem):
    def execute(self, message):
        prev_state = self.user_state.get_state()
        self.user_state.push_history(prev_state)
        self.user_state.set_state(message.text)
        self.add_item('Главное меню')
        self.add_item('Назад')
        self.id_champ = config.season_now[prev_state]
        table = champ_coll.aggregate(query_mongo.champ_pipl(self.id_champ))
        for j, stat in enumerate(table, 1):
            button = "{}. | {} |  И: {}  О: {}  M: {}-{}".format(
                        j,
                        stat['_id'],
                        stat['gamesPlayed'],
                        stat['points'],
                        stat['goalsScored'],
                        stat['goalsConceded']
                        )
                                    
            self.add_item(button)
        self.send(message)

class CalendarMenuItem(MenuItem):
    def execute(self, message):
        prev_state = self.user_state.get_state()
        self.user_state.push_history(prev_state)
        self.user_state.set_state(message.text)
        self.add_item('Главное меню')
        self.add_item('Назад')
        self.id_champ = config.season_now[prev_state]
        dates = champ_coll.aggregate(query_mongo.calendar_pipl(self.id_champ))
        for start_end_tour in dates:
            start = datetime.strptime(start_end_tour['one'],'%Y-%m-%d').strftime('%d %B')
            end = datetime.strptime(start_end_tour['end'],'%Y-%m-%d').strftime('%d %B')
            tour_button = ('{} | {} - {} | {}'.format(
                                                    '{}-й тур'.format(
                                                    start_end_tour['_id']),
                                                    start,
                                                    end,
                                                    ('Закончен' 
                                                    if start_end_tour['status'] == 'fin' 
                                                    else "")
                                                    )
                                                    )
            self.add_item(tour_button.strip())
        self.send(message)

class TourMenuItem(MenuItem):
    def execute(self, message):
        name_champ = self.user_state.get_history()[-1]
        self.add_item('Главное меню')
        self.add_item('Назад')
        tour = message.text.split("-")[0].strip()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Главное меню",
                                        callback_data="back"))
        list_date = []
        self.id_champ = config.season_now[name_champ]
        for match_tour in champ_coll.aggregate(query_mongo.tour_pipl(self.id_champ, int(tour))):
            for match in match_tour['matches']:
                true_date = datetime.strptime(match['date'],'%Y-%m-%d').strftime('%d %B')
                true_date_italic = formatting.mitalic(true_date,escape=True)
                if true_date_italic not in list_date:
                    list_date.append(true_date_italic)
                list_date.append(formatting.mbold('{} | {} | {}'.format(
                                                match['time'],
                                                match['title'].split(',')[0],
                                                match['score']), escape=True))
        text = formatting.mbold(message.text, escape=True)
        bot.send_message(message.chat.id,
                            f"{text}\n\n" +
                            '\n\n'.join(list_date),
                            parse_mode='MarkdownV2')

class TeamMenuItem(MenuItem):
    def execute(self, message):
        name_champ = self.user_state.get_history()[-1]
        self.id_champ = config.season_now[name_champ]
        list_date = []
        name_team = message.text.split("|")[1].strip()
        for match in champ_coll.aggregate(query_mongo.name_team_pipl(self.id_champ,name_team)):
            true_date = datetime.strptime(match['date'],
                                '%Y-%m-%d').strftime('%d %B')
            try:
                result = match['score']['direct']['main']
            except KeyError:
                result = ""
            list_date.append(
                formatting.mbold('{}  | {} - {} | {}\
                                '.format(true_date,
                                        match['home_team'],
                                        match['away_team'],
                                        result,
                                        escape=True)))
        logo = list(champ_coll.aggregate(query_mongo.img_pipl(self.id_champ,name_team)))
        bot.send_photo(message.chat.id,
                        logo[0]['home_team']['img'].replace('60x60', '400x400'),
                        caption='\n\n'.join(list_date),
                        parse_mode="MarkdownV2"
                        )

class ReviewMenuItem(MenuItem):
    def execute(self, message):
        self.user_state.push_history('Главное меню')
        self.user_state.set_state('Обзоры⚽')
        self.add_item('Назад')
        for championship, class_item in menu_items.items():
            if class_item is ReviewChampionatMenuItem:
                self.add_item(championship)
        self.send(message)

class ReviewChampionatMenuItem(MenuItem):
    def execute(self, message):
        prev_state = self.user_state.get_state()
        self.user_state.push_history(prev_state)
        self.user_state.set_state(message.text)
        self.add_item('Главное меню')
        self.add_item('Назад')
        if message.text == 'Последние добавленные':
            query = {}
        else:
            query = {'champ':message.text}
        for key in videos_coll.find(query).sort('date',-1).limit(50):
            self.add_item(key["title"])
        self.send(message)

class ReviewVideoItem(MenuItem):
    def execute(self, message):
        self.add_item('Главное меню')
        self.add_item('Назад')
        video_ref = videos_coll.find_one({'title':message.text})
        bot.send_message(message.chat.id,
                            "{}\n{}".format(message.text,
                            video_ref['link']))

class NewsMenuItem(MenuItem):
    def execute(self, message):
        self.user_state.push_history('Главное меню')
        self.user_state.set_state('Новости📰')
        self.add_item('Назад')
        for news_doc in news_coll.find().limit(50).sort('date', -1):
            title = '{} {}'.format(news_doc['date'].split()[1], news_doc['title']) 
            self.add_item(title)
        self.send(message)

class NewsOneMenuItem(MenuItem):
    def execute(self, message):
        news_doc = news_coll.find_one({'title':message.text.split(' ', 1)[1]})
        text = news_doc['text']
        if len(text) >= 1024:
            num_symb = text[:1024].rfind('.') + 1
            bot.send_photo(message.chat.id,
                            news_doc['logo'],
                            caption=text[:num_symb])
            for x in range(num_symb, len(text), 1024):
                bot.send_message(message.chat.id,
                                    text[x:x+1024])
        else:
            bot.send_photo(message.chat.id, 
                                news_doc['logo'],
                                caption=text,
                                )

class UpcomingMenuItem(MenuItem):
    def execute(self, message):
        self.user_state.push_history('Главное меню')
        self.user_state.set_state('Ближайшие матчи')
        self.add_item('Назад')
        for day, class_item in menu_items.items():
            if class_item is UpcomingDayMenuItem:
                if len(live.upcoming_match(day)) == 0:
                    continue
                self.add_item(day)
        self.send(message)

class UpcomingDayMenuItem(MenuItem):
    def execute(self, message):
        prev_state = self.user_state.get_state()
        self.user_state.push_history(prev_state)
        self.user_state.set_state(message.text)
        self.add_item('Главное меню')
        self.add_item('Назад')
        matches = live.upcoming_match(message.text)
        for match in matches:
            self.add_item(match)
        self.send(message)

class BackMenuItem(MenuItem):
    def execute(self, message):
        prev_state = self.user_state.pop_history()
        if prev_state:
            menu_item_class = menu_items[prev_state]
            if menu_item_class:
                message.text = prev_state
                menu_item = menu_item_class(message.chat.id, self.user_state)
                menu_item.execute(message)


menu_items = {
    'Чемпионаты🏆': ChampionshipsMenuItem,
    'Германия - Бундеслига 🇩🇪': CountryMenuItem,
    'Англия - Премьер-лига 🏴󠁧󠁢󠁥󠁮󠁧󠁿': CountryMenuItem,
    'МИР Российская Премьер-лига 🇷🇺':CountryMenuItem,
    'Испания - Примера 🇪🇸':CountryMenuItem,
    'Франция - Лига 1 🇫🇷':CountryMenuItem,
    'Италия - Серия А 🇮🇹':CountryMenuItem,
    'Таблица': TableMenuItem,
    'Календарь': CalendarMenuItem,
    'Назад': BackMenuItem,
    'Главное меню': MainMenuItem,
    'Обзоры⚽': ReviewMenuItem,
    'Последние добавленные':ReviewChampionatMenuItem,
    'Англия🏴󠁧󠁢󠁥󠁮󠁧󠁿': ReviewChampionatMenuItem, 
    'Германия🇩🇪':ReviewChampionatMenuItem, 
    'Россия🇷🇺':ReviewChampionatMenuItem,
    'Италия🇮🇹':ReviewChampionatMenuItem,
    'Испания🇪🇸':ReviewChampionatMenuItem,
    'Франция🇫🇷':ReviewChampionatMenuItem,
    'Квалификация Евро-2024🌍':ReviewChampionatMenuItem,
    'Лига чемпионов🌍':ReviewChampionatMenuItem,
    'Лига Европы🌍':ReviewChampionatMenuItem,
    'Кубок России':ReviewChampionatMenuItem,
    'Кубок Италии':ReviewChampionatMenuItem,
    'Кубок Испании':ReviewChampionatMenuItem,
    'Кубок Германии':ReviewChampionatMenuItem, 
    'Кубок Англии':ReviewChampionatMenuItem,
    'Кубок Франции':ReviewChampionatMenuItem,
    'Чемпионат мира🌍':ReviewChampionatMenuItem,
    'Новости📰': NewsMenuItem,
    'Ближайшие матчи': UpcomingMenuItem,
    'Live': UpcomingDayMenuItem,
    'Вчера':UpcomingDayMenuItem,
    'Сегодня': UpcomingDayMenuItem,
    'Завтра': UpcomingDayMenuItem,
}

@bot.message_handler(commands=['start'])
def start(message):
    user_state = UserState(message.from_user.id)
    user_state.clear_history()
    menu = MainMenuItem(message.chat.id, user_state)
    menu.execute(message)


@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == 'send' and message.chat.id == config.user_id:
        video.IS_SEND = True
        return
    if message.text == 'update' and message.chat.id == config.user_id:
        msg = bot.send_message(message.chat.id, 'Введи дату')
        return bot.register_next_step_handler(msg, update)
    user_state = UserState(message.from_user.id)
    menu_item_class = menu_items.get(message.text)
    try:
        if menu_item_class:
            menu_item = menu_item_class(message.chat.id, user_state)
        elif user_state.get_state() == 'Календарь':
            menu_item = TourMenuItem(message.chat.id, user_state)
        elif user_state.get_state() == 'Таблица':
            menu_item = TeamMenuItem(message.chat.id, user_state)
        elif user_state.get_state() == 'Новости📰':
            menu_item = NewsOneMenuItem(message.chat.id, user_state)
        elif user_state.get_history()[-1] == 'Обзоры⚽':
            menu_item = ReviewVideoItem(message.chat.id, user_state)
        else:
            return
        menu_item.execute(message)
    except Exception as e:
        return e
        
def update(message):
    try:
        datetime.strptime(message.text,'%Y-%m-%d')
        update = matches.FootballMatchParser()
        update.update_database_to_date(message.text)
    except ValueError:
        message.text = 'update'
        handle_text(message)
    

if __name__ == '__main__':
    threading.Thread(target=news.news).start()
    threading.Thread(target=matches.update).start()      
    threading.Thread(target=video.run_async).start()
    set_russian_locale()
    while True:
        try:
            bot.infinity_polling()
        except Exception:
            time.sleep(10)