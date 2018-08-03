INSERT INTO divisions (name) VALUES ("Male");
INSERT INTO divisions (name) VALUES ("Female");
INSERT INTO divisions (name) VALUES ("Open");

INSERT INTO leagues (name) VALUES ("New York");
INSERT INTO leagues (name) VALUES ("Paris");
INSERT INTO leagues (name) VALUES ("London");
INSERT INTO leagues (name) VALUES ("New Jersey");
INSERT INTO leagues (name) VALUES ("Dolphin City");
INSERT INTO leagues (name) VALUES ("Bearville");

INSERT INTO teams (league_id, division_id, name) VALUES (1, 1, "Omar and Fox");
INSERT INTO teams (league_id, division_id, name) VALUES (2, 1, "Wildcats");

INSERT INTO strength_rating_batches (name, start_date, end_date, computed_on) VALUES (
	"Default batch", "2000-05-19", "2020-06-18", "2020-07-19"

);

--INSERT INTO team_group_strength_ratings (team_id, group_id, strength_rating, batch_id) VALUES (
--  1, 1, .8, 1
--);

INSERT INTO team_group_strength_ratings (team_id, group_id, strength_rating, batch_id) VALUES (
  2, 1, 1.2, 1
);

INSERT INTO application_settings (strength_rating_batch_id) VALUES (
	1
);


INSERT INTO game_types (game_type, weight) VALUES ("Normal", 1.0);
INSERT INTO game_types (game_type, weight) VALUES ("Consolation Bracket", 1.075);
INSERT INTO game_types (game_type, weight) VALUES ("Semi-Final Bracket", 1.125);
INSERT INTO game_types (game_type, weight) VALUES ("Final Bracket", 1.175);

INSERT INTO groups (name) VALUES ("Global");
INSERT INTO groups (name) VALUES ("Cities/states that start with N or P");

INSERT INTO group_memberships (league_id, group_id) VALUES (1, 1);
INSERT INTO group_memberships (league_id, group_id) VALUES (2, 1);

INSERT INTO group_memberships (league_id, group_id) VALUES (1, 2);
INSERT INTO group_memberships (league_id, group_id) VALUES (2, 2);

INSERT INTO game_ranking_points (game_id, group_id, team1_ranking_points, team2_ranking_points)
VALUES (1, 1, 150.10, 50.10);

INSERT INTO game_ranking_points (game_id, group_id, team1_ranking_points, team2_ranking_points)
VALUES (2, 1, 150.10, 50.10);

INSERT INTO game_ranking_points (game_id, group_id, team1_ranking_points, team2_ranking_points)
VALUES (3, 1, 150.10, 50.10);


INSERT INTO games (game_date, team1_id, team1_points, team1_expulsions, team2_id, team2_points, team2_expulsions, game_type_id, 
entered_date, created_user_id) VALUES (
	"2018-02-15",
	1,
	100,
	0,
	2,
	50,
	0,
	1, -- Normal game
        "2018-02-16",
        1

);

INSERT INTO games (game_date, team1_id, team1_points, team1_expulsions, team2_id, team2_points, team2_expulsions, game_type_id,
entered_date, created_user_id) VALUES (
	"2018-02-16",
	1,
	100,
	0,
	2,
	50,
	0,
	1, -- Normal game
        "2018-02-17",
        1
);

INSERT INTO games (game_date, team1_id, team1_points, team1_expulsions, team2_id, team2_points, team2_expulsions, game_type_id,
entered_date, created_user_id
) VALUES (
	"2018-02-17",
	1,
	100,
	0,
	2,
	50,
	0,
	1, -- Normal game
        "2018-02-18",
        1
);

INSERT INTO users (username, hash, admin) VALUES (
	"admin",
	"pbkdf2:sha256:50000$iPHUDSbc$b50c5aa72ffb222c0850369bf77871bbac0e90d725ee38daa6946e2eeca9dad6",
	1
);


