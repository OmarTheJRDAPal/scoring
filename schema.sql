DROP TABLE IF EXISTS leagues;
DROP TABLE IF EXISTS game_types;
DROP TABLE IF EXISTS divisions;
DROP TABLE IF EXISTS teams;
DROP TABLE IF EXISTS games;

CREATE TABLE leagues (
	id INTEGER PRIMARY KEY,
	name TEXT
);

CREATE TABLE game_types (
	id INTEGER PRIMARY KEY,
	game_type TEXT,
	weight DECIMAL
);

CREATE TABLE divisions (
	id INTEGER PRIMARY KEY,
	name TEXT
);

CREATE TABLE teams (
	id INTEGER PRIMARY KEY,
	league_id INTEGER,
	division_id INTEGER,
	strength_rating DECIMAL
);

CREATE TABLE games (
	id INTEGER PRIMARY KEY,
	game_date DATE,
	game_type_id INTEGER,
	w_team_id INTEGER,
	w_team_score INTEGER,
	w_team_expulsions INTEGER,
	w_ranking_points DECIMAL,
	l_team_id INTEGER,
	l_team_score INTEGER,
	l_team_expulsions INTEGER,
	l_ranking_points DECIMAL
);
