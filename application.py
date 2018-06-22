from cs50 import SQL
from collections import defaultdict
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
import datetime
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
BAD_REQUEST = 400
NOT_FOUND = 404

from numpy import median

from helpers import apology, login_required, lookup

# Configure application
app = Flask(__name__)

# Ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# Custom filter

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False
Session(app)


class NumpyMedianAggregate(object):
  def __init__(self):
    self.values = []
  def step(self, value):
    self.values.append(value)
  def finalize(self):
    return median(self.values)


def sqlite_memory_engine_creator():
    con = sqlite3.connect('finance.db')
    con.create_aggregate("median", 1, NumpyMedianAggregate)
    return con

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db", creator=sqlite_memory_engine_creator)


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    return apology("TODO")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    return apology("TODO")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=str(request.form.get("username")))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

	username = str(request.form.get("username"))
	password = str(request.form.get("password"))

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 403)

	print username, password

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=username)

	print "here"

        # Ensure username exists and password is correct
        if len(rows) > 0:
            return apology("username already exists", 403)
        else:
            hash_value = str(generate_password_hash(password))
            result = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=username, hash=hash_value)
            print result
            # Remember which user has logged in
            session["user_id"] = result
            # Redirect user to home page
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

WIN_LOSS_POINTS_WIN = 200
WIN_LOSS_POINTS_LOSS = 100
WIN_LOSS_POINTS_TIE = 150

def point_spread_points(team, opponent):
	total_points_scored = team["points"] + opponent["points"]
	return team["points"] * 300.0 / total_points_scored

def win_loss_points(team, opponent):
	if team["points"] == opponent["points"]:
		return WIN_LOSS_POINTS_TIE
	elif team["points"] > opponent["points"]:
		return WIN_LOSS_POINTS_WIN
	elif team["points"] < opponent["points"]:
		return WIN_LOSS_POINTS_LOSS

def expulsion_points(team):
	return team["expulsions"] * 10

def lookup_teams(game, teams, reference_team_id):
	w_team = teams[teams["w_team_id"]]
	l_team = teams[teams["l_team_id"]]

	if reference_team_id == teams["w_team_id"]:
		return w_team, l_team
	elif reference_team_id == teams["l_team_id"]:
		return l_team, w_team
	else:
                raise Exception("Invalid team id")

def ranking_points_for_groups(weight, team, opponent, groups_srs):
	group_ranking_points = dict({})

        for group_id in groups_srs:
		strengths = groups_srs[group_id]
		wlp = win_loss_points(team, opponent)
		psp = point_spread_points(team, opponent)
		group_ranking_points[group_id] = ((wlp + psp) / 2.0) * weight * strengths[opponent["id"]] - expulsion_points(team)

	return group_ranking_points

@app.route("/leagues_for_division", methods=["GET"])
@login_required
def leagues_for_division():

    if not request.args.get("division_id"):
        return apology("must provide division_id", BAD_REQUEST)

    division_id = int(request.args.get("division_id"))

    # Query database for game weight
    leagues_result = db.execute("""
        SELECT leagues.id as league_id, teams.id AS team_id, name FROM leagues
        JOIN (SELECT * FROM teams WHERE division_id = :division_id) teams ON leagues.id = teams.league_id
    """, division_id=division_id)

    return jsonify(leagues_result)

@app.route("/team", methods=["GET"])
@login_required
def team():
    if not request.args.get("id"):
      return apology("must provide id", BAD_REQUEST)
    team_id = int(request.args.get("id"))

    teams_result = db.execute("""
	SELECT leagues.name league, divisions.name as division FROM teams 
        JOIN leagues ON leagues.id = teams.league_id
        JOIN divisions ON divisions.id = teams.division_id
        WHERE teams.id = :team_id
    """, team_id=team_id)

    if len(teams_result) != 1:
            return apology("couldn't find team", NOT_FOUND)

    team = teams_result[0]

    team_strength_ratings_result = db.execute("""
        SELECT * FROM team_group_strength_ratings
        JOIN groups ON groups.id = group_id
        WHERE team_id = :team_id
    """, team_id=team_id)


    """
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

    """

    games_result = db.execute("""
        SELECT * FROM games 
        JOIN game_ranking_points ON game_id = games.id
        JOIN application
        WHERE team1_id = :team_id OR team2_id = :team_id

    """, team_id=team_id)


    team["strength_ratings"] = team_strength_ratings_result
    return render_template("team.html", team=team)

