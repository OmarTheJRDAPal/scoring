from cs50 import SQL
from collections import defaultdict
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
import datetime
from dateutil import relativedelta
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
BAD_REQUEST = 400
NOT_FOUND = 404
INTERNAL_ERROR = 500

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
    print self.values
    return median([x for x in self.values if x is not None])

def sqlite_memory_engine_creator():
    con = sqlite3.connect('finance.db')
    con.execute("PRAGMA foreign_keys = ON")
    con.create_aggregate("median", 1, NumpyMedianAggregate)
    return con

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db", creator=sqlite_memory_engine_creator)


@app.route("/")
@login_required
def index():
    return render_template("index.html")

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

@app.route("/delete_game", methods=["POST"])
@login_required
def delete_game():
    if not request.form.get("game_id"):
        return apology("must provide game_id", BAD_REQUEST)

    game_id = int(request.form.get("game_id"))

    result = db.execute("""
	DELETE FROM games WHERE id = :game_id
    """, game_id=game_id)

    if result:
      flash("Deleted game", "success")
    else:
      flash("Could not delete game", "danger")
    return redirect("/games")

@app.route("/register", methods=["POST"])
@login_required
def register():
    """Log user in"""

    this_user_id = session["user_id"]

    rows = db.execute("SELECT * FROM users WHERE id = :user_id",
                      user_id=this_user_id)

    if len(rows) != 1:
      return apology("internal server error", 500)

    if not rows[0]["admin"]:
      return apology("you do not have permission to create a new user")

    username = str(request.form.get("username"))
    password = str(request.form.get("password"))

    # Ensure username was submitted
    if not username:
      return apology("must provide username", 403)

    # Ensure password was submitted
    elif not password:
      return apology("must provide password", 403)

    admin = 0
    if request.form.get("admin"):
      admin = 1

    hash_value = str(generate_password_hash(password))

    # Query database for username
    rows = db.execute("SELECT * FROM users WHERE username = :username",
                      username=username)

    # Ensure username exists and password is correct
    if len(rows) > 0:
      flash("That username %s already exists" % (username), "danger")
    else:
      hash_value = str(generate_password_hash(password))
      result = db.execute("INSERT INTO users (username, hash, admin) VALUES (:username, :hash, :admin)", username=username, hash=hash_value, admin=admin)
      flash("Successfully created user %s" % (username), "success")

    return redirect("/users")



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

	print "ranking points for groups"
	print "weight", weight
	print "team", team
	print "opponent", opponent
	print "groups srs", groups_srs

        for group_id in groups_srs:
            print group_id, "group_id"
            strengths = groups_srs[group_id]
            wlp = win_loss_points(team, opponent)
            psp = point_spread_points(team, opponent)

            both_unranked = strengths[opponent["id"]] == None and strengths[team["id"]] == None
            print both_unranked, "Both unranked", strengths[opponent["id"]], strengths[opponent["id"]] == None
            if both_unranked:
                 opponent_strength = 1.0
            elif strengths[opponent["id"]] == None:
                 group_ranking_points[group_id] = None
                 continue
            else:
                 opponent_strength = strengths[opponent["id"]]
            print "WLP", wlp, "PSP", psp, "WEIGHT", weight, "strengths", strengths[opponent["id"]], "expulsion points", expulsion_points(team)
            group_ranking_points[group_id] = ((wlp + psp) / 2.0) * weight * opponent_strength - expulsion_points(team)

        return group_ranking_points

@app.route("/add_league_to_group", methods=["POST"])
@login_required
def add_league_to_group():
    if not request.form.get("league_id"):
        return apology("must provide league_id", BAD_REQUEST)

    league_id = int(request.form.get("league_id"))

    if not request.form.get("group_id"):
        return apology("must provide group_id", BAD_REQUEST)

    group_id = int(request.form.get("group_id"))

    result = db.execute("""
        INSERT INTO group_memberships (league_id, group_id) VALUES (:league_id, :group_id)
    """, league_id=league_id, group_id=group_id)

    if result == None:
      flash("Could not add league to group", "danger")
    else:
      flash("Successfully added league to group", "success")
    return redirect("/group?id=" + str(group_id))

