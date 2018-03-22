from cs50 import SQL
from collections import defaultdict
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
import datetime
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

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

def ranking_points(game, teams, team_id):
	wlp = win_loss_points(game, team_id)
	psp = point_spread_points(game, team_id)

	team, opponent = lookup_teams(game, teams, team_id)

	return ((wlp + psp) / 2.0) * game["weight"] * opponent["strength_rating"] - expulsion_points(game, team_id)


def compute_month_strength_ratings(games, teams, since_date):
	division_teams = dict([])
	for team in teams:
		division_teams[team["id"]] = team

                team_ranking_points_past_year = defaultdict(lambda: 0)


                for past_game in games[:i]:
                        parsed_past_game_date = datetime.datetime.strptime(past_game["game_date"], "%Y-%m-%d")
                        if parsed_game_date - datetime.timedelta(years=1) <= parsed_past_game_date and parsed_past_game_date <= parsed_game_date:

                                team_ranking_points_past_year
                pass


@app.route("/ratings", methods=["GET"])
def ratings():

	print request
        if not request.args.get("start_date"):
            return apology("must provide start date", 403)

	start_date = request.args.get("start_date")

        if not request.args.get("end_date"):
            return apology("must provide end date", 403)

	end_date = request.args.get("end_date")

	print start_date
	print end_date

        # Query database for username
        team_ranking_point_averages = db.execute("""
                SELECT team_id, division_id, SUM(ranking_points) * 1.0 / COUNT(ranking_points) avg_ranking_points, COUNT(ranking_points) n_games FROM
                (
                        SELECT w_ranking_points ranking_points, w_team_id team_id, game_date FROM games
                        UNION ALL
                        SELECT l_ranking_points, l_team_id, game_date FROM games
                ) flat_games
                JOIN teams ON teams.id = team_id
		WHERE game_date >= :start AND game_date <= :end
                GROUP BY team_id
	""", start_date=start, end_date=end)
#            WHERE game_date >= :start AND game_date <= :end

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
