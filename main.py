from telebot import types, formatting
import config
from datetime import datetime
import locale
import sys
import live
import news 
import video 
import video
import time
import config
import matches
from pymongo import MongoClient
import threading
import telebot


user_states_collection = config.db['users']
news_coll = config.db['news']
calendar = config.db['foot']
bot = telebot.TeleBot(config.TOKEN)


def set_russian_locale():
    try:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'Russian_Russia')
        except locale.Error:
            print('Не удалось установить русскую локаль', file=sys.stderr)

client_champ = MongoClient()
DB_NAME = client_champ['video_database']
COLLECTION_NAME = 'videos'
video_coll = DB_NAME[COLLECTION_NAME]


class State:
    def __init__(self, *attribute):
        for i, attribute_value in enumerate(attribute, 1):
            attribute_name = f'state_{i}'
            setattr(self, attribute_name, attribute_value)
        self.items = []
        self.width = 1

    def add_item(self, item):
        self.items.append(item)

    def handle_input(self, bot, message):
        pass

    def send(self, bot, message):
        markup = types.ReplyKeyboardMarkup(row_width=self.width)
        markup.add(*self.items)
        bot.send_message(message.chat.id, self.state_1, reply_markup=markup)
        i = 0
        while True:
            i += 1
            try:
                bot.delete_message(message.chat.id, message.message_id - i)
            except:
                break



class MainMenuState(State):
    def __init__(self, *main_menu):
        super().__init__(*main_menu)
        main_menu : list = [
                            'Чемпионаты🏆',
                            'Новости📰',
                            'Обзоры⚽',
                            'Ближайшие матчи'
        ] 
        for key in main_menu:
            self.add_item(key)
        self.width = 2

    def handle_input(self, bot, message):
        if message.text in self.items: 
            ref_class = get_class(message.text)
            return ref_class(message.text)


class ChampionshipsMenuState(State):
    def __init__(self, *champ):
        super().__init__(*champ)
        self.add_item('Назад')
        for championship in state_classes[ChampionshipState]:
            self.add_item(championship)

    def handle_input(self, bot, message):
        if message.text == 'Назад':
            return MainMenuState('Главное меню')
        elif message.text in self.items: 
            return ChampionshipState(message.text)
        

class ChampionshipState(State):
    def __init__(self, *name):
        super().__init__(*name)
        self.add_item('Главное меню')
        self.add_item('Назад')
        self.add_item('Таблица')
        self.add_item('Календарь')

    def handle_input(self, bot, message):
        if message.text == 'Назад':
            return ChampionshipsMenuState('Чемпионаты🏆')
        elif message.text == 'Главное меню':
            return MainMenuState('Главное меню')
        elif message.text == 'Таблица':
            return Table(message.text, self.state_1)
        elif message.text == 'Календарь':
            return Calendar(message.text, self.state_1)
        else:
            return self
        

class Table(State):    
    def __init__(self, *name_country):
        super().__init__(*name_country)
        self.add_item('Главное меню')
        self.add_item('Назад')
        self.id_champ = config.season_now[self.state_2]
        table = calendar.aggregate(config.champ_pipeline(self.id_champ))
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


    def handle_input(self, bot, message):
        if message.text == 'Назад':
            return ChampionshipState(self.state_2, self.state_1)
        elif message.text == 'Главное меню':
            return MainMenuState('Главное меню')
        elif message.text in self.items:
            list_date = []
            name_team = message.text.split("|")[1].strip()
            for match_name in calendar.find({'id_champ':self.id_champ,
                                                        'link_title':
                                                        {'$regex':name_team}}
                                                        ).sort('pub_date', 1
                                                            ).limit(6):
                true_date = datetime.strptime(match_name['date'],
                                    '%Y-%m-%d').strftime('%d %B')
                try:
                    result = match_name['score']['direct']['main']
                except KeyError:
                    result = ""
                list_date.append(
                    formatting.mbold('{}  | {} | {}\
                                    '.format(true_date,
                                            match_name['link_title'].split(',')[0],
                                            result,
                                            escape=True)))
            logo = calendar.find_one({'$and':[{'teams.0.name':name_team}, 
                                                       {'id_champ':self.id_champ}]}, {'teams':1})
            bot.send_photo(message.chat.id,
                            logo['teams'][0]['icon'].replace('60x60', '400x400'),
                            #postgr.get_logo(mass_contry[country_button], text),
                            caption='\n\n'.join(list_date),
                            parse_mode="MarkdownV2"
                            )