@app.route("/group", methods=["GET"])
@login_required
def grp():
    if not request.args.get("id"):
        return apology("must provide id", BAD_REQUEST)

    group_id = int(request.args.get("id"))

    grp_result = db.execute("""
        SELECT id, name FROM groups WHERE id = :group_id
    """, group_id=group_id)

    if len(grp_result) == 1:
      grp_result = grp_result[0]
    else:
      return apology("could not find group with that ID", NOT_FOUND)

    leagues_result = db.execute("""
	SELECT leagues.name FROM group_memberships JOIN leagues ON leagues.id = group_memberships.league_id
        WHERE group_memberships.group_id = :group_id
    """, group_id=group_id)


    not_leagues_result = db.execute("""
        SELECT leagues.id, leagues.name FROM leagues WHERE leagues.id NOT IN (SELECT league_id FROM group_memberships WHERE
        group_id = :group_id)
    """, group_id=group_id)


    print "LEAGUES RESULT", leagues_result
    print "GRP RESULT", grp_result
    print "GROUP ID", group_id
    return render_template("group.html", leagues=leagues_result, grp=grp_result, grp_id=group_id, not_leagues=not_leagues_result)

@app.route("/groups", methods=["GET"])
@login_required
def groups():
    groups_result = db.execute("""
        SELECT id, name FROM groups
    """)
    return render_template("groups.html", grps=groups_result)

@app.route("/users", methods=["GET"])
@login_required
def users():
    users_result = db.execute("""
        SELECT id, username, admin FROM users
    """)
    return render_template("users.html", users=users_result)

@app.route("/teams_for_division", methods=["GET"])
@login_required
def teams_for_division():

    if not request.args.get("division_id"):
        return apology("must provide division_id", BAD_REQUEST)

    division_id = int(request.args.get("division_id"))

    teams_result = db.execute("""
        SELECT teams.id as team_id, leagues.name as league_name, teams.name as team_name FROM teams
        LEFT JOIN leagues ON leagues.id = teams.league_id
        WHERE division_id = :division_id
    """, division_id=division_id)

    return jsonify(teams_result)

@app.route("/add_league", methods=["POST"])
@login_required
def add_league():
    if not request.form.get("league_name"):
      return apology("must provide league name", BAD_REQUEST)
    league_name = str(request.form.get("league_name"))

    print league_name

    league_id = db.execute("""
	INSERT INTO leagues (name) VALUES (:name)
    """, name=league_name)

    if league_id == None:
      flash("Could not create league", "danger")
    else:
      flash("Successfully created league with id " + str(league_id), "success")
    return redirect("/add")

@app.route("/add_group", methods=["POST"])
@login_required
def add_group():
    if not request.form.get("name"):
      return apology("must provide group name", BAD_REQUEST)
    name = str(request.form.get("name"))

    group_id = db.execute("""INSERT INTO groups (name) VALUES (:name)""",
    name=name)

    if group_id == None:
      flash("Could not create group", "danger")
    else:
      flash("Successfully created group with id " + str(group_id), "success")
    return redirect("/groups")