@app.route("/game", methods=["GET"])
@login_required
def game():
    if not request.args.get("id"):
      return apology("must provide game id", BAD_REQUEST)
    game_id = int(request.args.get("id"))

    games_result = db.execute("""
        SELECT games.id as game_id, game_date, game_type, divisions.name as division, leagues.name as team1_league,
        leagues2.name as team2_league, team1_points, team2_points, team1_expulsions, team2_expulsions
         FROM games
        JOIN game_types ON game_type_id = game_types.id
        JOIN teams team_1_data ON team_1_data.id = team1_id
        JOIN leagues ON leagues.id = team_1_data.league_id
        JOIN teams team_2_data ON team_2_data.id = team2_id
        JOIN leagues leagues2 ON leagues2.id = team_2_data.league_id
        JOIN divisions ON divisions.id = team_1_data.division_id
	WHERE games.id = :game_id
    """, game_id=game_id)

    game_ranking_points = db.execute("""
	SELECT groups.name, team1_ranking_points, team2_ranking_points FROM game_ranking_points
	JOIN groups ON groups.id = game_ranking_points.group_id
	WHERE game_ranking_points.game_id = :game_id
    """, game_id=game_id)

    if len(games_result) != 1:
            return apology("couldn't find game", NOT_FOUND)

    game = games_result[0]
    game["ranking_points"] = game_ranking_points

    return render_template("game.html", game=game)

@app.route("/games", methods=["GET"])
@login_required
def games():

    divisions_result = db.execute("""
	SELECT id, name FROM divisions
    """)

    leagues_result = db.execute("""
	SELECT id, name FROM leagues
    """)

    kwargs = dict({})

    if request.args.get("division_id"):
      division_id = int(request.args.get("division_id"))
      kwargs["division_id"] = division_id
      division_filter_clause = "divisions.id = :division_id"
    else:
      division_filter_clause = "1"
      division_id = ""

    if request.args.get("league1_id"):
      league1_id = int(request.args.get("league1_id"))
      kwargs["league1_id"] = league1_id
      league1_filter_clause = "(leagues.id = :league1_id OR leagues2.id = :league1_id)"
    else:
      league1_filter_clause = "1"
      league1_id = ""

    if request.args.get("league2_id"):
      league2_id = int(request.args.get("league2_id"))
      kwargs["league2_id"] = league2_id
      league2_filter_clause = "(leagues.id = :league2_id OR leagues2.id = :league2_id)"
    else:
      league2_filter_clause = "1"  
      league2_id = ""

    print "division id", division_id, "league 1 id",  league1_id, "league 2 id", league2_id


    games_result = db.execute("""
        SELECT games.id as game_id, game_date, game_type, divisions.name as division, leagues.name as team1_league,
        leagues2.name as team2_league, team1_points, team2_points
         FROM games
        JOIN game_types ON game_type_id = game_types.id
        JOIN teams team_1_data ON team_1_data.id = team1_id
        JOIN leagues ON leagues.id = team_1_data.league_id
        JOIN teams team_2_data ON team_2_data.id = team2_id
        JOIN leagues leagues2 ON leagues2.id = team_2_data.league_id
        JOIN divisions ON divisions.id = team_1_data.division_id
	WHERE """ + division_filter_clause + 
    " AND " + league1_filter_clause + " AND " + league2_filter_clause, **kwargs)


    return render_template("games.html",
      games=games_result,
      divisions=divisions_result,
      leagues=leagues_result,
      division_id=division_id,
      league1_id=league1_id,
      league2_id=league2_id
    )

@app.route("/median", methods=["GET"])
@login_required
def median_egbert():
   divisions_result = db.execute("""
          SELECT median(id) FROM divisions
      """)
   for row in divisions_result:
	print row



