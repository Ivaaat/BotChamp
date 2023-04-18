import psycopg2.errorcodes
from championat import Calendar, Table
import time
conn = psycopg2.connect(dbname="champ", user="postgres", password="qwerty$", host="127.0.0.1")
cursor = conn.cursor()

conn.autocommit = True


def add_calendar(name):
    calendar = Calendar(name)
    tours = calendar.get_tour()
    dates = calendar.get_date()
    matches = calendar.get_matches()
    results = calendar.get_result()
    for i, j in enumerate(tours):
        tour = f"Тур {j}"
        try:
            calend = [tour,
                    matches[i],
                    dates[i],
                    results[i],
                    results[i] != ""
            ]
            cursor.execute(
                f"""INSERT INTO calendar_{name} ( 
                                    tour,
                                    matches,
                                    dates,
                                    results,
                                    ends
                                    )
                VALUES (%s,%s,%s,%s,%s)""",calend
                )
        except psycopg2.errors.UniqueViolation:
            calend.append(calend[1])
            calend.remove(calend[1])
            cursor.execute(
                f"""UPDATE calendar_{name} SET  
                                    tour = %s,
                                    dates = %s,
                                    results = %s,
                                    ends = %s
                                    WHERE matches = %s AND ends <> True
                                    """,calend
                )
        except psycopg2.errors.UndefinedTable:
            cursor.execute(f"""CREATE TABLE calendar_{name} (
                    tour TEXT , 
                    matches TEXT PRIMARY KEY,
                    dates TEXT,
                    results TEXT,
                    ends boolean
                    )""")
            add_calendar(name)
    time.sleep(5)


def get_calendar(name):
    cursor.execute(f"SELECT DISTINCT tour FROM calendar_{name}")
    match_from_calendar = {}
    for i in range(1, cursor.rowcount + 1):
        cursor1 = conn.cursor()
        cursor1.execute(f"""SELECT *
                            FROM calendar_{name} 
                            WHERE tour = %s
                            ORDER BY dates""",(f'Тур {int(i)}',))
        calend = cursor1.fetchall()
        matches= [' | '.join((match[2], match[1], match[3]))  for match in calend]
        end_match = [ends[4] for ends in calend]
        match_from_calendar[calend[0][0]] = {'Матчи': matches,
                                            'start':calend[0][2],
                                            'end':calend[-1][2],
                                            'Закончен': not False in end_match 
                                                                }
    cursor1.close()
    return match_from_calendar


def add_table(name):
    table = Table(name)
    logo_60x60 =  table.get_logo()
    logo = [link.replace('60x60', '300x300') for link in logo_60x60]
    name_team = table.get_name()
    points_stat = table.get_points()
    games_stat = table.get_games()
    wins_stat = table.get_wins()
    loses_stat = table.get_loss()
    draw_stat = table.get_draw()
    balls_stat = table.get_balls()
    for i in range(len(points_stat)):
        try:
            table = [name_team[i],
                    points_stat[i],
                    games_stat[i],
                    wins_stat[i],
                    loses_stat[i],
                    draw_stat[i],
                    balls_stat[i],
                    logo[i]]
            cursor.execute(
                f"""INSERT INTO {name} ( 
                                    team,
                                    points,
                                    games,
                                    win,
                                    lose,
                                    draw,
                                    balls,
                                    logo) 
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",table
                )
        except psycopg2.errors.UndefinedColumn:
            cursor.execute(f'ALTER TABLE {name} ADD COLUMN logo TEXT')
            add_table(name)
        except psycopg2.errors.UniqueViolation:
            table[7] = table[0]
            table.remove(table[0])
            cursor.execute(f"""UPDATE {name} SET
                    points = %s,
                    games = %s,
                    win = %s,
                    lose = %s,
                    draw = %s,
                    balls = %s
                    WHERE team = %s
                    """, table)
                    
        except psycopg2.errors.UndefinedTable:
            cursor.execute(f"""CREATE TABLE {name} (
                    team TEXT PRIMARY KEY, 
                    points VARCHAR(2),
                    games VARCHAR(2),
                    win VARCHAR(2),
                    lose VARCHAR(2),
                    draw VARCHAR(2),
                    balls VARCHAR(8),
                    logo TEXT)""")
            add_table(name)
    time.sleep(5)


def get_table(name):
    cursor.execute(f'SELECT team, games, points, balls FROM {name}')
    table_stat: dict = {}
    for stats in cursor:
        cursor1 = conn.cursor()
        query = (f"%{stats[0]}%",)
        cursor1.execute(f"""SELECT 
        dates, 
        matches, 
        results 
        FROM calendar_{name} WHERE matches LIKE %s AND ends """, query)
        calendar = cursor1.fetchall()[-6:]
        table_stat[stats[0]] = stats[1],\
                                stats[2], \
                                stats[3], \
                                [' | '.join((param[0], 
                                            param[1],
                                            param[2])) for param in calendar]
        cursor1.close()
    return table_stat


def get_logo(name, query):
    cursor.execute(f"SELECT logo FROM {name} WHERE team = %s",(query,))
    logo, = cursor.fetchone()
    return logo        