@app.route("/add_team", methods=["POST"])
@login_required
def add_team():
    if not request.form.get("division_id"):
      return apology("must provide division id", BAD_REQUEST)
    division_id = int(request.form.get("division_id"))

    if not request.form.get("league_id"):
      return apology("must provide league id", BAD_REQUEST)
    league_id = int(request.form.get("league_id"))

    if not request.form.get("name"):
      return apology("must provide name")

    name = str(request.form.get("name"))

    team_id = db.execute("""INSERT INTO teams (league_id, division_id, name) VALUES (:league_id, :division_id, :name)""",
	league_id=league_id, division_id=division_id, name=name)

    if team_id == None:
      flash("Could not create team", "danger")
    else:
      flash("Successfully created team with id " + str(team_id), "success")
    return redirect("/add")

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
        SELECT * FROM groups
        JOIN (SELECT * FROM application_settings LIMIT 1) application_settings ON 1
        JOIN teams ON teams.id = :team_id
        JOIN group_memberships ON group_memberships.league_id = teams.league_id AND group_memberships.group_id = groups.id
        LEFT JOIN team_group_strength_ratings tgsr ON tgsr.group_id = groups.id AND tgsr.team_id = :team_id AND
	tgsr.batch_id =  application_settings.strength_rating_batch_id
    """, team_id=team_id)

    print team_strength_ratings_result

    games_result = db.execute("""
        SELECT *, l1.name as l1_name, l2.name as l2_name FROM games 
        JOIN game_ranking_points ON game_id = games.id
	JOIN game_types ON game_types.id = game_type_id
	JOIN teams t1 ON t1.id = games.team1_id
	JOIN teams t2 ON t2.id = games.team2_id
	JOIN leagues l1 ON l1.id = t1.league_id
	JOIN leagues l2 ON l2.id = t2.league_id
        WHERE team1_id = :team_id OR team2_id = :team_id
	ORDER BY game_date DESC
    """, team_id=team_id)


    team["games"] = games_result
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
        leagues2.name as team2_league, team1_points, team2_points, team1_expulsions, team2_expulsions, username, entered_date
         FROM games
        JOIN game_types ON game_type_id = game_types.id
        JOIN teams team_1_data ON team_1_data.id = team1_id
        JOIN leagues ON leagues.id = team_1_data.league_id
        JOIN teams team_2_data ON team_2_data.id = team2_id
        JOIN leagues leagues2 ON leagues2.id = team_2_data.league_id
        JOIN divisions ON divisions.id = team_1_data.division_id
        LEFT JOIN users ON users.id = created_user_id
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
        SELECT games.id as game_id, game_date, game_type, divisions.name as division,
        leagues.name as team1_league, team_1_data.name as team1_name,
        leagues2.name as team2_league, team_2_data.name as team2_name, team1_points, team2_points
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

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "GET":
      divisions_result = db.execute("""
          SELECT * FROM divisions
      """)
      leagues_result = db.execute("""
          SELECT id, name FROM leagues
      """)

      teams_result = db.execute("""
          SELECT id, teams.name as name, leagues.name as league_name, divisions.name as division_name FROM teams
	  JOIN divisions ON divisions.id = teams.division_id
	  JOIN leagues ON leagues.id = teams.league_id
      """)

      teams_by_league = defaultdict(lambda: defaultdict(lambda: []))

      for team in teams_result:
        teams_by_league[team["league_name"]][team["division_name"]].append({
          "name": team["name"],
          "division": team["division_name"],
          "id": team["id"],
        })

      print teams_by_league


      return render_template("add.html", divisions=divisions_result, leagues=leagues_result)



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
      teams_result = db.execute("""
        SELECT teams.id as team_id, leagues.name as league_name, teams.name as team_name FROM teams
        LEFT JOIN leagues ON leagues.id = teams.league_id
      """)
      return render_template("enter.html", divisions=divisions_result, game_types=game_types_result, teams=teams_result)
    else:
        if not request.form.get("game_type_id"):
            return apology("must provide game_type_id", BAD_REQUEST)

        game_type_id = int(request.form.get("game_type_id"))

        if not request.form.get("game_date"):
            return apology("must provide game date", BAD_REQUEST)

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

        if team1_id == team2_id:
            return apology("a team cannot play itself", BAD_REQUEST)

        sr_results = db.execute("""
		SELECT common_groups.group_id as group_id, t1.strength_rating team1, t2.strength_rating team2 FROM (
			SELECT t1.group_id FROM group_memberships t1
			JOIN (
				SELECT group_memberships.* FROM teams
				JOIN group_memberships ON group_memberships.league_id = teams.league_id
				WHERE teams.id = :team2_id
			) t2 ON t2.group_id = t1.group_id
			JOIN teams ON teams.id = :team1_id
			WHERE t1.league_id = teams.league_id
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

	print "TEAM 1 RANKING POINTS", team1_ranking_points
	print "TEAM 2 RANKING POINTS", team2_ranking_points

        game_id = db.execute("""INSERT INTO games (game_date, game_type_id, team1_id, team1_points,
            team1_expulsions, team2_id, team2_points,
            team2_expulsions, created_user_id) VALUES (:game_date, :game_type_id,
            :team1_id, :team1_points, :team1_expulsions,
            :team2_id, :team2_points, :team2_expulsions, :user_id)""",
        game_date=game_date, game_type_id=game_type_id,
        team1_id=team1_id, team1_points=team1_points, team1_expulsions=team1_expulsions,
        team2_id=team2_id, team2_points=team2_points, team2_expulsions=team2_expulsions,
        user_id=session["user_id"])

	for group_id in team1_ranking_points:
		team1_group_rp = team1_ranking_points[group_id]
		team2_group_rp = team2_ranking_points[group_id]

		result = db.execute("""INSERT INTO game_ranking_points (game_id, group_id, team1_ranking_points, team2_ranking_points)
			VALUES (:game_id, :group_id, :team1_group_rp, :team2_group_rp)
		""", game_id=game_id, group_id=group_id, team1_group_rp=team1_group_rp, team2_group_rp=team2_group_rp)

        return redirect("/games")

def fetch_batch_rankings(batch_id, group_id):
	result = db.execute("""
		SELECT league_id, team_id, group_id, divisions.name as division_name, leagues.name as league_name, division_id, ranking_point_average, teams.name as name
		FROM team_group_rankings
		JOIN teams ON teams.id = team_id
                JOIN divisions ON divisions.id = teams.division_id
                JOIN leagues ON leagues.id = teams.league_id
                JOIN groups ON groups.id = group_id
                WHERE group_id = :group_id AND batch_id = :batch_id
        """, group_id=group_id, batch_id=batch_id)

	division_group_rankings = defaultdict(lambda: [])

	for row in result:
		division_group_rankings[row["division_name"]].append({
			"league_id": row["league_id"],
			"league": row["league_name"],
			"rp_average": row["ranking_point_average"],
			"name": row["name"]
		})

	return division_group_rankings

def fetch_batch_strengths(batch_id, group_id):
	result = db.execute("""
		SELECT league_id, team_id, group_id, divisions.name as division_name, leagues.name as league_name, division_id, strength_rating, teams.name as name
		FROM team_group_strength_ratings
		JOIN teams ON teams.id = team_id
                JOIN divisions ON divisions.id = teams.division_id
                JOIN leagues ON leagues.id = teams.league_id
                JOIN groups ON groups.id = group_id
                WHERE group_id = :group_id AND batch_id = :batch_id
        """, group_id=group_id, batch_id=batch_id)

	division_group_strengths = defaultdict(lambda: [])

	for row in result:
		division_group_strengths[row["division_name"]].append({
			"league_id": row["league_id"],
			"league": row["league_name"],
			"strength_rating": row["strength_rating"],
			"name": row["name"]
		})

	return division_group_strengths

@app.route("/strengths", methods=["GET"])
@login_required
def sr_batch():

    groups_result = db.execute("SELECT id, name FROM groups")
    group_names = {}
    for row in groups_result:
        group_names[str(row["id"])] = row["name"]

    batches_result = db.execute("SELECT id, name FROM strength_rating_batches")
    batch_names = {}
    for row in batches_result:
        batch_names[str(row["id"])] = row["name"]

    group_id_raw = request.args.get("group_id")
    if group_id_raw:
      group_id = int(group_id_raw)
    else:
      group_id = 1

    batch_id_raw = request.args.get("batch_id")
    if batch_id_raw:
      batch_id = int(batch_id_raw)
    else:
      current_batch_result = db.execute("""
        SELECT strength_rating_batch_id FROM application_settings LIMIT 1
      """)

      if len(current_batch_result) != 1:
        # TODO: handle error
        pass

      batch_id = int(current_batch_result[0]["strength_rating_batch_id"])

    division_group_strengths = fetch_batch_strengths(batch_id, group_id)
    print division_group_strengths, "DIVISION GROUP STRENGTHS"
    return render_template("strengths.html", group_names=group_names, division_group_strengths=division_group_strengths, grp_id=str(group_id), batch_id=str(batch_id), batch_names=batch_names)


    if not request.args.get("id"):
       return apology("must provide id", BAD_REQUEST)

    batch_id = int(request.args.get("id"))

    batch_result = db.execute("""
        SELECT team_id, teams.name as team_name, leagues.name as league_name, divisions.name as division_name, group_id, groups.name as group_name, strength_rating FROM team_group_strength_ratings
        JOIN teams ON teams.id = team_id
        JOIN divisions ON teams.division_id = divisions.id
        JOIN leagues ON teams.league_id = leagues.id
        JOIN groups ON groups.id = group_id
        WHERE batch_id = :batch_id
    """, batch_id=batch_id)

    groups_for_league = db.execute("""

    """)

    batch = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: None))))
    for row in batch_result:
      batch[row["division_name"]][row["league_name"]][row["team_name"]][row["group_name"]] = {
        "team_id": row["team_id"],
        "group_id": row["group_id"],
        "strength_rating": row["strength_rating"]
      }
    print batch

    return render_template("batch.html", batch=batch)