@app.route("/enter", methods=["GET", "POST"])
@login_required
def enter():
    if request.method == "GET":
      divisions_result = db.execute("""
          SELECT * FROM divisions
      """)
      game_types_result = db.execute("""
          SELECT * FROM game_types
      """)
      leagues_result = db.execute("""
          SELECT id, name FROM leagues
      """)

      return render_template("enter.html", divisions=divisions_result, game_types=game_types_result, leagues=leagues_result)
    else:
        if not request.form.get("game_type_id"):
            return apology("must provide game_type_id", BAD_REQUEST)

        game_type_id = int(request.form.get("game_type_id"))

        game_date = str(request.form.get("game_date"))

        # Query database for game weight
        weight_result = db.execute("""
                    SELECT weight FROM game_types WHERE id = :game_type_id       
        """, game_type_id=game_type_id)

        if len(weight_result) != 1:
            return apology("invalid game_type_id", BAD_REQUEST)

        game_weight = weight_result[0]["weight"]

        if not request.form.get("team1_id"):
            return apology("must provide team1_id", BAD_REQUEST)

        team1_id = int(request.form.get("team1_id"))

        if not request.form.get("team2_id"):
            return apology("must provide team2_id", BAD_REQUEST)

        team2_id = int(request.form.get("team2_id"))

        sr_results = db.execute("""
		SELECT common_groups.group_id as group_id, t1.strength_rating team1, t2.strength_rating team2 FROM (
			SELECT t1.group_id FROM group_memberships t1
			JOIN (
				SELECT * FROM group_memberships WHERE team_id = :team2_id
			) t2 ON t2.group_id = t1.group_id WHERE t1.team_id = :team1_id
		) common_groups
		JOIN (SELECT strength_rating_batch_id batch_id FROM application_settings LIMIT 1) settings ON 1
		LEFT JOIN team_group_strength_ratings t1 ON t1.group_id = common_groups.group_id AND t1.team_id = :team1_id AND settings.batch_id = t1.batch_id
		LEFT JOIN team_group_strength_ratings t2 ON t2.group_id = common_groups.group_id AND t2.team_id = :team2_id AND settings.batch_id = t2.batch_id
        """, team1_id=team1_id, team2_id=team2_id)

        strength_ratings = defaultdict(lambda: dict({}))
        for sr_result in sr_results:
            print sr_result
            strength_ratings[sr_result["group_id"]] = dict({
			team1_id: sr_result["team1"],
			team2_id: sr_result["team2"]
	    })

	print strength_ratings

        if not request.form.get("team1_points"):
            return apology("must provide team1_points", BAD_REQUEST)

        team1_points = int(request.form.get("team1_points"))

        if not request.form.get("team2_points"):
            return apology("must provide team2_points", BAD_REQUEST)

        team2_points = int(request.form.get("team2_points"))

        if not request.form.get("team1_expulsions"):
            return apology("must provide team1_expulsions", BAD_REQUEST)

        team1_expulsions = int(request.form.get("team1_expulsions"))

        if not request.form.get("team2_expulsions"):
            return apology("must provide team2_expulsions", BAD_REQUEST)

        team2_expulsions = int(request.form.get("team2_expulsions"))

        team1_info = {
            "expulsions": team1_expulsions,
            "id": team1_id,
            "points": team1_points
        }

        team2_info = {
            "expulsions": team2_expulsions,
            "id": team2_id,
            "points": team2_points
        }

        team1_ranking_points = ranking_points_for_groups(game_weight, team1_info, team2_info, strength_ratings)
        team2_ranking_points = ranking_points_for_groups(game_weight, team2_info, team1_info, strength_ratings)

        game_id = db.execute("""INSERT INTO games (game_date, game_type_id, team1_id, team1_points,
            team1_expulsions, team2_id, team2_points,
            team2_expulsions) VALUES (:game_date, :game_type_id,
            :team1_id, :team1_points, :team1_expulsions,
            :team2_id, :team2_points, :team2_expulsions)""",
        game_date=game_date, game_type_id=game_type_id,
        team1_id=team1_id, team1_points=team1_points, team1_expulsions=team1_expulsions,
        team2_id=team2_id, team2_points=team2_points, team2_expulsions=team2_expulsions
        )

	for group_id in team1_ranking_points:
		team1_group_rp = team1_ranking_points[group_id]
		team2_group_rp = team2_ranking_points[group_id]

		result = db.execute("""INSERT INTO game_ranking_points (game_id, group_id, team1_ranking_points, team2_ranking_points)
			VALUES (:game_id, :group_id, :team1_group_rp, :team2_group_rp)
		""", game_id=game_id, group_id=group_id, team1_group_rp=team1_group_rp, team2_group_rp=team2_group_rp)

        return redirect("/games")

def calculate_group_ranking_point_averages(start_date, end_date, group_id):

	result = db.execute("""
			SELECT league_id, team_id, group_name, group_id, division_name,
			league_name, division_id, SUM(1.0 * team_game_group_ranking_points) / COUNT(*) as team_group_rp_average FROM
			(
				SELECT league_id, teams.id as team_id, groups.name as group_name, group_id, games.id,
				CASE WHEN games.team1_id = teams.id
				THEN game_ranking_points.team1_ranking_points
				ELSE game_ranking_points.team2_ranking_points END team_game_group_ranking_points,
				divisions.name division_name, divisions.id division_id, leagues.name league_name, leagues.id
				FROM teams
				JOIN (SELECT * FROM games WHERE game_date >= :start_date AND game_date <= :end_date) games 
					ON games.team1_id = teams.id OR games.team2_id = teams.id
				JOIN game_ranking_points ON game_ranking_points.game_id = games.id
				JOIN divisions ON divisions.id = teams.division_id
				JOIN leagues ON leagues.id = teams.league_id
				JOIN groups ON groups.id = group_id
				WHERE group_id = :group_id
			)
			GROUP BY team_id, group_id
			ORDER BY team_group_rp_average DESC
	""", start_date=start_date, end_date=end_date, group_id=group_id)
	division_group_rankings = defaultdict(lambda: [])

	division_names = dict({})

	for row in result:
		print "row", row
		division_group_rankings[row["division_name"]].append({
			"league_id": row["league_id"],
			"league": row["league_name"],
			"rp_average": row["team_group_rp_average"]
		})

	return division_group_rankings