class Calendar(State):    
    def __init__(self, *country):
        super().__init__(*country)
        self.add_item('Главное меню')
        self.add_item('Назад')
        #self.name_champ = ' '.join(self.state_2.split()[:-1])
        self.id_champ = config.season_now[self.state_2]
        max_tour = calendar.find({'id_champ':self.id_champ}).sort('datetime',1).distinct('tour')
        #max_tour.sort(key = lambda x:int(x.split('-')[0]))
        for tour in max_tour:
            dates = calendar.find({'id_champ':self.id_champ, 'tour': tour}).sort('pub_date',1).distinct('pub_date')
            is_end = calendar.find_one({'id_champ':self.id_champ, 'tour': tour, 'status.label': 'dns'})
            date_start = datetime.fromtimestamp(dates[0])
            date_end = datetime.fromtimestamp(dates[-1])
            tour_button = ('{} | {} - {} | {}'.format(
                                                    '{}-й тур'.format(tour), 
                                                    datetime.strftime(date_start, '%d %B'), 
                                                    datetime.strftime(date_end, '%d %B'),
                                                    ('Закончен' 
                                                    if is_end is None 
                                                    else "")
                                                    )
                                                    )
            self.add_item(tour_button.strip())

    def handle_input(self, bot, message):
        if message.text == 'Назад':
            return ChampionshipState(self.state_2, self.state_1)
        elif message.text == 'Главное меню':
            return MainMenuState('Главное меню')
        elif message.text in self.items:
            tour = message.text.split("-")[0].strip()
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Главное меню",
                                            callback_data="back"))
            list_date = []
            for match_tour in calendar.find({'id_champ': self.id_champ, 'tour': int(tour)}, 
                                            {'link_title':1,
                                             'time':1,
                                             'result':1,
                                             'score':1,
                                             'pub_date': 1
                                             }).sort('pub_date', 1):
                true_date = datetime.fromtimestamp(match_tour['pub_date']).strftime('%d %B')
                true_date_italic = formatting.mitalic(true_date,escape=True)
                if true_date_italic not in list_date:
                    list_date.append(true_date_italic)
                try:
                    result = match_tour['score']['direct']['main']
                except KeyError:
                    result = ""
                list_date.append(formatting.mbold('{} | {} | {}'.format(
                                                match_tour['time'],
                                                match_tour['link_title'].split(',')[0],
                                                result), escape=True))
            text = formatting.mbold(message.text, escape=True)
            bot.send_message(message.chat.id,
                                f"{text}\n\n" +
                                '\n\n'.join(list_date),
                                parse_mode='MarkdownV2')


class NewsMenuState(State):
    def __init__(self, *news):
        super().__init__(*news)
        self.add_item('Назад')
        for news_doc in news_coll.find().limit(50).sort('date', -1):
            title = '{} {}'.format(news_doc['date'].split()[1], news_doc['title']) 
            self.add_item(title)

    def handle_input(self, bot, message):
        if message.text == 'Назад':
            return MainMenuState('Главное меню')
        elif message.text in self.items:
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
       


class ReviewsMenuState(State):
    def __init__(self, *review):
        super().__init__(*review)
        self.add_item('Назад')
        for championship in state_classes[ReviewChampionat]:
            self.add_item(championship)

    def handle_input(self, bot, message):
        if message.text == 'Назад':
            return MainMenuState('Главное меню')
        elif message.text in self.items: 
            return ReviewChampionat(message.text, self.state_1)
        

class ReviewChampionat(State):
    def __init__(self, *name):
        super().__init__(*name)
        self.add_item('Главное меню')
        self.add_item('Назад')
        if self.state_1 == state_classes[ReviewChampionat][0]:
            query = {}
        else:
            query = {'champ':self.state_1}
        for key in video_coll.find(query).sort('date',-1).limit(50):
            self.add_item(key["title"])

    def handle_input(self, bot, message):
        if message.text == 'Назад':
            return ReviewsMenuState(self.state_2)
        elif message.text == 'Главное меню':
            return MainMenuState('Главное меню')
        elif message.text in self.items:
            video_ref = video_coll.find_one({'title':message.text})
            bot.send_message(message.chat.id,
                                "{}\n{}".format(message.text,
                                video_ref['link']))
            

