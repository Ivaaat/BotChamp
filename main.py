import telebot
from telebot import types, formatting
from pymongo import MongoClient
from config import mass_contry
from datetime import datetime
import locale
import live
import news 
import video 
import time
import mongo
import config

bot = telebot.TeleBot(config.TOKEN)

db = config.client_champ['json_champ']
user_states_collection = db['users']
news_coll = db['news']
calendar = db['calendar_2022/2023']
table = db[f'table_2022/2023']
video_coll = db['video']

locale.setlocale(locale.LC_TIME, ('ru_RU', 'UTF-8'))


class State:
    def __init__(self, *args):
        for i, arg in enumerate(args, 1):
            attribute_name = f"state_{i}"
            attribute_value = arg
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
        try:
            ref_class = get_class(message.text)
            return ref_class(message.text)
        except KeyError:
            return


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
        j = 1
        for table_stat in table.find({'country':
                                        mass_contry[self.state_2]}
                                        ).sort('points',-1):
            button = "{}. | {} |  И: {}  О: {}  M: {}".format(
                        j,
                        table_stat['team'],
                        table_stat['games'],
                        table_stat['points'],
                        table_stat['balls']
                        )
                                    
            self.add_item(button)
            j += 1

    def handle_input(self, bot, message):
        if message.text == 'Назад':
            return ChampionshipState(self.state_2, self.state_1)
        elif message.text == 'Главное меню':
            return MainMenuState('Главное меню')
        elif message.text in self.items:
            list_date = []
            name_team = message.text.split("|")[1].strip()
            name_champ = ' '.join(self.state_2.split()[:-1])
            for match_name in calendar.find({'champ':name_champ,
                                                        'is_over':True, 
                                                        'title':
                                                        {'$regex':name_team}}
                                                        ).sort('datetime', -1
                                                            ).limit(6):
                true_date = datetime.strptime(match_name['date'],
                                    '%Y-%m-%d').strftime('%d %B')
                list_date.append(
                    formatting.mbold('{}  | {} | {}\
                                    '.format(true_date,
                                            match_name['title'].split(',')[0],
                                            match_name['result'],
                                            escape=True)))
            
            bot.send_photo(message.chat.id,
                            table.find_one({'team':name_team},
                                                {'logo': 1, '_id': 0})['logo'],
                            #postgr.get_logo(mass_contry[country_button], text),
                            caption='\n\n'.join(list_date),
                            parse_mode="MarkdownV2"
                            )


class Calendar(State):    
    def __init__(self, *country):
        super().__init__(*country)
        self.add_item('Главное меню')
        self.add_item('Назад')
        self.name_champ = ' '.join(self.state_2.split()[:-1])
        max_tour = calendar.find({'champ':self.name_champ}).sort('datetime',1).distinct('tour')
        max_tour.sort(key = lambda x:int(x.split('-')[0]))
        for tour in max_tour:
            dates = calendar.find({'champ':self.name_champ, 'tour': tour}).sort('datetime',1).distinct('datetime')
            end = calendar.find_one({'champ':self.name_champ, 'tour': tour, 'is_over': False})
            tour_button = ('{} | {} - {} | {}'.format(
                                                    tour, 
                                                    datetime.strftime(dates[0], '%d %B'), 
                                                    datetime.strftime(dates[-1], '%d %B'),
                                                    ('Закончен' 
                                                    if end is None 
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
            tour = message.text.split("|")[0].strip()
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Главное меню",
                                            callback_data="back"))
            list_date = []
            for match_tour in calendar.find({'champ': self.name_champ, 'tour': tour}).sort('datetime', 1):
                true_date = formatting.mitalic(
                    datetime.strptime(match_tour['date'],
                                    '%Y-%m-%d').strftime('%d %B'),escape=True)
                if true_date not in list_date:
                    list_date.append(true_date)
                list_date.append(formatting.mbold('{} | {} | {}'.format(
                                                match_tour['time'],
                                                match_tour['title'].split(',')[0],
                                                match_tour['result']), escape=True))
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
            query = {'country':self.state_1}
        for key in video_coll.find(query).sort('date',-1).limit(50):
            self.add_item(key["desc"])

    def handle_input(self, bot, message):
        if message.text == 'Назад':
            return ReviewsMenuState(self.state_2)
        elif message.text == 'Главное меню':
            return MainMenuState('Главное меню')
        elif message.text in self.items:
            video_ref = video_coll.find_one({'desc':message.text})
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
    state_data = user_states_collection.find_one({'chat_id': chat_id}, {'chat_id':0, '_id':0}),
    arg_state = []
    if state_data:
        for state in state_data:
            for value in state.values():
                arg_state.append(value)
        state_class = get_class(arg_state[0])
        if state_class:
            return state_class(*arg_state)
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


@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == 'update' and message.chat.id == config.user_id:
        mongo.update_all()
        return
    state = get_state(message.chat.id)
    new_state_name = state.handle_input(bot, message)
    if new_state_name:
        new_state_class = get_class(new_state_name.state_1)
        list_attr = []
        attributes = dir(new_state_name)
        for state_attr in attributes:
            if state_attr.startswith('state'):
                list_attr.append(getattr(new_state_name, state_attr))
        new_state = new_state_class(*list_attr)
        set_state(message.chat.id, new_state_name)
        new_state.send(bot, message)



if __name__ == '__main__':
    while True:
        try:
            bot.infinity_polling()
        except Exception:
            time.sleep(10)