@app.route("/recalculate", methods=["POST", "GET"])
@login_required
def recalculate():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        start_date_raw = request.form.get("start_date")
        end_date_raw = request.form.get("end_date")
        sr_name = str(request.form.get("strength_rating_memo"))
        print start_date_raw, end_date_raw, sr_name

        start_date = datetime.datetime.strptime(start_date_raw, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date_raw, "%Y-%m-%d")

        batch_id = db.execute("""INSERT INTO strength_rating_batches (name, start_date, end_date) VALUES (:sr_name, :start_date, :end_date)""",
		  sr_name=sr_name, start_date=start_date, end_date=end_date)

	db.execute("""

		WITH has_strength_now AS (
			SELECT team_id, group_id, strength_rating IS NOT NULL as has_strength_rating FROM team_group_strength_ratings
			JOIN application_settings ON batch_id = strength_rating_batch_id
		), ranking_point_averages AS (
		        SELECT team_id, group_id,
                	        SUM(1.0 * team_game_group_ranking_points) / COUNT(*) as ranking_point_average FROM
                        	(
                                	SELECT teams.id as team_id, groups.name as group_name, group_id, games.id,
	                                CASE WHEN games.team1_id = teams.id
        	                        THEN game_ranking_points.team1_ranking_points
                	                ELSE game_ranking_points.team2_ranking_points END team_game_group_ranking_points,
                        	        divisions.name division_name, divisions.id division_id, leagues.name league_name, leagues.id
                                	FROM teams
                                	JOIN (SELECT * FROM games WHERE game_date >= :start_date AND game_date <= :end_date) games
                                        	ON games.team1_id = teams.id OR games.team2_id = teams.id
	                                JOIN game_ranking_points ON game_ranking_points.game_id = games.id
        	                        JOIN divisions ON divisions.id = teams.division_id
                	                JOIN leagues ON leagues.id = teams.league_id
                        	        JOIN groups ON groups.id = group_id
	                        )
        	                GROUP BY team_id, group_id


		), median_ranking_point_averages AS (
			SELECT division_id, group_id, MEDIAN(rpa.ranking_point_average) median_rpa, COUNT(*) num_games
			FROM ranking_point_averages rpa
			JOIN teams ON teams.id = rpa.team_id
			GROUP BY division_id, group_id
		)

		INSERT INTO team_group_strength_ratings (batch_id, team_id, group_id, strength_rating)
		SELECT :batch_id, rpa.team_id, rpa.group_id, 
		CASE WHEN num_games >= 3 OR (has_strength_rating AND num_games >= 2) THEN -- eligible 
		ranking_point_average * 1.0/ median_rpa ELSE
		NULL END as strength_rating
		FROM ranking_point_averages rpa
		JOIN teams ON teams.id = rpa.team_id
        JOIN has_strength_now ON has_strength_now.team_id = teams.id AND has_strength_now.group_id = rpa.group_id
		JOIN median_ranking_point_averages mrpa ON mrpa.division_id = teams.division_id AND mrpa.group_id = rpa.group_id

	""", batch_id=batch_id, start_date=start_date, end_date=end_date)


        return render_template("recalculate_result.html")
    else:
        return render_template("recalculate.html")



@app.route("/rankings", methods=["GET"])
@login_required
def rankings():

    groups_result = db.execute("SELECT id, name FROM groups")
    group_names = {}
    for row in groups_result:
        group_names[row["id"]] = row["name"]

    start_date_raw = request.args.get("start_date")
    end_date_raw = request.args.get("end_date")
    group_id_raw = request.args.get("group_id")

    if not start_date_raw or not end_date_raw or not group_id_raw:
        return render_template("rankings.html", group_names=group_names, start_date=start_date_raw, end_date=end_date_raw, group_id=group_id_raw)

    if not request.args.get("group_id"):
        return apology("must provide group id", 400)

    group_id = int(group_id_raw)

    start_date = datetime.datetime.strptime(start_date_raw, "%Y-%m-%d")
    end_date = datetime.datetime.strptime(end_date_raw, "%Y-%m-%d")

    division_group_rankings = calculate_group_ranking_point_averages(start_date, end_date, group_id=group_id)
    return render_template("rankings.html", group_names=group_names, division_group_rankings=division_group_rankings, start_date=start_date_raw, end_date=end_date_raw, group_id=group_id_raw)


@app.route("/ratings", methods=["GET"])
@login_required
def ratings():

	return render_template("ratings.html", team_ranking_point_averages=team_ranking_point_averages)



def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
