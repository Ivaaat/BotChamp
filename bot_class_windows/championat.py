from xpath_ref import *
import requests
from lxml import html
from constants import mass_contry, mass_review, parse_site
import time
from pymongo import MongoClient
from datetime import datetime, timedelta
import locale
from PIL import Image,  ImageFilter, ImageEnhance
from PIL import ImageFont
from PIL import ImageDraw
from io import BytesIO

locale.setlocale(locale.LC_ALL, "")

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
    })


client = MongoClient()
db = client['json_champ']
users_col = db['users']


class Championat:
    def __init__(self,country = "") :
        self.country = country
        self.url = parse_site
        self.url_calendar = ""
        self.response_text = ""
        self.tree = ""
        self.calendar = {}
        #self.dict_table = {}
        self.tour = 1
        self.num_tour = []
        self.list_match = []
        self.list_datematch = []
        self.list_result = []
        self.list_games = []
        self.list_teams = []
        self.list_points = []
        self.list_result_six_matches = []
        self.list_ref_logo = []
        
        if self.country == "":
            self.country = "germany"
            
        self.url_championat = f'{self.url}/football/_{self.country}.html'

        response = sess.get(self.url_championat)
        self.response_text = response.text
        self.tree = html.fromstring(self.response_text)
    '''
    def get_response_championat(self):
        response = sess.get(self.url_championat)
        self.response_text = response.text
        self.tree = html.fromstring(self.response_text)
    '''
    



    def get_response_calendar(self):
        #response = sess.get(self.url_championat)
        #tree = html.fromstring(response.text)
        #parse_text = tree.xpath(parse_xpath_text)
        parse_calendar = self.tree.xpath(parse_xpath_text)
        self.url_calendar = f'{parse_site}{parse_calendar[0]}calendar'
        response = sess.get(self.url_calendar)  
        self.response_text = response.text
        self.tree = html.fromstring(self.response_text)

    def get_match(self):
        list_match = self.tree.xpath(parse_xpath_match)
        for i in range(0,len(list_match),2):
            self.list_match.append(' - '.join(list_match[i:i + 2]))
        return self.list_match
    
    def get_result(self):
        list_result = self.tree.xpath(parse_xpath_result)
        for i in range(0,len(list_result)):
            self.list_result.append(list_result[i].strip())
    
    def get_date(self):
        list_datematch = self.tree.xpath(date_xpath_match)
        for i in range(0,len(list_datematch)):
            self.list_datematch.append (" ".join(list_datematch[i].split()))
        return self.list_datematch

    def get_tour(self):
        list_tour = self.tree.xpath(num_xpath_tour)
        self.num_tour = list_tour
        self.tour = int(((len(set(list_tour))/2) + 1)/2)
        
    
    def request_calendar(self):
        tree = html.fromstring(self.response)
        parse_text = tree.xpath(parse_xpath_text)
        url = f'{parse_site}{parse_text[0]}calendar'
        response = sess.get(url)
        return response.text

    def get_teams(self):
        self.list_teams = self.tree.xpath(teams_xpath)

    def get_games(self):
         self.list_games = self.tree.xpath(games_xpath)

    def get_points(self):
        self.list_points = self.tree.xpath(points_xpath)

    def get_result_six_matches(self):
        self.list_result_six_matches = self.tree.xpath(results_xpath)

    def get_logo(self):
        self.list_ref_logo = self.tree.xpath(logo_ref_xpath)

        

    def get_keyboard():
        pass


            
class Calendar(Championat):
    def get_calendar(self):
        self.get_response_calendar()
        self.get_date()
        self.get_match()
        self.get_result()
        self.get_tour()
        for i in range(0,len(self.num_tour),self.tour):
            name_date = self.list_datematch[i:self.tour+i][0][:10] + '-' + self.list_datematch[i:self.tour+i][self.tour-1][:10]
            if '– : –' not in self.list_result[i:self.tour+i][self.tour-1]  :
                self.calendar['Тур ' + str(self.num_tour[i]) +' | '+ name_date +'| закончен'] =[
                                                            self.list_datematch[i:self.tour+i],
                                                            self.list_match[i:self.tour+i],
                                                            self.list_result[i:self.tour+i]
                                                            ]
            else:
                self.calendar['Тур ' + str(self.num_tour[i]) +' | '+ name_date] =[
                                                            self.list_datematch[i:self.tour+i],
                                                            self.list_match[i:self.tour+i],
                                                            self.list_result[i:self.tour+i]
                                                            ]
        return self.calendar