@app.route("/switch_to_batch", methods=["GET"])
@login_required
def switch_to_batch():

    if not request.args.get("id"):
       return apology("must provide id", BAD_REQUEST)

    batch_id = int(request.args.get("id"))

    lookup_batch_result = db.execute("""
        SELECT id FROM strength_rating_batches WHERE id = :id
    """, id=batch_id)

    if len(lookup_batch_result) != 1:
         return apology("batch does not exist", BAD_REQUEST)

    result = db.execute("""
      UPDATE application_settings SET strength_rating_batch_id = :batch_id
    """, batch_id=batch_id)

    if result == None:
      flash("Could not switch the batch", "danger")
    else:
      flash("Successfully switched to batch " + str(batch_id), "success")

    return redirect("/sr_batches")

@app.route("/sr_batches", methods=["GET"])
@login_required
def sr_batches():
    batches_result = db.execute("""
        SELECT id, name, start_date, end_date, computed_on FROM strength_rating_batches
    """)

    current_batch_result = db.execute("""
	SELECT strength_rating_batch_id FROM application_settings LIMIT 1
    """)

    if len(current_batch_result) != 1:
	# TODO: handle error
	pass

    current_batch = current_batch_result[0]["strength_rating_batch_id"]

    return render_template("batches.html", batches=batches_result, current_batch=current_batch)

