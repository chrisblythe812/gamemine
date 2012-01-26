var OloloSearch = {
	init: function () {
		OloloSearch._input = $('#header-search-box input[type=text]');
		OloloSearch._input
            .delayChange(function () {
	            var val = $.trim($(this).val());
	            if (val === '') {
	                OloloSearch.cancelSearch();
	                return;
	            }
				OloloSearch.search(val);
	        })
			.blur(function () {
				setTimeout(OloloSearch.cancelSearch, 500);
			});
	},
    
	_input: null,
    _ajaxRequest: null,
    _container: null, 
	
	cancelRequest: function () {
        if (OloloSearch._ajaxRequest) {
			OloloSearch._ajaxRequest.abort();
			OloloSearch._ajaxRequest = null;
		}
	},

	cancelSearch: function () {
        OloloSearch.cancelRequest();
        OloloSearch.getResultsContainer().hide();	
	},
    
	search: function (q) {
		OloloSearch.cancelRequest();
		
		var href = '/Search/Quick/?q=' + q;
        OloloSearch.getResultsContainer().find('#ololo-results-footer a')
            .attr('href', '/Search/?q=' + q);
		OloloSearch._ajaxRequest = jQuery.getJSON(href, function (data, status) {
            if (!data)
                return;
			OloloSearch.displayItems(data.items);
			OloloSearch._ajaxRequest = null;
		});
	},
	
	displayItems: function (items) {
		function getItemDisplay(item) {
			return $($.LI({},
                $.A({href: item.url}, 
				    $.IMG({src: item.icon}), 
					$.SPAN({Class: 'title'}, item.title),
					$.SPAN({Class: 'upc'}, item.upc),
					$.SPAN({Class: 'release-date'}, item.release_date)
				)
			));
		}
		
		var container = OloloSearch.getResultsContainer(),
            ul = container.find('ul');
		ul.empty();
		for (i in items) {
			ul.append(getItemDisplay(items[i]));
		}
		container.show();
	},
	
	getResultsContainer: function () {
		if (OloloSearch._container)
            return OloloSearch._container;
        OloloSearch._container = $(
            $.DIV({id: 'ololo-results-popup'}, 
                $.UL({}),
				$.DIV({id: 'ololo-results-footer'}, 
				    $.A({href: '#'}, 'View All Search Results')
				)
			));
		OloloSearch._container.hide();
		
		var inputOffset = OloloSearch._input.offset();
		OloloSearch._container.css({
            left: inputOffset.left + OloloSearch._input.width() - 260 + 8,
			top: inputOffset.top + OloloSearch._input.height() + 5
		});
		
		$('body').append(OloloSearch._container);
		return OloloSearch._container;
	}
}

$(document).ready(function () {
    OloloSearch.init();	
});