class Table(Championat):
    def __init__(self,country):
        super().__init__(country)
        self.dict_table = {}
    def get_table(self):
        self.get_teams()
        self.get_games()
        self.get_points()
        self.get_result_six_matches()
        self.get_logo()
        results = []
        num_match = 6
        for i in range(0, len(self.list_result_six_matches), num_match):
            results.append(self.list_result_six_matches[i : i + num_match])
        #картинки эмблем команд
        for i in range(len(self.list_teams)):
            self.dict_table[self.list_teams[i]] = {
            'Игры':int(self.list_games[i]),
            'Очки':int(self.list_points[i].strip()),
            'Последние результаты\n': '\n\n'.join(results[i]), 
            'Лого': self.list_ref_logo[i]
            }
        return self.dict_table
    

class Team(Championat):
    def __init__(self, name_team, dict_table_team):
        self.name_team = name_team
        self.dict_table_team = dict_table_team
        self.result_title = ""
        self.logo_list = []
        self.logo_ref_team = ""
    def get_logo(self):
        url1 = f'{parse_site}' + self.dict_table_team[self.name_team]['Лого']
        response1 = sess.get(url1)
        tree = html.fromstring(response1.text)
        self.logo_list = tree.xpath(logo_xpath)
        self.logo_ref_team = self.logo_list[0]
        self.result_title +=  '\n' + 'Последние результаты:\n' + self.dict_table_team[self.name_team]['Последние результаты\n']
        
    def get_calendar():
        pass
    def get_table():
        pass



def add_db(name, name_champ):
    country =  db[name]
    calendar = Calendar(name)
    calendar.get_response_calendar()
    calendar.get_date()
    calendar.get_match()
    calendar.get_result()
    calendar.get_tour()
    table = Table(name)
    table.get_table()
    dac = [calendar.num_tour[i] + " " + calendar.list_datematch[i] + " | " + calendar.list_match[i] + " | " + calendar.list_result[i]  for i in range(len(calendar.num_tour))]
    dac.sort(key = sortByAlphabet)
    dict_champ = {}
    #logo = {}
    dict_champ['Чемпионат'] = name_champ
    for i, name_team in enumerate(table.list_teams):
        games = [dac[i][2:].strip() for i in range(len(dac)) if name_team in dac[i]]
        # url = f'{parse_site}' + table.list_ref_logo[i]
        # response = sess.get(url)
        # tree = html.fromstring(response.text)
        # logo_list = tree.xpath(logo_xpath)
        dict_champ[name_team]={
                            'Таблица':{
                                        "Очки" : table.list_points[i],
                                        "Игры": table.list_games[i]
                                    },

                            'Календарь': games,
        }
        #logo[name_team] = logo_list[0]
        #country.update_one({"Чемпионат": '2022/2023'}, {'$set':{'Лого':{name_team:logo_list[0]}}})
        #country.update_one({"Чемпионат": '2022/2023'}, {'$set':{dict_champ[name_team]['Таблица']["Очки"]:table.list_points[i]}})
    #country.update_one({"Чемпионат": '2022/2023'}, {'$set':dict_champ,'$set':{'Лого':logo}})
    country.update_one({"Чемпионат": '2022/2023'}, {'$set':dict_champ})
    get_cal(name, name_champ)

def get_logo(db_name, name):
    country =  db[db_name]
    logo = country.find_one({"Чемпионат": '2022/2023'})
    try:
        return logo["Лого"][name]
    except KeyError:
        return logo["Лого"]['Шальке-04']
