INSERT INTO divisions (name) VALUES ("Male");
INSERT INTO divisions (name) VALUES ("Female");
INSERT INTO divisions (name) VALUES ("Open");

INSERT INTO leagues (name) VALUES ("New York");
INSERT INTO leagues (name) VALUES ("Paris");
INSERT INTO leagues (name) VALUES ("London");
INSERT INTO leagues (name) VALUES ("New Jersey");
INSERT INTO leagues (name) VALUES ("Dolphin City");
INSERT INTO leagues (name) VALUES ("Bearville");

INSERT INTO teams (league_id, division_id, strength_rating) VALUES (1, 1, .8);
INSERT INTO teams (league_id, division_id, strength_rating) VALUES (2, 1, 1.2);

INSERT INTO game_types (game_type, weight) VALUES ("Normal", 1.0);
INSERT INTO game_types (game_type, weight) VALUES ("Consolation Bracket", 1.075);
INSERT INTO game_types (game_type, weight) VALUES ("Semi-Final Bracket", 1.125);
INSERT INTO game_types (game_type, weight) VALUES ("Final Bracket", 1.175);

        team1_id INTEGER,
        team1_points INTEGER,
        team1_expulsions INTEGER,
        team1_ranking_points DECIMAL,

INSERT INTO games (game_date, team1_id, team1_score, w_team_expulsions, w_ranking_points, l_team_id, l_team_score, l_team_expulsions, l_ranking_points, game_type_id) VALUES (
	"2018-02-15",
	1,
	100,
	0,
	150.10,
	2,
	50,
	0,
	50.10,
	1 -- Normal game
);

INSERT INTO games (game_date, w_team_id, w_team_score, w_team_expulsions, w_ranking_points, l_team_id, l_team_score, l_team_expulsions, l_ranking_points, game_type_id) VALUES (
	"2018-02-16",
	1,
	100,
	0,
	150.10,
	2,
	50,
	0,
	50.10,
	1 -- Normal game
);

INSERT INTO games (game_date, w_team_id, w_team_score, w_team_expulsions, w_ranking_points, l_team_id, l_team_score, l_team_expulsions, l_ranking_points, game_type_id) VALUES (
	"2018-02-17",
	1,
	100,
	0,
	150.10,
	2,
	50,
	0,
	50.10,
	1 -- Normal game
);
