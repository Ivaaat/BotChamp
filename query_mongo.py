
def champ_pipl(id_champ_field):
    #champ_table в монго коллекция champ
    return [
        {
            '$match': {
                'id': id_champ_field
            }
        }, {
            '$lookup': {
                'from': 'matches', 
                'localField': '_id', 
                'foreignField': 'id_champ', 
                'as': 'games_champ'
            }
        }, {
            '$unwind': '$games_champ'
        }, {
            '$lookup': {
                'from': 'teams', 
                'localField': 'games_champ.id_home_team', 
                'foreignField': '_id', 
                'as': 'home_team'
            }
        }, {
            '$lookup': {
                'from': 'teams', 
                'localField': 'games_champ.id_away_team', 
                'foreignField': '_id', 
                'as': 'away_team'
            }
        }, {
            '$unwind': '$away_team'
        }, {
            '$unwind': '$home_team'
        }, {
            '$project': {
                'teams': [
                    '$home_team.name', '$away_team.name'
                ], 
                'score': '$games_champ.score', 
                'flags': '$games_champ.flags'
            }
        }, {
            '$unwind': {
                'path': '$teams', 
                'includeArrayIndex': 'arrayIndex'
            }
        }, {
            '$group': {
                '_id': '$teams', 
                'points': {
                    '$sum': {
                        '$cond': [
                            {
                                '$eq': [
                                    '$flags.is_played', 0
                                ]
                            }, 0, {
                                '$cond': [
                                    {
                                        '$eq': [
                                            '$score.totalHome', '$score.totalAway'
                                        ]
                                    }, 1, {
                                        '$cond': [
                                            {
                                                '$eq': [
                                                    '$arrayIndex', 0
                                                ]
                                            }, {
                                                '$cond': [
                                                    {
                                                        '$gt': [
                                                            '$score.totalHome', '$score.totalAway'
                                                        ]
                                                    }, 3, 0
                                                ]
                                            }, {
                                                '$cond': [
                                                    {
                                                        '$gt': [
                                                            '$score.totalAway', '$score.totalHome'
                                                        ]
                                                    }, 3, 0
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                }, 
                'goalsScored': {
                    '$sum': {
                        '$cond': [
                            {
                                '$eq': [
                                    '$arrayIndex', 0
                                ]
                            }, '$score.totalHome', '$score.totalAway'
                        ]
                    }
                }, 
                'goalsConceded': {
                    '$sum': {
                        '$cond': [
                            {
                                '$eq': [
                                    '$arrayIndex', 0
                                ]
                            }, '$score.totalAway', '$score.totalHome'
                        ]
                    }
                }, 
                'gamesPlayed': {
                    '$sum': {
                        '$cond': [
                            {
                                '$eq': [
                                    '$flags.is_played', 0
                                ]
                            }, 0, 1
                        ]
                    }
                }, 
                'wins': {
                    '$sum': {
                        '$cond': [
                            {
                                '$eq': [
                                    '$arrayIndex', 0
                                ]
                            }, {
                                '$cond': [
                                    {
                                        '$gt': [
                                            '$score.totalHome', '$score.totalAway'
                                        ]
                                    }, 1, 0
                                ]
                            }, {
                                '$cond': [
                                    {
                                        '$gt': [
                                            '$score.totalAway', '$score.totalHome'
                                        ]
                                    }, 1, 0
                                ]
                            }
                        ]
                    }
                }, 
                'losses': {
                    '$sum': {
                        '$cond': [
                            {
                                '$eq': [
                                    '$arrayIndex', 0
                                ]
                            }, {
                                '$cond': [
                                    {
                                        '$lt': [
                                            '$score.totalHome', '$score.totalAway'
                                        ]
                                    }, 1, 0
                                ]
                            }, {
                                '$cond': [
                                    {
                                        '$lt': [
                                            '$score.totalAway', '$score.totalHome'
                                        ]
                                    }, 1, 0
                                ]
                            }
                        ]
                    }
                }, 
                'draws': {
                    '$sum': {
                        '$cond': [
                            {
                                '$eq': [
                                    '$flags.is_played', 0
                                ]
                            }, 0, {
                                '$cond': [
                                    {
                                        '$eq': [
                                            '$score.totalHome', '$score.totalAway'
                                        ]
                                    }, 1, 0
                                ]
                            }
                        ]
                    }
                }
            }
        }, {
            '$addFields': {
                'goalDifference': {
                    '$subtract': [
                        '$goalsScored', '$goalsConceded'
                    ]
                }
            }
        }, {
            '$sort': {
                'points': -1, 
                'wins': -1, 
                'goalDifference': -1, 
                'goalsScored': -1
            }
        }
    ]

def date_pipl(date_field):
    #date_matches в монго в коллекции date
    return [
        {
            '$match': {
                'date': date_field
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

def pub_pipl(pub_date_field):
    #prev_match в монго в коллекции matches
    return [
        {
            '$match': {
                '$and': [
                    {
                        'pub_date': {
                            '$lt': pub_date_field
                        }
                    }, {
                        'status.label': {
                            '$nin': [
                                'post', 'cans', 'delay', 'dns', 'ntl', 'fin'
                            ]
                        }
                    }
                ]
            }
        }, {
            '$lookup': {
                'from': 'date', 
                'localField': 'id_date', 
                'foreignField': '_id', 
                'as': 'date'
            }
        }, {
            '$project': {
                'date': {
                    '$arrayElemAt': [
                        '$date.date', 0
                    ]
                }
            }
        }
    ]

def name_team_pipl(id_champ, name_team):
    #name_team в монго в коллекции champ
    return [
    {
        '$match': {
            'id': id_champ
        }
    }, {
        '$lookup': {
            'from': 'matches', 
            'localField': '_id', 
            'foreignField': 'id_champ', 
            'as': 'calendar'
        }
    }, {
        '$unwind': {
            'path': '$calendar'
        }
    }, {
        '$lookup': {
            'from': 'teams', 
            'localField': 'calendar.id_home_team', 
            'foreignField': '_id', 
            'as': 'home_team'
        }
    }, {
        '$lookup': {
            'from': 'teams', 
            'localField': 'calendar.id_away_team', 
            'foreignField': '_id', 
            'as': 'away_team'
        }
    }, {
        '$lookup': {
            'from': 'date', 
            'localField': 'calendar.id_date', 
            'foreignField': '_id', 
            'as': 'date'
        }
    }, {
        '$project': {
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
            'date': {
                '$arrayElemAt': [
                    '$date.date', 0
                ]
            }, 
            'status': '$calendar.status', 
            'tour': '$calendar.tour', 
            'score': '$calendar.score'
        }
    }, {
        '$match': {
            '$or': [
                {
                    'home_team': name_team
                }, {
                    'away_team': name_team
                }
            ]
        }
    }, {
        '$match': {
            'status.label': 'fin'
        }
    }
]

def img_pipl(id_champ, name_team):
    #img_team в монго в коллекции champ
    return [
    {
        '$match': {
            'id': id_champ
        }
    }, {
        '$lookup': {
            'from': 'matches', 
            'localField': '_id', 
            'foreignField': 'id_champ', 
            'as': 'calendar'
        }
    }, {
        '$lookup': {
            'from': 'teams', 
            'localField': 'calendar.id_home_team', 
            'foreignField': '_id', 
            'as': 'home_team'
        }
    }, {
        '$project': {
            'home_team': 1
        }
    }, {
        '$unwind': {
            'path': '$home_team'
        }
    }, {
        '$match': {
            'home_team.name': name_team
        }
    }
]

def calendar_pipl(id_champ):
    #start_end_tour в монго в коллекции champ
    return [
    {
        '$match': {
            'id': id_champ
        }
    }, {
        '$lookup': {
            'from': 'matches', 
            'localField': '_id', 
            'foreignField': 'id_champ', 
            'as': 'calendar'
        }
    }, {
        '$unwind': {
            'path': '$calendar'
        }
    }, {
        '$lookup': {
            'from': 'date', 
            'localField': 'calendar.id_date', 
            'foreignField': '_id', 
            'as': 'date'
        }
    }, {
        '$project': {
            'tour': '$calendar.tour', 
            'date': {
                '$arrayElemAt': [
                    '$date.date', 0
                ]
            }, 
            'status': '$calendar.status.label'
        }
    }, {
        '$group': {
            '_id': '$tour', 
            'matches': {
                '$push': '$$ROOT'
            }, 
            'status': {
                '$addToSet': '$status'
            }
        }
    }, {
        '$sort': {
            '_id': 1
        }
    }, {
        '$project': {
            'one': {
                '$first': '$matches.date'
            }, 
            'end': {
                '$last': '$matches.date'
            }, 
            'status': {
                '$first': '$status'
            }
        }
    }
]

def tour_pipl(id_champ, tour):
    #tour_matches в монго в коллекции champ
    return [
    {
        '$match': {
            'id': id_champ
        }
    }, {
        '$lookup': {
            'from': 'matches', 
            'localField': '_id', 
            'foreignField': 'id_champ', 
            'as': 'calendar'
        }
    }, {
        '$unwind': {
            'path': '$calendar'
        }
    }, {
        '$lookup': {
            'from': 'date', 
            'localField': 'calendar.id_date', 
            'foreignField': '_id', 
            'as': 'date'
        }
    }, {
        '$project': {
            'tour': '$calendar.tour', 
            'date': {
                '$arrayElemAt': [
                    '$date.date', 0
                ]
            }, 
            'title': '$calendar.link_title', 
            'time': '$calendar.time', 
            'score': {
                '$ifNull': [
                    '$calendar.score.direct.main', ''
                ]
            }
        }
    }, {
        '$match': {
            'tour': tour
        }
    }, {
        '$group': {
            '_id': '$tour', 
            'matches': {
                '$push': '$$ROOT'
            }
        }
    }
]