def get_cal(name, name_champ):
    country =  db[name]
    calendar = country.find_one({"Чемпионат": name_champ})
    i = 0
    asd = {}
    for j in range(40):
        try:
            list_table = []
            for team, stat in calendar.items():
                if team not in ['_id','Чемпионат','Календарь','Лого']:
                        table_str = '{}'.format(stat['Календарь'][j])
                        if table_str in list_table:
                            continue
                        list_table.append(table_str)
            i+=1
            list_table.sort(key = lambda date: datetime.strptime(sort_date(date), '%d-%m-%Y %H:%M'))
            for fdf in list_table:
                if fdf.endswith('– : –'):
                    ends = False
                    break
                ends = True
            asd[f'Тур {i}'] = {'Матчи':list_table,
                                'start':datetime.strptime(sort_date(list_table[0].split('|')[0].replace('.','-').strip()), '%d-%m-%Y %H:%M'),
                                'end': datetime.strptime(sort_date(list_table[len(list_table) - 1].split('|')[0].replace('.','-').strip()), '%d-%m-%Y %H:%M'),
                                'Закончен':ends,
                                            }
        except IndexError:
            break
    country.update_one({"Чемпионат": '2022/2023'}, {'$set':{'Календарь':asd}})
    return asd


def sortByAlphabet(inputStr):
    return int(inputStr[:2])

def sort_date(date):
    if len(date.split("|")[0].split()) == 1:
        date = date.split("|")[0].replace('.','-') + " 23:59"
        return date.strip()
    return date.split('|')[0].replace('.','-').strip()

def get_tab(name):
    country =  db[name]
    table = country.find_one({"Чемпионат": '2022/2023'})
    i = 1
    dict_table = {}
    try:
        for team, stat in table.items():
            if team not in ['_id','Чемпионат','Календарь','Лого']:
                i+=1
                asd =[teams for teams in stat['Календарь'] if not teams.endswith("– : –")]
                dict_table[team] = {
                'Игры':stat['Таблица']['Игры'],
                'Очки':stat['Таблица']['Очки'],
                'Последние результаты\n': asd[len(asd) - 6:], 
                'Лого': table['Лого'][team]
                }
        return dict_table
    except Exception as e:
            print(e)
            print(e)

def get_next_date(name):
    country =  db[name]
    calendar = country.find_one({"Чемпионат": '2022/2023'})
    now = datetime.now()
    date_min = []
    for tour in calendar['Календарь'].values():
        if tour['Закончен']:
            continue
        for date in tour['Матчи']:
            try:
                date_match = datetime.strptime(date.split('|')[0].replace('.', '-').strip(), '%d-%m-%Y %H:%M')
            except Exception:
                date_match = datetime.strptime(date.split()[0].replace('.', '-').strip() + ' 23:59', '%d-%m-%Y %H:%M')
            if date.endswith('– : –') and now < date_match:
                if date_match not in date_min:
                    date_min.append(date_match)
    date_min.sort()
    return date_min[0]

