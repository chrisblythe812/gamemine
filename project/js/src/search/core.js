var Search = {
	init: function () {
		Search.init_links();
	},
	
	init_links: function () {
		$('#search-results .paginator a').click(function () {
			$('#search-results').empty().addClass('loading');

			var a = $(this);
			jQuery.get(a.attr('href'), function (data, status) {
				if (status != 'success')
					return;
				$('#search-results')
					.removeClass('loading')
					.append(data);
				Search.init_links();
			});
			return false;
		});
		
		$('.subinfo select').change(function () {
			$('#search-results').empty().addClass('loading');
			var s = $(this),
				loc = window.location;
			jQuery.post(loc, {order_by: s.val()}, function (data, status) {
				if (status != 'success')
					return;
				$('#search-results')
					.removeClass('loading')
					.append(data);
				Search.init_links();
			});
		});
		
    $.fn.prepareLinks();
	}
};

$(document).ready(function () {
	Search.init();	
});
