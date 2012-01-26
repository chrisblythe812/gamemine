var Profile = {
    init: function () {
		Profile.init_grid_actions();
	}, 
	
	init_grid_actions: function () {
		$('.profile-page-with-grid .page-with-grid-content a.grid-action').click(function () {
			var href = $(this).attr('href');
			jQuery.getJSON(href, function (data, status) {
				if (status != 'success')
				    return;
				var c = $('.profile-page-with-grid .page-with-grid-content');
				c.find('table').remove();
				c.append(data.table);
				Profile.init_grid_actions();
			});
			return false;
		});
	}	
}

$(document).ready(function () {
    Profile.init();    
});
