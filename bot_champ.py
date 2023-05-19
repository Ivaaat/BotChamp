import telebot
from telebot import formatting
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton 
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import time
from datetime import datetime
from config import mass_contry
from config import list_name_site, db, text_start
from config import user_id, bot
# import news 
# import video 
# import flask
from live import upcoming_match
import mongo
#import postgr
import locale
from abc import ABC, abstractmethod
from telebot.handler_backends import State, StatesGroup
from telebot import custom_filters

locale.setlocale(locale.LC_TIME, ('ru_RU', 'UTF-8'))

bot.set_my_commands(
    commands=[
        telebot.types.BotCommand("start", "start_parse"),
    ],
)

BACK = 'Назад'
MAIN_MENU = 'Главное меню'

class MyStates(StatesGroup):
    # Just name variables differently
    null = State()
    one = State() # creating instances of State class is enough from now
    second = State()
    three = State()
    four = State()

# СТАРТУЕМ ОТСЮДА
#@bot.message_handler(content_types='text')
# Создаем четыре кнопки "Чемпионаты🏆" и "Новости📰  'Обзоры⚽' "Ближайшие матчи", после вызова старта"
@bot.message_handler(commands=['start'])
def main(message):
    step = Step()
    if step.users.find_one({'_id': message.chat.id}) is None:
        name = f'{message.chat.first_name} {message.chat.username}'
        step.users.insert_one({'_id':message.chat.id, 
                              'Name': name,
                              'Push':False
                              })
        bot.send_message(user_id,
                         f"Новый пользователь {name}")
    step.markup.add(*DICT_CLASS,row_width=2
                )
    push = step.users.find_one({'_id':message.chat.id, 'Push': True}) is None
    bot.set_state(message.from_user.id, MyStates.null, message.chat.id)
    bot.send_message(message.chat.id,
                           text_start.format(
                                             message.chat.first_name, 
                                             message.chat.username, 
                                             bot.user.username, 
                                             'не' if push else ' '),
                           reply_markup=step.markup)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['main_keyboard'] = step.markup
    bot.delete_my_commands()
    bot.set_my_commands(commands=[
        telebot.types.BotCommand("push", "push notifications")])

#обработка inline-кнопки главное меню
@bot.callback_query_handler(func=lambda call: call.data == 'back')
def callback_query(call):
    bot.answer_callback_query(call.id, "Главное меню")
    bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
    main(call.message)


@bot.message_handler(state=MyStates.null)
def null_step(message):
    users = db['users']
    try:
        class_instance = DICT_CLASS[message.text]
        bot.set_state(message.from_user.id, MyStates.one, message.chat.id)
        bot.send_message(message.chat.id, 
                        class_instance.message_text,
                        reply_markup=class_instance.markup)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['class_instance'] = class_instance
            data['null_keyboard'] = class_instance.markup
    except KeyError:
        text = class_instance.message_text
        if message.text == '/push':
            id = message.chat.id
            if users.find_one({'_id':id, 'Push':True}) is None:
                push = True
                text = 'Жди уведомлений!'
            else:
                not push 
                text = 'Уведомлений не будет!'
            users.update_one({'_id':id}, {'$set':{'Push':push}})
        elif message.text == "update" and user_id == message.chat.id:
            mongo.update()
            for name in mass_contry.values():
                bot.send_message(message.chat.id, f'Обновил {name}')
                time.sleep(5)
            text = 'Обновил таблицы'
        elif message.text == 'users' and user_id == message.chat.id:
            list_users = [user['Name'] for user in users.find()]
            text =  '\n'.join(list_users)
        elif message.text == 'send' and user_id == message.chat.id:
            list_users = [user['_id'] for user in users.find()]
            for id in list_users:
                bot.send_message(id, "Вышло обновление. Жми /start")
        bot.send_message(message.chat.id, text)
        main(message)


