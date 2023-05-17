import telebot
from telebot import types, formatting
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
from datetime import datetime
from config import mass_contry
from config import list_name_site, db, text_start
from config import user_id, channel_link
from config import channel_id, bot
import news 
import video 
import flask
from live import upcoming_match
#import postgr
import mongo
from mongo import view_users, get_push
from mongo import set_push, get_list_user
import locale
from abc import ABC, abstractmethod



locale.setlocale(locale.LC_TIME, ('ru_RU', 'UTF-8'))

bot.set_my_commands(
    commands=[
        telebot.types.BotCommand("start", "start_parse"),
    ],
)

BACK = 'Назад'
MAIN_MENU = 'Главное меню'


# СТАРТУЕМ ОТСЮДА
#@bot.message_handler(content_types='text')
@bot.message_handler(commands='start')
def main(message):
    markup = types.ReplyKeyboardMarkup()
    users_col = db['users']
    if users_col.find_one({'_id': message.chat.id}) is None:
        name = f'{message.chat.first_name} {message.chat.username}'
        users_col.insert_one({'_id':message.chat.id, 
                              'Name': name,
                              'Push':False
                              })
        bot.send_message(user_id,
                         f"Новый пользователь {name}")
    markup.add(ChampButton.button,
               News.button,
               Review.button,
               UpcomingMatches.button,
               row_width = 2
                )
    push = users_col.find_one({'_id':message.chat.id, 'Push': True}) is None
    msg = bot.send_message(message.chat.id,
                           text_start.format(
                                             message.chat.first_name, 
                                             message.chat.username, 
                                             bot.user.username, 
                                             'не' if push else ' '),
                           reply_markup=markup)

    bot.delete_my_commands()
    bot.set_my_commands(commands=[
        telebot.types.BotCommand("push", "push notifications")])
    bot.register_next_step_handler(msg, null_step)


# обработка inline-кнопки главное меню
@bot.callback_query_handler(func=lambda call: call.data == 'back')
def callback_query(call):
    bot.answer_callback_query(call.id, "Главное меню")
    bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
    main(call.message)


class СhampBot(ABC):
    @abstractmethod
    def get_buttons(self):
        self.markup = types.ReplyKeyboardMarkup()
        self.markup.add(BACK)

    @abstractmethod
    def one_step(self):
        self.markup = types.ReplyKeyboardMarkup(row_width=1)
        self.markup.add(MAIN_MENU, BACK)
    
    def check_text_in_markup(markup, message_text):
        for list_row in markup.keyboard:
            for text in list_row:
                if text['text'] == message_text:
                    return True
        return False


