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
                          username=request.form.get("username"))

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

def point_spread_points(game, team_id):
	total_points_scored = game["w_team_score"] + game["l_team_score"]
	if game["w_team_id"] == team_id:
		team_scored = game["w_team_score"]
	elif game["l_team_id"] == team_id:
		team_scored = game["l_team_score"]
	else:
		raise Exception("Invalid team id")

	return team_scored * 300.0 / total_points_scored

def win_loss_points(game, team_id):
	if game["w_team_score"] == game["l_team_score"]:
		return WIN_LOSS_POINTS_TIE
	elif game["w_team_id"] == team_id:
		return WIN_LOSS_POINTS_WIN
	elif game["l_team_id"] == team_id:
		return WIN_LOSS_POINTS_LOSS
	else:
		raise Exception("Invalid team id")

def expulsion_points(game, team_id):
	if game["w_team_id"] == team_id:
		return 10 * game["w_team_expulsions"]
	elif game["l_team_id"] == team_id:
		return 10 * game["l_team_expulsions"]
	else:
		raise Exception("Invalid team id")
def lookup_teams(game, teams, reference_team_id):
	w_team = teams[teams["w_team_id"]]
	l_team = teams[teams["l_team_id"]]

	if reference_team_id == teams["w_team_id"]:
		return w_team, l_team
	elif reference_team_id == teams["l_team_id"]:
		return l_team, w_team
	else:
                raise Exception("Invalid team id")

def ranking_points(weight, w_team, l_team):
	wlp = win_loss_points(game, team_id)
	psp = point_spread_points(game, team_id)

	team, opponent = lookup_teams(game, teams, team_id)

	return ((wlp + psp) / 2.0) * game["weight"] * opponent["strength_rating"] - expulsion_points(game, team_id)

@app.route("/leagues_for_division", methods=["GET"])
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


@app.route("/enter", methods=["GET"])
def enter():
    # Query database for game weight
    divisions_result = db.execute("""
        SELECT * FROM divisions
    """)
    return render_template("enter.html", divisions=divisions_result)


@app.route("/calc_rps", methods=["GET"])
def rps():
    if not request.form.get("game_type_id"):
        return apology("must provide game_type_id", BAD_REQUEST)

    game_type_id = request.form.get("game_type_id")

    # Query database for game weight
    weight_result = db.execute("""
                SELECT weight FROM game_types WHERE id = :game_type_id       
    """, game_type_id=game_type_id)

    if len(weight_result) != 1:
        return apology("invalid game_type_id", BAD_REQUEST)

    game_weight = weight_result[0]["weight"]

    if not request.form.get("w_team_id"):
        return apology("must provide w_team_id", BAD_REQUEST)

    w_team_id = request.form.get("w_team_id")

    if not request.form.get("l_team_id"):
        return apology("must provide l_team_id", BAD_REQUEST)

    l_team_id = request.form.get("l_team_id")

    sr_results = db.execute("""
                SELECT id, strength_rating FROM teams WHERE id = :w_team_id OR id = :l_team_id
    """, w_team_id=w_team_id, l_team_id=l_team_id)

    if len(sr_results) != 2:
        return apology("1 or more unknown/invalid team ids", BAD_REQUEST)

    strength_ratings = dict({})
    for sr_result in sr_results:
        strength_ratings[sr_result["id"]] = sr_result["strength_rating"]

    w_team_strength_rating = strength_ratings[w_team_id]
    l_team_strength_rating = strength_ratings[l_team_id]

    if not request.form.get("w_team_points"):
        return apology("must provide w_team_points", BAD_REQUEST)

    w_team_points = request.form.get("w_team_points")

    if not request.form.get("l_team_points"):
        return apology("must provide l_team_points", BAD_REQUEST)

    l_team_points = request.form.get("l_team_points")

    if not request.form.get("w_team_expulsions"):
        return apology("must provide w_team_expulsions", BAD_REQUEST)

    w_team_expulsions = request.form.get("w_team_expulsions")

    if not request.form.get("l_team_expulsions"):
        return apology("must provide l_team_expulsions", BAD_REQUEST)

    l_team_expulsions = request.form.get("l_team_expulsions")

    w_team_info = {
        "expulsions": w_team_expulsions,
        "strength_rating": w_team_strength_rating,
        "id": w_team_id,
        "points": w_team_points
    }

    l_team_info = {
        "expulsions": l_team_expulsions,
        "strength_rating": l_team_strength_rating,
        "id": l_team_id,
        "points": l_team_points
    }

@app.route("/ratings", methods=["GET"])
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


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    return apology("TODO")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