@bot.message_handler(state=MyStates.one)
def one_step(message):
    try:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            class_instance = data['class_instance']
            if message.text == BACK:
                bot.send_message(message.chat.id, 
                        class_instance.message_text,
                        reply_markup=data['main_keyboard'])
                bot.set_state(message.from_user.id, MyStates.null, message.chat.id)
                return
            elif class_instance.check_text_in_markup(data['null_keyboard'], 
                                                message.text):
                class_instance.one_step(message)
                class_instance.second_step
                bot.set_state(message.from_user.id, MyStates.second, message.chat.id)
                data['class_instance'] = class_instance
                data['one_keyboard'] = class_instance.markup
            else:
                raise AttributeError
    except AttributeError:
        data['class_instance'] = class_instance
        bot.set_state(message.from_user.id, MyStates.one, message.chat.id)


@bot.message_handler(state=MyStates.second)
def second_step(message):
        try:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                class_instance = data['class_instance']
                if message.text == MAIN_MENU:
                    bot.delete_state(message.from_user.id, message.chat.id)
                    bot.send_message(message.chat.id, 
                        class_instance.message_text,
                        reply_markup=data['main_keyboard'])
                    bot.set_state(message.from_user.id, MyStates.null, message.chat.id) 
                    return
                elif message.text == BACK :
                    bot.send_message(message.chat.id, 
                        class_instance.message_text,
                        reply_markup=data['null_keyboard'])
                    bot.set_state(message.from_user.id, MyStates.one, message.chat.id) 
                    return
                elif class_instance.check_text_in_markup(data['one_keyboard'], message.text):
                    class_instance.second_step(message)
                    class_instance.third_step
                    bot.set_state(message.from_user.id, MyStates.three, message.chat.id)
                    data['class_instance'] = class_instance
                    data['second_keyboard'] = class_instance.markup
                else:
                    raise AttributeError
        except AttributeError:
            data['class_instance'] = class_instance
            bot.set_state(message.from_user.id, MyStates.second, message.chat.id)


@bot.message_handler(state=MyStates.three)
def third_step(message):
    try:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            class_instance = data['class_instance']
            if message.text == MAIN_MENU:
                bot.delete_state(message.from_user.id, message.chat.id)
                bot.send_message(message.chat.id, 
                        class_instance.message_text,
                        reply_markup=data['main_keyboard'])
                bot.set_state(message.from_user.id, MyStates.null, message.chat.id) 
            elif message.text == BACK:
                bot.send_message(message.chat.id, 
                            class_instance.message_text,
                            reply_markup=data['one_keyboard']) 
                bot.set_state(message.from_user.id, MyStates.second, message.chat.id) 
                return
            elif class_instance.check_text_in_markup(data['second_keyboard'], message.text):
                class_instance.third_step(message)
                class_instance.four_step
                bot.set_state(message.from_user.id, MyStates.four, message.chat.id)
                data['class_instance'] = class_instance
                data['three_keyboard'] = class_instance.markup
            else:
                raise AttributeError
    except AttributeError:
        data['class_instance'] = class_instance
        bot.set_state(message.from_user.id, MyStates.three, message.chat.id)
 
