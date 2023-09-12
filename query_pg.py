create_table_champ = '''CREATE TABLE champ (
id serial PRIMARY KEY,
name_tournament TEXT , 
priority INT,
img TEXT,
id_old int UNIQUE,
link TEXT)'''

create_table_date = '''CREATE TABLE date (
                            id serial PRIMARY KEY,
                            date TEXT UNIQUE)'''

create_table_teams = '''CREATE TABLE teams (
id serial PRIMARY KEY,
name TEXT , 
img TEXT,
id_old int UNIQUE)'''

create_table_matches = '''CREATE TABLE matches (
                            id serial PRIMARY KEY,
                            id_old int UNIQUE,
                            section TEXT , 
                            link TEXT,
                            time TEXT,
                            groups JSON,
                            flags JSON,
                            result JSON,
                            status JSON,
                            pub_date timestamp,
                            score JSON,
                            total_home int,
                            total_away int,
                            roundForLTAndMC TEXT,
                            tour int,
                            periods JSON,
                            time_str TEXT,
                            link_title TEXT,
                            id_date INTEGER REFERENCES date(id),
                            id_champ INTEGER REFERENCES champ(id),
                            id_home_team INTEGER REFERENCES teams(id),
                            id_away_team INTEGER REFERENCES teams(id)
                            )'''

create_index = '''CREATE INDEX date_idx ON matches (id_date)
CREATE INDEX champ_idx ON matches (id_champ)
CREATE INDEX away_team_idx ON matches (id_away_team)
CREATE INDEX home_team_idx ON matches (id_home_team)'''

select_tour_calendar = '''SELECT home_team.name as hteam, away_team.name as ateam, mt.score->>'totalHome' as totalHome, mt.score->>'totalAway' as totalAway   FROM champ
                join matches as mt on champ.id = mt.id_champ
                join teams as home_team on mt.id_home_team = home_team.id
                join teams as away_team on mt.id_away_team = away_team.id
                where champ.id_old = (%s) and mt.tour = (%s)
                order by mt.pub_date'''

select_champ_table = '''SELECT
    teams.name,
    COUNT(matches.score) AS games,
    SUM(CASE WHEN matches.total_home > matches.total_away AND matches.id_home_team = teams.id THEN 1 ELSE 0 END) +
    SUM(CASE WHEN matches.total_away > matches.total_home AND matches.id_away_team = teams.id THEN 1 ELSE 0 END) AS wins,
    SUM(CASE WHEN matches.total_home = matches.total_away THEN 1 ELSE 0 END) AS draws,
    SUM(CASE WHEN matches.total_home < matches.total_away AND matches.id_home_team = teams.id THEN 1 ELSE 0 END) +
    SUM(CASE WHEN matches.total_away < matches.total_home AND matches.id_away_team = teams.id THEN 1 ELSE 0 END) AS losses,
    SUM(CASE WHEN matches.id_home_team = teams.id THEN matches.total_home ELSE 0 END) +
    SUM(CASE WHEN matches.id_away_team = teams.id THEN matches.total_away ELSE 0 END) AS goals_for,
	SUM(CASE WHEN matches.id_home_team = teams.id THEN matches.total_away ELSE 0 END) +
    SUM(CASE WHEN matches.id_away_team = teams.id THEN matches.total_home ELSE 0 END) AS goals_against,
    SUM(CASE WHEN (matches.total_home > matches.total_away AND matches.id_home_team = teams.id) OR (matches.total_away > matches.total_home AND matches.id_away_team = teams.id) THEN 3 ELSE 0 END) +
    SUM(CASE WHEN matches.total_home = matches.total_away THEN 1 ELSE 0 END) AS points,
	SUM(CASE WHEN matches.id_home_team = teams.id THEN matches.total_home - matches.total_away ELSE 0 END) +
    SUM(CASE WHEN matches.id_away_team = teams.id THEN matches.total_away - matches.total_home ELSE 0 END) AS goal_difference
FROM 
    teams
LEFT JOIN
    matches ON (teams.id = matches.id_home_team OR teams.id = matches.id_away_team)
JOIN champ c ON c.id = matches.id_champ
where c.id_old = %s
GROUP BY
    teams.name
ORDER BY
    points DESC, goal_difference DESC,
    goals_for DESC'''

select_date_matches = '''SELECT home_team.name as home_team, away_team.name as away_team, m.total_home as goal1, m.total_away as goal2, m.time, c.name_tournament FROM date
JOIN matches m ON m.id_date = date.id
JOIN teams away_team ON m.id_away_team = away_team.id
JOIN teams home_team ON m.id_home_team = home_team.id
JOIN champ c ON c.id = m.id_champ
WHERE date.date = %s and c.priority > 100
ORDER BY m.pub_date'''

select_calendar = '''SELECT roundForLTAndMC, ARRAY_AGG(d.date)  as dates, (CASE WHEN(BOOL_AND(m.score is  null)) THEN '' ELSE 'Закончен' END) as end FROM champ as c
JOIN matches m ON m.id_champ = c.id
JOIN date d ON  d.id = m.id_date
WHERE c.id_old = %s
GROUP BY roundForLTAndMC, tour
ORDER BY tour ASC'''

insert_date = "INSERT INTO date (date) VALUES (%s) ON CONFLICT (date) DO UPDATE SET date = date.date RETURNING id"
insert_champ = "INSERT INTO champ (name_tournament, priority, img, id_old, link) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (id_old) DO UPDATE SET id_old = champ.id_old RETURNING id"
insert_team = "INSERT INTO teams (name, img, id_old) VALUES (%s,%s,%s) ON CONFLICT (id_old) DO UPDATE SET id_old = teams.id_old RETURNING id"
insert_match = """INSERT INTO matches (
                        id_old,
                        section , 
                        link,
                        time,
                        groups,
                        flags,
                        result,
                        status,
                        pub_date,
                        score,
                        total_home,
                        total_away,        
                        roundForLTAndMC,
                        tour,
                        periods,
                        time_str,
                        link_title,
                        id_date,
                        id_champ,
                        id_home_team,
                        id_away_team
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (id_old) DO NOTHING"""