class ChampButton(СhampBot):
    button = types.KeyboardButton('Чемпионаты🏆')
    message_text = 'Выбери чемпионат'
    button_calendar = 'Календарь🗓'
    button_table = 'Таблица⚽'
    calendar = db['calendar_2022/2023']
    table = db[f'table_2022/2023']

    def get_buttons(self):
        super().get_buttons()
        for key in mass_contry:
            self.markup.add(key)
        return self.markup
    
    def one_step(self, message):
        super().one_step()
        self.country_button = message.text
        self.champ = ' '.join(self.country_button.split()[:-1])
        bot.delete_message(message.chat.id, message.message_id)
        self.markup.add(self.button_calendar, 
                        self.button_table,row_width=2)
        return bot.send_message(message.chat.id, 
                                self.country_button, 
                                reply_markup=self.markup)
        
    def second_step(self, message):
        if message.text == self.button_calendar:
            self.third_step = self.view_tour
            return bot.send_message(message.chat.id,
                            '{} Выбери тур, чтобы узнать результаты:'.format(
                    self.country_button
                            ), reply_markup=self.calendar_button())
        elif message.text == self.button_table:
            self.third_step = self.team_button
            return bot.send_message(message.chat.id,
                        '{}.Таблица чемпионата!\n\
Выбери команду, чтобы узнать последние результаты'.format(
                    self.country_button),
                        reply_markup=self.table_button()
                        )
        else:
            return bot.send_message(message.chat.id,
                                f'{message.chat.first_name}!✅Выбери!\n\n\
                                    🔙Назад\n\n\
                🗓Календарь          📊Таблица\
                ')
    
    def third_step(self, message):
        pass

    def calendar_button(self):
        super().one_step()
        max_tour = self.calendar.find({'champ':self.champ}).sort('datetime',1).distinct('tour')
        max_tour.sort(key = lambda x:int(x.split('-')[0]))
        for tour in max_tour:
            dates = self.calendar.find({'champ':self.champ, 'tour': tour}).sort('datetime',1).distinct('datetime')
            end = self.calendar.find_one({'champ':self.champ, 'tour': tour, 'is_over': False})
            tour_button = ('{} | {} - {} | {}'.format(
                                                    tour, 
                                                    datetime.strftime(dates[0], '%d %B'), 
                                                    datetime.strftime(dates[-1], '%d %B'),
                                                    ('Закончен' 
                                                    if end is None 
                                                    else "")
                                                    )
                                                    )
            button = types.KeyboardButton(tour_button.strip())
            self.markup.add(button)
        return self.markup

    def table_button(self):
        super().one_step()
        j = 1
        for table_stat in self.table.find({'country':
                                           mass_contry[self.country_button]}
                                           ).sort('points',-1):
            button = types.KeyboardButton(
                                    "{}. | {} |  И: {}  О: {}  M: {}".format(
                                        j,
                                        table_stat['team'],
                                        table_stat['games'],
                                        table_stat['points'],
                                        table_stat['balls']
                                        )
                                    )
            self.markup.add(button)
            j += 1
        return self.markup
    
    # Нажатие на кнопку с названием команды
    def team_button(self, message):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Главное меню", callback_data="back"))
        name_team = message.text.split("|")[1].strip()
        list_date = []
        for match_name in self.calendar.find({'champ':self.champ,
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
        bot.delete_message(message.chat.id, message.message_id)
        return bot.send_photo(message.chat.id,
                            mongo.get_logo(name_team),
                            #postgr.get_logo(mass_contry[country_button], text),
                            caption='\n\n'.join(list_date),
                            reply_markup=markup,
                            parse_mode="MarkdownV2"
                            )

    
    # Обработка нажатия на кнопку с туром
    def view_tour(self, message):
        tour = message.text.split("|")[0].strip()
        bot.delete_message(message.chat.id, message.message_id)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Главное меню",
                                        callback_data="back"))
        list_date = []
        for match_tour in self.country_calendar.find({'champ': self.champ, 'tour': tour}).sort('datetime', 1):
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
        return bot.send_message(message.chat.id,
                            f"{text}\n\n" +
                            '\n\n'.join(list_date),
                            reply_markup=markup,
                            parse_mode='MarkdownV2')
            

class News(СhampBot):
    button = types.KeyboardButton('Новости📰')
    news_coll = db['news']
    message_text = 'Новости📰'

    def get_buttons(self):
        super().get_buttons()
        for news in News.news_coll.find().limit(50).sort('date', -1):
            title = '{} {}'.format(news['date'].split()[1], news['title']) 
            self.markup.add(types.KeyboardButton(title))
        return self.markup
    
    def one_step(self, message):
        news_doc = News.news_coll.find_one({'title':message.text.split(' ', 1)[1]})
        logo = news_doc['logo']
        text = news_doc['text']
        if len(text) >= 1024:
            num_symb = text[:1024].rfind('.') + 1
            bot.send_photo(message.chat.id,
                            logo,
                            caption=text[:num_symb])
            for x in range(num_symb, len(text), 1024):
                return bot.send_message(message.chat.id,
                                    text[x:x+1024])
        else:
            return bot.send_photo(message.chat.id, 
                                logo,
                                caption=text,
                                )
        

class UpcomingMatches(СhampBot):
    message_text = 'Выбери день'
    button = types.KeyboardButton('Ближайшие матчи')

    def get_buttons(self):
        super().get_buttons()
        buttons = ['Live','Вчера', 'Сегодня', 'Завтра']
        if len(upcoming_match(buttons[0])) != 0:
            self.markup.add(buttons[0])
        self.markup.add(*[x for x in buttons[1:]])
        return self.markup
    
    def one_step(self, message):
        super().one_step()
        matches = upcoming_match(message.text)
        if matches is None:
            return bot.send_message(message.chat.id, 'Нет матчей')
        for match in matches:
            self.markup.add(match)
        return bot.send_message(message.chat.id, message.text,
                                reply_markup=self.markup)
    
    def second_step(self, message):
        return bot.send_message(message.chat.id, 
                                message.text,
                                )
    

