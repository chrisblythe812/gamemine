var BuyIntro2 = {
    updatePaginatorLinks: function () {
        	$('.intro2-page .paginator a').click(function () {
    		BuyIntro2.requestContent($(this).text());
			return false;
		});
	},

	requestContent: function (page) {
    	function getId(v) {
    		v = v.split('-');
    		v = v[v.length - 1];
    		return v;
    	}

    	function getIds(s) {
    		var ids = [];
    		$(s).each(function () { ids.push(getId($(this).attr('id'))); });
    		return ids.join(',');
    	}

    	function pushParams(p, n, s) {
    		var c = getIds(s);
    		if (c) {
    			p.push(n + '=' + c);
    		}
    	}

    	var p = [];

    	var q = $('.search-area #search-query').val();
    	if (q == 'Title, Publisher, UPC')
    		q = '';
    	if (q) {
    		p.push('q=' + escape(q));
    	}
    	else if ($('#trade-100').attr('checked')) {
    		$.get('?wimgw', function (data, status) {
    			if (status != 'success') {
    				alert('Error');
    				return;
    			}
    			$('#intro-wimgw-page-content-center').html(data);
    		});
    	}

    	var c = $('.banner-categories a.selected');
    	if (c.size() > 0) {
    		p.push('c=' + c.parent().attr('id').split('-').slice(2).join('-'));
    	}
    	pushParams(p, 'g', '#genres-filter input.other:checked');
    	pushParams(p, 'y', '#years-filter input.other:checked');
    	pushParams(p, 'r', '#rating-filter input.other:checked');
    	pushParams(p, 'pr', '#price-filter input.other:checked');
    	pushParams(p, 't', '#trade-filter input.other:checked');
    	pushParams(p, 'a', '#availability-filter input.other:checked');
    	pushParams(p, 'e', '#esrb-filter input.other:checked');

    	c = $('#coming-filter input:checked').attr('id');
    	if (c) {
    		p.push('cs=' + getId(c));
    	}

    	if (page) {
    		p.push('p=' + escape(page));
    	}

    	var href = '?' + p.join('&');
    	if (q) {
    	    var target = $('#intro-wimgw-page-content-center');
    		target.load(href);
    	    $('html, body').animate({scrollTop: target.offset().top}, 500);
    	} else {
        	if ($('#catalog-grid').size() == 0) {
            	$('#intro-wimgw-page-content-center').html('<div id="catalog-grid"><div id="catalog-grid-title"><div class="paginator"></div></div><div id="catalog-grid-content"><ul class="catalog-items"></ul></div><div id="catalog-grid-footer"><div class="paginator"></div></div></div>');
        	}
        	Catalog.requestItems(href, {
        		afterComplete: BuyIntro2.updatePaginatorLinks
        	});
    	}
    },

    updateFilters: function (skip_request) {
    	skip_request = skip_request || false;
    	$('.intro2-page').find('.checkbox-block-type-1 input[type=checkbox], .checkbox-block-type-2 input[type=checkbox], .checkbox-block-type-3 input[type=checkbox]').each(function () {
    		if ($(this).attr('checked')) {
    			$(this).parent().addClass('checked');
    		} else {
    			$(this).parent().removeClass('checked');
    		}
    	});

    	if ($('#intro-browse-games-page-content #price-filter .other:checked').size())
    		$('#intro-browse-games-page-content #catalog-sidebar-banners').show();
    	else
    		$('#intro-browse-games-page-content #catalog-sidebar-banners').hide();

    	if (!skip_request)
    		BuyIntro2.requestContent();
    },

    initCarouselSwitchers: function () {
    	var doRequest = function (what) {
    		return function () {
                random_string = new Date().getTime();
    			var href = introConfig.wimgwURL + '?r=' + random_string + '&carousel=' + what;
    			if (catalogConfig.currentCategory) {
    				href += '&c=' + catalogConfig.currentCategory;
    			}
    			$.get(href, function (data, status) {
    				if (status != 'success')
    					return;

    				data = $(data);
    				$('.intro2-page .banner-carousel').empty().removeClass('rent trade buy').addClass(what).append(data);
    				$('#intro-carousel').jcarousel({
        				scroll: 5,
        				itemFallbackDimension: 120
        		    });
    				BuyIntro2.initCarouselSwitchers();
    			});
    			return false;
    		};
    	},
    	requestMostRentals = doRequest('rent'),
    	requestHottestTradeIns = doRequest('trade'),
    	requestBestSellers = doRequest('buy');

    	$('.intro2-page .banner-carousel #switchto-most-rentals').click(requestMostRentals);
    	$('.intro2-page .banner-carousel #switchto-hottest-tradins').click(requestHottestTradeIns);
    	$('.intro2-page .banner-carousel #switchto-best-sellers').click(requestBestSellers);
    }
};