class UpcomingMatchesMenuState(State):
    def __init__(self, *match):
        super().__init__(*match)
        self.add_item('Назад')
        for championship in state_classes[ViewUpcomingMatches]:
            if len(live.upcoming_match(championship)) == 0:
                continue
            self.add_item(championship)

    def handle_input(self, bot, message):
        if message.text == 'Назад':
            return MainMenuState('Главное меню')
        elif message.text in self.items:
            return ViewUpcomingMatches(message.text, self.state_1)
        

class ViewUpcomingMatches(State):
    def __init__(self, *match):
        super().__init__(*match)
        self.add_item('Главное меню')
        self.add_item('Назад')
        matches = live.upcoming_match(self.state_1)
        for match in matches:
            self.add_item(match)

    def handle_input(self, bot, message):
        if message.text == 'Назад':
            return UpcomingMatchesMenuState(self.state_2)
        elif message.text == 'Главное меню':
            return MainMenuState('Главное меню')



state_classes = {
    MainMenuState : ['Главное меню'],
    ChampionshipsMenuState : ['Чемпионаты🏆'],
    NewsMenuState: ['Новости📰'],
    ReviewsMenuState: ['Обзоры⚽'],
    UpcomingMatchesMenuState: ['Ближайшие матчи'],
    ChampionshipState: [
                        'Германия - Бундеслига 🇩🇪',
                        'Англия - Премьер-лига 🏴󠁧󠁢󠁥󠁮󠁧󠁿',
                        'МИР Российская Премьер-лига 🇷🇺',
                        'Испания - Примера 🇪🇸',
                        'Франция - Лига 1 🇫🇷',
                        'Италия - Серия А 🇮🇹'
                        ],
    Table:['Таблица'],
    Calendar: ['Календарь'],
    ReviewChampionat:
                    [
                    'Последние добавленные',
                    'Англия🏴󠁧󠁢󠁥󠁮󠁧󠁿', 
                    'Германия🇩🇪', 
                    'Россия🇷🇺',
                    'Италия🇮🇹',
                    'Испания🇪🇸',
                    'Франция🇫🇷',
                    'Квалификация Евро-2024🌍',
                    'Лига чемпионов🌍',
                    'Лига Европы🌍',
                    'Кубок России',
                    'Кубок Италии',
                    'Кубок Испании',
                    'Кубок Германии', 
                    'Кубок Англии',
                    'Кубок Франции',
                    'Чемпионат мира🌍'
                    ],
    ViewUpcomingMatches: [
                        'Live',  
                        'Вчера',
                        'Сегодня',
                        'Завтра'
                        ]
    }



def get_state(chat_id):
    state_data = user_states_collection.find_one({'chat_id': chat_id}, {'chat_id':0, '_id':0})
    if state_data:
        state_class = get_class(state_data['state_1'])
        if state_class:
            return state_class(*list(state_data.values()))
    return MainMenuState('Главное меню')


def get_class(button_text_find):
    for ref_class, list_button_text in state_classes.items(): 
        for text in list_button_text:
            if text == button_text_find:
                return ref_class


def set_state(chat_id, state):
    attributes = dir(state)
    for mongo_state in attributes:
        if mongo_state.startswith('state'):
            user_states_collection.update_one({'chat_id': chat_id}, {'$set': {mongo_state: getattr(state, mongo_state)}}, upsert=True)


@bot.message_handler(commands=['start'])
def start(message):
    state = MainMenuState('Главное меню')
    set_state(message.chat.id, state)
    state.send(bot, message)

def update(message):
    try:
        datetime.strptime(message.text,'%Y-%m-%d')
        update = matches.FootballMatchParser()
        update.update_database_to_date(message.text)
    except ValueError:
        message.text = 'update'
        handle_text(message)



@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == 'send' and message.chat.id == config.user_id:
        video.IS_SEND = True
        return
    if message.text == 'update' and message.chat.id == config.user_id:
        msg = bot.send_message(message.chat.id, 'Введи дату')
        return bot.register_next_step_handler(msg, update)
    state = get_state(message.chat.id)
    new_state_name = state.handle_input(bot, message)
    if new_state_name:
        new_state_class = type(new_state_name)
        list_attr = []
        attributes = dir(new_state_name)
        for state_attr in attributes:
            if state_attr.startswith('state'):
                list_attr.append(getattr(new_state_name, state_attr))
        new_state = new_state_class(*list_attr)
        set_state(message.chat.id, new_state_name)
        new_state.send(bot, message)





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