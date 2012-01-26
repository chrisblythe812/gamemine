var Catalog = {

  filters: ['new-releases', 'best-sellers', 'top-trades', 'top-rentals', 'coming-soon'],
  filtersObject: null,

  init: function () {
    Catalog.filtersObject = {};
    for (var i = 0; i < Catalog.filters.length; ++i)
      Catalog.filtersObject[Catalog.filters[i]] = '';
  },

  createCatalogNode: function (item) {
    var
    id = item.id || 0,
    short_name = item.short_name || '',
    name = item.name || '',
    href = item.url || '#',
    cover = item.cover || null,
    actions = item.actions || [];

    var node = $(
      $.DIV({Class: 'catalog-item-record'},
	    $.DIV({Class: 'catalog-item-cover empty'},
		  $.A({title: name, href: href}, short_name)),
	    $.DIV({Class: 'catalog-item-title'},
		  $.A({title: name, href: href}, short_name),
		  $.DIV({Class: 'catalog-item-title-overlay'})
		 ),
	    $.DIV({Class: 'catalog-item-actions'})
	   ));

    if (item.category) {
      node.find('.catalog-item-actions').before($.DIV({Class: 'catalog-item-category'}, item.category));
    }

    if (item.price) {
      node.find('.catalog-item-actions').before($.DIV({Class: 'catalog-item-price'}, $.SPAN({}, item.price)));
      if (item.pre_owned) {
	node.find('.catalog-item-price span').addClass('pre_owned');
      }
    }

    if (item.rent_status) {
      node.find('.catalog-item-actions').before($.DIV({Class: 'catalog-item-rent-status'}, $.SPAN({}, item.rent_status)));
      if (item.is_top_rental) {
	node.find('.catalog-item-rent-status span').addClass('top-rentals');
      }
    }

    if (item.trade_value) {
      node.find('.catalog-item-actions').before($.DIV({Class: 'catalog-item-trade-value'}, $.SPAN({}, item.trade_value)));
      if (item.is_hot_trade) {
	node.find('.catalog-item-trade-value span').addClass('hot-trade');
      }
    }

    if (cover) {
      var cover_div = node.find('.catalog-item-cover');
      cover_div.removeClass('empty');
      cover_div.find('a').empty().append($.IMG({src: cover, width: item.cover_w || 140, height: item.cover_h || 190}));
    }

    var d = node.find('.catalog-item-actions');
    if (actions.buy)
      d.append($.A({href: actions.buy, Class: 'link-dialog catalog-item-action-buy', title: 'Buy'}, 'Buy'));
    if (actions.trade)
      d.append($.A({href: actions.trade, Class: 'link-dialog catalog-item-action-trade', title: 'Trade'}, 'Trade'));
    if (actions.rent)
      d.append($.A({href: actions.rent, Class: 'link-dialog catalog-item-action-rent', title: 'Rent'}, 'Rent'));
    return node;
  },

  showLoadedItems: function (items) {
    var catalog_grid_content = $('#catalog-grid-content');
    var ul = catalog_grid_content.find('ul.catalog-items');
    ul.empty();
    if (items.length) {
      ul.removeClass('empty');
    }
    else {
      ul.addClass('empty');
    }
    for (var i = 0; i < items.length; ++i)
    {
      var item = items[i];
      var node = Catalog.createCatalogNode(item);
      var li = $($.LI({Class: 'catalog-item', id: 'catalog-item-' + item.id}));
      li.append(node);
      ul.append(li).append(' ');
    }
    Catalog.initDetailsHint();
    $.fn.prepareLinks();
  },

  scrollToItems: function (){
    var target = $('#catalog-toolbar');
    $('body').animate({scrollTop: target.attr('offsetTop') - 9}, 500);
  },

  catalogRequest: null,

  requestItems: function(href, options) {
    $.details_hint.close();

    options = options || {};
    (options.beforeStart || jQuery.noop)();

    var catalog_grid_content = $('#catalog-grid-content');
    catalog_grid_content.addClass('loading');
    var paginator = $('.paginator');
    paginator.hide();

    if (Catalog.catalogRequest)
      Catalog.catalogRequest.abort();

    Catalog.catalogRequest = jQuery.getJSON(href, function (data, textStatus, xhr) {
      if (!xhr.status) return;

      (options.beforeRequest || jQuery.noop)();

      data = data || {};
      var status = data.status || 'Fail';
      if (status == 'OK')
      {
	Catalog.showLoadedItems(data.items || []);
	(options.afterRequest || jQuery.noop)();
	$("#offer_msg_buy").html(data.offer_msg_buy);
	$("#offer_msg_trade").html(data.offer_msg_trade);
      }
      else
      {
	// TODO: Show error message
	alert('Error');
      }
      catalog_grid_content.removeClass('loading');

      var s = '';
      var no_paginator = data.no_paginator || false;
      if (!no_paginator) {
	if (data.page_range.left_end) {
	  for (var i in data.page_range.left_end) {
	    if (i != '0') s += ' | ';
	    var n = data.page_range.left_end[i];
	    s += '<a href="?p=' + n + '">' + n + '</a>';
	  }
	  s += ' ... ';
	}
	for (var i in data.page_range.range) {
	  if (i != '0') s += ' | ';
	  var n = data.page_range.range[i];
	  if (n == data.page_number)
	    s += '<span class="current">' + n + '</span>';
	  else
	    s += '<a href="?p=' + n + '">' + n + '</a>';
	}
	if (data.page_range.right_end) {
	  s += ' ... ';
	  for (var i in data.page_range.right_end) {
	    if (i != '0') s += ' | ';
	    var n = data.page_range.right_end[i];
	    s += '<a href="?p=' + n + '">' + n + '</a>';
	  }
	}
	if (s != '' && data.show_all_link) {
	  s += ' | <a href="?p=show%20all">Show All</a>';
	}
      }
      paginator.html(s);

      paginator.show();
      Catalog.updatePaginatorLinks();
      (options.afterComplete || jQuery.noop)();
    });
  },

  quickGameSearchIn: (catalogConfig || {}).quickGameSearchIn || '/catalog/',

  findGameQuickly: function findGameQuickly(q, params, options){
    options = options || {};

    $('#catalog-toolbar-filter li.selected').removeClass('selected');

    params = params || {};
    page = parseInt(params.p) || 1;
    q = escape(q);

    window.urlRouter.quiteInvoke(function () {
      if (page == 1)
	window.location = '#quick-game-finder?q=' + q;
      else
	window.location = '#quick-game-finder?q=' + q + '&p=' + page;
    });

    var href= $('#catalog-toolbar-search form').attr('action') + '?q=' + q + '&p=' + page;
    Catalog.requestItems(href, options);
  },

  selectFilter: function (filter, params, options) {
    options = options || {};

    params = params || {};
    page = params.p || 1;

    window.urlRouter.quiteInvoke(function () {
      if (page == 1)
	window.location = '#' + filter;
      else
	window.location = '#' + filter + '?p=' + page;
    });

    var quickGameFinder = $('#catalog-toolbar-search input[type=text]');
    quickGameFinder.wipeSearchBox();

    var toolbar = $('#catalog-toolbar-filter');
    toolbar.find('li.selected').removeClass('selected');
    var a = toolbar.find('a[filterId=' + filter + ']');
    a.parent().addClass('selected');
    var href = a.attr('href') + '?p=' + page;

    Catalog.requestItems(href, options);
  },

  changePage: function(page) {
    var parts = window.urlRouter.splitLocation(window.location);

    var anchor = parts[1] || 'new-releases';
    var params = parts[2] || {};
    params.p = page;

    var options = {
      beforeStart: Catalog.scrollToItems
    };

    if (anchor in Catalog.filtersObject)
      Catalog.selectFilter(anchor, params, options);
    else if (anchor === 'quick-game-finder') {
      var q = params.q || '';
      Catalog.findGameQuickly(q, params, options);
    }
  },

  updatePaginatorLinks: function() {
    if ($('body').hasClass('intro2-page'))
      return;
    var paginator = $('.paginator');
    paginator.find('a').each(function() {
      var p = 1;
      $(this).attr('href').match(/\?(.+)$/);
      var params = RegExp.$1.split("&");
      for (var i = 0; i < params.length; i++) {
	var tmp = params[i].split("=");
	if (tmp[0] == 'p')
	  p = unescape(tmp[1]);
      }
      $(this).attr('href', '#');
      $(this).click(function(){
	Catalog.changePage(p);
	return false;
      });
    });
  },

  getItemHintContent: function (data)
  {
    var
    publisher = data.publisher || '',
    release_date = data.release_date || '',
    rating = data.rating || '',
    genres = data.genres || '',
    ratio = data.ratio || 'N/A',
    percents = data.percents + '%' || '0%',
    players = data.number_of_players || '—',
    cover = data.cover;

    var res = $(
      $.DIV({Class: 'item-hint'},
	    $.DIV({Class: 'item-hint-cover'}),
	    $.DIV({Class: 'item-hint-data'},
		  $.DL({},
		       $.DT({}, 'Publisher:'),
		       $.DD({}, publisher),

		       $.DT({}, 'Release:'),
		       $.DD({}, release_date),

		       $.DT({}, 'ESRB:'),
		       $.DD({}, rating),

		       $.DT({}, 'Players:'),
		       $.DD({}, players),

		       $.DT({}, 'Genres:'),
		       $.DD({}, genres)
		      )
		 ),
	    $.DIV({'Class': 'item-hint-rating'},
		  $.DIV({'Class': 'item-hint-ratio'}, ratio),
		  $.DIV({'Class': 'item-hint-rating'},
			$.DIV({'Class': 'item-hint-rating-content'}, percents)
		       )
		 ),
	    $.DIV({'Class': 'item-hint-prices'},
		  $.DIV({'Class': 'item-hint-price-buy'}, 'Price: ', $.SPAN({}, data.inventory.buy)),
		  $.DIV({'Class': 'item-hint-price-trade'}, 'Trade: ', $.SPAN({}, data.inventory.trade)),
		  $.DIV({'Class': 'item-hint-price-rent'}, 'Rent: ', $.SPAN({}, data.inventory.rent))
		 )
	   ));
    var cover_div = res.find('.item-hint-cover');
    if (cover)
      cover_div.append($.IMG({src: cover, width: 170, height: 220}));
    res.find('.item-hint-rating-content').css('width', percents);
    return res;
  },

  initDetailsHint: function () {
    function do_init(selector){
      $(selector).details_hint({}, function(){
	var element = $(this), href = element.attr('href') + 'hint-details/';
	jQuery.getJSON(href, function(data){
	  var content = Catalog.getItemHintContent(data);
	  $.details_hint.setContent(element, content);
	});
      });
    }

    do_init('#catalog-grid-content .catalog-item-cover a');
    do_init('.games-thumb-list .catalog-item a');
    do_init('#what-is-my-game-worth-page-content a.item-title');
  }
};
Catalog.init();

