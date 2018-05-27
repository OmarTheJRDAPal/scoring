from cs50 import SQL
from collections import defaultdict
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
import datetime
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

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

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


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

def ranking_points(weight, team, opponent):
	wlp = win_loss_points(team, opponent)
	psp = point_spread_points(team, opponent)
	return ((wlp + psp) / 2.0) * weight * opponent["strength_rating"] - expulsion_points(team)

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
def games:
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
      return render_template("enter.html", divisions=divisions_result, game_types=game_types_result)
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
                    SELECT id, strength_rating FROM teams WHERE id = :team1_id OR id = :team2_id
        """, team1_id=team1_id, team2_id=team2_id)

        if len(sr_results) != 2:
            return apology("1 or more unknown/invalid team ids", BAD_REQUEST)

        strength_ratings = dict({})
        for sr_result in sr_results:
            strength_ratings[sr_result["id"]] = sr_result["strength_rating"]

        team1_strength_rating = strength_ratings[team1_id]
        team2_strength_rating = strength_ratings[team2_id]

        if not request.form.get("team1_points"):
            return apology("must provide team1_points", BAD_REQUEST)

        team1_points = int(request.form.get("team1_points"))

        if not request.form.get("team2_points"):
            return apology("must provide team2_points", BAD_REQUEST)

        team2_points = int(request.form.get("team2_points"))

        print request.form.get("team1_expulsions")

        if not request.form.get("team1_expulsions"):
            return apology("must provide team1_expulsions", BAD_REQUEST)

        team1_expulsions = int(request.form.get("team1_expulsions"))

        if not request.form.get("team2_expulsions"):
            return apology("must provide team2_expulsions", BAD_REQUEST)

        team2_expulsions = int(request.form.get("team2_expulsions"))

        team1_info = {
            "expulsions": team1_expulsions,
            "strength_rating": team1_strength_rating,
            "id": team1_id,
            "points": team1_points
        }

        team2_info = {
            "expulsions": team2_expulsions,
            "strength_rating": team2_strength_rating,
            "id": team2_id,
            "points": team2_points
        }

        team1_ranking_points = ranking_points(game_weight, team1_info, team2_info)
        team2_ranking_points = ranking_points(game_weight, team2_info, team1_info)

        result = db.execute("""INSERT INTO games (game_date, game_type_id, team1_id, team1_points, 
            team1_expulsions, team1_ranking_points, team2_id, team2_points, 
            team2_expulsions, team2_ranking_points) VALUES (:game_date, :game_type_id, 
            :team1_id, :team1_points, :team1_expulsions, :team1_ranking_points,
            :team2_id, :team2_points, :team2_expulsions, :team2_ranking_points)""", 
        game_date=game_date, game_type_id=game_type_id,
        team1_id=team1_id, team1_points=team1_points, team1_expulsions=team1_expulsions, team1_ranking_points=team1_ranking_points,
        team2_id=team2_id, team2_points=team2_points, team2_expulsions=team2_expulsions, team2_ranking_points=team2_ranking_points
        )

        return redirect("/games/")

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