class Step:
    
    users = db['users']

    def __init__(self) -> None:
        self.markup = ReplyKeyboardMarkup()

    def null_step(self, message):
        try:
            class_instance = DICT_CLASS[message.text]
            class_instance.button = message.text
            msg = bot.send_message(message.chat.id, 
                                class_instance.message_text,
                                    reply_markup=class_instance.markup)
            # bot.register_next_step_handler(msg, 
            #                                 self.one_step, 
            #                                 class_instance
            #                                 )
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['button_1'] = message.text
        except KeyError:
            if message.text == '/push':
                id = message.chat.id
                if self.users.find_one({'_id':id, 'Push':True}) is None:
                    push = True
                    text = 'Жди уведомлений!'
                else:
                    not push 
                    text = 'Уведомлений не будет!'
                self.users.update_one({'_id':id}, {'$set':{'Push':push}})
            elif message.text == "update" and user_id == message.chat.id:
                mongo.update()
                for name in mass_contry.values():
                    bot.send_message(message.chat.id, f'Обновил {name}')
                    time.sleep(5)
                text = 'Обновил таблицы'
            elif message.text == 'users' and user_id == message.chat.id:
                list_users = [user['Name'] for user in self.users.find()]
                text =  '\n'.join(list_users)
            elif message.text == 'send' and user_id == message.chat.id:
                list_users = [user['_id'] for user in self.users.find()]
                for id in list_users:
                    bot.send_message(id, "Вышло обновление. Жми /start")
            bot.send_message(message.chat.id, text)
            main(message)


    def one_step(self, message, class_instance):
        try:
            if message.text == BACK:
                #return main(message)
                class_instance.markup = self.markup
                message.text = class_instance.button
                return self.null_step(message)
            if class_instance.check_text_in_markup(class_instance.markup, 
                                                   message.text):
                class_instance.button_1 = message.text
                msg = class_instance.one_step(message)
                bot.register_next_step_handler(msg, 
                                                    self.second_step, 
                                                    class_instance,
                                                    )
                return class_instance.second_step

            else:
                raise AttributeError
        except AttributeError:
            return self.one_step(message, class_instance)
            # msg = bot.send_message(message.chat.id,
            #                         class_instance.button,
            #                         reply_markup=class_instance.markup)
            return bot.register_next_step_handler(message, 
                                                self.one_step, 
                                                class_instance,
                                            )
        

    def second_step(self, message, class_instance):
        try:
            if message.text == MAIN_MENU:
                return main(message)
            elif message.text == BACK :
                message.text = class_instance.button
                return self.null_step(message)
            elif class_instance.check_text_in_markup(class_instance.markup_1, message.text):
                msg = class_instance.second_step(message)
                bot.register_next_step_handler(msg, 
                                                    self.third_step, 
                                                    class_instance,
                                                    )
            else:
                raise AttributeError
        except AttributeError:
                return self.one_step(message, class_instance)
                # msg = bot.send_message(message.chat.id,
                #                     class_instance.button_1,
                #                     reply_markup=class_instance.markup)
                # return bot.register_next_step_handler(msg, 
                #                                     self.second_step, 
                #                                     class_instance,
                #                                     )
        
        
    def third_step(self, message, class_instance):
        if message.text == MAIN_MENU:
            return main(message)
        elif message.text == BACK:
            message.text = class_instance.button_1
            return self.one_step(message, class_instance)
        elif class_instance.check_text_in_markup(class_instance.markup_2, message.text):
            msg = class_instance.third_step(message)
            bot.register_next_step_handler(msg, 
                                            self.third_step, 
                                            class_instance,
                                            )
        else:
            msg = bot.send_message(message.chat.id,
                                    class_instance.button,
                                    reply_markup=class_instance.markup)
            return bot.register_next_step_handler(msg, 
                                                self.third_step, 
                                                class_instance,
                                                )


class СhampBot(ABC):

    @abstractmethod
    def __init__(self):
        self.markup = ReplyKeyboardMarkup()
        self.markup.add(BACK)

    @abstractmethod
    def one_step(self):
        self.markup = ReplyKeyboardMarkup(row_width=1)
        self.markup.add(MAIN_MENU, BACK)
        # i = 0
        # while True:
        #     try:
        #         i+=1
        #         bot.delete_message(message.chat.id, message.message_id - i)
        #     except:
        #         break

    @staticmethod
    def check_text_in_markup(markup, message_text):
        for list_row in markup.keyboard:
            for text in list_row:
                if text['text'] == message_text:
                    return True
        return False


