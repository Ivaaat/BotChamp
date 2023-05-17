import xpath
import requests
from lxml import html
from config import parse_site
from config import User_agent


def parent_word(month):
    if month.split()[1].endswith("ь"):
        month = month.replace('ь', 'я', 1)
    elif month.split()[1].endswith("й"):
        month = month.replace('й', 'я', 1)
    else:
        month = month.replace('т', 'та', 1)
    return month


class Championat:
    def __init__(self, country):
        self.country = country
        self.url = parse_site
        self.url_calendar = ""
        self.calendar = {}
        self.list_ref_logo = []
        if self.country == "":
            self.country = "germany"
        self.url_championat = f'{self.url}/football/_{self.country}.html'
        self.sess = requests.Session()
        self.sess.headers.update(User_agent)
        response = self.sess.get(self.url_championat)
        self.response_text = response.text
        self.tree = html.fromstring(self.response_text)


class Calendar(Championat):
    def __init__(self, country):
        super().__init__(country)
        parse_calendar = self.tree.xpath(xpath.parse_text)
        self.url_calendar = '{}{}'.format(parse_site, parse_calendar[2])
        response = self.sess.get(self.url_calendar)
        self.response_text = response.text
        self.tree = html.fromstring(self.response_text)

    def get_date(self):
        return [" ".join(date.replace('.', '-').split()) for date in
                self.tree.xpath(xpath.date_match)]

    def get_tour(self):
        return self.tree.xpath(xpath.num_tour)

    def get_matches(self):
        return [match.split(",")[0] for match in self.tree.xpath(
            xpath.games)]

    def get_result(self):
        return [result.replace('– : –','').strip() for result in
                self.tree.xpath(xpath.result)]


class Table(Championat):
    def __init__(self, country):
        super().__init__(country)
        self.treelogo = self.tree
        parse_table = self.tree.xpath(xpath.parse_text)
        url_table = f'{parse_site}{parse_table[3]}'
        response = self.sess.get(url_table)
        self.response_text = response.text
        self.tree = html.fromstring(self.response_text)
        self.dict_table = {}

    def get_name(self):
        names_teams = self.tree.xpath(xpath.name_xpath)
        return names_teams[:int(len(names_teams)/3)]

    def get_points(self):
        num_points = [ball.strip() for ball in self.tree.xpath(
            xpath.points)]
        return num_points[:int(len(num_points)/3)]

    def get_games(self):
        num_games = self.tree.xpath(xpath.game_table)
        return num_games[:int(len(num_games)/3)]

    def get_wins(self):
        num_wins = [win.strip() for win in self.tree.xpath(xpath.wins)]
        return num_wins[:int(len(num_wins)/3)]

    def get_draw(self):
        num_draw = [
            draw.strip() for draw in self.tree.xpath(xpath.draws)]
        return num_draw[:int(len(num_draw)/3)]

    def get_loss(self):
        num_loss = [
            lose.strip() for lose in self.tree.xpath(xpath.loses)]
        return num_loss[:int(len(num_loss)/3)]

    def get_balls(self):
        num_balls = [
            ball.strip() for ball in self.tree.xpath(xpath.balls)]
        return num_balls[:int(len(num_balls)/3)]

    def get_six_match(self):
        six_match = self.tree.xpath('//td[10]/a/span/@title')
        return six_match[:int(len(six_match)/3)]

    def get_logo(self):
        return self.treelogo.xpath(xpath.logo_ref)