def get_start_end_tour(name, next_date, rgb=(255,255,255),name_champ=""):
    country =  db[name]
    calendar = country.find_one({"Чемпионат": '2022/2023'})
    for name_tour, tour in calendar['Календарь'].items():
        if tour['Закончен']:
            continue
        next_date = tour['end']
        if next_date == tour['start']:
        #if next_date.date() == tour['start'].date():
            dict_match = {}
            for name_match in tour['Матчи']:
                date_match = datetime.strptime(name_match.split('|')[0].split()[0].replace('.', '-'), '%d-%m-%Y').strftime('%d %B, %A').upper()
                time_match = name_match.split('|')[0].split()[1]
                if 'Шальке' in name_match:
                    asdx = name_match.split('|')[1].strip().replace('-', ' ',1)
                    #match = asdx.replace('-', time_match)
                    clear_name = asdx.split("-")
                    
                else:
                    #match = name_match.split('|')[1].strip().replace('-', time_match)
                    clear_name = name_match.split('|')[1].split("-")
                if date_match not in dict_match:
                    list_match_logo = []
                list_match_logo.append(time_match)
                for name_team in clear_name:
                    list_match_logo.append({name_team.strip() : get_logo(name, name_team.strip())})
                dict_match[date_match] = list_match_logo
        #elif datetime.now() > tour['end']:
        elif next_date == tour['end']:
            dict_match = {}
            for name_match in tour['Матчи']:
                date_match = datetime.strptime(name_match.split('|')[0].split()[0].replace('.', '-'), '%d-%m-%Y').strftime('%d %B, %A').upper()
                if date_match.split(",")[0].endswith("Ь"):
                    date_match = date_match.replace('Ь','Я', 1)
                elif date_match.split(",")[0].endswith("Й"):
                    date_match = date_match.replace('Й','Я', 1)
                else:
                    date_match = date_match.replace('Т','ТА', 1)
                results_match = name_match.split('|')[2].strip()
                if 'Шальке' in name_match:
                    asdx = name_match.split('|')[1].strip().replace('-', ' ',1)
                    clear_name = asdx.split("-")
                else:
                    clear_name = name_match.split('|')[1].split("-")
                if date_match not in dict_match:
                    list_match_logo = []
                list_match_logo.append(results_match)
                for name_team in clear_name:
                    list_match_logo.append({name_team.strip() : get_logo(name, name_team.strip())})
                dict_match[date_match] = list_match_logo
        else:
            continue
        folder_name = 'bot_class_windows'
        #img = Image.open(f"pic\{name}.png")
        img = Image.open(f"{folder_name}\pic\\IdNH9O5FXe.jpg")
        rez = len(tour['Матчи']) + len(dict_match)
        font = ImageFont.truetype(f"{folder_name}\\ttf\gilroy-black.ttf", 30)
        sadcx = font.getlength(max(calendar.keys(), key=lambda i:len(i)))
        #print(max(calendar.keys(), key=lambda i:len(i)))
        img = img.resize((2 * int(sadcx) + 400 , rez * 50 + 105))
        draw = ImageDraw.Draw(img)
        logo_champ = Image.open(f"{folder_name}\pic\{name}.png")
        param_resize = (100,100)
        logo_champ = logo_champ.resize(param_resize)
        img.paste(logo_champ, (0, 0), logo_champ)
        #img.paste(logo_champ, (img.width-param_resize[0], 0), logo_champ)
        #img.paste(logo_champ, (0, img.height - param_resize[0]), logo_champ)
        img.paste(logo_champ, (img.width-param_resize[0], img.height - param_resize[0]), logo_champ)
        label = "@Champ_footbaall"
        _, _, w, h = draw.textbbox((0, 0), label, font=font)
        pic_channel = Image.new('L', (w, h))
        ImageDraw.Draw(pic_channel).text((0, 0), label, fill=150, font=font)
        pic_channel1 = pic_channel.rotate(90, resample=Image.BICUBIC, expand=True)
        #for o in range(2):
            #img.paste((0, 0, 0), (30, o * int(font.getlength(label)) + 100 + 50 * o), pic_channel1)
            #img.paste((0, 0, 0), (img.width - 60, o *int(font.getlength(label)) + 100 + 50 * o), pic_channel1)\
        img.paste((0, 0, 0), (30, 105), pic_channel1)
        #img.paste((0, 0, 0), (img.width - 60, int(img.height/2) -int(font.getlength(label)) - rez), pic_channel1)
        #img.paste((0, 0, 0), (30, int(img.height/2) + rez), pic_channel1)
        img.paste((0, 0, 0), (img.width - 60,img.height - int(font.getlength(label)) - 105), pic_channel1)

        font1 = ImageFont.truetype(f"{folder_name}\\ttf\gilroy-black.ttf", 60)
        ImageDraw.Draw(pic_channel).text((0, 0), label, fill=100, font=font1)
        img.paste((0, 0, 0), (int(img.width-font1.getlength(label)/2), int(img.height-font1.get(label)/2)), pic_channel)

        #i = 0
        #img.paste((0, 0, 0), (int((img.width-w)/2), i), pic_channel)
        j = 5
        draw.text((int((img.width-font.getlength(name_champ)))/2, j), name_champ, rgb, font=font, align = "center")
        j = 55
        _, _, w, _ = draw.textbbox((0, 0), name_tour, font=font)
        draw.text((int((img.width-w))/2, j), name_tour , rgb, font=font, align = "center")
        logo_width = 50
        logo_height = 50
        shift = 5
        for date, match_url in dict_match.items():
            j += 50
            _, _, w, _ = draw.textbbox((0, 0), date, font=font)
            draw.text((int((img.width-w))/2, j), date , (0,0,0), font=font, align = "center")
            e = 0
            for match_list in match_url:
                font = ImageFont.truetype(f"{folder_name}\\ttf\gilroy-black.ttf", 30)
                try:
                    for match, url in match_list.items():
                        if e == 0:
                            #response_left_team = sess.get(url)
                            #logo_left_team = Image.open(BytesIO(response_left_team.content))
                            logo_left_team = Image.open(f"{folder_name}\pic\\football\{name}\{match}.png")
                            logo_left_team = logo_left_team.resize ((logo_width,logo_height))
                            coord_x_left = int((img.width/2)-time_width)
                            _, _, w, _ = draw.textbbox((0, 0), match, font=font)
                            draw.text((coord_x_left - w - shift, j), match, rgb, font=font, align = "center")
                            img.paste(logo_left_team, (coord_x_left - logo_width - w - shift, j - 5), logo_left_team )
                            e = 1
                        elif e == 1:
                            #response_right_team = sess.get(url)
                            #logo_right_team = Image.open(BytesIO(response_right_team.content))
                            logo_right_team = Image.open(f"{folder_name}\pic\\football\{name}\{match}.png")
                            logo_right_team = logo_right_team.resize ((logo_width,logo_height))
                            coord_x_right = int((img.width/2)+time_width)
                            _, _, w, _ = draw.textbbox((0, 0), match, font=font)
                            draw.text((coord_x_right + shift, j), match , rgb, font=font, align = "center")
                            img.paste(logo_right_team, (coord_x_right + w + shift, j - 5), logo_right_team)
                            e = 0
                except Exception:
                        j += 50
                        font = ImageFont.truetype(f"{folder_name}\\ttf\gilroy-black.ttf", 25)
                        _, _, w, _ = draw.textbbox((0, 0), match_list, font=font)
                        draw.text((int((img.width-w))/2, j), match_list , rgb, font=font, align = "center")
                        time_width = w/2
        #img.paste((0, 0, 0), (int((img.width-font.getlength(label))/2), j + 50), pic_channel)
        img.save(f'{folder_name}\pic\\football\{name}1.png')
        img.show()
        return img

