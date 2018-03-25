$(function () {
	$("#league_select").change(function () {
		var select = $(this);
		$.get({
			url: "/divisions_for_league",
			data: {
				league_id: select.val(),
			},
			success: function (data) {
				console.log(data);
			}
		})
	})
});