jQuery(document).ready(function (){
    jQuery('#intro-new-releases-carousel').jcarousel({
		scroll: 4,
		itemFallbackDimension: 55
    });

    $('.intro2-page #intro-carousel').jcarousel({
		scroll: 5,
		itemFallbackDimension: 120
    });

    /* New Buy Page */

    BuyIntro2.updatePaginatorLinks();
    BuyIntro2.initCarouselSwitchers();

    $('.intro2-page').find('#coming-filter input[type=checkbox]').click(function () {
    	$('.intro2-page #trade-100').attr('checked', false);
    	if ($('#coming-filter input:checked').size() > 0) {
    		$('#years-filter input.first').attr('checked', true);
    		$('#years-filter input.other').attr('checked', false);
    		BuyIntro2.updateFilters(true);
    	}
    });

    $('.intro2-page').find('#years-filter input.other').click(function () {
    	$('.intro2-page #trade-100').attr('checked', false);
    	if ($('#years-filter input.other:checked').size() > 0) {
    		$('#coming-filter input[type=checkbox]').attr('checked', false);
    		BuyIntro2.updateFilters(true);
    	}
    });

    $('.intro2-page').find('.checkbox-block-type-1').each(function () {
    	var block = $(this);

    	block.find('input[type=checkbox].first').click(function () {
    		$('.intro2-page #trade-100').attr('checked', false);
    		var others = block.find('input[type=checkbox].other:checked');
        	if (others.size() == 0) {
        		$(this).attr('checked', true);
        	} else if ($(this).attr('checked')) {
        		others.attr('checked', false);
        	}
        	BuyIntro2.updateFilters();
    	});

    	block.find('input[type=checkbox].other').click(function () {
    		$('.intro2-page #trade-100').attr('checked', false);
    		var first = block.find('input[type=checkbox].first');
        	first.attr('checked', block.find('input[type=checkbox].other:checked').size() == 0);
        	BuyIntro2.updateFilters();
    	});
    });

    $('.intro2-page').find('.checkbox-block-type-2').each(function () {
    	var block = $(this);

    	block.find('input[type=checkbox].other').click(function () {
        	$('.intro2-page #trade-100').attr('checked', false);

        	if ($('#intro-browse-games-page-content').size()) {
        		var b1, b2, b3;
        		if (block.find('#price-filter').size()) {
        			b1 = '#price-filter';
        			b2 = '#trade-filter';
        			b3 = '#availability-filter';
        		}
        		else if (block.find('#trade-filter').size()) {
        			b1 = '#trade-filter';
        			b2 = '#price-filter';
        			b3 = '#availability-filter';
        		}
        		else if (block.find('#availability-filter').size()) {
        			b1 = '#availability-filter';
        			b2 = '#price-filter';
        			b3 = '#trade-filter';
        		}
        		if ($(b1).find('input:checked').size()) {
        			$(b2).find('input[type=checkbox]').attr('checked', false);
        			$(b3).find('input[type=checkbox]').attr('checked', false);
        		}
        	}

        	BuyIntro2.updateFilters();
    	});
    });

    $('.intro2-page').find('.checkbox-block-type-3').each(function () {
    	var block = $(this);

    	block.find('input[type=checkbox]').click(function () {
        	$('.intro2-page #trade-100').attr('checked', false);
    		var c = $(this).attr('checked');
    		block.find('input:checked').attr('checked', false);
    		$(this).attr('checked', c);
    		BuyIntro2.updateFilters();
    	});
    });

    $('.intro2-page').find('.banner-categories a').click(function () {
    	$('.intro2-page #trade-100').attr('checked', false).parent().removeClass('checked');
    	$('.banner-categories a').removeClass('selected');
    	$(this).addClass('selected');
    	BuyIntro2.requestContent();
    	return false;
    });

    $('.intro2-page #trade-100').click(function () {
    	var c = $(this).attr('checked');
		$('#catalog-sidebar input:checked').attr('checked', false);
    	if (c) {
    		$(this).attr('checked', true);
    		$('.banner-categories a').removeClass('selected');
    	} else {
    		$('#genres-filter .first, #years-filter .first').attr('checked', true);
    	}
    	BuyIntro2.updateFilters();
    });

    $('#goto-wimgw').click(function () {
    	window.location = '/What-is-My-Game-Worth/';
    	return false;
    });

    $('#intro-browse-games-page-content #catalog-sidebar-banners').hide();
});
