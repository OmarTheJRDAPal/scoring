$(function () {

	var teamSelectTmplHtml = $("#teams_select_menu_template").html();
	var teamSelectTmpl = _.template(teamSelectTmplHtml);
	$("#division_select").change(function () {
		var select = $(this);
		$.get({
			url: "/teams_for_division",
			data: {
				division_id: select.val(),
			},
			success: function (data) {
				var team1Select = teamSelectTmpl({
					teams: data,
				});
				var team2Select = teamSelectTmpl({
					teams: data,
				});
				$("#team_1_select").html(team1Select);
				$("#team_2_select").html(team2Select);
			}
		})
	})
});
