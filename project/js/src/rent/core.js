var Rent = {
	init: function () {
		Rent.init_list_actions();
		Rent.init_search_widget();
	},
	
	init_list_actions: function () {
		$('.list-page .rating a').click(function () {
            var a = $(this),
                href = a.attr('href');
			jQuery.getJSON(href, function (data, status) {
                if (status != 'success')
                    return;
				a.parents('ul.rating').removeClass('stars0 stars1 stars2 stars3 stars4 stars5')
				    .addClass('stars' + data.ratio.rating);
			});
			return false;
		});
		
		$('.rent-list-action').each(function (index, a) {
			$(a)
			.data('_action', $(a).attr('href'))
			.attr('href', '#')
			.click(function () {
				var href = $(this).data('_action');
				jQuery.getJSON(href, function (data, status) {
					if (status != 'success')
						return;
					if (data.message) {
						alert(data.message);
						return;
					}
					$('#rent-list-grid').empty().append(data.html);
					$('.rent-list-size').empty().text(data.rent_list.size);
					$('.lists-size').empty().text(data.lists_size);
					Rent.init_list_actions();
				});
				return false;				
			});
		});
		
		var disableDnD;
		
		$('.item-notes a').each(function (index, a) {
			var a = $(a);
			a.click(function () { return false; });
			a.editable(a.attr('href'), {
				name: 'notes',
				width: 150,
				height: 18,
				placeholder: 'add note',
				onblur: 'submit',
				onedit: function () { disableDnD = true; },
				onsubmit: function () { disableDnD = false; },
				onreset: function () { disableDnD = false; }
			});
		});
		
		$('.rent-list-page #rent-list-table').tableDnD({
			onDragClass: 'dragging',
			onDrop: function(table, row) {
				if (disableDnD) {
					$('.item-notes input').blur();
					return;
				}
				row = $(row);
				var rowId = row.attr('id');
				$(table).find('tr').each(function (index, r) {
					if ($(r).attr('id') == rowId) {
						var id = rowId.split('-')[2],
							href = '/Rent/Move-To/' + id + '/' + (index - 1) + '/';
						jQuery.getJSON(href, function (data, status) {
							if (status != 'success')
								return;
							$('#rent-list-grid').empty().append(data.html);
							$('.rent-list-size').empty().text(data.rent_list.size);
							Rent.init_list_actions();
						});
						return false;
					}
				});
			}
		});
	},
	
	init_search_widget: function () {
		$('.list-page #add-by-upc-widget input[type="text"]').each(function(index, input){
			$(input)
				.searchbox('Enter Game Title or UPC')
				.autocomplete('/Search/By-UPC/', {
					maxItemsToShow: 5,
					matchContains: 1,
					width: 500,
					
					onItemSelect: function (li) {
						if (li == null) 
							return;
						$(input).wipeSearchBox();
						var id = li.extra[0],
							loc = window.location.toString(),
							action = null;
						if (/\/Rent\/List\/$/.test(loc)) {
							action = '/Rent/Add/' + id + '/';
						}
						else if (/\/Trade\/List\/$/.test(loc)) {
							action = '/Trade/Add/' + id + '/';
						}
						else if (/\/Buy\/List\/$/.test(loc)) {
							action = '/Cart/Add/' + id + '/';
						}
						else
							return;
						
						$.fn.openWizardByUrl(action);
					}
			});
		});
	}
};

$(document).ready(function () {
	Rent.init();

    var total = $('#list-banner-rotator img').length;
    var rand = Math.floor(Math.random() * total);

    $('#list-banner-rotator').nivoSlider({
        pauseTime: 8000,
        directionNav: false,
        controlNav: false,
		startSlide: rand
    });
});
