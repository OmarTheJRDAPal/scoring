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

@app.route("/games", methods=["GET"])
@login_required
def games():
    games_result = db.execute("""
        SELECT game_date, game_type, divisions.name as division, leagues.name as team1_league,
        leagues2.name as team2_league
         FROM games
        JOIN game_types ON game_type_id = game_types.id
        JOIN teams team_1_data ON team_1_data.id = team1_id
        JOIN leagues ON leagues.id = team_1_data.league_id
        JOIN teams team_2_data ON team_2_data.id = team2_id
        JOIN leagues leagues2 ON leagues2.id = team_2_data.league_id
        JOIN divisions ON divisions.id = team_1_data.division_id
    """)
    return render_template("games.html", games=games_result)

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
		SELECT common_groups.group_id as group_id, IFNULL(t1.strength_rating, 1.0) team1, IFNULL(t2.strength_rating, 1.0) team2 FROM (
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

        return redirect("/games/")

def calculate_group_ranking_point_averages(start_date, end_date, group_id=None):

	kwargs = dict({
		"start_date": start_date,
		"end_date": end_date,
	})

	if group_id is None:
		group_id_filter_str = "1"
	else:
		group_id_filter_str = "group_id = :group_id"
		kwargs["group_id"] = group_id

	result = db.execute("""
			SELECT league_id, team_id, group_name, group_id, division_name,
			league_name, division_id, SUM(1.0 * team_game_group_ranking_points) / COUNT(*) as team_group_rp_average FROM
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
				WHERE """ + group_id_filter_str + """
			)
			GROUP BY team_id, group_id
			ORDER BY team_group_rp_average DESC
	""", **kwargs)
	division_group_rankings = defaultdict(lambda: [])

	division_names = dict({})
	group_names = dict({})

	for row in result:
		group_names[row["group_id"]] = row["group_name"]
		division_names[row["division_id"]] = row["division_name"]
		division_group_rankings[row["group_id"], row["division_id"]].append({
			"league_id": row["league_id"],
			"league": row["league"],
			"rp_average": row["team_group_rp_average"]
		})

	return group_names, division_names, division_group_rankings

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

        batch_id = db.execute("""INSERT INTO strength_rating_batches (name) VALUES (:sr_name)""",
		  sr_name=sr_name)

	db.execute("""

		WITH has_strength_now AS (
			SELECT team_id, group_id, strength_rating IS NOT NULL FROM team_group_strength_ratings
			JOIN application_settings ON batch_id = strength_rating_batch_id
		)
		WITH ranking_point_averages AS (
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

		SELECT :batch_id, team_id, group_id, 

		CASE WHEN num_games >= 3 OR (has_strength_rating AND num_games >= 2) THEN -- eligible 
		ranking_point_average * 1.0/ median_rpa strength_rating ELSE
		NULL END as new_strength
		FROM ranking_point_averages rpa
		JOIN teams ON teams.id = rpa.team_id
		JOIN median_ranking_point_averages mrpa ON mrpa.division_id = teams.division_id

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

    group_names, division_names, division_group_rankings = calculate_group_ranking_point_averages(start_date, end_date, group_id=group_id)
    return render_template("rankings.html", group_names=group_names, division_names=division_names, division_group_rankings=division_group_rankings, start_date=start_date_raw, end_date=end_date_raw, group_id=group_id_raw)


@app.route("/ratings", methods=["GET"])
@login_required
def ratings():

    if not request.args.get("start_date"):
        return apology("must provide start date", 400)

	start_date_raw = request.args.get("start_date")

        if not request.args.get("end_date"):
            return apology("must provide end date", 400)

	end_date_raw = request.args.get("end_date")

	start_date = datetime.datetime.strptime(start_date_raw, "%Y-%m-%d")
	end_date = datetime.datetime.strptime(end_date_raw, "%Y-%m-%d")

        # Query database for username
        team_ranking_point_averages = db.execute("""
                SELECT team_id, division_id, SUM(ranking_points) * 1.0 / COUNT(ranking_points) avg_ranking_points, COUNT(ranking_points) n_games FROM
                (
                        SELECT w_ranking_points ranking_points, w_team_id team_id, game_date FROM games
                        UNION ALL
                        SELECT l_ranking_points, l_team_id, game_date FROM games
                ) flat_games
                JOIN teams ON teams.id = team_id
		WHERE game_date >= :start_date AND game_date <= :end_date
                GROUP BY team_id
	""", start_date=start_date, end_date=end_date)

	rps_in_division = defaultdict(lambda: [])
	print team_ranking_point_averages
	for rp_average in team_ranking_point_averages:
		n_games = rp_average["n_games"]
		avg_ranking_points = rp_average["avg_ranking_points"]
		division_id = rp_average["division_id"]
		team_id = rp_average["team_id"]
		print n_games

		if n_games > 2:
			rps_in_division[division_id].append(avg_ranking_points)

	medians = defaultdict(lambda: None)

	print rps_in_division, "RPS IN DIVISION"

	for division_id, ranking_point_averages in rps_in_division.iteritems():			
		print median(ranking_point_averages), ranking_point_averages
		medians[division_id] = median(ranking_point_averages)

	for rp_average in team_ranking_point_averages:
		rp_average["median"] = medians[rp_average["division_id"]] 
		rp_average["strength_rating"] = rp_average["avg_ranking_points"] * 1.0 / rp_average["median"]

	return render_template("ratings.html", team_ranking_point_averages=team_ranking_point_averages)



def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
