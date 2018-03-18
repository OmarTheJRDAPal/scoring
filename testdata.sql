INSERT INTO divisions (name) VALUES ("Male");
INSERT INTO divisions (name) VALUES ("Female");
INSERT INTO divisions (name) VALUES ("Open");

INSERT INTO leagues (name) VALUES ("New York");
INSERT INTO leagues (name) VALUES ("Paris");
INSERT INTO leagues (name) VALUES ("London");
INSERT INTO leagues (name) VALUES ("New Jersey");
INSERT INTO leagues (name) VALUES ("Dolphin City");
INSERT INTO leagues (name) VALUES ("Bearville");

INSERT INTO teams (league_id, division_id) VALUES (1, 1);
INSERT INTO teams (league_id, division_id) VALUES (2, 1);

INSERT INTO game_types (game_type, weight) VALUES ("Normal", 1.0);
INSERT INTO game_types (game_type, weight) VALUES ("Consolation Bracket", 1.075);
INSERT INTO game_types (game_type, weight) VALUES ("Semi-Final Bracket", 1.125);
INSERT INTO game_types (game_type, weight) VALUES ("Final Bracket", 1.175);

INSERT INTO games (game_date, w_team_id, w_team_score, w_team_expulsions, l_team_id, l_team_score, l_team_expulsions, game_type_id) VALUES (
	"2018-02-15",
	1,
	100,
	0,
	2,
	50,
	0,
	1 -- Normal game
);
