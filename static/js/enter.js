$(function () {

	var leagueSelectTmplHtml = $("#leagues_select_menu_template").html();
	var leagueSelectTmpl = _.template(leagueSelectTmplHtml);
	$("#division_select").change(function () {
		var select = $(this);
		$.get({
			url: "/leagues_for_division",
			data: {
				division_id: select.val(),
			},
			success: function (data) {
				var team1Select = leagueSelectTmpl({
					leagues: data,
				});
				var team2Select = leagueSelectTmpl({
					leagues: data,
				});
				$("#team_1_select").html(team1Select);
				$("#team_2_select").html(team2Select);
			}
		})
	})
});