jQuery(document).ready(function() {
  var quickGameFinder = $('#catalog-toolbar-search input[type=text]');
  quickGameFinder
    .delayChange(function () {
      var val = $(this).val();
      if (!val) {
	$(this).blur();
	Catalog.selectFilter('new-releases');
	return;
      }
      Catalog.findGameQuickly(val);
    })
    .searchbox('Quick Game Finder');


  $('#catalog-toolbar-filter a').each(function (index) {
    $(this).parent()
      .prepend('<div class="left-decoration" />')
      .append('<div class="right-decoration" />');

    var
    href = $(this).attr('href'),
    shref = href.split('/');
    shref.reverse();
    var filter = shref.shift() || shref.shift();
    $(this)
      .attr('filterId', filter)
      .click(function () {
	Catalog.selectFilter(filter);
	return false;
      });
  });

  var anchor = window.urlRouter.anchor(window.location);
  var filters = Catalog.filters;
  for (var i = 0; i < filters.length; ++i)
  {
    window.urlRouter.add(filters[i], Catalog.selectFilter);
  }

  $('#catalog-toolbar-search form').submit(function () { return false });

  var quick_game_finder = function (anchor, params) {
    params = params || {};
    var q = params.q || false;
    var p = parseInt(params.p) || 1;
    if (q)
    {
      q = decodeURIComponent(q);
      quickGameFinder.val(q).removeClass('empty');
      Catalog.findGameQuickly(q, {p: p});
    }
    else
      Catalog.selectFilter('new-releases');
  };

  window.urlRouter
    .add('quick-game-finder', quick_game_finder)
    .startRoute();

  $('#catalog-filter-by-genre #catalog-filter-by-genre-current').attachPopup(
    '#catalog-genre-list', {
      beforeOpen: function(link, pupup) {
	link.hide();
      },
      afterClose: function(link) {
	link.show();
      }
    });

  Catalog.updatePaginatorLinks();
  Catalog.initDetailsHint();
});
