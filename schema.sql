DROP TABLE IF EXISTS leagues;
DROP TABLE IF EXISTS game_types;
DROP TABLE IF EXISTS divisions;
DROP TABLE IF EXISTS teams;
DROP TABLE IF EXISTS games;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS groups;
DROP TABLE IF EXISTS group_memberships;
DROP TABLE IF EXISTS game_ranking_points;

CREATE TABLE groups (
        id INTEGER PRIMARY KEY,
	name TEXT
);

CREATE TABLE group_memberships (
	team_id INTEGER,
	group_id INTEGER
);

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
	division_id INTEGER
);

CREATE TABLE strength_rating_batches (
	id INTEGER PRIMARY KEY,
	name VARCHAR
);

CREATE TABLE team_group_strength_ratings (
	id INTEGER PRIMARY KEY,
	batch_id INTEGER,
	team_id INTEGER,
	group_id DECIMAL,
        strength_rating DECIMAL
);

CREATE TABLE game_ranking_points (
	id INTEGER PRIMARY KEY,
        game_id INTEGER,
	group_id INTEGER,
	team1_ranking_points DECIMAL,
	team2_ranking_points DECIMAL
);

CREATE TABLE games (
	id INTEGER PRIMARY KEY,
	game_date DATE,
	game_type_id INTEGER,
	team1_id INTEGER,
	team1_points INTEGER,
	team1_expulsions INTEGER,
    team2_id INTEGER,
    team2_points INTEGER,
    team2_expulsions INTEGER
);

CREATE TABLE application_settings (
	strength_rating_batch_id INTEGER
);


CREATE TABLE users (
	id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
	username TEXT NOT NULL,
	hash TEXT NOT NULL
);

CREATE UNIQUE INDEX 'username' ON "users" ("username");
