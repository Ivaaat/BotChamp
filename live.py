from datetime import timedelta, date
from pymongo import MongoClient

class UpcomingMatches:
    def __init__(self, day = 0) -> None:
        client = MongoClient()
        self.db = client['championat']
        self.day = day
        #self.matches = self.db[str(date.today() + timedelta(self.day))].find_one({}, {'_id':0})
        pipl = [
    {
        '$match': {
            'date': str(date.today() + timedelta(self.day))
        }
    }, {
        '$lookup': {
            'from': 'matches', 
            'localField': '_id', 
            'foreignField': 'id_date', 
            'as': 'matches'
        }
    }, {
        '$unwind': '$matches'
    }, {
        '$lookup': {
            'from': 'champ', 
            'localField': 'matches.id_champ', 
            'foreignField': '_id', 
            'as': 'name_champ'
        }
    }, {
        '$lookup': {
            'from': 'teams', 
            'localField': 'matches.id_home_team', 
            'foreignField': '_id', 
            'as': 'home_team'
        }
    }, {
        '$lookup': {
            'from': 'teams', 
            'localField': 'matches.id_away_team', 
            'foreignField': '_id', 
            'as': 'away_team'
        }
    }, {
        '$match': {
            'name_champ.priority': {
                '$gte': 100
            }
        }
    }, {
        '$project': {
            'name_champ': 1, 
            'matches': {
                'status': '$matches.status', 
                'result': '$matches.result', 
                'score': '$matches.score', 
                'time': '$matches.time', 
                'flags': '$matches.flags', 
                'roundForLTAndMC': '$matches.roundForLTAndMC', 
                'home_team': {
                    '$arrayElemAt': [
                        '$home_team.name', 0
                    ]
                }, 
                'away_team': {
                    '$arrayElemAt': [
                        '$away_team.name', 0
                    ]
                }, 
                'goal1': '$matches.result.detailed.goal1', 
                'goal2': '$matches.result.detailed.goal2', 
                'full_res': '$matches.result.full_res'
            }
        }
    }, {
        '$group': {
            '_id': {
                '$arrayElemAt': [
                    '$name_champ.name_tournament', 0
                ]
            }, 
            'matches': {
                '$push': '$matches'
            }
        }
    }
]
        self.tournaments = self.db['date'].aggregate(pipl)
        #self.tournament_top = [champ for champ in self.matches.values() if champ['priority'] >= 100]
        self.list_matches = []


    def get_matches(self):
        for tournament in self.tournaments:
            for match in tournament['matches']:
                self.serializer_match(tournament['_id'], match)
        return self.list_matches
        
    
    def serializer_match(self, tournament, match):
        name_champ = '{}, {}'.format(tournament, match['roundForLTAndMC']) 
        if name_champ not in self.list_matches:
            self.list_matches.append(name_champ)
        try:
            match_result = '{} : {}'.format(match['goal1'],
                                            
                                            match['goal2']) 
            full_res = match['result']['full_res']
        except KeyError:
            match_result = ''
            full_res = ''
        if match['flags']['live'] == 1:
            time_match =", {} Live".format(match['status']['name']) 
        elif match['flags']['is_played'] :
            time_match = ''
        else:
            time_match =", {} ".format(match['time']) 
        result = '| {} - {} {} | {} {}'.format(
                    match['home_team'],
                    match['away_team'],
                    match_result,
                    time_match,
                    full_res)
        self.list_matches.append(result)
    

class Live(UpcomingMatches):
    def __init__(self) -> None:
        super().__init__()

    def get_matches(self):
        for tournament in self.tournaments:
            for match in tournament['matches']:
                if match['flags']['live'] != 1:
                    continue
                self.serializer_match(tournament['_id'], match)
        return self.list_matches
    
    def serializer_match(self, tournament, match):
        name_champ = '{}, {}'.format(tournament, match['roundForLTAndMC']) 
        if name_champ not in self.list_matches:
            self.list_matches.append(name_champ)
        time_match =", {} Live".format(match['status']['name']) 
        result = '| {} - {}, {} : {} | {}'.format(
                    match['home_team'],
                    match['away_team'],
                    match['goal1'],
                    match['goal2'],
                    time_match,
                    )
        self.list_matches.append(result)

class Today(UpcomingMatches):
    def __init__(self) -> None:
        super().__init__(1)

    def serializer_match(self, tournament, match):
        name_champ = '{}, {}'.format(tournament, match['roundForLTAndMC']) 
        if name_champ not in self.list_matches:
            self.list_matches.append(name_champ)
        result = '| {} - {} | {}'.format(
                    match['home_team'],
                    match['away_team'],
                    match['status']['name'],
                    )
        self.list_matches.append(result)

class Tomorrow(UpcomingMatches):
    def __init__(self) -> None:
        super().__init__()


class Yesterday(UpcomingMatches):
    def __init__(self) -> None:
        super().__init__(-1)

    def serializer_match(self, tournament, match):
        name_champ = '{}, {}'.format(tournament, match['roundForLTAndMC']) 
        if name_champ not in self.list_matches:
            self.list_matches.append(name_champ)
        try:
            result = '| {} - {}, {} : {} | '.format(
                        match['home_team'],
                        match['away_team'],
                        match['goal1'],
                        match['goal2'],
                        )
            self.list_matches.append(result)
        except:
            result = '| {} - {} | {}'.format(
                        match['home_team'],
                        match['away_team'],
                        'Не сыгран')
            self.list_matches.append(result)

    


def upcoming_match(button):
    button_name = {'Live':Live, 
                   'Сегодня':Tomorrow, 
                   'Вчера': Yesterday, 
                   'Завтра':Today
                   }
    day = button_name[button]()
    return day.get_matches()