class ChampButton(СhampBot):
    message_text = 'Выбери чемпионат'
    button_calendar = 'Календарь🗓'
    button_table = 'Таблица⚽'
    calendar = db['calendar_2022/2023']
    table = db[f'table_2022/2023']

    def __init__(self):
        super().__init__()
        self.markup.add(*mass_contry,row_width=1)
    
    def one_step(self, message):
        super().one_step()
        self.country_button = message.text
        self.champ = ' '.join(self.country_button.split()[:-1])
        self.markup.add(self.button_calendar, 
                        self.button_table,row_width=2)
        return bot.send_message(message.chat.id, 
                                self.country_button, 
                                reply_markup=self.markup)
        
    def second_step(self, message):
        if message.text == self.button_calendar:
            self.third_step = self.tour_button
            return bot.send_message(message.chat.id,
                            '{} Выбери тур, чтобы узнать результаты:'.format(
                    self.country_button
                            ), reply_markup=self.calendar_button())
        else:
            self.third_step = self.team_button
            return bot.send_message(message.chat.id,
                        '{}.Таблица чемпионата!\n\
Выбери команду, чтобы узнать последние результаты'.format(
                    self.country_button),
                        reply_markup=self.table_button()
                        )
      
    
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
            self.markup.add(tour_button.strip())
        return self.markup

    def table_button(self):
        super().one_step()
        j = 1
        for table_stat in self.table.find({'country':
                                           mass_contry[self.country_button]}
                                           ).sort('points',-1):
            button = "{}. | {} |  И: {}  О: {}  M: {}".format(
                        j,
                        table_stat['team'],
                        table_stat['games'],
                        table_stat['points'],
                        table_stat['balls']
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
        
        return bot.send_photo(message.chat.id,
                            self.table.find_one({'team':name_team},
                                                {'logo': 1, '_id': 0})['logo'],
                            #postgr.get_logo(mass_contry[country_button], text),
                            caption='\n\n'.join(list_date),
                            reply_markup=markup,
                            parse_mode="MarkdownV2"
                            )

    
    # Обработка нажатия на кнопку с туром
    def tour_button(self, message):
        tour = message.text.split("|")[0].strip()
        bot.delete_message(message.chat.id, message.message_id)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Главное меню",
                                        callback_data="back"))
        list_date = []
        for match_tour in self.calendar.find({'champ': self.champ, 'tour': tour}).sort('datetime', 1):
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
    news_coll = db['news']
    message_text = 'Новости📰'

    def __init__(self):
        super().__init__()
        for news in News.news_coll.find().limit(50).sort('date', -1):
            title = '{} {}'.format(news['date'].split()[1], news['title']) 
            self.markup.add(title)
    
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
   
    def __init__(self):
        super().__init__()
        buttons = ['Live','Вчера', 'Сегодня', 'Завтра']
        if len(upcoming_match(buttons[0])) != 0:
            self.markup.add(buttons[0])
        self.markup.add(*buttons[1:])
    
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
        pass
    

class Review(СhampBot):
    message_text = 'Выбери обзор'
    video_coll = db['video']

    def __init__(self):
        super().__init__()
        self.markup.add(*list_name_site,row_width=1)
    
    def one_step(self, message):
        super().one_step()
        if message.text == list_name_site[0]:
            query = {}
        else:
            query = {'country':message.text}
        for key in self.video_coll.find(query).sort('date',-1).limit(50):
            self.markup.add(key["desc"])
        return bot.send_message(message.chat.id, 'Выбери обзор',
                            reply_markup=self.markup)

    def second_step(self, message):
        video_ref = self.video_coll.find_one({'desc':message.text})
        return bot.send_message(message.chat.id,
                                "{}\n{}".format(message.text,
                                video_ref['link']))

DICT_CLASS = {'Чемпионаты🏆':ChampButton(),
                'Новости📰':News(),
                'Обзоры⚽':Review(),
                'Ближайшие матчи':UpcomingMatches()}

#bot.enable_save_next_step_handlers(delay=2)

#bot.load_next_step_handlers()

if __name__ == '__main__':
    while True:
        try:
            bot.add_custom_filter(custom_filters.StateFilter(bot))
            bot.infinity_polling()
        except Exception:
            time.sleep(10)