@app.route("/recalculate", methods=["POST", "GET"])
@login_required
def recalculate():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        start_date_raw = request.form.get("start_date")
        end_date_raw = request.form.get("end_date")

        rankings_start_date_raw = request.form.get("start_date")
        rankings_end_date_raw = request.form.get("end_date")
        sr_name = str(request.form.get("strength_rating_memo"))
        print start_date_raw, end_date_raw, sr_name

        start_date = datetime.datetime.strptime(start_date_raw, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date_raw, "%Y-%m-%d")

        rankings_start_date = datetime.datetime.strptime(rankings_start_date_raw, "%Y-%m-%d")
        rankings_end_date = datetime.datetime.strptime(rankings_end_date_raw, "%Y-%m-%d")

	computed_on = datetime.datetime.now()

        batch_id = db.execute("""INSERT INTO strength_rating_batches (name, start_date, end_date, computed_on) VALUES (:sr_name, :start_date, :end_date, :computed_on)""",
		  sr_name=sr_name, start_date=start_date, end_date=end_date, computed_on=computed_on)

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


	db.execute("""

		WITH has_strength_now AS (
			SELECT team_id, group_id, strength_rating IS NOT NULL as has_strength_rating FROM team_group_strength_ratings
			JOIN application_settings ON batch_id = strength_rating_batch_id
		), ranking_point_averages AS (
		        SELECT team_id, group_id,
                	        SUM(1.0 * team_game_group_ranking_points) / COUNT(*) as ranking_point_average, COUNT(*) num_games FROM
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


		)
		INSERT INTO team_group_rankings (batch_id, team_id, group_id, ranking_point_average)
		SELECT :batch_id, rpa.team_id, rpa.group_id, 
		CASE WHEN num_games >= 3 OR (has_strength_rating AND num_games >= 2) THEN -- eligible 
		ranking_point_average * 1.0 ELSE
		NULL END as ranking_point_average
		FROM ranking_point_averages rpa
		JOIN teams ON teams.id = rpa.team_id
        JOIN has_strength_now ON has_strength_now.team_id = teams.id AND has_strength_now.group_id = rpa.group_id

	""", batch_id=batch_id, start_date=rankings_start_date, end_date=rankings_end_date)

        result = db.execute("""
           UPDATE application_settings SET strength_rating_batch_id = :batch_id
        """, batch_id=batch_id)

        return redirect("/sr_batches")
    else:
        return render_template("recalculate.html")



@app.route("/rankings", methods=["GET"])
@login_required
def rankings():

    groups_result = db.execute("SELECT id, name FROM groups")
    group_names = {}
    for row in groups_result:
        group_names[str(row["id"])] = row["name"]

    batches_result = db.execute("SELECT id, name FROM strength_rating_batches")
    batch_names = {}
    for row in batches_result:
        batch_names[str(row["id"])] = row["name"]

    group_id_raw = request.args.get("group_id")
    if group_id_raw:
      group_id = int(group_id_raw)
    else:
      group_id = 1

    batch_id_raw = request.args.get("batch_id")
    if batch_id_raw:
      batch_id = int(batch_id_raw)
    else:
      current_batch_result = db.execute("""
        SELECT strength_rating_batch_id FROM application_settings LIMIT 1
      """)

      if len(current_batch_result) != 1:
        # TODO: handle error
        pass

      batch_id = int(current_batch_result[0]["strength_rating_batch_id"])

    division_group_rankings = fetch_batch_rankings(batch_id, group_id)
    print division_group_rankings, "DIVISION GROUP RANKINGS"
    return render_template("rankings.html", group_names=group_names, division_group_rankings=division_group_rankings, grp_id=str(group_id), batch_id=str(batch_id), batch_names=batch_names)

def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
