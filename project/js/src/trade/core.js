var Trade = {
	init: function () {
		Trade.init_list_actions();
	},
	
	init_list_actions: function () {
		$('#trade-list-grid .trade-list-action').each(function (index, a) {
			$(a)
			.data('_action', $(a).attr('href'))
			.attr('href', '#')
			.click(function () {
				var href = $(this).data('_action');
				jQuery.getJSON(href, function (data, status) {
					if (status != 'success')
						return;
					$('#trade-list-grid').empty().append(data.html);
					$('.trade-list-size').empty().text(data.trade_list.size);
          $('.lists-size').empty().text(data.lists_size);
					Trade.init_list_actions();
				});
				return false;				
			});
		});
	}
};

$(document).ready(function () {
	Trade.init();	
});