class Review(СhampBot):
    message_text = 'Выбери обзор'
    button = types.KeyboardButton('Обзоры⚽')
    video_coll = db['video']

    
    def get_buttons(self):
        super().get_buttons()
        for key in list_name_site:
            self.markup.add(key)
        return self.markup

    def one_step(self, message):
        super().one_step()
        if message.text == list_name_site[0]:
            query = {}
        else:
            query = {'country':message.text}
        for key in self.video_coll.find(query).sort('date',-1).limit(50):
            button_champ_rev = types.KeyboardButton(key["desc"])
            self.markup.add(button_champ_rev)
        return bot.send_message(message.chat.id, 'Выбери обзор',
                            reply_markup=self.markup)

    def second_step(self, message):
        video_ref = self.video_coll.find_one({'desc':message.text})
        return bot.send_message(message.chat.id,
                                "{}\n{}".format(message.text,
                                video_ref['link']))


# Создаем три кнопки "Чемпионаты🏆" и "Новости📰  'Обзоры⚽' после вызова старта"
def null_step(message):
    champ = ChampButton()
    news = News()
    review = Review()
    upcoming = UpcomingMatches()
    for class_instance in [champ, news, review, upcoming]:
        if class_instance.button.text == message.text:
            buttons = class_instance.get_buttons()
            msg = bot.send_message(message.chat.id, 
                                   class_instance.message_text,
                                    reply_markup=buttons)
            return bot.register_next_step_handler(msg, 
                                                  one_step, 
                                                  class_instance
                                                  )
    if message.text == '/push':
        if get_push(message.chat.id) is False:
            set_push(message.chat.id, True)
            bot.send_message(message.chat.id, 'Жди уведомлений!')
        else:
            set_push(message.chat.id, False)
            bot.send_message(message.chat.id, 'Уведомлений не будет!')
        main(message)
    elif message.text == "update" and user_id == message.chat.id:
        mongo.update()
        bot.send_message(message.chat.id, 'Обновил')
        for name in mass_contry.values():
            #postgr.add_table(name)
            #postgr.add_calendar(name)
            bot.send_message(message.chat.id, f'Обновил {name}')
            time.sleep(5)
        bot.send_message(message.chat.id, 'Обновил таблицы')
        main(message)
    elif message.text == 'users' and user_id == message.chat.id:
        bot.send_message(user_id, view_users())
    elif message.text == 'send' and user_id == message.chat.id:
        user_list = get_list_user()
        for id in user_list:
            bot.send_message(id, "Вышло обновление. Жми /start")
    else:
        main(message)


def one_step(message, class_instance):
    try:
        if message.text == BACK:
            return main(message)
        if class_instance.check_text_in_markup(class_instance.markup, message.text):
                msg = class_instance.one_step(message)
                class_instance.second_step
                return bot.register_next_step_handler(msg, 
                                                    second_step, 
                                                    class_instance,
                                                    )
        else:
            msg = bot.send_message(message.chat.id,
                                   class_instance.button.text,
                                   reply_markup=class_instance.markup)
            raise AttributeError
    except AttributeError:
        return bot.register_next_step_handler(msg, 
                                            one_step, 
                                            class_instance,
                                        )
    

def second_step(message, class_instance):
    try:
        if message.text == MAIN_MENU:
            return main(message)
        elif message.text == BACK :
            message.text = class_instance.button.text
            return null_step(message)
        elif class_instance.check_text_in_markup(class_instance.markup, message.text):
            msg = class_instance.second_step(message)
            class_instance.third_step
            return bot.register_next_step_handler(msg, 
                                                third_step, 
                                                class_instance,
                                                )
        else:
            msg = bot.send_message(message.chat.id,
                                   class_instance.button.text,
                                   reply_markup=class_instance.markup)
            raise AttributeError
    except AttributeError:
            return bot.register_next_step_handler(msg, 
                                                second_step, 
                                                class_instance,
                                                )
    
    
def third_step(message, class_instance):
    if message.text == MAIN_MENU:
        return main(message)
    elif message.text == BACK:
        class_instance.get_buttons()
        message.text = class_instance.country_button
        return one_step(message, class_instance)
    elif class_instance.check_text_in_markup(class_instance.markup, message.text):
        msg = class_instance.third_step(message)
        bot.register_next_step_handler(msg, 
                                        third_step, 
                                        class_instance,
                                        )
    else:
        msg = bot.send_message(message.chat.id,
                                   class_instance.button.text,
                                   reply_markup=class_instance.markup)
        return bot.register_next_step_handler(msg, 
                                            third_step, 
                                            class_instance,
                                            )


bot.enable_save_next_step_handlers(delay=2)

bot.load_next_step_handlers()

if __name__ == '__main__':
    while True:
        try:
            bot.infinity_polling()
        except Exception:
            time.sleep(10)