#get_start_end_tour('italy', get_next_date('italy'), name_champ = "Серия А, Чемпионат Италии")
#get_start_end_tour('russiapl', get_next_date('russiapl'),name_champ ="РПЛ, Чемпионат России")
#get_start_end_tour('germany', get_next_date('germany'), name_champ = "Бундеслига, Чемпионат Германии")
#get_start_end_tour('spain', get_next_date('spain'), name_champ="Ла Лига, Чемпионат Испании")
#get_start_end_tour('england', get_next_date('england'), name_champ='АПЛ, Чемпионат Англии')
#get_start_end_tour('france', get_next_date('france'), name_champ="Лига 1, Чемпионат Франции")

def news_pic(logo_news, text_news):
    folder_name = 'bot_class_windows'
    response_left_team = sess.get(logo_news)
    news_pic = Image.open(BytesIO(response_left_team.content))
    news_pic = news_pic.resize ((735,490))
    news_pic.convert("RGBA")
    enhancer = ImageEnhance.Brightness(news_pic)
    news_pic = enhancer.enhance(0.65)
    draw = ImageDraw.Draw(news_pic)
    font_size = 35
    font = ImageFont.truetype(f"{folder_name}\\ttf\gilroy-black.ttf", font_size)
    _, _, w, h = draw.textbbox((0, 0), text_news, font=font)
    if w > news_pic.width:
        list_text= []
        list_text1 = text_news.split()
        a = 4
        for j in range(0,len(list_text1),4):
            list_text.append(' '.join(list_text1[j:a]))
            a+=4
        i = 0
        for text in list_text:
            _, _, w, h = draw.textbbox((0, 0), text, font=font)
            draw.text((int((news_pic.width-w))/2, (int((news_pic.height-h))/2) + i), text, font=font, align = "center")
            i+=font_size
        return news_pic
    list_symb = ['.', ',', '-']
    for symb in list_symb:
        if text_news.find(symb) != -1:
            list_text = text_news.split(symb, 1)
            i = 0
            for text in list_text:
                _, _, w, h = draw.textbbox((0, 0), text, font=font)
                draw.text((int((news_pic.width-w))/2, (int((news_pic.height-h))/2) + i), text, font=font, align = "center")
                i+=font_size
            return news_pic
    draw.text((int((news_pic.width-w))/2, int((news_pic.height-h))/2), text_news, font=font, align = "center")
    return news_pic
    